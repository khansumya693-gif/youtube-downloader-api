from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import re
import time
import urllib.parse
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)

# ১. মঙ্গোডিবি কানেকশন (ইউজার ও পাসওয়ার্ড এনকোড করা হয়েছে)
username = urllib.parse.quote_plus("sumyakhan542")
password = urllib.parse.quote_plus("sumya1100")
MONGO_URI = f"mongodb+srv://{username}:{password}@cluster0.1toogst.mongodb.net/?retryWrites=true&w=majority"

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
        # ২. ডাটাবেসে চেক করা (Caching Logic)
        cached_data = collection.find_one({"video_url": url})
        if cached_data:
            if current_time - cached_data['timestamp'] < 21600:
                return jsonify(cached_data['data'])

        # ৩. yt-dlp কনফিগারেশন (Cookie যুক্ত করা হয়েছে)
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            # সরাসরি MP4 এবং HTTPS প্রোটোকল নিশ্চিত করা
            "format": "best[ext=mp4][protocol=https]/best[protocol=https]",
            "cookiefile": "cookies.txt",  # নিশ্চিত করুন cookies.txt ফাইলটি মেইন ফোল্ডারে আছে
            "nocheckcertificate": True,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            data = ydl.extract_info(url, download=False)

        all_formats = data.get("formats", [])
        final_formats = []

        # ৪. Manifest এবং m3u8 ফিল্টার করার লজিক
        for f in all_formats:
            # শুধুমাত্র অডিও+ভিডিও আছে এমন ফরম্যাট নেওয়া
            if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                video_url = f.get("url", "")
                
                # ফিল্টার: লিঙ্কটিতে 'manifest' বা 'm3u8' থাকা চলবে না
                if "manifest" not in video_url and "m3u8" not in video_url:
                    final_formats.append({
                        "format_id": f.get("format_id"),
                        "resolution": f.get("format_note") or f.get("resolution"),
                        "extension": f.get("ext"),
                        "filesize_mb": round(f.get("filesize", 0) / (1024 * 1024), 2) if f.get("filesize") else "Unknown",
                        "url": video_url
                    })

        response_data = {
            "title": data.get("title"),
            "thumbnail": data.get("thumbnail"),
            "channel": data.get("uploader"),
            "formats": final_formats[:3] # সেরা ৩টি রেজাল্ট দিবে
        }

        # ৫. ডাটাবেসে সেভ করা
        collection.update_one(
            {"video_url": url},
            {"$set": {"timestamp": current_time, "data": response_data}},
            upsert=True
        )

        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
