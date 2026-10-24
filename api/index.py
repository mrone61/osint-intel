from flask import Flask, request, jsonify
from flask_cors import CORS
import instaloader

app = Flask(__name__)
CORS(app)
L = instaloader.Instaloader()

@app.route('/')
@app.route('/api/ig')
def get_ig():
    username = request.args.get('u')
    if not username:
        return jsonify({"error": "isi ?u=username"}), 400
    try:
        profile = instaloader.Profile.from_username(L.context, username)
        posts = []
        for p in profile.get_posts():
            if len(posts) >= 8: break
            posts.append({
                "tanggal": str(p.date),
                "caption": (p.caption[:80] if p.caption else ""),
                "lokasi": p.location.name if p.location else "Tidak tag lokasi",
                "link": f"https://instagram.com/p/{p.shortcode}/"
            })
        return jsonify({
            "username": profile.username,
            "nama": profile.full_name,
            "bio": profile.biography,
            "followers": profile.followers,
            "is_private": profile.is_private,
            "posts": posts
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
