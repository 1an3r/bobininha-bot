import asyncio
import aiohttp
import discord
import yt_dlp
from discord import app_commands
from discord.ext import commands
from classes.Utils import Utils
from classes.YTDLSource import YTDLSource
from database.on_search import on_search
from database.SQLite3 import SQLite3DB

# DESCRIPTION: Grupo de comandos Sound; Sound play: Toca um meme da base de dados; Sound add: Coloca um meme na base de dados. Sound remove: Remove um meme da base de dados; Sound list: Lista todos os memes na base de dados.
class Sound(app_commands.Group):
    def __init__(self, bot):
        super().__init__(name="sound", description="Toca memes 😊.")
        self.bot = bot
        self.db = SQLite3DB()

    @app_commands.command(name="play", description="Toca um meme 🔈.")
    @app_commands.describe(name="Nome do meme")
    @app_commands.autocomplete(name=on_search)
    async def play(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer()

        (voice_client, voice_channel) = await Utils.connect_to_channel(interaction)

        if not voice_client or not voice_channel:
            return

        try:
            sound_name = name.lower()
            if sound_name not in self.db.get_soundboard_db(): # Assumed get_soundboard_db exists
                await interaction.followup.send(
                    f"❌ Áudio '{name}' não encontrado. Use `/list` para ver os áudios disponíveis.")
                return

            url = self.db.get_sound_by_name(sound_name)

            await Utils(self.bot).player_call(voice_client, url)
            await interaction.followup.send(f"🎵 Tocando som: {name}")

        except Exception as e:
            if voice_client.is_connected():
                await voice_client.disconnect()
            await interaction.followup.send(f"❌ Erro ao reproduzir áudio: {str(e)}")

    @app_commands.command(name="add", description="Adiciona um meme a base de dados ➕.")
    @app_commands.describe(name="Nome do meme", url="URL do meme")
    async def add(self, interaction: discord.Interaction, url: str, name: str):
        await interaction.response.defer()

        try:
            if name.lower() in SQLite3DB().get_all_sound_names():
                await interaction.followup.send(f"❌ Já existe um áudio com o nome '{name}'. Use outro nome.")
                return

            if url in SQLite3DB().get_all_sound_urls():
                await interaction.followup.send(
                    f"❌ Já existe um áudio com este endereço, seu nome é {SQLite3DB().get_sound_by_url(url)[0]}.\n\rDigite /list para ver a lista completa de áudios disponíveis 😄")
                return

            if len(name.lower()) >= 15:
                await interaction.followup.send(
                    "❌ Este nome é muito grande. Por favor mantenha a diretriz de nomes de até 15 caracteres.")
                return

            if " " in name.lower():
                await interaction.followup.send(
                    "❌ Este nome contém um espaço. Favor retirar os espaços e utilizar apenas caracteres ASCII não especiais.")
                return

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.head(url) as response:
                        if response.status != 200:
                            await interaction.followup.send("❌ URL não encontrada ou inacessível.")
                            return

                except Exception as e:
                    await interaction.followup.send(f"❌ URL inválida. Erro: {e}")
                    return

            ytdl = yt_dlp.YoutubeDL(YTDLSource.ytdl_format_options)
            loop = asyncio.get_event_loop()

            try:
                info = await loop.run_in_executor(
                    None, lambda: ytdl.extract_info(url, download=False)
                )

            except yt_dlp.utils.DownloadError:
                await interaction.followup.send(
                    "❌ Não foi possível processar a URL. Verifique se é um link de áudio/vídeo válido.")
                return

            duration = info.get('duration', 0)

            if duration > 120:
                await interaction.followup.send(
                    f"❌ O áudio excede o limite de 2 minutos. Duração detectada: **{int(duration // 60)}m {int(duration % 60)}s**.")
                return

            SQLite3DB().save_sound(name, url, interaction.user.name)

            await interaction.followup.send(f"✅ Áudio '{name}' adicionado com sucesso!")

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao adicionar áudio: {str(e)}")

    @app_commands.command(name="remove", description="Remove um meme da base de dados ➖.")
    @app_commands.describe(name="Nome do meme")
    @app_commands.autocomplete(name=on_search)
    async def remove_audio(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer()
        audio_name = name.lower()

        if audio_name not in SQLite3DB().get_soundboard_db():
            await interaction.followup.send(f"❌ Áudio '{name}' não encontrado.")
            return

        SQLite3DB().remove_sound(audio_name)

        await interaction.followup.send(f"✅ Áudio '{name}' removido com sucesso!")

    @app_commands.command(name="list", description="Lista os memes da base de dados 🧾.")
    async def list_audios(self, interaction: discord.Interaction):
        await interaction.response.defer()

        if not SQLite3DB().get_soundboard_db_columns():
            await interaction.followup.send("📭 Nenhum áudio foi adicionado ainda.")
            return

        object_list = SQLite3DB().get_soundboard_db_columns()

        name_width = max(max(len(item["name"]) for item in object_list), len("Nome")) + 2
        user_width = max(max(len(item["user"]) for item in object_list), len("Usuário")) + 2
        date_width = len(str(object_list[0]["created_at"])) + 2  # Dates are fixed length (e.g., 2025-06-27)

        header = (
            f"{'Nome':<{name_width}} {'Usuário':<{user_width}} {'Data':<{date_width}}"
        )
        separator = (
            f"{'-':-<{name_width}} {'-':-<{user_width}} {'-':-<{date_width}}"
        )

        description_list = []
        for item in object_list:
            name = item["name"][:name_width - 2] if len(item["name"]) > name_width - 2 else item["name"]
            user = item["user"][:user_width - 2] if len(item["user"]) > user_width - 2 else item["user"]
            description_list.append(
                f"{name:<{name_width}} {user:<{user_width}} {item['created_at']:<{date_width}}"
            )

        table = "\n".join([header, separator] + description_list)
        description = f"```plaintext\n{table}\n```"

        embed = discord.Embed(
            title="Áudios Disponíveis",
            description=description,
            color=0x00ff00
        )
        await interaction.followup.send(embed=embed)

def setup(bot: commands.Bot):
    bot.tree.add_command(Sound(bot))