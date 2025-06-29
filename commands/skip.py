import asyncio
import discord
from discord.types import embed

from classes.Controls import AudioControls
from classes.Utils import Utils
from classes.YTDLSource import YTDLSource
from database.SQLite3 import SQLite3DB


# DESCRIPTION: Chama a Bobininha para a chamada
def setup(bot):
    @bot.tree.command(name="skip", description="Pula para a próxima música da fila 🦘.")
    async def skip(interaction: discord.Interaction):
        await interaction.response.defer()

        (voice_client, voice_channel) = await Utils.connect_to_channel(interaction)

        if not voice_client.is_playing():
            await interaction.followup.send("Música skippada. Próxima: ")
            return

        queue_skip = SQLite3DB().get_skip()

        try:
            if queue_skip:
                voice_client.stop()

                SQLite3DB().remove_music(queue_skip[0][0])

                player = await YTDLSource.from_url(queue_skip[1][0], loop=bot.loop, stream=True)

                info = await YTDLSource.get_url_info(queue_skip[1][0], False)

                title = info.get('title', '')
                duration = info.get('duration', 0)
                voice_client.play(player)

                await interaction.followup.send(f"🎵 Tocando {title}. Duração {duration} segundos.")

                view = AudioControls(voice_client)

                embed = discord.Embed(
                    title=f"🎶 Tocando agora: {info['title']}",
                    url=info['webpage_url'],
                    description=f"Canal: {info['uploader']}",
                    color=discord.Color.blurple()
                )
                await interaction.followup.send(embed=embed, view=view)

                while voice_client.is_playing():
                    await asyncio.sleep(1)

                SQLite3DB().remove_music(queue_skip[1][0])

        except Exception as e:
            await interaction.followup.send(f"❌ Erro: {str(e)}")
            print(e)