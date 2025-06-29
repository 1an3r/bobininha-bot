import discord
from discord import voice_client

# View com botões
class AudioControls(discord.ui.View):
    def __init__(self, voice_client):
        super().__init__(timeout=None)
        self.voice_client = voice_client

    @discord.ui.button(label="⏸ Pause", style=discord.ButtonStyle.gray)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()

    @discord.ui.button(label="▶ Play", style=discord.ButtonStyle.green)
    async def play(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()

    @discord.ui.button(label="⏹ Stop", style=discord.ButtonStyle.red)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if self.voice_client and self.voice_client.is_paused() or self.voice_client.is_playing():
            self.voice_client.stop()