import discord
from database.Database import Database

# DESCRIPTION: Procura um áudio na lista de áudios (e retorna os resultados mais próximos)
def setup(bot):
    @bot.tree.command(name="search", description="Procura áudios pelo nome")
    async def search_audio_command(interaction: discord.Interaction, keyword: str):
        results = search_audio(keyword)
    
        if not results:
            await interaction.response.send_message("🔍 Nenhum áudio encontrado.")
            return
    
        formatted_result = "\n".join([f"• {k}" for k in results])
        embed = discord.Embed(title="Resultados da busca", description=formatted_result, color=0x00ffcc)
        await interaction.response.send_message(embed=embed)

    def search_audio(keyword: str) -> dict:
        keyword = keyword.lower()
        return {k: v for k, v in Database().get_database().items() if keyword in k.lower()}