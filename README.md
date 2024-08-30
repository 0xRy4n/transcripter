
# Transcripter

<p align="center">
  <img src="https://github.com/0xry4n/transcripter/actions/workflows/housekeeping.yml/badge.svg" alt="Linting and Documentation">
  <a href="https://app.codacy.com/gh/0xRy4n/transcripter/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade">
    <img src="https://app.codacy.com/project/badge/Grade/7233dfa7498c4801bbfc024b2675b2b0" alt="Codacy Badge">
  <a href="https://opensource.org/licenses/MIT">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
  </a>
  </a>
</p>

![Transcripter](https://i.imgur.com/jg9sc7p.gif)


Transcripter is a tool for indexing and searching YouTube video transcripts. It makes use of the YouTube Data API to fetch video details and transcripts, and collates and stores the transcript chunks in Redis for efficient full-text search.

Transcripter's main purpose is to provide a simple way to add transcript-search functionality to your application. Inspired by (but unrelated to) <https://ippsec.rocks/>. 

## Structure

- `transcripter/`: Main package
  - `core/`: Core functionality
    - `redis_manager.py`: Manages Redis operations
    - `youtube_manager.py`: Handles YouTube API interactions
  - `services/`: Service layer
    - `indexing_service.py`: Manages the indexing process
    - `search_service.py`: Manages the search process
  - `config.py`: Configuration management
  - `logs.py`: Logging management
- `examples/`: Example applications
  - `basic/`: Basic example
    - `app.py`: Simple application demonstrating usage
- `index-config.yml`: Configuration file for indexing. Used by the example app.
- `docker-compose.yml`: Docker compose file for the example app.

## How It Works

1. The `IndexingService` periodically fetches video details and transcripts from configured YouTube playlists, channels, or individual videos.
2. Transcripts are processed and stored in Redis using the `RedisManager`.
3. The `YouTubeManager` handles interactions with the YouTube API.
4. Indexed data can be searched efficiently using Redis's full-text search capabilities.

## Installation

```bash
make install
```
or
```bash
pip3 install git+https://github.com/0xRy4n/transcripter
```

**Note**: Transcripter _requires_ a Redis Stack server to run. It's recommended to use the official Docker image like so:

```bash
docker run -d --name redis-stack-server -p 6379:6379 redis/redis-stack-server:latest`
```

You can run the Redis Stack either locally or remote, depending on your preference.

## Configuration

### Environment Variables

Set the following environment variables:

- `YOUTUBE_API_KEY`: Your YouTube API key
- `REDIS_HOST`: Redis server host
- `REDIS_PORT`: Redis server port
- `REDIS_PASSWORD`: Redis server password (if applicable)
- `REDIS_INDEX`: Name of the Redis index to use
- `TRANSCRIPTER_LOG_LEVEL`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### Indexing Configuration

Configure the indexing process in your application by specifying a `indexing-config.yml` file like so:

```yaml
# Change me
sources:
  playlists:
    # playlist id
    - PLlkHl5i0GaAlBvAhi9R7S4vQ0IhR3ePCU
  channels:
    - # channel id
  videos:
    - # video id

indexing:
  interval: 3600  # Reindex every hour
```

You can then pass the path to this file in to the `Config` object:

```python
config = Config(config_path='path/to/indexing-config.yml')
```
By default, it will search for a file called `indexing-config.yml` in the root directory of the repository (one directory up from the `transcripter` directory).


Alternatively, you can simply instantiate `Config` without any arguments, and set each property directly:
```python
from transcripter.config import Config

config = Config()
config.playlists = ['playlist_id1', 'playlist_id2']
config.channels = ['channel_id1', 'channel_id2']
config.videos = ['video_id1', 'video_id2']
config.indexing_interval = 3600  # Indexing interval in seconds
```

## Starting the Indexing Service

```python
from transcripter.services.indexing_service import IndexingService

indexing_service = IndexingService(config)
```
Indexing your videos is easy.
```python
indexing_service.index_all()
```
Once a video has been indexed, it will not be indexed again, and it's transcript won't be pulled on successive runs. 

You'll likely want to run the indexing service periodically as a background job. It is up to you to decide how you would like to implement this.

## Searching

You can search the indexed data using the `SearchService` class.

```python
from transcripter.services.search_service import SearchService

search_service = SearchService(config)
```

You can then search for videos by title:

```python
search_service.search('search query')
```

It will return a list of stored transcript chunks in the following format:
```json
[
  {
    "snippet": "directory don't worry about it too much it's not going to be on the test there's not going to be a test but if there were",
    "start_time": 300.56,
    "timecode": "00:05:00",
    "video_id": "_haJQY-Y70E",
    "video_title": "Linux Structure and Commands - Intro to Hacking w/ HTB Academy #4"
  },
  {
    "snippet": "directory don't worry about it too much it's not going to be on the test there's not going to be a test but if there were",
    "start_time": 300.56,
    "timecode": "00:05:00",
    "video_id": "_haJQY-Y70E",
    "video_title": "Linux Structure and Commands - Intro to Hacking w/ HTB Academy #4"
  }
]
```

## Example Web App

A fully functional example web app is included in the `examples/basic` directory. It is a simple web app that allows you to search for videos by title. It is built with Flask and uses Bootstrap for the frontend.

You can change the `index-config.yml` file in the root of the repository to configure the playlists, channels, and videos you want to index.

Additionally, you can opt to either create a `.env` file in the root of the repository and set the environment variables directly, or set them in your operating system's environment variables.

The example app is containerized with Docker, making it simple to run:
```bash
docker compose up
```

Alternatively, you can run the app without Docker by installing the dependencies and running the `app.py` directly:

First you'll need to run Redis Stack in a docker container:
```bash
docker run -d --name redis-stack-server -p 6379:6379 redis/redis-stack-server:latest
```

Then install the dependencies and run the app:
```bash
pip3 install -e .
python3 examples/basic/app.py
```
