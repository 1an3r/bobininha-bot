import discord
from discord.ext import commands
import asyncio
import aiohttp
import os
import json
from typing import Dict, Optional
import yt_dlp

# Configurações do bot
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='/', intents=intents)

# Dicionário para armazenar os áudios adicionados
audio_database: Dict[str, str] = {}

# Arquivo para persistir os áudios
AUDIO_DB_FILE = "audio_database.json"

# Configurações do yt-dlp
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
            # Pega o primeiro item se for uma playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


def load_audio_database():
    """Carrega o banco de dados de áudios do arquivo JSON"""
    global audio_database
    try:
        if os.path.exists(AUDIO_DB_FILE):
            with open(AUDIO_DB_FILE, 'r', encoding='utf-8') as f:
                audio_database = json.load(f)
    except Exception as e:
        print(f"Erro ao carregar banco de dados de áudio: {e}")
        audio_database = {}


def save_audio_database():
    """Salva o banco de dados de áudios no arquivo JSON"""
    try:
        with open(AUDIO_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(audio_database, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erro ao salvar banco de dados de áudio: {e}")


@bot.event
async def on_ready():
    """Evento quando o bot está pronto"""
    print(f'{bot.user} conectou ao Discord!')
    load_audio_database()

    # Sincroniza os comandos slash
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos slash")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")


@bot.tree.command(name="add", description="Adiciona um áudio ao bot")
async def add_audio(interaction: discord.Interaction, url: str, nome: str):
    """Comando para adicionar um áudio"""
    await interaction.response.defer()

    try:
        # Verifica se o nome já existe
        if nome.lower() in audio_database:
            await interaction.followup.send(f"❌ Já existe um áudio com o nome '{nome}'. Use outro nome.")
            return

        # Verifica se a URL é válida
        async with aiohttp.ClientSession() as session:
            try:
                async with session.head(url) as response:
                    if response.status != 200:
                        await interaction.followup.send("❌ URL não encontrada ou inacessível.")
                        return
            except Exception:
                await interaction.followup.send("❌ URL inválida.")
                return

        # Adiciona ao banco de dados
        audio_database[nome.lower()] = url
        save_audio_database()

        await interaction.followup.send(f"✅ Áudio '{nome}' adicionado com sucesso!")

    except Exception as e:
        await interaction.followup.send(f"❌ Erro ao adicionar áudio: {str(e)}")


@bot.tree.command(name="play", description="Toca um áudio na sua sala de voz")
async def play_audio(interaction: discord.Interaction, nome: str):
    """Comando para tocar um áudio"""
    await interaction.response.defer()

    try:
        # Verifica se o usuário está em uma sala de voz
        if not interaction.user.voice:
            await interaction.followup.send("❌ Você precisa estar em uma sala de voz para usar este comando!")
            return

        # Verifica se o áudio existe
        audio_name = nome.lower()
        if audio_name not in audio_database:
            await interaction.followup.send(
                f"❌ Áudio '{nome}' não encontrado. Use `/list` para ver os áudios disponíveis.")
            return

        # Conecta à sala de voz
        voice_channel = interaction.user.voice.channel
        voice_client = await voice_channel.connect()

        try:
            # Prepara o áudio
            url = audio_database[audio_name]
            player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)

            # Toca o áudio
            voice_client.play(player, after=lambda e: print(f'Erro no player: {e}') if e else None)

            await interaction.followup.send(f"🎵 Tocando '{nome}' na sala {voice_channel.name}")

            # Espera o áudio terminar
            while voice_client.is_playing():
                await asyncio.sleep(1)

            # Desconecta da sala
            await voice_client.disconnect()

        except Exception as e:
            if voice_client.is_connected():
                await voice_client.disconnect()
            await interaction.followup.send(f"❌ Erro ao reproduzir áudio: {str(e)}")

    except Exception as e:
        await interaction.followup.send(f"❌ Erro: {str(e)}")


@bot.tree.command(name="list", description="Lista todos os áudios disponíveis")
async def list_audios(interaction: discord.Interaction):
    """Comando para listar todos os áudios"""
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
    """Comando para remover um áudio"""
    audio_name = nome.lower()

    if audio_name not in audio_database:
        await interaction.response.send_message(f"❌ Áudio '{nome}' não encontrado.")
        return

    del audio_database[audio_name]
    save_audio_database()

    await interaction.response.send_message(f"✅ Áudio '{nome}' removido com sucesso!")


@bot.tree.command(name="stop", description="Para a reprodução e sai da sala de voz")
async def stop_audio(interaction: discord.Interaction):
    """Comando para parar a reprodução"""
    voice_client = interaction.guild.voice_client

    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        await interaction.response.send_message("⏹️ Reprodução parada e saí da sala de voz.")
    else:
        await interaction.response.send_message("❌ Não estou tocando nada no momento.")


@bot.tree.command(name="help", description="Mostra todos os comandos disponíveis")
async def help_command(interaction: discord.Interaction):
    """Comando de ajuda"""
    embed = discord.Embed(
        title="🤖 Comandos do Bot de Áudio",
        description="Aqui estão todos os comandos disponíveis:",
        color=0x0099ff
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


# Tratamento de erros
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    print(f"Erro: {error}")


if __name__ == "__main__":
    # Carrega o token do arquivo .env ou variável de ambiente
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ Token do bot não encontrado!")
        print("Crie um arquivo .env com: DISCORD_TOKEN=seu_token_aqui")
        exit(1)

    bot.run(token)
