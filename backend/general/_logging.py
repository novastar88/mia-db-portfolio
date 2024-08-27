from loguru import logger
import sys
from utilities import main as utilities

config = utilities.config_reader()
logging_config = config["logging"]

file = {"sink": "C:\\Users\\Mateusz\\PycharmProjects\\zdania_mia_db-v3\\backend\\logs\\log.log",
        "format": logging_config["format_file"], "level": logging_config["level_file"], "rotation": "1 day", "retention": "1 week"}
console = {"sink": sys.stderr, "format": logging_config["format_console"],
           "colorize": True, "level": logging_config["level_console"]}


logger.configure(handlers=[file, console])
