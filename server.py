import os
import time
import urllib.parse
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import yt_dlp

app = Flask(__name__)
CORS(app)

# ১. মঙ্গোডিবি কানেকশন (সরাসরি আপনার ইউজার ও পাসওয়ার্ড দিয়ে)
try:
    username = urllib.parse.quote_plus("sumyakhan542")
    password = urllib.parse.quote_plus("sumya1100")
    # অ্যাপ নাম (Cluster0) এবং সঠিক কানেকশন স্ট্রিং নিশ্চিত করা
    MONGO_URI = f"mongodb+srv://{username}:{password}@cluster0.1toogst.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client['youtube_downloader']
    collection = db['link_cache']
    # কানেকশন চেক করার জন্য একটি কমান্ড
    client.admin.command('ping')
    print("MongoDB Connected Successfully!")
except Exception as e:
    print(f"MongoDB Connection Error: {e}")

# ২. ভিডিও তথ্য সংগ্রহের ফাংশন
def get_video_info(video_url):
    try:
        # প্রথমে ডাটাবেসে চেক করা
        cached_data = collection.find_one({"video_url": video_url})
        if cached_data:
            if time.time() - cached_data['timestamp'] < 21600:
                return cached_data['data']
    except Exception as e:
        print(f"Database Read Error: {e}")

    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "format": "best[ext=mp4][protocol=https]/best[protocol=https]",
        "cookiefile": "cookies.txt",
        "nocheckcertificate": True,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            formats = info.get('formats', [])
            
            final_formats = []
            for f in formats:
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    v_url = f.get('url', '')
                    if "manifest" not in v_url and "m3u8" not in v_url:
                        final_formats.append({
                            "quality": f.get("format_note") or f.get("resolution"),
                            "ext": f.get("ext"),
                            "url": v_url
                        })

            result = {
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "formats": final_formats[:3]
            }

            # ডাটাবেসে সেভ করা (এটি অপশনাল, এরর হলে যেন প্রোগ্রাম না থামে)
            try:
                collection.update_one(
                    {"video_url": video_url},
                    {"$set": {"data": result, "timestamp": time.time()}},
                    upsert=True
                )
            except:
                pass
                
            return result

    except Exception as e:
        return {"error": f"YT-DLP Error: {str(e)}"}

# ৩. এপিআই রাউট
@app.route('/get_info', methods=['GET'])
def fetch_info():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"error": "URL is required"}), 400
    
    data = get_video_info(video_url)
    return jsonify(data)

@app.route('/')
def home():
    return "YouTube Downloader API is Running!"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    # collection.drop() 
