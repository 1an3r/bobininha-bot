import asyncio
import aiohttp
import discord
from discord import app_commands
from classes.Utils import Utils, limit_str_len
from classes.YTDLSource import YTDLSource
from classes.Controls import AudioControls
from database.SQLite3 import SQLite3DB
from database.on_search_music import on_search_queue
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# DESCRIPTION: Grupo de comandos Music. Music play: \nToca uma música ou coloca na fila. Music skip: Pula uma música.
class Music(app_commands.Group):
    def __init__(self, bot):
        super().__init__(name="music", description="Toca coisinhas 😊.")
        self.bot = bot

    @app_commands.command(name="play", description="Toca uma música ou playlist 🎶.")
    async def play(self, interaction: discord.Interaction):
        await interaction.response.defer()
        logger.info("/music play was called")
        try:
            queue_size = SQLite3DB().count_queue()

            if queue_size == 0:
                await interaction.followup.send("Não existe uma fila para ser tocada.")
                SQLite3DB().debugging_queue()
                queue_size = SQLite3DB().count_queue()

            (voice_client, voice_channel) = await Utils.connect_to_channel(interaction)
            logger.info("Voice client connected as %s in channel %s", voice_client, voice_channel)

            await interaction.followup.send(f"Chamando a bobininha para tocar.")

            logger.debug("Queue size: %s", queue_size)
            await self.play_queue(interaction, voice_client, queue_size)

        except discord.ClientException:
            logger.exception("Discord Client Exception: Usually trying to play audio when audio is already playing...")
            return

        except IndexError:
            logger.exception("Index Error: Usually trying to access an index that doesn't exist inside given list")
            return

        except Exception:
            logger.exception("Exception Error: ")
            return

    @app_commands.command(name="skip", description="Pula para a próxima música da fila. 🦘.")
    async def skip(self, interaction: discord.Interaction):
        await interaction.response.defer()
        logger.info("/music skip was called")
        try:
            (voice_client, voice_channel) = await Utils.connect_to_channel(interaction)
            if not voice_client.is_playing() and not voice_client.is_paused():
                await interaction.followup.send("Eu não estou tocando nada...☹️")
                logger.warning("Voice client is not playing;")
                return

            voice_client.stop()

            logger.info("voice_client.stop() was called;")

        except discord.ClientException:
            logger.exception("Discord Client Exception: Usually trying to play audio when audio is already playing;")
            return

        except IndexError:
            logger.exception("Index Error: Usually trying to access an index that doesn't exist inside given list;")
            return

        except Exception:
            logger.exception("Exception Error: ")
            return

    async def play_next(self, interaction: discord.Interaction, voice_client: discord.VoiceClient, song):
        logger.info("play_next method was called;")
        try:
            if not song.url:
                logger.error("url cannot be empty: %s", song.url)
                return

            if voice_client.is_playing() or voice_client.is_paused():
                logger.error("voice client is already playing")
                return

            player = await YTDLSource.from_url(song.url, loop=self.bot.loop, stream=True, noplaylist=True)

            if not player:
                logger.error("Player cannot be None: %s", player)
                return

            else:
                logger.info("Player Source set as: %s;", song.url)

            await interaction.followup.send(f"Tocando... {player.data["title"]} | {player.data["duration"]}")

            voice_client.play(player)

            while voice_client.is_playing():
                await asyncio.sleep(1)

            SQLite3DB().set_played(song.id)
            player.cleanup()

        except discord.ClientException:
            logger.exception("Discord Client Exception: Usually trying to play audio when audio is already playing...")
            return

        except Exception:
            logger.exception("Exception Error: ")
            return

    async def play_queue(self, interaction: discord.Interaction, voice_client: discord.VoiceClient, queue_size: int):
        logger.info("play_queue method was called")
        while queue_size > 0:
            logger.debug("entered while loop inside play_queue")
            try:
                if not voice_client.is_playing() and not voice_client.is_paused():
                    song = SQLite3DB().get_queue()[0]
                    logger.debug("Fetched next song to play, retrieved as: %s", song)
                    await self.play_next(interaction, voice_client, song)
                    queue_size = SQLite3DB().count_queue()
                    logger.debug("Queue size: %s", queue_size)

            except discord.ClientException:
                logger.exception("Discord Client Exception: Usually trying to play audio when audio is already playing...")
                return

            except IndexError:
                logger.exception("Index Error: Usually trying to access an index that doesn't exist inside given list")
                return

            except Exception:
                logger.exception("Exception Error: ")
                return

    @app_commands.command(name="queue", description="Mostra a fila de músicas 🎶.")
    async def view_queue(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            queue = SQLite3DB().get_queue()
            queue_size = SQLite3DB().count_queue()

            if queue_size == 0:
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

        except Exception as e:
            await interaction.followup.send(f"Erro no comando queue: {e}")

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


def setup(bot):
    bot.tree.add_command(Music(bot))