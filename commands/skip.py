import discord
from classes.Utils import Utils
from commands.Play import Play
from database.SQLite3 import SQLite3DB


def setup(bot):
    @bot.tree.command(name="skip", description="Pula para a próxima música da fila 🦘.")
    async def skip(interaction: discord.Interaction):
        await interaction.response.defer()

        (voice_client, voice_channel) = await Utils.connect_to_channel(interaction)

        if not voice_client or not voice_client.is_connected():
            await interaction.followup.send("Não estou conectado a um canal de voz.")
            return

        if not voice_client.is_playing():
            await interaction.followup.send("Nada para pular.")
            return

        try:
            voice_client.stop()

            SQLite3DB().remove_current_music()
            print("Música atual removida da fila após o comando skip.")

            await Play(bot).play_next_in_queue(interaction, voice_client)

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao pular música: {str(e)}")
            print(f"Erro no comando skip: {e}")