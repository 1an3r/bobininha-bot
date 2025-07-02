import asyncio
import traceback

import aiohttp
import discord
from discord import app_commands
from classes.Utils import Utils, limit_str_len
from classes.YTDLSource import YTDLSource
from database.SQLite3 import SQLite3DB
from database.on_search_music import on_search_queue
import logging

logger = logging.getLogger(__name__ + "Logger")
logger.setLevel(logging.DEBUG)

# DESCRIPTION: Grupo de comandos Music. Music play: \nToca uma música ou coloca na fila. Music skip: Pula uma música.
class Music(app_commands.Group):
    def __init__(self, bot):
        super().__init__(name="music", description="Toca coisinhas 😊.")
        self.bot = bot
        self.logger = logger

    @app_commands.command(name="play", description="Toca uma música ou playlist 🎶.")
    async def play(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            queue = SQLite3DB().get_queue()
            queue_size = SQLite3DB().count_queue()
            self.logger.debug(f"Queue: {queue}; Queue size: {queue_size}", queue, queue_size)

            if not queue or queue_size == 0:
                await interaction.followup.send("Fila vazia.")
                SQLite3DB().debugging_queue()
                return

            (voice_client, voice_channel) = await Utils.connect_to_channel(interaction)

            if not voice_client.is_playing():
                await self.play_next(interaction, voice_client)

        except discord.ClientException:
            await interaction.followup.send("Falhei em uma operação do cliente do Discord...")
            self.logger.exception("Failed during Discord client operation.")
            return

        except IndexError:
            await interaction.followup.send("Erro de indexação...")
            self.logger.exception("Index error handling queue.")
            return

        except Exception as error:
            await interaction.followup.send(f"Erro inesperado: {error}.")
            self.logger.exception("Failed due to unexpected error.")
            return

    @app_commands.command(name="skip", description="Pula para a próxima música da fila. 🦘.")
    async def skip(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            (voice_client, voice_channel) = await Utils.connect_to_channel(interaction)

            if not voice_client.is_playing() and not voice_client.is_paused():
                await interaction.followup.send("Não tem nada tocando, você não quis dizer /music play?")
                return

            queue = SQLite3DB().get_queue()
            queue_size = SQLite3DB().count_queue()
            skipped_music = queue[0]
            self.logger.debug(f"Queue: {queue}; Queue size: {queue_size}; Skipped Music: {skipped_music};")

            SQLite3DB().set_played(skipped_music.id)
            queue = SQLite3DB().get_queue()
            next_song = queue[0]
            self.logger.debug(f"Queue: {queue}; Next Song: {next_song};")

            if not queue or queue_size == 0:
                await interaction.followup.send("Fila vazia.")
                return
            else:
                await interaction.followup.send(f"Pulando a música: {skipped_music.title}.")
                voice_client.stop()
                self._on_music_finish(interaction, voice_client, next_song)

        except discord.ClientException:
            await interaction.followup.send("Falhei em uma operação do cliente do Discord...")
            self.logger.exception("Failed during Discord client operation.")
            return

        except IndexError:
            await interaction.followup.send("Erro de indexação...")
            self.logger.exception("Failed due to index error handling queue.")
            return

        except Exception as error:
            await interaction.followup.send(f"Erro inesperado: {error}.")
            self.logger.exception("Failed due to unexpected error.")
            return

    @app_commands.command(name="queue", description="Mostra a fila de músicas 🎶.")
    async def view_queue(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            queue = SQLite3DB().get_queue()
            queue_size =SQLite3DB().count_queue()

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

        except Exception as error:
            await interaction.followup.send(f"Erro inesperado: {error}.")
            self.logger.exception("Failed due to unexpected error.")
            return

    @app_commands.command(name="add", description="Adiciona música na fila 🎶.")
    @app_commands.describe(url="URL da música")
    async def add(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()

        async with aiohttp.ClientSession() as session:
            try:
                async with session.head(url) as response:
                    if response.status != 200:
                        await interaction.followup.send("❌ URL não encontrada ou inacessível.")
                        return

                    data = await YTDLSource.from_url(url)
                    logger.debug(f"data object from url provided: {data}.")

            except Exception as error:
                await interaction.followup.send(f"Erro inesperado: {error}.")
                self.logger.exception("Failed due to unexpected error.")
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


    async def play_next(self, interaction: discord.Interaction, voice_client: discord.VoiceClient):
        queue = SQLite3DB().get_queue()
        queue_size =SQLite3DB().count_queue()
        logger.debug(f"Queue: {queue}; Queue_size: {queue_size};")

        if not queue or queue_size == 0:
            await interaction.followup.send(f"Acabou a fila!")
            logger.debug(f"Queue: {queue};")
            return

        try:
            song = queue[0]
            logger.debug(f"Song: {song}.")
            player = await YTDLSource.from_url(song.url, loop=self.bot.loop, stream=True)
            logger.debug(f"Player source: {player.data};")

            if not voice_client.is_playing():
                voice_client.play(player, after=self._on_music_finish(interaction, voice_client, song))
                await interaction.followup.send(f"Tocando agora: {song.title}.")
                logger.debug(f"Playing now: {song.title}; VoiceClient state: {voice_client.is_playing()}.")
            else:
                logger.debug(f"Returned inside if statement at play_next.")
                return

        except discord.ClientException:
            await interaction.followup.send("Falhei em uma operação do cliente do Discord...")
            logger.exception("Failed during Discord client operation.")

        except IndexError:
            await interaction.followup.send("Erro de indexação.")
            logger.exception("Failed due to index error.")
            return

        except Exception as error:
            await interaction.followup.send(f"Erro inesperado: {error}")
            self.logger.exception("Failed due to unexpected error.")
            return

    def _on_music_finish(self, interaction, voice_client, song):
        logger.debug(f"Song call _on_music_finish: {song}.")
        SQLite3DB().set_played(song.id)

        asyncio.run_coroutine_threadsafe(self.play_next(interaction, voice_client), loop=self.bot.loop)

def setup(bot):
    bot.tree.add_command(Music(bot))