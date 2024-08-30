from loguru import logger
from youtube_transcript_api import YouTubeTranscriptApi
from pyyoutube import Api
from transcripter.config import Config
from typing import Dict, List, Optional, Union


class YouTubeManager:
    """
    A class to manage interactions with the YouTube API, including fetching video details and transcripts.

    Attributes:
        config (Config): Configuration object containing API keys and other settings.
        api_client (Api): YouTube API client initialized with the provided API key.
    """

    def __init__(self, config: Config) -> None:
        """
        Initializes the YouTubeManager with the given configuration.

        Args:
            config (Config): Configuration object containing API keys and other settings.
        """
        self.config = config
        self.api_client = Api(api_key=self.config.YOUTUBE_API_KEY)
        logger.info("YouTubeManager initialized")

    def get_all_video_details_from_playlist(
        self, playlist_id: str
    ) -> Dict[str, Dict[str, Union[str, int]]]:
        """
        Fetches details of all videos in a given playlist.

        Args:
            playlist_id (str): The ID of the playlist to fetch video details from.

        Returns:
            Dict[str, Dict[str, Union[str, int]]]: A dictionary where keys are video IDs and values are dictionaries
            containing video details such as title, publish date, and video ID.
        """
        logger.info(f"Fetching video details for playlist: {playlist_id}")
        playlist_items = self.api_client.get_playlist_items(
            playlist_id=playlist_id, limit=50, count=None
        ).items
        logger.debug(f"Playlist items: {playlist_items}")
        return self._get_video_details(playlist_items)

    def get_all_video_details_from_channel(
        self, channel_id: str
    ) -> Dict[str, Dict[str, Union[str, int]]]:
        """
        Fetches details of all videos in a given channel.

        Args:
            channel_id (str): The ID of the channel to fetch video details from.

        Returns:
            Dict[str, Dict[str, Union[str, int]]]: A dictionary where keys are video IDs and values are dictionaries
            containing video details such as title, publish date, and video ID.
        """
        logger.info(f"Fetching video details for channel: {channel_id}")
        if not channel_id:
            logger.error("Channel ID is None")
            return {}
        channel_response = self.api_client.get_channel_info(channel_id=channel_id)
        if not channel_response.items:
            logger.error(f"No channel found for ID: {channel_id}")
            return {}
        channel_item = channel_response.items[0]
        if not hasattr(channel_item, "contentDetails") or not hasattr(
            channel_item.contentDetails, "relatedPlaylists"
        ):
            logger.error(f"Channel {channel_id} does not have expected content details")
            return {}
        playlist_id = channel_item.contentDetails.relatedPlaylists.uploads
        return self.get_all_video_details_from_playlist(playlist_id)

    def get_video_details(self, video_id: str) -> Dict[str, Union[str, int]]:
        """
        Fetches details of a single video.

        Args:
            video_id (str): The ID of the video to fetch details for.

        Returns:
            Dict[str, Union[str, int]]: A dictionary containing video details such as title, publish date, and video ID.
        """
        logger.info(f"Fetching video details for video: {video_id}")
        if not video_id:
            logger.error("Video ID is None")
            return {}
        video_response = self.api_client.get_video_by_id(video_id=video_id)
        video = video_response.items[0]
        return {
            "title": video.snippet.title,
            "publish_date": video.snippet.publishedAt,
            "video_id": video.id,
        }

    def _get_video_details(self, items: List) -> Dict[str, Dict[str, Union[str, int]]]:
        """
        Helper method to extract video details from a list of playlist items.

        Args:
            items (List): A list of playlist items.

        Returns:
            Dict[str, Dict[str, Union[str, int]]]: A dictionary where keys are video IDs and values are dictionaries
            containing video details such as title, publish date, and video ID.
        """
        videos = {
            item.contentDetails.videoId: {
                "title": item.snippet.title,
                "publish_date": item.snippet.publishedAt,
                "video_id": item.contentDetails.videoId,
            }
            for item in items
        }
        logger.debug(f"Fetched details for {len(videos)} videos")
        return videos

    def get_transcript_details_from_video(
        self, video_id: str
    ) -> Optional[List[Dict[str, Union[str, float]]]]:
        """
        Fetches the transcript of a given video.

        Args:
            video_id (str): The ID of the video to fetch the transcript for.

        Returns:
            Optional[List[Dict[str, Union[str, float]]]]: A list of dictionaries containing transcript details such as
            start time and text, or None if an error occurs.
        """
        logger.info(f"Fetching transcript for video: {video_id}")
        try:
            return YouTubeTranscriptApi.get_transcript(video_id)
        except Exception as e:
            logger.error(f"Error fetching transcript for video {video_id}: {str(e)}")
            return None

    @staticmethod
    def merge_transcript_chunks(
        chunks: List[Dict[str, Union[str, float]]],
    ) -> List[Dict[str, Union[str, float]]]:
        """
        Merges adjacent transcript chunks into larger chunks.

        Args:
            chunks (List[Dict[str, Union[str, float]]]): A list of dictionaries containing transcript details such as
            start time and text.

        Returns:
            List[Dict[str, Union[str, float]]]: A list of merged transcript chunks.
        """
        logger.debug(f"Merging {len(chunks)} transcript chunks")
        merged_list = [
            {
                "start": chunks[i]["start"],
                "text": chunks[i]["text"] + " " + chunks[i + 1]["text"],
            }
            for i in range(0, len(chunks) - 1, 2)
        ]
        if len(chunks) % 2 != 0:
            merged_list.append(chunks[-1])
        logger.debug(f"Merged into {len(merged_list)} chunks")
        return merged_list
