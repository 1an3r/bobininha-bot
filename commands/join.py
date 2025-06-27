import asyncio
import discord
from classes.Utils import Utils
from classes.YTDLSource import YTDLSource

# DESCRIPTION: Chama a Bobininha para a chamada
def setup(bot):
    @bot.tree.command(name="join", description="PÔ CARA, DENOVO CARAAA? 👻 ")
    async def invoke(interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            (voice_client, voice_channel) = await Utils.connect_to_channel(interaction)

            if not voice_client or not voice_channel:
                return

            player = await YTDLSource.from_url("https://www.myinstants.com/media/sounds/file_378300.mp3", loop=bot.loop, stream=True)

            voice_client.play(player, after=lambda e: print(f'Erro no player: {e}') if e else None)

            await interaction.followup.send(f"👁️🫦👁️ Po cara me chamando dnv cara")

            while voice_client.is_playing():
                await asyncio.sleep(1)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro: {str(e)}")
