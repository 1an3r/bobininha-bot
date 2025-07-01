import asyncio
import aiohttp
import discord
from discord import app_commands
from classes.Utils import Utils, limit_str_len
from classes.YTDLSource import YTDLSource
from classes.Controls import AudioControls
from database.SQLite3 import SQLite3DB
from database.on_search_music import on_search_queue

# DESCRIPTION: Grupo de comandos Music. Music play: \nToca uma música ou coloca na fila. Music skip: Pula uma música.
class Music(app_commands.Group):
    def __init__(self, bot):
        super().__init__(name="music", description="Toca coisinhas 😊.")
        self.bot = bot

    @app_commands.command(name="play", description="Toca uma música ou playlist 🎶.")
    async def play(self, interaction: discord.Interaction):
        await interaction.response.defer()

        queue = SQLite3DB().get_queue()

        (voice_client, voice_channel) = await Utils.connect_to_channel(interaction)

        while len(queue) != 0:
            await self.play_loop(interaction, voice_client)


    @app_commands.command(name="skip", description="Pula para a próxima música da fila. 🦘.")
    async def skip(self, interaction: discord.Interaction):
        await interaction.response.defer()

        await interaction.followup.send("Ainda estamos implementando o skip, volte mais tarde...")

    @app_commands.command(name="queue", description="Mostra a fila de músicas 🎶.")
    async def view_queue(self, interaction: discord.Interaction):
        await interaction.response.defer()

        queue = SQLite3DB().get_queue()

        if len(queue) == 0:
            await interaction.followup.send("A fila de músicas está vazia! 🎶")
            return

        embed = discord.Embed(
            title="Fila de Músicas",
            description="Aqui estão as próximas músicas na fila:",
            color=discord.Color.blue()
        )

        description_text = ""

        for i, item in enumerate(queue):
            description_text += f"{i+1} - {limit_str_len(item.title)} - User: {item.user}\n"
            if len(description_text) > 1900:
                description_text += "/n... e mais."
                break

        embed.description = description_text
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="add", description="Adiciona música na fila 🎶.")
    @app_commands.describe(url="URL da música")
    async def add(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()

        if not url:
            return

        async with aiohttp.ClientSession() as session:
            try:
                async with session.head(url) as response:
                    if response.status != 200:
                        await interaction.followup.send("❌ URL não encontrada ou inacessível.")
                        return
                    data = await YTDLSource.from_url(url)

            except Exception as e:
                await interaction.followup.send(f"❌ URL inválida. Erro: {e}")
                return

        title = str(data.title)
        username = str(interaction.user.display_name)
        SQLite3DB().append_to_queue(url, title, username)
        await interaction.followup.send(f"Adicionei a música {title} à fila com sucesso.")

    @app_commands.command(name="remove", description="Remove uma música da fila 🎶.")
    @app_commands.describe(title="Título da música")
    @app_commands.autocomplete(title=on_search_queue)
    async def remove(self, interaction: discord.Interaction, title: str):
        await interaction.response.defer()

        SQLite3DB().remove_music_by_title(title)

        await interaction.followup.send(f"Deletei a música: {title} da fila.")


    async def play_loop(self, interaction: discord.Interaction, voice_client: discord.VoiceClient):
        queue = SQLite3DB().get_queue()

        if not queue[0]:
            await interaction.followup.send("Acabou a fila.")
            return

        player = await YTDLSource.from_url(queue[0].url, loop=self.bot.loop, stream=True)
        voice_client.play(player)

        while voice_client.is_playing():
            await asyncio.sleep(1)

        SQLite3DB().set_played(queue[0].id)

def setup(bot):
    bot.tree.add_command(Music(bot))