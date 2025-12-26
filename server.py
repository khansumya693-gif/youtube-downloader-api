
from flask import Flask, request, jsonify
import yt_dlp
import re

app = Flask(__name__)

YOUTUBE_REGEX = r"(youtube\.com|youtu\.be)"

@app.route("/info")
def info():
    url = request.args.get("url", "")

    if not re.search(YOUTUBE_REGEX, url):
        return jsonify({"error": "Only YouTube links allowed"}), 400

    ydl_opts = {
        "quiet": True,
        "skip_download": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        data = ydl.extract_info(url, download=False)

    return jsonify({
        "title": data.get("title"),
        "duration": data.get("duration"),
        "thumbnail": data.get("thumbnail"),
        "formats": data.get("formats")
    })

app.run(host="0.0.0.0", port=5000)
