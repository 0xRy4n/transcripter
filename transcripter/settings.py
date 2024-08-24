import os
from pathlib import Path
from typing import Union
from loguru import logger
from dotenv import load_dotenv


logger.add("/var/log/transcripter.log", format="{time} {level} {message}", level="INFO")

def get_env(var: str, default: Union[str, int], required=False) -> Union[str, int]:
    """Get environment variable or return exception"""
    try:
        return os.environ[var]
    except KeyError as e:
        if default:
            return default
        elif required:
            logger.error(f"Environment variable {var} not set")
            raise e
        else:
            return None


ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(ENV_PATH, override=True)

REDIS_HOST = get_env("REDIS_HOST", "localhost")
REDIS_PORT = get_env("REDIS_PORT", 6379)
REDIS_PASSWORD = get_env("REDIS_PASSWORD", None)
REDIS_DB = get_env("REDIS_DB", 0)
REDIS_INDEX = get_env("REDIS_INDEX", "video_index")

YOUTUBE_API_KEY = get_env("YOUTUBE_API_KEY", None)
YOUTUBE_PLAYLIST_ID = get_env("YOUTUBE_PLAYLIST_ID", None)
