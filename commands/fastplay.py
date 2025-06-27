from database.Database import Database
import asyncio
from classes.YTDLSource import YTDLSource
from classes.Utils import Utils
from discord import app_commands
import discord

# DESCRIPTION: Toca um áudio baseado em uma URL
def setup(bot):
    @bot.tree.command(name="fastplay", description="Toca um áudio baseado em uma URL")
    async def play_audio_url(interaction, url: str):
        await interaction.response.defer()

        (voice_client, voice_channel) = await Utils.connect_to_channel(interaction)

        try:
            player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)

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