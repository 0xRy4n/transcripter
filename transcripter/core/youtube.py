from youtube_transcript_api import YouTubeTranscriptApi
from pyyoutube import Api

from transcripter.settings import YOUTUBE_API_KEY
from transcripter.settings import logger


youtube_api_client = Api(api_key=YOUTUBE_API_KEY)


def get_all_video_details_from_playlist(playlist_id: str) -> dict:
    """Get all videos from a YouTube playlist"""
    playlist_items = youtube_api_client.get_playlist_items(
        playlist_id=playlist_id
    ).items

    videos = {}
    for item in playlist_items:
        videos[item.contentDetails.videoId] = {
            "title": item.snippet.title,
            "publish_date": item.snippet.publishedAt,
            "video_id": item.contentDetails.videoId,
        }

    return videos


def get_transcript_details_from_video(video_id: str) -> list[dict]:
    """Get transcript from a YouTube video"""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
    except Exception as e:
        logger.error(f"Error getting transcript for video {video_id}: {e}")
        raise e

    return transcript


def merge_transcript_chunks(chunks: list[dict]) -> list[dict]:
    merged_list = []

    for i in range(0, len(chunks) - 1, 2):
        # Merge the text keys and keep the start key from the first dict
        merged_dict = {
            "start": chunks[i]["start"],
            "text": chunks[i]["text"] + " " + chunks[i + 1]["text"],
        }
        merged_list.append(merged_dict)

    # If the list length is odd, append the last dict as is
    if len(chunks) % 2 != 0:
        merged_list.append(chunks[-1])

    return merged_list
