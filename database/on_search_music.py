from discord import app_commands
from database.SQLite3 import SQLite3DB
import discord


async def on_search_queue(interaction: discord.Interaction, cur_keyword: str):
    try:
        music_queue = SQLite3DB().get_queue()
        print(f"This is the music queue: {music_queue}")
        suggestions = []

        if 0 < len(cur_keyword) < 3:
            short_music_titles = [music.title for music in music_queue if len(music.title) < 5]

            suggestions = [music for music in short_music_titles if cur_keyword.lower() in s.lower()]

        elif len(cur_keyword) >= 3:
            suggestions = [music.title for music in music_queue if cur_keyword.lower() in music.title.lower()]

        return [
            app_commands.Choice(name=nome, value=nome)
            for nome in suggestions[:25]
        ]

    except Exception as e:
        print(f"Error during autocomplete: {e}")
        return []
