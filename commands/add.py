import asyncio
import yt_dlp
from database.Databobinase import SQLiteDatabase
import aiohttp

# DESCRIPTION: Adiciona um áudio na lista de áudios
def setup(bot):
    @bot.tree.command(name="add", description="Adiciona um áudio")
    async def add(interaction, url: str, name: str):
        await interaction.response.defer()

        try:
            if name.lower() in SQLiteDatabase().get_all_names():
                await interaction.followup.send(f"❌ Já existe um áudio com o nome '{name}'. Use outro nome.")
                return

            if url in SQLiteDatabase().get_all_urls():
                await interaction.followup.send(f"❌ Já existe um áudio com este endereço, seu nome é {SQLiteDatabase().get_by_url(url)[0]}.\n\rDigite /list para ver a lista completa de áudios disponíveis 😄")
                return

            if len(name.lower()) >= 15:
                await interaction.followup.send("❌ Este nome é muito grande. Por favor mantenha a diretriz de nomes de até 15 caracteres.")
                return

            if " " in name.lower():
                await interaction.followup.send("❌ Este nome contém um espaço. Favor retirar os espaços e utilizar apenas caracteres ASCII não especiais.")
                return

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.head(url) as response:
                        if response.status != 200:
                            await interaction.followup.send("❌ URL não encontrada ou inacessível.")
                            return

                except Exception as e:
                    await interaction.followup.send(f"❌ URL inválida. Erro: {e}")
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

            SQLiteDatabase().save(name, url, interaction.user.name)

            await interaction.followup.send(f"✅ Áudio '{name}' adicionado com sucesso!")

        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao adicionar áudio: {str(e)}")