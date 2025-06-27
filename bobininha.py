import discord
from discord.ext import commands
from dotenv import load_dotenv
from database.Database import Database
import os
import importlib

load_dotenv(".env")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='/', intents=intents)

async def connect_to_channel(interaction: discord.Interaction) -> discord.VoiceClient:
    if not interaction.user.voice or not interaction.user.voice.channel:
        raise RuntimeError("Usuário não está conectado a um canal de voz.")

    voice_channel = interaction.user.voice.channel
    voice_client = interaction.guild.voice_client

load_commands(bot)

@bot.event
async def on_ready():
    print(f'{bot.user} conectou ao Discord!')
    Database()

    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos slash")
    except Exception as e:
        print(f"Erro ao sincronizar comandos: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    print(f"Erro: {error}")

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ Token do bot não encontrado!")
        print("Crie um arquivo .env com: DISCORD_TOKEN=seu_token_aqui")
        exit(1)

    bot.run(token)