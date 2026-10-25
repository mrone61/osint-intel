from http.server import BaseHTTPRequestHandler
import urllib.parse, json, urllib.request, concurrent.futures

# List server target langsung
TARGETS = [
    "https://www.detik.com/search/searchall?query={}",
    "https://www.kompas.com/search/{}",
    "https://www.liputan6.com/search?q={}",
    "https://www.cnnindonesia.com/search/?query={}",
    "https://www.tribunnews.com/search?q={}",
    "https://www.antaranews.com/search/{}",
    "https://www.kumparan.com/search?q={}",
    "https://www.tempo.co/search?q={}",
    "https://jabar.antaranews.com/search?q={}",
    "https://www.okezone.com/tag/{}",
    "https://www.sindonews.com/search?q={}",
    "https://www.merdeka.com/search/{}",
    "https://www.suara.com/search?q={}",
    "https://www.viva.co.id/search?q={}",
    "https://pddikti.kemdiktisaintek.go.id/search/{}",
    "https://sinta.kemdiktisaintek.go.id/authors?q={}",
]

def cek_server(url_template, q):
    url = url_template.format(urllib.parse.quote(q))
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 Chrome/122"})
        with urllib.request.urlopen(req, timeout=7) as r:
            html = r.read().decode('utf-8','ignore')
            # Kalau nama ada di html server itu, anggap valid
            if q.lower() in html.lower():
                domain = urllib.parse.urlparse(url).netloc
                return {"title": f"{q} ditemukan di {domain}", "url": url, "source": domain, "valid": True}
    except:
        pass
    return None

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('q',[''])[0].strip()
        self.send_response(200)
        self.send_header('Content-type','application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        
        if not q or len(q) < 3:
            self.wfile.write(b'{"results":[]}'); return

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as ex:
            futs = [ex.submit(cek_server, t, q) for t in TARGETS]
            for f in concurrent.futures.as_completed(futs):
                try:
                    res = f.result()
                    if res: results.append(res)
                except: pass

        self.wfile.write(json.dumps({
            "query": q,
            "results": results,
            "google_found": len(results),
            "engine": "direct-shoot-v11"
        }, ensure_ascii=False).encode())
