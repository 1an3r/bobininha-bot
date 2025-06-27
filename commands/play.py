from database.Database import Database
import asyncio
from classes.YTDLSource import YTDLSource
from classes.Utils import Utils
from discord import app_commands
import discord

# DESCRIPTION: Toca um áudio da lista de áudios
def setup(bot):
    @bot.tree.command(name="play", description="Toca um áudio")
    @app_commands.describe(name="Nome do áudio")
    @app_commands.autocomplete(name=autocomplete_audios)
    async def play_audio(interaction, name: str):
        await interaction.response.defer()

        (voice_client, voice_channel) = await Utils.connect_to_channel(interaction)

        try:
            audio_name = name.lower()
            if audio_name not in Database().get_database():
                await interaction.followup.send(
                    f"❌ Áudio '{name}' não encontrado. Use `/list` para ver os áudios disponíveis.")
                return

            url = Database().get_database_by(audio_name)
            player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)

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

async def autocomplete_audios(interaction: discord.Interaction, current: str):
    try:
        all_audios = Database().get_database().keys()
        suggestions = [a for a in all_audios if current.lower() in a.lower()]
        return [
            app_commands.Choice(name=nome, value=nome)
            for nome in suggestions[:25]
        ]
    except Exception as e:
        return [e]
