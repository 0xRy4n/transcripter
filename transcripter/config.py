import os
import yaml

from pathlib import Path
from typing import Dict, List, Optional, Union
from dotenv import load_dotenv
from loguru import logger

from transcripter import logs  # noqa

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path, override=True)


class Config:
    def __init__(self, config_path: Optional[str] = None) -> None:
        self.REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
        self.REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
        self.REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
        self.REDIS_DB: int = int(os.getenv("REDIS_DB", 0))
        self.REDIS_INDEX: str = os.getenv("REDIS_INDEX", "video_index")
        self.YOUTUBE_API_KEY: Optional[str] = os.getenv("YOUTUBE_API_KEY")

        self.indexing_config: Dict[str, Union[Dict[str, List[str]], Dict[str, int]]] = (
            self._load_indexing_config(config_path)
        )

        logger.info(f"Loaded indexing config: {self.indexing_config}")

        self.transcript_chunk_size: int = 3  # Default to 3, but make this configurable

    def _load_indexing_config(
        self, config_path: Optional[str]
    ) -> Dict[str, Union[Dict[str, List[str]], Dict[str, int]]]:
        logger.info(f"Received config path: {config_path}")
        if config_path is None:
            default_path = Path(__file__).parent.parent / "indexing-config.yml"
            logger.info(f"Trying default path: {default_path}")
            if default_path.exists():
                config_path = str(default_path)
            else:
                logger.info("No default indexing config found, using default")
                return self._get_default_indexing_config()

        logger.info(f"Loading config from: {config_path}")
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        return self._validate_and_fill_config(config)

    def _get_default_indexing_config(
        self,
    ) -> Dict[str, Union[Dict[str, List[str]], Dict[str, int]]]:
        return {
            "sources": {"playlists": [], "channels": [], "videos": []},
            "indexing": {"interval": 3600},  # Default to 1 hour
        }

    def _validate_and_fill_config(
        self, config: Dict[str, Union[Dict[str, List[str]], Dict[str, int]]]
    ) -> Dict[str, Union[Dict[str, List[str]], Dict[str, int]]]:
        default_config = self._get_default_indexing_config()

        config.setdefault("sources", default_config["sources"])
        for source_type in default_config["sources"]:
            config["sources"].setdefault(
                source_type, default_config["sources"][source_type]
            )

        config.setdefault("indexing", default_config["indexing"])
        config["indexing"].setdefault(
            "interval", default_config["indexing"]["interval"]
        )

        return config

    def update_indexing_config(
        self,
        playlists: Optional[List[str]] = None,
        channels: Optional[List[str]] = None,
        videos: Optional[List[str]] = None,
        interval: Optional[int] = None,
    ) -> None:
        if playlists is not None:
            self.indexing_config["sources"]["playlists"] = playlists
        if channels is not None:
            self.indexing_config["sources"]["channels"] = channels
        if videos is not None:
            self.indexing_config["sources"]["videos"] = videos
        if interval is not None:
            self.indexing_config["indexing"]["interval"] = interval

    @property
    def playlists(self) -> List[str]:
        return self.indexing_config["sources"]["playlists"]

    @property
    def channels(self) -> List[str]:
        return self.indexing_config["sources"]["channels"]

    @property
    def videos(self) -> List[str]:
        return self.indexing_config["sources"]["videos"]

    @property
    def indexing_interval(self) -> int:
        return self.indexing_config["indexing"]["interval"]
