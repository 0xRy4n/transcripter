from loguru import logger
import sys
import os


def configure_logging():
    log_level = os.getenv("TRANSCRIPTER_LOG_LEVEL", "INFO")
    logger.remove()  # Remove default handler
    logger.add(sys.stderr, level="DEBUG")  # Add a handler to stderr
    logger.add(
        "logs/transcripter.log", rotation="500 MB", level=log_level
    )  # Add a file handler


configure_logging()
