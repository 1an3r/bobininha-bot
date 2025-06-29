import asyncio
from typing import Optional
from discord import app_commands
from discord.ext import commands
from classes.Utils import Utils
from classes.YTDLSource import YTDLSource
from database.on_search import on_search
from database.Databobinase import SQLiteDatabase

# DESCRIPTION: toca musiquinha
class Play(app_commands.Group):
    queue = []

    def __init__(self, bot):
        super().__init__(name="play", description="Toca coisinhas 😊.")
        self.bot = bot

    @app_commands.command(name="sound", description="Toca um meme 🔈.")
    @app_commands.describe(name="Nome do meme")
    @app_commands.autocomplete(name=on_search)
    async def play_sound(self, interaction, name: str):
        await interaction.response.defer()

        (voice_client, voice_channel) = await Utils.connect_to_channel(interaction)

        try:
            audio_name = name.lower()
            if audio_name not in SQLiteDatabase().get_database():
                await interaction.followup.send(
                    f"❌ Áudio '{name}' não encontrado. Use `/list` para ver os áudios disponíveis.")
                return

            url = SQLiteDatabase().get_by_name(audio_name)
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)

            if not voice_client or not voice_channel:
                return

            voice_client.play(player)

            await interaction.followup.send(f"🎵 Tocando '{name}' na sala {voice_channel.name}")

            while voice_client.is_playing():
                await asyncio.sleep(1)

        except Exception as e:
            if voice_client.is_connected():
                await voice_client.disconnect()
            await interaction.followup.send(f"❌ Erro ao reproduzir áudio: {str(e)}")

    @app_commands.command(name="music", description="Coloca uma música na fila e toca a primeira 🎶.")
    @app_commands.describe(url="Nome da música")
    async def play_music(self, interaction, url: str, noplaylist: Optional[bool]):
        await interaction.response.defer()

        self.queue.append(url)

        (voice_client, voice_channel) = await Utils.connect_to_channel(interaction)

        if voice_client.is_playing():
            await interaction.followup.send("Já estou tocando algo. Vou te adicionar na fila.")
            return

        try:
            if len(self.queue) == 0:
                await interaction.followup.send("Por algum motivo, não existe nada na fila ☹️, tente novamente.")
                return

            current_url = self.queue[0]

            player = await YTDLSource.from_url(current_url, loop=self.bot.loop, stream=True)

            if not voice_client or not voice_channel:
                await interaction.followup.send("Das duas uma, ou você não está em um canal, ou eu não estou.Verifique, e tente novamente 🧐.")
                return

            info = await YTDLSource.get_url_info(current_url, False)
            title = info.get('title', '')
            duration = info.get('duration', 0)
            voice_client.play(player)

            await interaction.followup.send(f"🎵 Tocando {title}. Duração {duration} segundos.")

            while voice_client.is_playing():
                await asyncio.sleep(1)

            self.queue.pop(0)

        except Exception as e:
            if voice_client.is_connected():
                await voice_client.disconnect()

            await interaction.followup.send(f"❌ Erro ao reproduzir áudio: {str(e)}")


    @app_commands.command(name="fast", description="Toca um meme ou música, limite: 3 minutos 😄.")
    async def play_fast(self, interaction, url: str):
        await interaction.response.defer()

        (voice_client, voice_channel) = await Utils.connect_to_channel(interaction)

        try:
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)

            if not voice_client or not voice_channel:
                return

            voice_client.play(player)

            await interaction.followup.send(f"🎵 Tocando {url}")

            while voice_client.is_playing():
                await asyncio.sleep(1)

        except Exception as e:
            if voice_client.is_connected():
                await voice_client.disconnect()
            await interaction.followup.send(f"❌ Erro ao reproduzir áudio: {str(e)}")

def setup(bot: commands.Bot):
    bot.tree.add_command(Play(bot))