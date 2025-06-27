import asyncio

import yt_dlp

from database.Database import Database
import aiohttp

# DESCRIPTION: Adiciona um áudio na lista de áudios
def setup(bot):
    @bot.tree.command(name="add", description="Adiciona um áudio")
    async def add(interaction, url: str, name: str):
        await interaction.response.defer()

        try:
            if name.lower() in Database().get_database():
                await interaction.followup.send(f"❌ Já existe um áudio com o nome '{name}'. Use outro nome.")
                return

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.head(url) as response:
                        if response.status != 200:
                            await interaction.followup.send("❌ URL não encontrada ou inacessível.")
                            return
                except Exception:
                    await interaction.followup.send("❌ URL inválida.")
                    return

            ytdl_opts = {
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True,
            }

            ytdl = yt_dlp.YoutubeDL(ytdl_opts)
            loop = asyncio.get_event_loop()

            try:
                info = await loop.run_in_executor(
                    None, lambda: ytdl.extract_info(url, download=False)
                )
            except yt_dlp.utils.DownloadError:
                await interaction.followup.send(
                    "❌ Não foi possível processar a URL. Verifique se é um link de áudio/vídeo válido.")
                return

            duration = info.get('duration', 0)

            if duration > 120:
                await interaction.followup.send(
                    f"❌ O áudio excede o limite de 2 minutos. Duração detectada: **{int(duration // 60)}m {int(duration % 60)}s**.")
                return

            Database().save(name, url)

            await interaction.followup.send(f"✅ Áudio '{name}' adicionado com sucesso!")

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao adicionar áudio: {str(e)}")