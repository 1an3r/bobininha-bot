import discord
from discord import ui, ButtonStyle
from classes.Utils import limit_str_len


class SearchResultView(ui.View):
    def __init__(self, results, interaction: discord.Interaction, callback_func):
        super().__init__(timeout=60)
        self.interaction = interaction
        self.callback_func = callback_func

        for i, entry in enumerate(results):
            button = ui.Button(
                label=limit_str_len(entry.get("title", f"Resultado {i+1}")),
                style=ButtonStyle.primary
            )
            button.callback = self.make_callback(entry["url"])
            self.add_item(button)

    def make_callback(self, url):
        async def callback(interaction: discord.Interaction):
            await interaction.response.defer()
            await self.callback_func(interaction, url)
        return callback
