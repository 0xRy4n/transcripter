from flask import Flask, request, jsonify, render_template
from redisearch import Client, Query

app = Flask(__name__)

# Connect to RediSearch
redis_search = Client("video_index")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search", methods=["GET"])
def search():
    query_str = request.args.get("q", "")
    if not query_str:
        return jsonify([])

    # Use an exact match within the 'text' field
    exact_query_str = f'@text:"{query_str}"'

    # Perform the search on RediSearch
    query = Query(exact_query_str).return_fields(
        "video_id", "video_title", "text", "timecode"
    )
    results = redis_search.search(query)

    # Process and format the results, ensuring only matching text is included
    response_data = [
        {
            "video_id": doc.video_id,
            "video_title": doc.video_title,
            "snippet": doc.text,
            "timecode": doc.timecode,
        }
        for doc in results.docs
        if query_str.lower() in doc.text.lower()
    ]

    return jsonify(response_data)


if __name__ == "__main__":
    app.run(debug=True)
