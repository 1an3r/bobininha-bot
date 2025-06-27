import discord
import os

# DESCRIPTION: Lista os comandos da Bobininha
def setup(bot):
    @bot.tree.command(name="help", description="Mostra todos os comandos disponíveis")
    async def help_command(interaction: discord.Interaction):
        embed = discord.Embed(
            title="Comandos da Bobininha:",
            description=None,
            color=0x0099ff
        )

        def load_helps():
            for filename in os.listdir("commands"):
                if filename.endswith(".py") and not filename.startswith("_"):
                    command = filename.replace(".py", "")
                    description = "Sem descrição disponível."

                    filepath = os.path.join("commands", filename)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            for line in f:
                                if line.startswith("# DESCRIPTION:"):
                                    description = line.replace("# DESCRIPTION:", "").strip()
                                    break
                    except Exception as e:
                        print(f"Erro ao ler descrição para {command}: {e}")

                    embed.add_field(
                        name=f"/{command}",
                        value=description,
                        inline=False
                    )

        load_helps()

        await interaction.response.send_message(embed=embed)