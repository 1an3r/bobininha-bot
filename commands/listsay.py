from database.SQLite3 import SQLite3DB
import discord

# DESCRIPTION: Lista os áudios
def setup(bot):
    @bot.tree.command(name="listsay", description="Lista todos os áudios disponíveis")
    async def list_audios(interaction: discord.Interaction):
        await interaction.response.defer()

        if not SQLite3DB().get_soundboard_db_columns():
            await interaction.followup.send("📭 Nenhum áudio foi adicionado ainda.")
            return

        object_list = SQLite3DB().get_soundboard_db_columns()

        # Set fixed column widths to ensure alignment
        name_width = max(max(len(item["name"]) for item in object_list), len("Nome")) + 2
        user_width = max(max(len(item["user"]) for item in object_list), len("Usuário")) + 2
        date_width = len(str(object_list[0]["created_at"])) + 2  # Dates are fixed length (e.g., 2025-06-27)

        # Create table header
        header = (
            f"{'Nome':<{name_width}} {'Usuário':<{user_width}} {'Data':<{date_width}}"
        )
        separator = (
            f"{'-':-<{name_width}} {'-':-<{user_width}} {'-':-<{date_width}}"
        )

        # Create table rows, truncating long names/users if necessary
        description_list = []
        for item in object_list:
            name = item["name"][:name_width - 2] if len(item["name"]) > name_width - 2 else item["name"]
            user = item["user"][:user_width - 2] if len(item["user"]) > user_width - 2 else item["user"]
            description_list.append(
                f"{name:<{name_width}} {user:<{user_width}} {item['created_at']:<{date_width}}"
            )

        # Combine header, separator, and rows into a code block
        table = "\n".join([header, separator] + description_list)
        description = f"```plaintext\n{table}\n```"

        embed = discord.Embed(
            title="Áudios Disponíveis",
            description=description,
            color=0x00ff00
        )
        await interaction.followup.send(embed=embed)