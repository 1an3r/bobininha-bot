from database.Database import Database
import discord

# DESCRIPTION: Remove um áudio da lista de áudios
def setup(bot):
    @bot.tree.command(name="remove", description="Remove um áudio do bot")
    async def remove_audio(interaction: discord.Interaction, name: str):
        audio_name = name.lower()

        if audio_name not in Database().get_database():
            await interaction.response.send_message(f"❌ Áudio '{name}' não encontrado.")
            return

        Database().remove(audio_name)

        await interaction.response.send_message(f"✅ Áudio '{name}' removido com sucesso!")