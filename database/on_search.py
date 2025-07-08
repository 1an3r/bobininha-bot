from discord import app_commands
from database.SQLite3 import SQLite3DB
import discord
import logging

logger = logging.getLogger(__name__)


async def on_search_sound(interaction: discord.Interaction, current: str):
    try:
        all_audios = SQLite3DB().get_soundboard_db()
        suggestions = []

        if 0 < len(current) < 3:
            short_audio_titles = [
                audio.name for audio in all_audios if len(audio.name) < 5]

            suggestions = [
                audio for audio in short_audio_titles if current.lower() in audio.lower()]

        elif len(current) >= 3:
            suggestions = [
                audio.name for audio in all_audios if current.lower() in audio.name.lower()]

        return [
            app_commands.Choice(name=nome, value=nome)
            for nome in suggestions[:25]
        ]

    except Exception:
        logger.exception("Error during autocomplete:")
        return []
