import redis
import re
from loguru import logger
from typing import Dict, List, Optional, Union
from transcripter.config import Config


class RedisManager:
    """
    Manages interactions with Redis, including connection, indexing, and document operations.

    Attributes:
        config (Config): Configuration object containing Redis settings.
        redis_client (Optional[redis.Redis]): Redis client instance.
    """

    def __init__(self, config: Config) -> None:
        """
        Initializes the RedisManager with the given configuration.

        Args:
            config (Config): Configuration object containing Redis settings.
        """
        self.config: Config = config
        self.redis_client: Optional[redis.Redis] = None
        logger.info("RedisManager initialized")

    def ensure_connection(self) -> None:
        """
        Ensures a connection to the Redis server. If not connected, establishes a new connection
        and creates the index.
        """
        if self.redis_client is None:
            self.redis_client = redis.Redis(
                host=self.config.REDIS_HOST,
                port=self.config.REDIS_PORT,
                password=self.config.REDIS_PASSWORD,
                db=self.config.REDIS_DB,
            )
            logger.info("Redis connection established")
        self._create_index()

    def _create_index(self) -> None:
        """
        Creates an index in Redis for storing documents. If the index already exists, logs a message.
        """
        try:
            self.redis_client.execute_command(
                "FT.CREATE",
                self.config.REDIS_INDEX,
                "ON",
                "HASH",
                "PREFIX",
                "1",
                "doc:",
                "SCHEMA",
                "text",
                "TEXT",
                "WEIGHT",
                "5.0",
                "video_id",
                "TAG",
                "video_title",
                "TEXT",
                "WEIGHT",
                "2.0",
                "video_publish_date",
                "TEXT",
                "start_time",
                "NUMERIC",
                "SORTABLE",
                "timecode",
                "TEXT",
            )
            logger.info("Redis index created successfully")
        except redis.exceptions.ResponseError as e:
            if "Index already exists" in str(e):
                logger.info("Redis index already exists")
            else:
                logger.error(f"Error creating Redis index: {str(e)}")
                raise

    def add_document(self, doc_id: str, **fields: Union[str, int, float]) -> None:
        """
        Adds a document to Redis.

        Args:
            doc_id (str): The ID of the document.
            **fields (Union[str, int, float]): The fields of the document.
        """
        logger.debug(f"Adding document: {doc_id}")
        fields = {k: str(v) for k, v in fields.items()}
        self.redis_client.hset(f"doc:{doc_id}", mapping=fields)

    def search(self, query_string: str) -> Dict[str, Union[int, List[Dict[str, str]]]]:
        """
        Searches for documents in Redis based on the query string.

        Args:
            query_string (str): The query string to search for.

        Returns:
            Dict[str, Union[int, List[Dict[str, str]]]]: The search results, including total count and documents.
        """
        logger.debug(f"Searching with query: {query_string}")
        try:
            query = f"(@text:{query_string}) | (@video_title:{query_string})"
            result = self.redis_client.execute_command(
                "FT.SEARCH", self.config.REDIS_INDEX, query, "LIMIT", 0, 1000
            )
            logger.debug(f"Raw search result: {result}")
            return self._parse_search_result(result)
        except Exception as e:
            logger.error(f"Error during Redis search: {str(e)}")
            return {"total": 0, "docs": []}

    def _parse_search_result(
        self, result: List[Union[int, List[bytes]]]
    ) -> Dict[str, Union[int, List[Dict[str, str]]]]:
        """
        Parses the raw search result from Redis.

        Args:
            result (List[Union[int, List[bytes]]]): The raw search result.

        Returns:
            Dict[str, Union[int, List[Dict[str, str]]]]: The parsed search result, including total count and documents.
        """
        if not result or len(result) < 1:
            logger.warning("Empty search result from Redis")
            return {"total": 0, "docs": []}

        total_results = result[0]
        documents = [
            {
                k.decode(): v.decode()
                for k, v in zip(result[i + 1][::2], result[i + 1][1::2])
            }
            for i in range(1, len(result), 2)
        ]

        logger.debug(f"Parsed {len(documents)} documents from search result")
        return {"total": total_results, "docs": documents}

    def get_raw_sample(self) -> List[Dict[str, Dict[str, str]]]:
        """
        Retrieves a sample of raw documents from Redis.

        Returns:
            List[Dict[str, Dict[str, str]]]: A list of dictionaries containing document keys and their fields.
        """
        keys = self.redis_client.keys("doc:*")
        sample = [
            {
                key.decode(): {
                    k.decode(): v.decode()
                    for k, v in self.redis_client.hgetall(key).items()
                }
            }
            for key in keys[:5]
        ]
        return sample

    def get_all_indexed_video_ids(self) -> List[str]:
        """
        Retrieves all indexed video IDs from Redis.

        Returns:
            List[str]: A list of indexed video IDs.
        """
        keys = self.redis_client.keys("doc:*")
        video_ids = {
            re.match(r"^(.*)_(?!.*_)", key.decode().split(":")[1]).group(1)
            for key in keys
            if len(key.decode().split(":")) > 1
        }
        return list(video_ids)

    def get_partially_indexed_videos(
        self,
    ) -> Dict[str, Dict[str, Union[int, List[str]]]]:
        """
        Retrieves information about partially indexed videos from Redis.

        Returns:
            Dict[str, Dict[str, Union[int, List[str]]]]: A dictionary containing video IDs, chunk counts, and chunks.
        """
        keys = self.redis_client.keys("doc:*")
        video_chunks = {}
        for key in keys:
            key_parts = key.decode().split(":")
            if len(key_parts) > 1:
                video_id, chunk_info = key_parts[1].split("_", 1)
                if video_id not in video_chunks:
                    video_chunks[video_id] = set()
                video_chunks[video_id].add(chunk_info)

        return {
            video_id: {
                "chunk_count": len(chunks),
                "chunks": sorted(list(chunks)),
            }
            for video_id, chunks in video_chunks.items()
        }

    def document_exists(self, doc_id: str) -> bool:
        """
        Checks if a document exists in Redis.

        Args:
            doc_id (str): The ID of the document.

        Returns:
            bool: True if the document exists, False otherwise.
        """
        exists = self.redis_client.exists(f"doc:{doc_id}")
        logger.debug(f"Document {doc_id} exists: {exists}")
        return bool(exists)

    def get_all_documents(
        self,
    ) -> Dict[str, Union[int, List[Dict[str, Union[str, Dict[str, str]]]]]]:
        """
        Retrieves all documents from Redis.

        Returns:
            Dict[str, Union[int, List[Dict[str, Union[str, Dict[str, str]]]]]]: A dictionary containing total keys and a sample of documents.
        """
        keys = self.redis_client.keys("doc:*")
        documents = [
            {
                "key": key.decode(),
                "fields": {
                    k.decode(): v.decode()
                    for k, v in self.redis_client.hgetall(key).items()
                },
            }
            for key in keys
        ]
        total_keys = len(keys)
        logger.info(
            f"Total keys: {total_keys}, Retrieved {len(documents)} documents from Redis"
        )
        return {"total_keys": total_keys, "sample": documents}

    def get_document_count(self) -> int:
        """
        Retrieves the total number of documents in Redis.

        Returns:
            int: The total number of documents.
        """
        return self.redis_client.dbsize()

    def get_index_info(self) -> Dict[str, Union[str, int, float, bool, None]]:
        """
        Retrieves information about the Redis index.

        Returns:
            Dict[str, Union[str, int, float, bool, None]]: A dictionary containing index information.
        """
        try:
            info = self.redis_client.execute_command("FT.INFO", self.config.REDIS_INDEX)
            return {
                (k.decode() if isinstance(k, bytes) else str(k)): (
                    v.decode() if isinstance(v, bytes) else v
                )
                for k, v in zip(info[::2], info[1::2])
            }
        except Exception as e:
            logger.error(f"Error getting index info: {str(e)}")
            return {}

    def check_redisearch(self) -> bool:
        """
        Checks if the RediSearch module is loaded in Redis.

        Returns:
            bool: True if the RediSearch module is loaded, False otherwise.
        """
        try:
            modules = self.redis_client.execute_command("MODULE LIST")
            logger.debug(f"Redis modules: {modules}")
            return any(module[1] == b"search" for module in modules)
        except Exception as e:
            logger.error(f"Error checking RediSearch module: {str(e)}")
            return False
