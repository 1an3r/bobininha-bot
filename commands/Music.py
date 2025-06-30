import asyncio
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
        super().__init__(name="play", description="Toca coisinhas 😊.")
        self.bot = bot
        self.db = SQLite3DB()

    def after_song_finished(self, voice_client: discord.VoiceClient, error: Optional[Exception], interaction: discord.Interaction):
        if error:
            print(f"Player error in after_song_finished: {error}")
            return

        self.db.remove_current_music()
        print("Música anterior removida da fila após término ou interrupção.")

        asyncio.run_coroutine_threadsafe(self.play_next_in_queue(interaction, voice_client), self.bot.loop)

    async def play_next_in_queue(self, interaction: discord.Interaction, voice_client: discord.VoiceClient):
        if not voice_client or not voice_client.is_connected():
            if self.db.count_queue() > 0:
                await interaction.followup.send("Não estou conectado a um canal de voz para continuar a fila.")
            return

        if self.db.count_queue() == 0:
            await interaction.followup.send("A fila está vazia. Fim da reprodução.")

            if voice_client.is_playing():
                voice_client.stop()
            await voice_client.disconnect()
            return

        current_url = self.db.get_current_queue_music()
        if not current_url:
            await interaction.followup.send("Por algum motivo, não existe nada na fila ☹️, tente novamente.")
            return

        try:
            player = await YTDLSource.from_url(current_url, loop=self.bot.loop, stream=True)

            info = player.data
            title = info.get('title', 'Título Desconhecido')
            duration = info.get('duration', 0)
            description = info.get('uploader', 'Canal Desconhecido')
            url = info.get('webpage_url', current_url)

            view = AudioControls(voice_client)

            voice_client.play(player, after=lambda e: self.after_song_finished(voice_client, e, interaction))

            embed = discord.Embed(
                title=f"🎶 Tocando agora: {title}",
                url=url,
                description=f"Canal: {description} | duração: {duration} segundos",
                color=discord.Color.blurple()
            )

            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, view=view)
            else:
                await interaction.response.send_message(embed=embed, view=view)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao reproduzir áudio: {str(e)}")
            print(f"Erro ao reproduzir áudio em play_next_in_queue: {e}")
            if voice_client.is_connected():
                await voice_client.disconnect()

    async def play_queue(self, interaction: discord.Interaction, voice_client: discord.VoiceClient, url: str, user: str):
        self.db.append_to_queue(url, user)
        await interaction.followup.send(f"Adicionado à fila: {url}")

        if not voice_client.is_playing():
            await self.play_next_in_queue(interaction, voice_client)
        else:
            await interaction.followup.send("Música adicionada à fila e será tocada em breve.")

    @app_commands.command(name="fast", description="Toca um meme ou música, limite: 3 minutos 😄.")
    async def play_fast(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()

        (voice_client, voice_channel) = await Utils.connect_to_channel(interaction)

        if not voice_client or not voice_channel:
            return

        try:
            await Utils.player_call(voice_client, url)
            await interaction.followup.send(f"🎵 Tocando som.")

        except Exception as e:
            if voice_client.is_connected():
                await voice_client.disconnect()
            await interaction.followup.send(f"❌ Erro ao reproduzir áudio: {str(e)}")

    @app_commands.command(name="play", description="Adiciona uma música à fila ou começa a tocar se a fila estiver vazia.")
    @app_commands.describe(url="URL do YouTube ou Spotify da música.")
    async def play_music(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()

        (voice_client, voice_channel) = await Utils.connect_to_channel(interaction)

        if not voice_client or not voice_channel:
            return

        try:
            await self.play_queue(interaction, voice_client, url, str(interaction.user))

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao adicionar música à fila: {str(e)}")
            print(f"Erro em play_music: {e}")

    @app_commands.command(name="skip", description="Pula para a próxima música da fila. 🦘")
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
            print("Música atual removida da fila após o comando skip.")

            await Music(self.bot).play_next_in_queue(interaction, voice_client)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao pular música: {str(e)}")
            print(f"Erro no comando skip: {e}")

def setup(bot: commands.Bot):
    bot.tree.add_command(Music(bot))