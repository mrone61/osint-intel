from http.server import BaseHTTPRequestHandler
import json, re, urllib.request, urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            m = re.search(r'u=([^&]+)', self.path)
            if not m:
                self.send_json({"error": "need ?u=username"}, 400)
                return
            username = urllib.parse.unquote(m.group(1)).strip().lstrip('@').lower()
            
            # Ambil halaman HTML publik, bukan API
            url = f"https://www.instagram.com/{username}/"
            headers = {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
                "Referer": "https://www.instagram.com/",
                "X-Requested-With": "XMLHttpRequest",
            }
            req = urllib.request.Request(url, headers=headers)
            
            html = ""
            with urllib.request.urlopen(req, timeout=15) as r:
                html = r.read().decode('utf-8', errors='ignore')

            # Coba cari data JSON yang nempel di HTML
            # Instagram simpan data di window._sharedData atau script type="application/ld+json"
            user_data = None
            
            # Method 1: cari profilePage_xxxx
            match = re.search(r'"profilePage_[0-9]+":\{"data":\{"user":(.*?),"__typename"', html)
            if not match:
                match = re.search(r'"user":\{"username":"%s".*?\}\}' % re.escape(username), html, re.DOTALL)
            
            if match:
                try:
                    # ambil og tags sebagai fallback paling aman
                    bio = re.search(r'<meta property="og:description" content="([^"]+)"', html)
                    pic = re.search(r'<meta property="og:image" content="([^"]+)"', html)
                    title = re.search(r'<meta property="og:title" content="([^"]+)"', html)
                    
                    # parsing followers dari description: "1M Followers, 500 Following, 100 Posts"
                    followers = following = posts = 0
                    full_name = username
                    if title:
                        full_name = title.group(1).split('•')[0].split('(')[0].strip()
                    
                    desc = bio.group(1) if bio else ""
                    # desc contoh: "1,234 Followers, 567 Following, 89 Posts - See Instagram..."
                    nums = re.findall(r'([\d,.KM]+)\s+Followers.*?([\d,.KM]+)\s+Following.*?([\d,.KM]+)\s+Posts', desc)
                    if nums:
                        followers, following, posts = nums[0]

                    result = {
                        "username": username,
                        "full_name": full_name,
                        "bio": desc,
                        "followers": followers,
                        "following": following,
                        "posts": posts,
                        "profile_pic": pic.group(1) if pic else "",
                        "source": "html-meta",
                        "note": "Data dari HTML publik karena API IG lagi limit (429)"
                    }
                    self.send_json(result)
                    return
                except Exception as e2:
                    pass

            # Kalau sampai sini masih gagal, kasih error yang jelas
            self.send_json({"error": f"Masih ke-block 429, IG lagi ketat. HTML length: {len(html)}", "hint": "Coba test username 'instagram' dulu"}, 500)

        except Exception as e:
            self.send_json({"error": str(e), "hint": "Vercel IP di-limit IG. Tunggu 10 menit atau coba username lain"}, 500)

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
