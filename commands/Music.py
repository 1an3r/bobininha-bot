import asyncio
import aiohttp
import discord
import logging

from discord import app_commands

from classes.Utils import Utils, limit_str_len
from classes.YTDLSource import YTDLSource
from classes.ButtonList import ButtonList

from database.SQLite3 import SQLite3DB
from database.on_search_music import on_search_queue

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# DESCRIPTION: Grupo de comandos Music.
class Music(app_commands.Group):
    def __init__(self, bot):
        super().__init__(name="music", description="Toca coisinhas 😊.")
        self.bot = bot

    @app_commands.command(name="play", description="Toca uma música")
    async def play(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        logger.info("/music play was called")
        try:
            queue_size = SQLite3DB().count_queue()
            if queue_size == 0:
                await interaction.followup.send("Não existe uma fila para ser tocada.")
                SQLite3DB().nuking_queue_table()
                logger.info(
                    "Nuking the queue table contents since it was called without any suitable members.")
                return

            (voice_client, voice_channel) = await Utils.connect_to_channel(interaction)
            logger.info("Voice client connected as %s in channel %s",
                        voice_client, voice_channel)

            await interaction.followup.send(f"Chamando a bobininha para tocar.")

            logger.debug("Queue size: %s", queue_size)
            await self.play_queue(voice_channel, voice_client, queue_size)

        except discord.ClientException:
            logger.exception(
                "Discord Client Exception: Usually trying to play audio when audio is already playing...")
            return

        except IndexError:
            logger.exception(
                "Index Error: Usually trying to access an index that doesn't exist inside given list")
            return

        except Exception:
            logger.exception("Exception Error: ")
            return

    @app_commands.command(name="skip", description="Pula para a próxima música da fila. 🦘.")
    async def skip(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        logger.info("/music skip was called")
        try:
            (voice_client, _) = await Utils.connect_to_channel(interaction)
            if not voice_client.is_playing() and not voice_client.is_paused():
                await interaction.followup.send("Eu não estou tocando nada...☹️")
                logger.warning("Voice client is not playing;")
                return

            voice_client.stop()

            logger.info("voice_client.stop() was called;")

        except discord.ClientException:
            logger.exception(
                "Discord Client Exception: Usually trying to play audio when audio is already playing;")
            return

        except IndexError:
            logger.exception(
                "Index Error: Usually trying to access an index that doesn't exist inside given list;")
            return

        except Exception:
            logger.exception("Exception Error: ")
            return

    async def play_next(self, voice_channel: discord.VoiceChannel, voice_client: discord.VoiceClient, song):
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

            await voice_channel.send(f"Tocando: {limit_str_len(player.data['title'], limit=80)}.")

            voice_client.play(player)

            while voice_client.is_playing():
                await asyncio.sleep(1)

            SQLite3DB().set_played(song.id)
            player.cleanup()

        except discord.ClientException:
            logger.exception(
                "Discord Client Exception: Usually trying to play audio when audio is already playing...")
            return

        except Exception:
            logger.exception("Exception Error: ")
            return

    async def play_queue(self, voice_channel: discord.VoiceChannel, voice_client: discord.VoiceClient, queue_size: int):
        logger.info("play_queue method was called: %s, %s, %s", voice_channel, voice_client, queue_size)
        while queue_size > 0:
            logger.debug("entered while loop inside play_queue")
            try:
                if not voice_client.is_playing() and not voice_client.is_paused():
                    song = SQLite3DB().get_queue()[0]
                    logger.debug(
                        "Fetched next song to play, retrieved as: %s", song)
                    await self.play_next(voice_channel, voice_client, song)
                    queue_size = SQLite3DB().count_queue()
                    logger.debug("Queue size: %s", queue_size)

            except discord.ClientException:
                logger.exception(
                    "Discord Client Exception: Usually trying to play audio when audio is already playing...")
                return

            except IndexError:
                logger.exception(
                    "Index Error: Usually trying to access an index that doesn't exist inside given list")
                return

            except Exception:
                logger.exception("Exception Error: ")
                return

        queue_size = SQLite3DB().count_queue()

        if queue_size == 0:
            SQLite3DB().nuking_queue_table()
            logger.info("Nuking queue table contents since the player ended.")
            await voice_channel.send("A música acabou, mas não fique triste. Chame /music add para colocar a próxima, /music play para eu tocar ela, e seremos felizes para sempre 😁.")
            return

    @app_commands.command(name="queue", description="Mostra a fila de músicas 🎶.")
    async def view_queue(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        logger.info("Called /music queue.")
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
                description_text += f"{i+1} - {limit_str_len(item.title)} - User: {
                    item.user}\n"
                if len(description_text) > 1900:
                    description_text += "/n... e mais."
                    break

            embed.description = description_text
            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"Erro no comando queue: {e}")


    @app_commands.command(name="add", description="Adiciona música na fila 🎶.")
    @app_commands.describe(url="URL da música ou palavra-chave")
    async def add(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer(thinking=True)

        if YTDLSource.is_url(url):
            await self.process_url(interaction, url)
        else:
            try:
                results = await YTDLSource.search_youtube(url)
                if not results:
                    await interaction.followup.send("❌ Nenhum resultado encontrado.")
                    return

                embed = discord.Embed(
                    title="🎵 Resultados da Busca",
                    description="Escolha a música clicando em um dos botões abaixo:",
                    color=discord.Color.green()
                )
                await interaction.followup.send(embed=embed, view=ButtonList(results, interaction, self.process_url))
            except Exception:
                logger.exception("Erro durante a busca por palavra-chave.")
                await interaction.followup.send("❌ Ocorreu um erro ao buscar a música.")

    @app_commands.command(name="remove", description="Remove uma música da fila 🎶.")
    @app_commands.describe(title="Título da música")
    @app_commands.autocomplete(title=on_search_queue)
    async def remove(self, interaction: discord.Interaction, title: str):
        await interaction.response.defer()

        SQLite3DB().remove_music_by_title(title)

        await interaction.followup.send(f"Deletei a música: {title} da fila.")

    @app_commands.command(name="clear", description="Limpa a fila 🧹.")
    async def clear(self, interaction: discord.Interaction):
        await interaction.response.defer()

        SQLite3DB().nuking_queue_table()

        await interaction.followup.send(f"Limpei toda a fila de músicas, espero que você saiba o que está fazendo... 😱")

    async def process_url(self, interaction: discord.Interaction, url: str):
        logger.info("callback was called with URL: %s", url)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url) as response:
                    if response.status != 200:
                        await interaction.followup.send("❌ URL não encontrada ou inacessível.")
                        return

            data = await YTDLSource.extract_info_async(url)
            #logger.warning("Data extracted from URL: %s", data)
            title = str(data["title"])
            username = str(interaction.user.display_name)
            seconds = int(data["duration"])
            formatted_time_string = f"{(seconds // 60):02d}:{(seconds % 60):02d}"
            
            logger.debug("Adding song to queue: %s by %s", title, username)
            SQLite3DB().append_to_queue(url, title, username)

            await interaction.followup.send(
                f"✅ Adicionei **{limit_str_len(title)}** - `{formatted_time_string}` à fila com sucesso."
            )

        except Exception:
            logger.exception("Erro ao processar a URL.")
            await interaction.followup.send("❌ Ocorreu um erro ao processar a música.")


def setup(bot):
    bot.tree.add_command(Music(bot))