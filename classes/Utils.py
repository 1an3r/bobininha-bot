import asyncio
import discord
from classes.YTDLSource import YTDLSource


def limit_str_len(string: str, limit: int = 25):
    if (len(string) - 3) > limit:
        return string[:(limit - 3)] + "..."

    return string


class Utils:
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def connect_to_channel(interaction: discord.Interaction, timeout: float = 90.0) -> discord.VoiceClient:
        if not interaction.user.voice or not interaction.user.voice.channel:
            raise RuntimeError("Usuário não está conectado a um canal de voz.")

        voice_channel = interaction.user.voice.channel
        voice_client = interaction.guild.voice_client

        if voice_client:
            if voice_client.channel != voice_channel:
                await voice_client.move_to(voice_channel, timeout=timeout)
        else:
            voice_client = await voice_channel.connect(timeout=timeout)

        return (voice_client, voice_channel)

    async def disconnect_from_channel(interaction: discord.Interaction):
        await interaction.guild.voice_client.disconnect()

    async def player_call(self, voice_client,  url):
        player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)

        if voice_client.is_playing():
            voice_client.stop()

        voice_client.play(player)

        while voice_client.is_playing():
            await asyncio.sleep(1)
