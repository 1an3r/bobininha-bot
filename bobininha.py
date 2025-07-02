import discord
from discord.ext import commands
from dotenv import load_dotenv
from database.JSONDatabase import JSONDatabase
import os
import importlib
from database.SQLite3 import SQLite3DB
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'std': {
            'format': '%(asctime)s: %(module)s in %(filename)s *%(levelname)s* %(funcName)s():%(lineno)d - %(message)s',
            'datefmt': '%b %d %H:%M:%S'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'std',
            'level': 'INFO'
        },
        'file': {
            'class': 'logging.FileHandler',
            'formatter': 'std',
            'level': 'DEBUG',
            'filename': 'bobininha.log',
            'mode': 'w',
        }
    },

    'loggers': {
            'discord': {
                'level': 'WARNING',
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'asyncio': {
                'level': 'WARNING',
                'handlers': ['console', 'file'],
                'propagate': False
            }
        },

    'root': {
        'handlers': ['console', 'file'],
        'level': 'WARNING',
    }
}

logging.config.dictConfig(LOGGING_CONFIG)

logger = logging.getLogger(__name__)

load_dotenv(".env")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='/', intents=intents)

def load_commands(bot_instance):
    for filename in os.listdir("commands"):
        if filename.endswith(".py") and not filename.startswith("_"):
            module = importlib.import_module(f"commands.{filename[:-3]}")
            if hasattr(module, "setup"):
                module.setup(bot_instance)

load_commands(bot)

@bot.event
async def on_ready():
    print(f'{bot.user} conectou ao Discord!')
    JSONDatabase()
    SQLite3DB()

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