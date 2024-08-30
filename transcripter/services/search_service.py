from loguru import logger
from transcripter.core.redis_manager import RedisManager
from transcripter.config import Config
from typing import List, Dict, Union


class SearchService:
    """
    Service for searching indexed YouTube videos and their transcripts in Redis.

    Attributes:
        config (Config): Configuration object containing settings.
        redis_manager (RedisManager): Manager for interacting with Redis.
    """

    def __init__(self, config: Config) -> None:
        """
        Initializes the SearchService with the given configuration.

        Args:
            config (Config): Configuration object containing settings.
        """
        self.config: Config = config
        self.redis_manager: RedisManager = RedisManager(self.config)
        logger.info("SearchService initialized")
        self._ensure_connection()

    def _ensure_connection(self) -> None:
        """
        Ensures a connection to the Redis server.
        """
        self.redis_manager.ensure_connection()

    def search(self, query_str: str) -> List[Dict[str, Union[str, float]]]:
        """
        Searches for documents in Redis based on the query string.

        Args:
            query_str (str): The query string to search for.

        Returns:
            List[Dict[str, Union[str, float]]]: A list of dictionaries containing search results with video details.
        """
        if not query_str:
            logger.debug("Empty search query")
            return []

        logger.info(f"Searching for: {query_str}")
        results = self.redis_manager.search(query_str)
        logger.debug(f"Raw search results: {results}")

        filtered_results: List[Dict[str, Union[str, float]]] = [
            {
                "video_id": doc.get("video_id", ""),
                "video_title": doc.get("video_title", ""),
                "snippet": doc.get("text", ""),
                "start_time": float(doc.get("start_time", 0)),
                "timecode": doc.get("timecode", "00:00:00"),
            }
            for doc in results.get("docs", [])
        ]

        logger.info(f"Found {len(filtered_results)} results for query: {query_str}")
        logger.debug(f"Filtered results: {filtered_results}")
        return filtered_results

    def get_all_indexed_video_ids(self) -> List[str]:
        """
        Retrieves all indexed video IDs from Redis.

        Returns:
            List[str]: A list of all indexed video IDs.
        """
        return self.redis_manager.get_all_indexed_video_ids()
