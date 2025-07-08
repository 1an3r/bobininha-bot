import asyncio
import aiohttp
import discord
import yt_dlp
from discord import app_commands
from discord.ext import commands
from classes.Utils import Utils
from classes.YTDLSource import YTDLSource
from database.on_search import on_search_sound
from database.SQLite3 import SQLite3DB
import logging

logger = logging.getLogger(__name__)


# DESCRIPTION: Grupo de comandos Sound; Sound play: Toca um meme da base de dados; Sound add: Coloca um meme na base de dados. Sound remove: Remove um meme da base de dados; Sound list: Lista todos os memes na base de dados.
class Sound(app_commands.Group):
    def __init__(self, bot):
        super().__init__(name="sound", description="Toca memes 😊.")
        self.bot = bot

    @app_commands.command(name="play", description="Toca um meme 🔈.")
    @app_commands.describe(name="Nome do meme")
    @app_commands.autocomplete(name=on_search_sound)
    async def play(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer(thinking=False)

        (voice_client, voice_channel) = await Utils.connect_to_channel(interaction)

        if not voice_client or not voice_channel:
            return

        try:
            sound_name = name.lower()
            soundboard = SQLite3DB().get_soundboard_db()
            for item in soundboard:
                if sound_name == item.name:
                    url = item.url

            if not url:
                await voice_channel.send(
                    f"❌ Áudio '{name}' não encontrado. Use `/list` para ver os áudios disponíveis.")
                logger.warning("Sound %s not found", name)
                return

            await interaction.followup.send(f"🎵 Tocando som: {name}") a
            await Utils(self.bot).player_call(voice_client, url)

        except Exception:
            logger.exception("Unexpected error: ")
            return

    @app_commands.command(name="add", description="Adiciona um meme a base de dados ➕.")
    @app_commands.describe(name="Nome do meme", url="URL do meme")
    async def add(self, interaction: discord.Interaction, url: str, name: str):
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            voice_channel = interaction.user.voice.channel
            soundboard = SQLite3DB().get_soundboard_db()
            for item in soundboard:
                if name.lower() == item.name:
                    await voice_channel.send(f"Já existe um áudio com o nome {
                        name}. Use outro nome.")
                    return
                if url == item.url:
                    await voice_channel.send(f"Já existe um áudio com este endereço, seu nome é {
                        item.name}.\nDigite /list para ver a lista completa de áudios disponíveis 😁.")
                    return

            if len(name.lower()) >= 15:
                await voice_channel.send(
                    "❌ Este nome é muito grande. Por favor mantenha a diretriz de nomes de até 15 caracteres.")
                return

            if " " in name.lower():
                await voice_channel.send(
                    "❌ Este nome contém um espaço. Favor retirar os espaços e utilizar apenas caracteres ASCII não especiais.")
                return

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.head(url) as response:
                        if response.status != 200:
                            await voice_channel.send(
                                "❌ URL não encontrada ou inacessível.")
                            logger.error(
                                "Error: Url returned code: %d.", response.status)
                            return

                except Exception:
                    logger.exception("Unexpected error:")
                    return

            ytdl = yt_dlp.YoutubeDL(YTDLSource.ytdl_format_options)
            loop = asyncio.get_event_loop()

            try:
                info = await loop.run_in_executor(
                    None, lambda: ytdl.extract_info(url, download=False)
                )

            except yt_dlp.utils.DownloadError:
                await voice_channel.send(
                    "❌ Não foi possível processar a URL. Verifique se é um link de áudio/vídeo válido.")
                logger.error("Failed to process URL.")
                return

            duration = info.get('duration', 0)

            if duration > 120:
                await voice_channel.send(
                    f"❌ O áudio excede o limite de 2 minutos. Duração detectada: **{int(duration // 60)}m {int(duration % 60)}s**.")
                logger.error(
                    "Failed to add sound, since it exceeds duration limit.")
                return

            SQLite3DB().save_sound(name, url, interaction.user.name)

            await voice_channel.send(f"✅ Áudio '{name}' adicionado com sucesso!")

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao adicionar áudio: {str(e)}")

    @app_commands.command(name="remove", description="Remove um meme da base de dados ➖.")
    @app_commands.describe(name="Nome do meme")
    @app_commands.autocomplete(name=on_search_sound)
    async def remove_audio(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer()
        try:
            audio_name = name.lower()
            soundboard = SQLite3DB().get_soundboard_db()

            for item in soundboard:
                if audio_name == item.name:
                    SQLite3DB().remove_sound_by_name(audio_name)
                    await interaction.followup.send(f"Áudio {name} removido com sucesso!")
                    logger.info("Sound %s removed from database", audio_name)
                    return

            await interaction.followup.send(f"Não achei um áudio com esse nome, verifique os nomes com /sound list.")

        except Exception:
            logger.exception("Unexpected error:")
            return

    @app_commands.command(name="list", description="Lista os memes da base de dados 🧾.")
    async def list_audios(self, interaction: discord.Interaction):
        await interaction.response.defer()
        soundboard = SQLite3DB().get_soundboard_db()

        if len(soundboard) == 0 or soundboard is None:
            logger.info("No list present")
            await interaction.followup.send("Nenhum áudio na base de dados.")
            return

        description_list = []
        for item in soundboard:
            description_list.append(
                f"{item.name} - {item.user}"
            )

        table = "\n".join(description_list)
        description = f"```plaintext\n{table}\n```"

        embed = discord.Embed(
            title="Áudios Disponíveis",
            description=description,
            color=0x00ff00
        )
        await interaction.followup.send(embed=embed)


def setup(bot: commands.Bot):
    bot.tree.add_command(Sound(bot))
