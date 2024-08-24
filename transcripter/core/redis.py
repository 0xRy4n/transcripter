from redis import Redis
from redisearch import Client, TextField, NumericField, Query
from redis.exceptions import ResponseError
from transcripter.settings import logger
from transcripter.settings import (
    REDIS_HOST,
    REDIS_PORT,
    REDIS_INDEX,
)


redis_search = Client(REDIS_INDEX, host=REDIS_HOST, port=REDIS_PORT)
redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT)

# Create an index with fields for text and timecode
try:
    redis_search.create_index(
        [
            TextField("text"),
            TextField("video_id"),
            TextField("video_title"),
            TextField("video_publish_date"),
            NumericField("timecode"),
        ]
    )
except ResponseError:
    pass  # assume index already exists


def document_exists(client, document_id):
    """Check if a document with the given ID exists."""
    query = Query(f"@video_id:{document_id.split(':')[0]}").paging(0, 1)
    results = client.search(query)
    return any(doc.id == document_id for doc in results.docs)


def get_unique_video_ids():
    unique_prefixes = set()  # Use a Python set for uniqueness
    cursor = 0

    while True:
        cursor, keys = redis_client.scan(cursor=cursor, match="*")
        for key in keys:
            # Extract the prefix before the ':'
            prefix = key.decode("utf-8").split(":")[0]
            # Add the prefix to the set
            unique_prefixes.add(prefix)

        if cursor == 0:
            break

    # Return the list of unique prefixes
    return list(unique_prefixes)


def add_transcript_to_redis(
    video_id: str,
    video_title: str,
    video_publish_date: str,
    transcript_list: list[dict],
) -> bool:
    try:
        # Iterate over each transcript chunk in the list
        for i, chunk in enumerate(transcript_list):
            text: str = chunk.get("text")
            timecode: float = chunk.get("start")
            publish_date: str = video_publish_date
            video_title: str = video_title
            document_id: str = f"{video_id}:{i+1}"

            # Check if the document with the specific ID already exists
            if document_exists(redis_search, document_id):
                logger.info(f"Document with ID {document_id} already exists. Skipping.")
                continue

            # Add the document to the index if it doesn't exist
            logger.info(f"Adding document with ID {document_id} to the index")
            redis_search.add_document(
                document_id,
                text=text,
                timecode=timecode,
                video_id=video_id,
                video_title=video_title,
                video_publish_date=publish_date,
            )

        return True
    except Exception as e:
        logger.error(f"Error: {e}")
        return False
