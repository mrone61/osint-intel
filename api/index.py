from http.server import BaseHTTPRequestHandler
import urllib.parse, json, urllib.request, concurrent.futures, re

MEDIA = ["detik.com","kompas.com","liputan6.com","cnnindonesia.com","tribunnews.com","antaranews.com","kumparan.com","tempo.co","jpnn.com","okezone.com","sindonews.com","merdeka.com","suara.com"]

def extract_id_links(raw_text):
    # Ambil semua link .id dan media .com
    pat1 = r'https?://[^\s"<>]+\.id[^\s"<>]*'
    pat2 = r'https?://[^\s"<>]*(?:detik\.com|kompas\.com|liputan6\.com|cnnindonesia\.com|tribunnews\.com)[^\s"<>]*'
    links = re.findall(pat1, raw_text) + re.findall(pat2, raw_text)
    clean = []
    for l in links:
        l = l.split('&')[0].split('"')[0].split("'")[0]
        if len(l) < 15: continue
        if "google.com" in l or "bing.com" in l or "duckduckgo.com" in l or "gstatic" in l: continue
        clean.append(urllib.parse.unquote(l))
    return clean

def get_from_google(q):
    try:
        url = f"https://www.google.com/search?q={urllib.parse.quote_plus(q)}&num=25&hl=id"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122 Safari/537.36"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return extract_id_links(r.read().decode('utf-8','ignore'))
    except: return []

def get_from_duckduckgo(q):
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(q)}"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 Firefox/124"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return extract_id_links(r.read().decode('utf-8','ignore'))
    except: return []

def get_from_bing(q):
    try:
        url = f"https://www.bing.com/search?q={urllib.parse.quote_plus(q)}&mkt=id-ID"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 Edge/122"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return extract_id_links(r.read().decode('utf-8','ignore'))
    except: return []

def get_all_links(q):
    all_links = []
    all_links += get_from_google(q)
    if len(all_links) < 5:
        all_links += get_from_duckduckgo(q)
    if len(all_links) < 5:
        all_links += get_from_bing(q)
    # Dedup
    return list(dict.fromkeys(all_links))[:25]

def cek_valid(url, q):
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 Chrome/122"})
        with urllib.request.urlopen(req, timeout=6) as r:
            html = r.read().decode('utf-8','ignore').lower()
            return q.lower().strip() in html
    except: return False

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('q',[''])[0].strip()
        self.send_response(200)
        self.send_header('Content-type','application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        if not q or q.isdigit() or len(q) < 3:
            self.wfile.write(b'{"results":[],"google_found":0}'); return

        links = get_all_links(q)
        valid = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
            futs = {ex.submit(cek_valid, u, q): u for u in links}
            for f in concurrent.futures.as_completed(futs):
                u = futs[f]
                try:
                    if f.result():
                        d = urllib.parse.urlparse(u).netloc
                        valid.append({"title": f"{q} - {d}", "url": u, "source": d, "valid": True})
                except: pass

        self.wfile.write(json.dumps({
            "query": q,
            "results": valid,
            "google_found": len(links),
            "engine": "google+duckduckgo+bing"
        }, ensure_ascii=False).encode())
