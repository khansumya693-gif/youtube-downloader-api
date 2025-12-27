from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import re
import time
import urllib.parse
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)

username = urllib.parse.quote_plus("Sumyakhan")
password = urllib.parse.quote_plus("Zw2BA7BMOtbs7lbJ")

# এখানে আপনার সংগৃহীত মঙ্গোডিবি লিঙ্কটি দিন
MONGO_URI = "mongodb+srv://{username}:{password}@cluster0.1toogst.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['youtube_downloader']
collection = db['link_cache']

YOUTUBE_REGEX = r"(youtube\.com|youtu\.be)"

@app.route("/info")
def info():
    url = request.args.get("url", "")
    if not url or not re.search(YOUTUBE_REGEX, url):
        return jsonify({"error": "একটি সঠিক ইউটিউব লিংক দিন"}), 400

    current_time = time.time()

    try:
        # ১. ডাটাবেসে চেক করা (Caching Logic)
        cached_data = collection.find_one({"video_url": url})
        if cached_data:
            # চেক: ২১৬০০ সেকেন্ড = ৬ ঘণ্টা
            if current_time - cached_data['timestamp'] < 21600:
                return jsonify(cached_data['data'])

        # ২. নতুন ডাটা সংগ্রহ
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "format": "best[height<=360][ext=mp4]/best[ext=mp4]/best",
        }

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

        response_data = {
            "title": data.get("title"),
            "thumbnail": data.get("thumbnail"),
            "channel": data.get("uploader"),
            "formats": final_formats
        }

        # ৩. ডাটাবেসে সেভ বা আপডেট করা
        collection.update_one(
            {"video_url": url},
            {"$set": {"timestamp": current_time, "data": response_data}},
            upsert=True
        )

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
