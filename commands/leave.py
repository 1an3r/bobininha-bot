import discord
from classes.Utils import Utils

# DESCRIPTION: Retira a Bobininha do recinto 🥹
def setup(bot):
    @bot.tree.command(name="leave", description="Retira a Bobininha do recinto 🥹")
    async def revoke(interaction: discord.Interaction):
        await interaction.response.send_message("Eu só queria um amigo... 🥹")

        try:
            await Utils.disconnect_from_channel(interaction)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro: {str(e)}")