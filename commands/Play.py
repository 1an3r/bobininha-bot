import asyncio
from typing import Optional

import discord
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

        SQLite3DB().append_to_queue(url, interaction.user.name)

        current_url = SQLite3DB().get_current_queue_music()

        (voice_client, voice_channel) = await Utils.connect_to_channel(interaction)

        if voice_client.is_playing():
            await interaction.followup.send("Já estou tocando algo. Vou te adicionar na fila.")
            return

        if not voice_client or not voice_channel:
            await interaction.followup.send("Das duas uma, ou você não está em um canal, ou eu não estou. Verifique, e tente novamente 🧐.")
            return

        if not current_url:
            await interaction.followup.send("Por algum motivo, não existe nada na fila ☹️, tente novamente.")
            return

        try:
            player = await YTDLSource.from_url(current_url, loop=self.bot.loop, stream=True)

            info = await YTDLSource.get_url_info(current_url, False)
            title = info.get('title', '')
            duration = info.get('duration', 0)
            voice_client.play(player)

            await interaction.followup.send(f"🎵 Tocando {title}. Duração {duration} segundos.")

            view = AudioControls(voice_client)
            embed = discord.Embed(
                title=f"🎶 Tocando agora: {info['title']}",
                url=info['webpage_url'],
                description=f"Canal: {info['uploader']}",
                color=discord.Color.blurple()
            )
            await interaction.followup.send(embed=embed, view=view)

            while voice_client.is_playing():
                await asyncio.sleep(1)

            SQLite3DB().remove_music(current_url)

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