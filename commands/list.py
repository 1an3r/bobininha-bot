from database.Database import Database
import discord

# DESCRIPTION: Lista os áudios
def setup(bot):
    @bot.tree.command(name="list", description="Lista todos os áudios disponíveis")
    async def list_audios(interaction: discord.Interaction):
        await interaction.response.defer()

        if not Database().get_database():
            await interaction.followup.send("📭 Nenhum áudio foi adicionado ainda.")
            return

        audio_list = Database().get_all_keys()

        embed = discord.Embed(
            title="🎵 Áudios Disponíveis",
            description=audio_list,
            color=0x00ff00
        )

        await interaction.followup.send(embed=embed)