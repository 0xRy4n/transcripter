from loguru import logger
from transcripter.core import RedisManager, YouTubeManager
from transcripter.config import Config
from itertools import zip_longest
from typing import List, Dict, Union, Optional, Any


class IndexingService:
    """
    Service for indexing YouTube videos and their transcripts into Redis.

    Attributes:
        config (Config): Configuration object containing settings.
        youtube_manager (YouTubeManager): Manager for interacting with YouTube API.
        redis_manager (RedisManager): Manager for interacting with Redis.
    """

    def __init__(self, config: Config) -> None:
        """
        Initializes the IndexingService with the given configuration.

        Args:
            config (Config): Configuration object containing settings.
        """
        self.config: Config = config
        self.youtube_manager: YouTubeManager = YouTubeManager(self.config)
        self.redis_manager: RedisManager = RedisManager(self.config)
        logger.info("IndexingService initialized")
        self._ensure_connection()

    def _ensure_connection(self) -> None:
        """
        Ensures a connection to the Redis server.
        """
        self.redis_manager.ensure_connection()

    def index_all(self) -> List[Dict[str, Union[List[str], Dict[str, List[str]]]]]:
        """
        Indexes all configured playlists, channels, and videos.

        Returns:
            List[Dict[str, Union[List[str], Dict[str, List[str]]]]]: A list of dictionaries containing indexed and newly indexed video IDs.
        """
        logger.info("Starting index_all")
        results: List[Dict[str, Union[List[str], Dict[str, List[str]]]]] = []

        results.extend(
            self._index_entities(
                self.config.playlists, self._index_playlist, "playlists"
            )
        )
        results.extend(
            self._index_entities(self.config.channels, self._index_channel, "channels")
        )
        results.extend(
            self._index_entities(self.config.videos, self._index_video, "videos")
        )

        return results

    def _index_entities(
        self, entities: Optional[List[str]], index_method: Any, entity_type: str
    ) -> List[Dict[str, Union[List[str], Dict[str, List[str]]]]]:
        """
        Indexes a list of entities (playlists, channels, or videos) using the provided index method.

        Args:
            entities (Optional[List[str]]): List of entity IDs to index.
            index_method (Any): Method to use for indexing the entities.
            entity_type (str): Type of entities being indexed (e.g., "playlists", "channels", "videos").

        Returns:
            List[Dict[str, Union[List[str], Dict[str, List[str]]]]]: A list of dictionaries containing indexed and newly indexed video IDs.
        """
        if entities:
            return [index_method(entity_id) for entity_id in entities]
        else:
            logger.info(f"No {entity_type} configured for indexing")
            return []

    def _index_playlist(
        self, playlist_id: str
    ) -> Dict[str, Union[List[str], Dict[str, List[str]]]]:
        """
        Indexes all videos in a given playlist.

        Args:
            playlist_id (str): The ID of the playlist to index.

        Returns:
            Dict[str, Union[List[str], Dict[str, List[str]]]]: A dictionary containing indexed and newly indexed video IDs.
        """
        logger.info(f"Indexing playlist: {playlist_id}")
        video_details: Dict[str, Dict[str, Union[str, int]]] = (
            self.youtube_manager.get_all_video_details_from_playlist(playlist_id)
        )
        logger.info(
            f"Retrieved {len(video_details)} videos from playlist {playlist_id}"
        )
        return self._index_videos(video_details)

    def _index_channel(
        self, channel_id: str
    ) -> Dict[str, Union[List[str], Dict[str, List[str]]]]:
        """
        Indexes all videos in a given channel.

        Args:
            channel_id (str): The ID of the channel to index.

        Returns:
            Dict[str, Union[List[str], Dict[str, List[str]]]]: A dictionary containing indexed and newly indexed video IDs.
        """
        logger.info(f"Indexing channel: {channel_id}")
        video_details: Dict[str, Dict[str, Union[str, int]]] = (
            self.youtube_manager.get_all_video_details_from_channel(channel_id)
        )
        return self._index_videos(video_details)

    def _index_video(
        self, video_id: str
    ) -> Dict[str, Union[List[str], Dict[str, List[str]]]]:
        """
        Indexes a single video.

        Args:
            video_id (str): The ID of the video to index.

        Returns:
            Dict[str, Union[List[str], Dict[str, List[str]]]]: A dictionary containing indexed and newly indexed video IDs.
        """
        logger.info(f"Indexing video: {video_id}")
        video_details: Dict[str, Union[str, int]] = (
            self.youtube_manager.get_video_details(video_id)
        )
        return self._index_videos({video_id: video_details})

    def _index_videos(
        self, video_details: Dict[str, Dict[str, Union[str, int]]]
    ) -> Dict[str, Union[List[str], Dict[str, List[str]]]]:
        """
        Indexes a collection of videos.

        Args:
            video_details (Dict[str, Dict[str, Union[str, int]]]): A dictionary containing video details.

        Returns:
            Dict[str, Union[List[str], Dict[str, List[str]]]]: A dictionary containing indexed and newly indexed video IDs.
        """
        indexed: List[str] = []
        newly_indexed: List[str] = []

        for video_id, details in video_details.items():
            try:
                logger.debug(f"Processing video: {video_id}")
                if not self.redis_manager.document_exists(video_id):
                    transcript: Optional[List[Dict[str, Union[str, float]]]] = (
                        self.youtube_manager.get_transcript_details_from_video(video_id)
                    )
                    if transcript:
                        self._process_transcript(video_id, details, transcript)
                        newly_indexed.append(video_id)
                        logger.info(f"Indexed video {video_id}")
                    else:
                        logger.warning(f"No transcript available for video {video_id}")
                else:
                    logger.info(f"Video {video_id} already indexed")
                indexed.append(video_id)
            except Exception as e:
                logger.error(f"Error indexing video {video_id}: {str(e)}")

        logger.info(
            f"Indexing complete. Total indexed: {len(indexed)}, Newly indexed: {len(newly_indexed)}"
        )
        logger.debug(f"Indexed videos: {indexed}")
        logger.debug(f"Newly indexed videos: {newly_indexed}")
        return {"indexed": indexed, "newly_indexed": newly_indexed}

    def _process_transcript(
        self,
        video_id: str,
        details: Dict[str, Union[str, int]],
        transcript: List[Dict[str, Union[str, float]]],
    ) -> None:
        """
        Processes and indexes the transcript of a video.

        Args:
            video_id (str): The ID of the video.
            details (Dict[str, Union[str, int]]): Details of the video.
            transcript (List[Dict[str, Union[str, float]]]): Transcript of the video.
        """
        chunk_size: int = self.config.transcript_chunk_size
        grouped_transcript: List[List[Dict[str, Union[str, float]]]] = list(
            zip_longest(*[iter(transcript)] * chunk_size, fillvalue=None)
        )

        for i, group in enumerate(grouped_transcript):
            group = [
                chunk for chunk in group if chunk is not None
            ]  # Remove None values
            merged_text: str = " ".join(chunk["text"] for chunk in group)
            start_time: float = group[0]["start"]

            self.redis_manager.add_document(
                f"doc:{video_id}_{i}",
                text=merged_text,
                video_id=video_id,
                video_title=details["title"],
                video_publish_date=details["publish_date"],
                start_time=start_time,
                timecode=self._format_timecode(start_time),
            )

    def _format_timecode(self, seconds: float) -> str:
        """
        Formats a time in seconds into a timecode string (HH:MM:SS).

        Args:
            seconds (float): Time in seconds.

        Returns:
            str: Formatted timecode string.
        """
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def get_all_documents(
        self,
    ) -> Dict[str, Union[int, List[Dict[str, Union[str, Dict[str, str]]]]]]:
        """
        Retrieves all documents from Redis.

        Returns:
            Dict[str, Union[int, List[Dict[str, Union[str, Dict[str, str]]]]]]: A dictionary containing total keys and a sample of documents.
        """
        return self.redis_manager.get_all_documents()
