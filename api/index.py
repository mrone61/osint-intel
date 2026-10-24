from http.server import BaseHTTPRequestHandler
import urllib.parse, urllib.request, re, json

def search_duckduckgo(query):
    try:
        q = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={q}"
        headers = {"User-Agent": "Mozilla/5.0"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode('utf-8', errors='ignore')
        
        results = []
        # ambil link hasil
        for m in re.finditer(r'<a rel="nofollow" class="result__url" href="([^"]+)".*?>(.*?)</a>.*?<a class="result__a" href="[^"]+">(.*?)</a>', html, re.S):
            raw_url = m.group(1)
            title = re.sub('<[^>]+>', '', m.group(3)).strip()
            # decode duckduckgo redirect
            if "duckduckgo.com/l/?" in raw_url:
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(raw_url).query)
                if 'uddg' in parsed:
                    raw_url = parsed['uddg'][0]
            if raw_url.startswith("http"):
                results.append({"title": title[:120], "url": raw_url, "source": "duckduckgo"})
            if len(results) >= 10:
                break
        return results
    except Exception as e:
        return [{"title": f"Error search: {e}", "url": "", "source": "error"}]

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        query = (qs.get('q') or qs.get('u') or qs.get('name') or [None])[0]

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        if not query:
            self.wfile.write(json.dumps({"error": "need ?q=nama atau ?u=nama", "contoh": "/api?q=Joko Widodo"}).encode())
            return

        query = query.strip()
        results = search_duckduckgo(query)

        # tambahkan sumber terbuka langsung
        extra = [
            {"title": f"Wikipedia - {query}", "url": f"https://en.wikipedia.org/wiki/Special:Search?search={urllib.parse.quote_plus(query)}", "source": "wikipedia"},
            {"title": f"Google News - {query}", "url": f"https://news.google.com/search?q={urllib.parse.quote_plus(query)}", "source": "google_news"},
            {"title": f"Twitter/X - {query}", "url": f"https://twitter.com/search?q={urllib.parse.quote_plus(query)}", "source": "twitter"},
        ]

        data = {
            "query": query,
            "total": len(results) + len(extra),
            "results": extra + results,
            "note": "LEGAL PUBLIC OSINT - hanya link publik, tidak simpan data pribadi"
        }
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode())
