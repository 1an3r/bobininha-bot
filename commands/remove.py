from discord import app_commands
from database.on_search import on_search
from database.Databobinase import SQLiteDatabase
import discord

# DESCRIPTION: Remove um áudio da lista de áudios
def setup(bot):
    @bot.tree.command(name="remove", description="Remove um áudio do bot")
    @app_commands.describe(name="Nome do áudio a ser removido")
    @app_commands.autocomplete(name=on_search)
    async def remove_audio(interaction: discord.Interaction, name: str):
        await interaction.response.defer()
        audio_name = name.lower()

        if audio_name not in SQLiteDatabase().get_database():
            await interaction.followup.send(f"❌ Áudio '{name}' não encontrado.")
            return

        SQLiteDatabase().remove(audio_name)

        await interaction.followup.send(f"✅ Áudio '{name}' removido com sucesso!")