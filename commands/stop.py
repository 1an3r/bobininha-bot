import discord
from classes.Utils import Utils

# DESCRIPTION: Para de tocar o que estiver tocando
def setup(bot):
    @bot.tree.command(name="stop", description="Para de tocar o que estiver tocando 🛑.")
    async def stop_audio(interaction: discord.Interaction):
        await interaction.response.send_message("Áudio atual foi parado.")
        (voice_client, voice_channel) = await Utils.connect_to_channel(interaction)

        if not voice_client:
            interaction.response("Você não está em nenhum canal de áudio.")
            return

        voice_client.stop()