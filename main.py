from transcripter.settings import YOUTUBE_PLAYLIST_ID
from transcripter.settings import logger
from transcripter.core import add_transcript_to_redis
from transcripter.core import merge_transcript_chunks
from transcripter.core import get_unique_video_ids
from transcripter.core import (
    get_all_video_details_from_playlist,
    get_transcript_details_from_video,
)
from transcripter.web import site


def main():
    # Get detailed video data from the playlist
    playlist_videos = get_all_video_details_from_playlist(YOUTUBE_PLAYLIST_ID)
    playlist_video_ids = list(playlist_videos.keys())  # Extract video IDs
    redis_video_ids = get_unique_video_ids()

    # Determine which videos are unindexed and which are already indexed
    unindexed_video_ids = list(set(playlist_video_ids) - set(redis_video_ids))
    indexed_video_ids = list(set(playlist_video_ids) - set(unindexed_video_ids))

    # Log already indexed videos with full video details
    for video_id in indexed_video_ids:
        video = playlist_videos[video_id]
        logger.info(f"Video '{video['title']}' ({video_id}) already indexed")

    # Process and index unindexed videos
    for video_id in unindexed_video_ids:
        video = playlist_videos[video_id]
        logger.info(f"Processing video '{video['title']}' ({video_id})")
        transcript = get_transcript_details_from_video(video_id)

        for _ in range(0, 2):
            transcript = merge_transcript_chunks(transcript)

        add_transcript_to_redis(
            video_id, video.get("title"), video.get("publish_date"), transcript
        )


if __name__ == "__main__":
    main()
    site.app.run(debug=True)
