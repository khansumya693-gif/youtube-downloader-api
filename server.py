from flask import Flask, request, jsonify
from flask_cors import CORS  # ১. এটি ইম্পোর্ট করুন
import yt_dlp
import re

app = Flask(__name__)
CORS(app)  # ২. এটি যোগ করুন, যা সব ওয়েবসাইটকে আপনার API ব্যবহারের অনুমতি দেবে

YOUTUBE_REGEX = r"(youtube\.com|youtu\.be)"

@app.route("/info")
def info():
    url = request.args.get("url", "")
    if not url or not re.search(YOUTUBE_REGEX, url):
        return jsonify({"error": "একটি সঠিক ইউটিউব লিংক দিন"}), 400

    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "format": "best[height<=360][ext=mp4]/best[ext=mp4]/best",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            data = ydl.extract_info(url, download=False)

        all_formats = data.get("formats", [])
        final_formats = []

        for f in all_formats:
            if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                final_formats.append({
                    "format_id": f.get("format_id"),
                    "resolution": f.get("format_note") or f.get("resolution"),
                    "extension": f.get("ext"),
                    "filesize_mb": round(f.get("filesize", 0) / (1024 * 1024), 2) if f.get("filesize") else "Unknown",
                    "url": f.get("url")
                })

        return jsonify({
            "title": data.get("title"),
            "thumbnail": data.get("thumbnail"),
            "formats": final_formats
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
