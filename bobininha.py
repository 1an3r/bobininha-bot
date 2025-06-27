import discord
from discord.ext import commands
import asyncio
import aiohttp
import os
import json
from typing import Dict, Optional
import yt_dlp
from dotenv import load_dotenv

load_dotenv(".env")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='/', intents=intents)

audio_database: Dict[str, str] = {}

AUDIO_DB_FILE = "audio_database.json"

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

async def connect_to_channel(interaction: discord.Interaction) -> discord.VoiceClient:
    if not interaction.user.voice or not interaction.user.voice.channel:
        raise RuntimeError("Usuário não está conectado a um canal de voz.")

    voice_channel = interaction.user.voice.channel
    voice_client = interaction.guild.voice_client

    if voice_client:
        if voice_client.channel != voice_channel:
            await voice_client.move_to(voice_channel)
    else:
        voice_client = await voice_channel.connect()

    return (voice_client, voice_channel)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

def load_audio_database():
    global audio_database
    try:
        if os.path.exists(AUDIO_DB_FILE):
            with open(AUDIO_DB_FILE, 'r', encoding='utf-8') as f:
                audio_database = json.load(f)
    except Exception as e:
        print(f"Erro ao carregar banco de dados de áudio: {e}")
        audio_database = {}

def save_audio_database():
    try:
        with open(AUDIO_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(audio_database, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erro ao salvar banco de dados de áudio: {e}")

@bot.event
async def on_ready():
    print(f'{bot.user} conectou ao Discord!')
    load_audio_database()

    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos slash")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")

@bot.tree.command(name="add", description="Adiciona um áudio ao bot")
async def add_audio(interaction: discord.Interaction, url: str, nome: str):
    await interaction.response.defer()

    try:
        if nome.lower() in audio_database:
            await interaction.followup.send(f"❌ Já existe um áudio com o nome '{nome}'. Use outro nome.")
            return

        async with aiohttp.ClientSession() as session:
            try:
                async with session.head(url) as response:
                    if response.status != 200:
                        await interaction.followup.send("❌ URL não encontrada ou inacessível.")
                        return
            except Exception:
                await interaction.followup.send("❌ URL inválida.")
                return

        audio_database[nome.lower()] = url
        save_audio_database()

        await interaction.followup.send(f"✅ Áudio '{nome}' adicionado com sucesso!")

    except Exception as e:
        await interaction.followup.send(f"❌ Erro ao adicionar áudio: {str(e)}")

@bot.tree.command(name="play", description="Toca um áudio na sua sala de voz")
async def play_audio(interaction: discord.Interaction, nome: str):
    await interaction.response.defer()

    try:
        audio_name = nome.lower()
        if audio_name not in audio_database:
            await interaction.followup.send(
                f"❌ Áudio '{nome}' não encontrado. Use `/list` para ver os áudios disponíveis.")
            return

        (voice_client, voice_channel) = await connect_to_channel(interaction)

        try:
            url = audio_database[audio_name]
            player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)

            if not voice_client:
                return

            voice_client.play(player, after=lambda e: print(f'Erro no player: {e}') if e else None)

            await interaction.followup.send(f"🎵 Tocando '{nome}' na sala {voice_channel.name}")

            while voice_client.is_playing():
                await asyncio.sleep(1)

        except Exception as e:
            if voice_client.is_connected():
                await voice_client.disconnect()
            await interaction.followup.send(f"❌ Erro ao reproduzir áudio: {str(e)}")

    except Exception as e:
        await interaction.followup.send(f"❌ Erro: {str(e)}")

@bot.tree.command(name="list", description="Lista todos os áudios disponíveis")
async def list_audios(interaction: discord.Interaction):
    if not audio_database:
        await interaction.response.send_message("📭 Nenhum áudio foi adicionado ainda.")
        return

    audio_list = "\n".join([f"• {name}" for name in audio_database.keys()])
    embed = discord.Embed(
        title="🎵 Áudios Disponíveis",
        description=audio_list,
        color=0x00ff00
    )

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="remove", description="Remove um áudio do bot")
async def remove_audio(interaction: discord.Interaction, nome: str):
    audio_name = nome.lower()

    if audio_name not in audio_database:
        await interaction.response.send_message(f"❌ Áudio '{nome}' não encontrado.")
        return

    del audio_database[audio_name]
    save_audio_database()

    await interaction.response.send_message(f"✅ Áudio '{nome}' removido com sucesso!")

@bot.tree.command(name="stop", description="Para a reprodução e sai da sala de voz")
async def stop_audio(interaction: discord.Interaction):
    await interaction.response.send_message("Áudio atual foi parado.")
    (voice_client, voice_channel) = await connect_to_channel(interaction)

    if not voice_client:
        await interaction.response("Você não está em nenhum canal de áudio.")
        return

    voice_client.stop()

@bot.tree.command(name="venha", description="PÔ CARA, DENOVO CARAAA? 👻 ")
async def invoke(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        (voice_client, voice_channel) = await connect_to_channel(interaction)

        if not voice_client:
            return

        player = await YTDLSource.from_url("https://www.myinstants.com/media/sounds/file_378300.mp3", loop=bot.loop, stream=True)

        voice_client.play(player, after=lambda e: print(f'Erro no player: {e}') if e else None)

        await interaction.followup.send(f"👁️🫦👁️ Po cara me chamando dnv cara")

        while voice_client.is_playing():
            await asyncio.sleep(1)

    except Exception as e:
        await interaction.followup.send(f"❌ Erro: {str(e)}")

@bot.tree.command(name="help", description="Mostra todos os comandos disponíveis")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Comandos do Bot de Áudio",
        description="Aqui estão todos os comandos disponíveis:",
        color=0x0099ff
    )

    embed.add_field(
        name="/venha",
        value="Bobininha começa a lhe assombrar. 👻",
        inline=False
    )

    embed.add_field(
        name="/add <url> <nome>",
        value="Adiciona um novo áudio ao bot",
        inline=False
    )

    embed.add_field(
        name="/play <nome>",
        value="Toca um áudio na sua sala de voz",
        inline=False
    )

    embed.add_field(
        name="/list",
        value="Lista todos os áudios disponíveis",
        inline=False
    )

    embed.add_field(
        name="/remove <nome>",
        value="Remove um áudio do bot",
        inline=False
    )

    embed.add_field(
        name="/stop",
        value="Para a reprodução e sai da sala de voz",
        inline=False
    )

    await interaction.response.send_message(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    print(f"Erro: {error}")

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ Token do bot não encontrado!")
        print("Crie um arquivo .env com: DISCORD_TOKEN=seu_token_aqui")
        exit(1)

    bot.run(token)