from discord import app_commands
from database.Databobinase import SQLiteDatabase
import discord


async def on_search(interaction: discord.Interaction, current: str):
    try:
        all_audios = list(SQLiteDatabase().get_database())
        suggestions = []

        if 0 < len(current) < 2:
            short_audio_names = [name for name in all_audios if len(name) < 5]

            suggestions = [s for s in short_audio_names if current.lower() in s.lower()]

        elif len(current) >= 2:
            suggestions = [a for a in all_audios if current.lower() in a.lower()]

        return [
            app_commands.Choice(name=nome, value=nome)
            for nome in suggestions[:25]
        ]

    except Exception as e:
        print(f"Error during autocomplete: {e}")
        return []
