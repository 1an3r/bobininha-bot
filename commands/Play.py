import asyncio
from typing import Optional

import discord
import yt_dlp
from discord import app_commands
from discord.ext import commands
from classes.Utils import Utils
from classes.YTDLSource import YTDLSource
from classes.Controls import AudioControls
from database.on_search import on_search
from database.SQLite3 import SQLite3DB

# DESCRIPTION: toca musiquinha
class Play(app_commands.Group):
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
            if audio_name not in SQLite3DB().get_soundboard_db():
                await interaction.followup.send(
                    f"❌ Áudio '{name}' não encontrado. Use `/list` para ver os áudios disponíveis.")
                return

            url = SQLite3DB().get_sound_by_name(audio_name)
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)

            if not voice_client or not voice_channel:
                return

            voice_client.play_queue(player)

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

        SQLite3DB().append_to_queue(url, interaction.user.name)

        (voice_client, voice_channel) = await Utils.connect_to_channel(interaction)

        if not voice_client or not voice_channel:
            await interaction.followup.send("Das duas uma, ou você não está em um canal, ou eu não estou. Verifique, e tente novamente 🧐.")
            return

        if not voice_client.is_playing():
            await self.play_queue(interaction, voice_client, False)


    @app_commands.command(name="fast", description="Toca um meme ou música, limite: 3 minutos 😄.")
    async def play_fast(self, interaction, url: str):
        await interaction.response.defer()

        (voice_client, voice_channel) = await Utils.connect_to_channel(interaction)

        try:
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)

            if not voice_client or not voice_channel:
                return

            voice_client.play_queue(player)

            await interaction.followup.send(f"🎵 Tocando {url}")

            while voice_client.is_playing():
                await asyncio.sleep(1)

        except Exception as e:
            if voice_client.is_connected():
                await voice_client.disconnect()
            await interaction.followup.send(f"❌ Erro ao reproduzir áudio: {str(e)}")

    async def play_queue(self, interaction, voice_client, is_skip = False):
        print("bobininha por favor pare")
        while True:
            print(SQLite3DB().count_queue())
            current_url = SQLite3DB().get_current_queue_music()
            if not current_url:
                await interaction.followup.send("Por algum motivo, não existe nada na fila ☹️, tente novamente.")
                return

            player = await YTDLSource.from_url(current_url, loop=self.bot.loop, stream=True)

            info = player.data
            title = info.get('title', '')
            duration = info.get('duration', 0)
            description = info.get('uploader', '')
            url = info.get('webpage_url', '')

            view = AudioControls(voice_client)

            embed = discord.Embed(
                title=f"🎶 Tocando agora: {title}",
                url=url,
                description=f"Canal: {description} | duração: {duration}",
                color=discord.Color.blurple()
            )
            await interaction.followup.send(embed=embed, view=view)

            if voice_client.is_playing():
                voice_client.stop()

            voice_client.play(player)

            while voice_client.is_playing():
                await asyncio.sleep(1)

            if not voice_client.is_playing() and is_skip == False:
                print("sung sung sung hatur, a dor sumiu")
                SQLite3DB().remove_current_music()

            if not voice_client.is_playing() and not is_skip:
                break

def setup(bot: commands.Bot):
    bot.tree.add_command(Play(bot))