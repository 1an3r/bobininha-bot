import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import importlib
from database.SQLite3 import SQLite3DB
from logging import config, getLogger
from yaml import safe_load, YAMLError

def config_loggers():
    with open('logger_config.yaml') as f:
        yaml_config = safe_load(f)
    config.dictConfig(yaml_config)


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
    SQLite3DB()

    synced = await bot.tree.sync()
    logger.info("Sincronizados %d comandos slash", len(synced))


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    print(f"Erro: {error}")

if __name__ == "__main__":
    try:
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            logger.info("❌ Token do bot não encontrado!")
            logger.info("Crie um arquivo .env com: DISCORD_TOKEN=seu_token_aqui")
            exit(1)
        config_loggers()
        bot.run(token)

    except discord.ClientException:
        logger.exception(
            "Discord Client Exception: Usually trying to play audio when audio is already playing...")

    except IndexError:
        logger.exception(
            "Index Error: Usually trying to access an index that doesn't exist inside given list")

    except FileNotFoundError as e:
        print(f"[ERROR]: {e}")

    except YAMLError as e:
        print(f"[ERROR]: {e}")

    except Exception as e:
        logger.exception(f"Erro: {e}")