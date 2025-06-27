import discord

class Utils:
    def __init__(self, bot):
        self.bot = bot

    async def connect_to_channel(interaction: discord.Interaction) -> discord.VoiceClient:
        if not interaction.user.voice or not interaction.user.voice.channel:
            raise RuntimeError("Usuário não está conectado a um canal de voz.")

        voice_channel = interaction.user.voice.channel
        voice_client = interaction.guild.voice_client

        if voice_client:
            if voice_client.channel != voice_channel:
                await voice_client.move_to(voice_channel)
        else:
            voice_client = await voice_channel.connect()

        return (voice_client, voice_channel)