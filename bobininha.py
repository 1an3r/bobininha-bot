import discord
from discord.ext import commands
from dotenv import load_dotenv
from database.JSONDatabase import JSONDatabase
import os
import importlib
from database.SQLite3 import SQLite3DB
from logging import config, getLogger
from yaml import safe_load, YAMLError


def config_loggers():
    try:
        with open('logger_config.yaml') as f:
            yaml_config = safe_load(f)
        config.dictConfig(yaml_config)

    except FileNotFoundError as e:
        print("logging file not found: %s", e)

    except YAMLError as e:
        print("Error parsing yaml configuration file: %s", e)

    except Exception as e:
        print("Unexpected error: %s", e)


logger = getLogger(__name__)

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
    logger.info('%s conectou ao Discord!', {bot.user})
    JSONDatabase()
    SQLite3DB()

    try:
        synced = await bot.tree.sync()
        logger.info("Sincronizados %d comandos slash", len(synced))
    except Exception as e:
        logger.error(f"Erro ao sincronizar comandos: {e}")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    print(f"Erro: {error}")

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.info("❌ Token do bot não encontrado!")
        logger.info("Crie um arquivo .env com: DISCORD_TOKEN=seu_token_aqui")
        exit(1)
    config_loggers()
    bot.run(token)
