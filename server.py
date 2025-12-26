from flask import Flask, request, jsonify
import yt_dlp
import re

app = Flask(__name__)

# ইউটিউব লিংক যাচাই করার রেজেক্স
YOUTUBE_REGEX = r"(youtube\.com|youtu\.be)"

@app.route("/info")
def info():
    url = request.args.get("url", "")

    if not url or not re.search(YOUTUBE_REGEX, url):
        return jsonify({"error": "একটি সঠিক ইউটিউব লিংক দিন"}), 400

    # yt-dlp কনফিগারেশন
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        # ৩৬০পি এবং সাউন্ডসহ ফাইলটি আগে খোঁজার চেষ্টা করবে
        "format": "best[height<=360][ext=mp4]/best[ext=mp4]/best",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            data = ydl.extract_info(url, download=False)

        all_formats = data.get("formats", [])
        final_formats = []

        for f in all_formats:
            # শর্ত: ভিডিও কোডেক এবং অডিও কোডেক দুটোই থাকতে হবে (none হওয়া যাবে না)
            if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                # শুধুমাত্র দরকারি তথ্যগুলো ফিল্টার করে নিচ্ছি
                final_formats.append({
                    "format_id": f.get("format_id"),
                    "resolution": f.get("format_note") or f.get("resolution"),
                    "extension": f.get("ext"),
                    "filesize_mb": round(f.get("filesize", 0) / (1024 * 1024), 2) if f.get("filesize") else "Unknown",
                    "url": f.get("url")  # এই লিংকে সাউন্ড থাকবেই
                })

        # যদি কোনো কম্বাইন্ড ফরম্যাট না পাওয়া যায়
        if not final_formats:
            return jsonify({"error": "সাউন্ডসহ কোনো ভিডিও ফরম্যাট পাওয়া যায়নি"}), 404

        return jsonify({
            "title": data.get("title"),
            "duration_sec": data.get("duration"),
            "thumbnail": data.get("thumbnail"),
            "channel": data.get("uploader"),
            "formats": final_formats
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Render বা অন্য প্ল্যাটফর্মে হোস্টিং করার জন্য উপযুক্ত পোর্ট
    app.run(host="0.0.0.0", port=5000)
