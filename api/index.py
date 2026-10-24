from http.server import BaseHTTPRequestHandler
import json, re, random
import urllib.request

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Ambil username dari ?u=
            path = self.path
            m = re.search(r'u=([^&]+)', path)
            if not m:
                self.send_json({"error": "username required ?u=username"}, 400)
                return
            username = m.group(1).strip().lstrip('@')

            # List User-Agent random biar gak ke-detect bot
            agents = [
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36",
                "Instagram 327.0.0.0.0 Android (34/14; 560dpi; 1440x3088; samsung; SM-S928B; dm3q; qcom; en_US; 559035960)"
            ]

            # Coba endpoint 1: web_profile_info (paling stabil)
            url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={username}"
            req = urllib.request.Request(url, headers={
                "User-Agent": random.choice(agents),
                "X-IG-App-ID": "936619743392459",
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": f"https://www.instagram.com/{username}/",
            })
            
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    data = json.loads(r.read().decode('utf-8'))
                    user = data['data']['user']
            except:
                # Fallback endpoint 2
                url2 = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={username}"
                req2 = urllib.request.Request(url2, headers={
                    "User-Agent": random.choice(agents),
                    "X-IG-App-ID": "936619743392459",
                })
                with urllib.request.urlopen(req2, timeout=10) as r2:
                    data = json.loads(r2.read().decode('utf-8'))
                    user = data['data']['user']

            result = {
                "username": user.get('username'),
                "full_name": user.get('full_name'),
                "bio": user.get('biography'),
                "followers": user.get('follower_count'),
                "following": user.get('following_count'),
                "posts": user.get('media_count'),
                "is_private": user.get('is_private'),
                "is_verified": user.get('is_verified'),
                "profile_pic": user.get('profile_pic_url_hd') or user.get('profile_pic_url'),
                "external_url": user.get('external_url'),
                "category": user.get('category_name'),
            }
            
            self.send_json(result)

        except Exception as e:
            self.send_json({"error": f"IG Block / Username tidak ditemukan: {str(e)}", "hint": "Coba username lain atau tunggu 2 menit"}, 500)

    def send_json(self, obj, code=200):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
