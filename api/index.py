
from http.server import BaseHTTPRequestHandler
import urllib.parse, json, urllib.request, concurrent.futures, re

MEDIA = ["detik.com","kompas.com","liputan6.com","cnnindonesia.com","tribunnews.com","antaranews.com","kumparan.com","tempo.co"]

def get_links(q):
    links = []
    # 1. Coba Google
    try:
        url = f"https://www.google.com/search?q={urllib.parse.quote_plus(q)}&num=25&hl=id"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 Chrome/122"})
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read().decode('utf-8','ignore')
            links = re.findall(r'/url\?q=(https?://[^&]+)', raw)
            links = [urllib.parse.unquote(x).split('&')[0] for x in links]
    except: pass
    # 2. Kalau Google 0, pakai DuckDuckGo (ini yang nyelamatin)
    if len(links) < 3:
        try:
            url2 = f"https://duckduckgo.com/html/?q={urllib.parse.quote_plus(q+' site:.id')}"
            req2 = urllib.request.Request(url2, headers={"User-Agent":"Mozilla/5.0 Chrome/122"})
            with urllib.request.urlopen(req2, timeout=10) as r2:
                raw2 = r2.read().decode('utf-8','ignore')
                more = re.findall(r'(https?://[^\s"]+\.id[^\s"]*)', raw2)
                more2 = re.findall(r'(https?://[^\s"]*detik\.com[^\s"]*)', raw2)
                links += more + more2
        except: pass
    # Bersihin
    clean = []
    for l in links:
        if "google.com" in l or "duckduckgo" in l: continue
        if ".id" in l or any(m in l for m in MEDIA):
            clean.append(l)
    return list(dict.fromkeys(clean))[:20]

def cek(url, q):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 Chrome/122"})
        with urllib.request.urlopen(req, timeout=6) as r:
            return q.lower() in r.read().decode('utf-8','ignore').lower()
    except: return False

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('q',[''])[0]
        self.send_response(200)
        self.send_header('Content-type','application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        if not q or q.isdigit():
            self.wfile.write(b'{"results":[]}'); return
        g = get_links(q)
        valid = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
            futs = {ex.submit(cek, u, q): u for u in g}
            for f in concurrent.futures.as_completed(futs):
                u = futs[f]
                if f.result():
                    d = urllib.parse.urlparse(u).netloc
                    valid.append({"title":f"{q} di {d}","url":u,"source":d,"valid":True})
        self.wfile.write(json.dumps({"query":q,"results":valid,"google_found":len(g)}, ensure_ascii=False).encode())
