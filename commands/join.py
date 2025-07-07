import asyncio
import discord
from classes.Utils import Utils
from classes.YTDLSource import YTDLSource
import logging

logger = logging.getLogger(__name__)

# DESCRIPTION: Chama a Bobininha para a chamada
def setup(bot):
    @bot.tree.command(name="join", description="PÔ CARA, DENOVO CARAAA? 👻 ")
    async def invoke(interaction: discord.Interaction):
        try:
            (voice_client, voice_channel) = await Utils.connect_to_channel(interaction)

            if not voice_client or not voice_channel:
                return

            player = await YTDLSource.from_url("https://www.youtube.com/watch?v=YLM2miAsYik", loop=bot.loop, stream=True)

            voice_client.play(player)

            voice_channel.send(f"👁️🫦👁️ Pô cara me chamando denovo cara??")

            while voice_client.is_playing():
                await asyncio.sleep(1)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro: {str(e)}")
