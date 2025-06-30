import asyncio
from time import sleep
from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands
from classes.Utils import Utils
from classes.YTDLSource import YTDLSource
from classes.Controls import AudioControls
from database.SQLite3 import SQLite3DB

# DESCRIPTION: Grupo de comandos Music. Music play: Toca uma música ou coloca na fila. Music skip: Pula uma música.
class Music(app_commands.Group):
    def __init__(self, bot):
        super().__init__(name="music", description="Toca coisinhas 😊.")
        self.bot = bot

    async def after_song_finished(self, voice_client: discord.VoiceClient, error: Optional[Exception], interaction: discord.Interaction):
        try:
            if error:
                print(f"Player error in after_song_finished: {error}")
                return

            await self.bot.loop.run_in_executor(
                None,
                lambda: SQLite3DB().remove_current_music()
            )

            asyncio.run_coroutine_threadsafe(self.play_next_in_queue(interaction, voice_client), self.bot.loop)

        except Exception as e:
            print(f"Música anterior removida da fila após término ou interrupção. Erro {e}.")

    async def play_next_in_queue(self, interaction: discord.Interaction, voice_client: discord.VoiceClient):
        if not voice_client or not voice_client.is_connected():
            await interaction.followup.send("Não estou conectado a um canal...")
            return

        if not SQLite3DB().count_queue():
            await interaction.followup.send("A fila acabou...")
            return

        next_song_url = await self.bot.loop.run_in_executor(None, lambda: SQLite3DB().get_current_queue_music())

        try:
            player = await YTDLSource.from_url(next_song_url, loop=self.bot.loop, stream=True)

            voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.after_song_finished(voice_client, e, interaction), self.bot.loop))

            await interaction.followup.send(f"🎵 Tocando próxima música na fila: **{player.title}**", view=AudioControls(voice_client))

        except Exception as e:
            print(f"Erro ao tocar próxima música da fila: {e}")
            await interaction.followup.send(f"❌ Erro ao tocar próxima música da fila: {str(e)}")
            await self.bot.loop.run_in_executor(None, lambda: SQLite3DB().remove_current_music())
            await self.play_next_in_queue(interaction, voice_client)

    @app_commands.command(name="play", description="Toca uma música ou playlist 🎶.")
    @app_commands.describe(url="URL da música ou playlist")
    async def play_music(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()

        await self.bot.loop.run_in_executor(None, lambda: SQLite3DB().append_to_queue(url, str(interaction.user)))

        (voice_client, voice_channel) = await Utils.connect_to_channel(interaction)

        if not voice_client or not voice_channel:
            return

        next_song = await self.bot.loop.run_in_executor(None, lambda: SQLite3DB().get_current_queue_music())

        player = await YTDLSource.from_url(next_song, loop=self.bot.loop, stream=True)

        try:
            if not voice_client.is_playing():
                voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(
                    self.after_song_finished(voice_client, e, interaction), self.bot.loop
                ))

                await interaction.followup.send(f"🎵 Tocando: **{player.title}**",
                                                view=AudioControls(voice_client))
            else:
                await interaction.followup.send(f"🎵 Adicionado à fila: **{player.data.get('title', 'Música')}**")

        except Exception as e:
            if voice_client and voice_client.is_connected() and not voice_client.is_playing():
                await voice_client.disconnect()
            await interaction.followup.send(f"❌ Erro: {str(e)}")

    @app_commands.command(name="skip", description="Pula para a próxima música da fila. 🦘.")
    async def skip(self, interaction: discord.Interaction):
        await interaction.response.defer()

        (voice_client, voice_channel) = await Utils.connect_to_channel(interaction)

        if not voice_client or not voice_client.is_connected():
            await interaction.followup.send("Não estou conectado a um canal de voz.")
            return

        if not voice_client.is_playing():
            await interaction.followup.send("Nada para pular.")
            return

        try:
            voice_client.stop()
            SQLite3DB().remove_current_music()
            await self.play_next_in_queue(interaction, voice_client)

            await interaction.followup.send("Música pulada. Tocando a próxima na fila...")

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao pular música: {str(e)}")
            print(f"Erro em skip: {e}")

    @app_commands.command(name="queue", description="Mostra a fila de músicas 🎶.")
    async def view_queue(self, interaction: discord.Interaction):
        await interaction.response.defer()

        queue_list = await self.bot.loop.run_in_executor(None, lambda: SQLite3DB().get_queue())

        if not queue_list:
            await interaction.followup.send("A fila de músicas está vazia! 🎶")
            return

        embed = discord.Embed(
            title="Fila de Músicas",
            description="Aqui estão as próximas músicas na fila:",
            color=discord.Color.blue()
        )

        description_text = ""
        for i, item in enumerate(queue_list):
            description_text += f"{i + 1}. **{item['url']}** (Adicionado por: {item['user']})\n"
            if len(description_text) > 1900:
                description_text += "\n... e mais."
                break

        embed.description = description_text
        await interaction.followup.send(embed=embed)

def setup(bot):
    bot.tree.add_command(Music(bot))