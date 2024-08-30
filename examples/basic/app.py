from flask import Flask, request, jsonify, render_template
from transcripter.config import Config
from transcripter.services import IndexingService, SearchService
from transcripter.logs import configure_logging
from loguru import logger

configure_logging()

app = Flask(__name__)
config = Config()
indexing_service = IndexingService(config)
search_service = SearchService(config)


@app.route("/")
def index():
    logger.info("Serving index page")
    return render_template("index.html")


@app.route("/search")
def search():
    query = request.args.get("q", "")
    logger.info(f"Search request received with query: {query}")
    if len(query) < 3:
        logger.warning("Search query too short")
        return jsonify([])

    results = search_service.search(query)
    logger.info(f"Returning {len(results)} search results")
    return jsonify(results)


@app.route("/indexed_documents")
def indexed_documents():
    docs = indexing_service.get_all_documents()
    return jsonify(docs)


if __name__ == "__main__":
    logger.info("Starting the application")
    app.run(host="0.0.0.0", port=5000, debug=True)
