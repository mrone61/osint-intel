from http.server import BaseHTTPRequestHandler
import urllib.parse, urllib.request, json, re, concurrent.futures

def fetch_duckduckgo(query, max_results=80):
    results = []
    try:
        q = urllib.parse.quote_plus(query)
        # 2 halaman duckduckgo
        for page in [0, 30]:
            url = f"https://html.duckduckgo.com/html/?q={q}&s={page}"
            headers = {"User-Agent": "Mozilla/5.0"}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as r:
                html = r.read().decode('utf-8', errors='ignore')
            # parse hasil
            for m in re.finditer(r'class="result__url" href="([^"]+)".*?class="result__a"[^>]*>(.*?)</a>', html, re.S):
                raw_url = m.group(1)
                title = re.sub('<[^>]+>', '', m.group(2)).strip()
                if "duckduckgo.com/l/?" in raw_url:
                    qs = urllib.parse.parse_qs(urllib.parse.urlparse(raw_url).query)
                    if 'uddg' in qs:
                        raw_url = qs['uddg'][0]
                if raw_url.startswith("http") and "duckduckgo.com" not in raw_url:
                    domain = urllib.parse.urlparse(raw_url).netloc.replace('www.','')
                    results.append({"title": title[:100], "url": raw_url, "source": domain})
            if len(results) >= max_results:
                break
    except Exception as e:
        print(e)
    return results

def fetch_bing(query, max_results=40):
    results = []
    try:
        q = urllib.parse.quote_plus(query)
        url = f"https://www.bing.com/search?q={q}&count=50"
        headers = {"User-Agent": "Mozilla/5.0"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode('utf-8', errors='ignore')
        for m in re.finditer(r'<li class="b_algo"><h2><a href="([^"]+)"[^>]*>(.*?)</a>', html):
            raw_url = m.group(1)
            title = re.sub('<[^>]+>', '', m.group(2)).strip()
            domain = urllib.parse.urlparse(raw_url).netloc.replace('www.','')
            if raw_url.startswith("http"):
                results.append({"title": title[:100], "url": raw_url, "source": domain})
            if len(results) >= max_results:
                break
    except:
        pass
    return results

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        q = (qs.get('q') or [None])[0]

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        if not q:
            self.wfile.write(json.dumps({"error": "need ?q=nama"}).encode())
            return

        q = q.strip()
        
        # PARALEL AMBIL DARI 2 SEARCH ENGINE BIAR DAPAT RATUSAN
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
            f1 = ex.submit(fetch_duckduckgo, q, 80)
            f2 = ex.submit(fetch_bing, q, 50)
            r1 = f1.result()
            r2 = f2.result()

        all_results = r1 + r2
        # deduplicate by url
        seen = set()
        unique = []
        for r in all_results:
            if r['url'] not in seen:
                seen.add(r['url'])
                unique.append(r)

        data = {
            "query": q,
            "total_found": len(unique),
            "message": f"Berhasil menemukan {len(unique)} situs di internet yang menyebut '{q}'",
            "results": unique[:150]  # batasi 150 biar gak berat
        }
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
