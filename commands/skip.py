import discord
from classes.Utils import Utils
from commands.Play import Play
from database.SQLite3 import SQLite3DB


# DESCRIPTION: Chama a Bobininha para a chamada
def setup(bot):
    @bot.tree.command(name="skip", description="Pula para a próxima música da fila 🦘.")
    async def skip(interaction: discord.Interaction):
        is_skip = True
        await interaction.response.defer()

        (voice_client, voice_channel) = await Utils.connect_to_channel(interaction)

        if not voice_client.is_playing():
            await interaction.followup.send("Nada para pular.")
            return

        try:
            voice_client.stop()
            if not voice_client.is_playing() and is_skip:
                print("tudo muito doloroso. tung tung tung sahur")
                SQLite3DB().remove_current_music()

            await Play(bot).play_queue(interaction, voice_client, True)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro: {str(e)}")
            print(e)