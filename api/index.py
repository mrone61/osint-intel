from http.server import BaseHTTPRequestHandler
import json, re, urllib.request, urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            m = re.search(r'u=([^&]+)', self.path)
            if not m:
                self.send_json({"error": "need ?u=username"}, 400); return
            username = urllib.parse.unquote(m.group(1)).strip().lstrip('@')

            url = f"https://www.instagram.com/{username}/"
            headers = {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html",
            }
            req = urllib.request.Request(url, headers=headers)
            html = urllib.request.urlopen(req, timeout=15).read().decode('utf-8', errors='ignore')

            # AMBIL DARI OG TAGS - INI PALING STABIL
            title = re.search(r'<meta property="og:title" content="([^"]+)"', html)
            desc = re.search(r'<meta property="og:description" content="([^"]+)"', html)
            img = re.search(r'<meta property="og:image" content="([^"]+)"', html)

            full_name = username
            followers = following = posts = "-"
            bio = ""

            if title:
                # title contoh: "mr_one61 (@mr_one61) • Instagram photos and videos"
                full_name = title.group(1).split('(')[0].split('•')[0].strip()

            if desc:
                bio = desc.group(1)
                # bio contoh: "2,234 Followers, 1,234 Following, 56 Posts - See..."
                f = re.search(r'([\d,\.KM]+)\s+Followers', bio)
                fg = re.search(r'([\d,\.KM]+)\s+Following', bio)
                p = re.search(r'([\d,\.KM]+)\s+Posts', bio)
                if f: followers = f.group(1)
                if fg: following = fg.group(1)
                if p: posts = p.group(1)

            if not title and not desc:
                self.send_json({"error": f"IG tidak kembalikan data untuk @{username}", "html_snippet": html[:500]}, 500)
                return

            result = {
                "username": username,
                "full_name": full_name,
                "bio": bio,
                "followers": followers,
                "following": following,
                "posts": posts,
                "profile_pic": img.group(1) if img else "",
                "source": "og-tags",
                "status": "LIVE"
            }
            self.send_json(result)

        except Exception as e:
            self.send_json({"error": str(e)}, 500)

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
