from http.server import BaseHTTPRequestHandler
import urllib.parse, json, urllib.request, concurrent.futures

TEMPLATES = {
"pddikti.kemdiktisaintek.go.id": "https://pddikti.kemdiktisaintek.go.id/search/{q_path}",
"sinta.kemdiktisaintek.go.id": "https://sinta.kemdiktisaintek.go.id/authors?q={q_plus}",
"detik.com": "https://www.detik.com/search/searchall?query={q_plus}",
"kompas.com": "https://www.kompas.com/search?q={q_plus}",
"cnnindonesia.com": "https://www.cnnindonesia.com/search?query={q_plus}",
"tribunnews.com": "https://www.tribunnews.com/search?q={q_plus}",
"tempo.co": "https://www.tempo.co/search?q={q_plus}",
"ui.ac.id": "https://www.ui.ac.id/?s={q_plus}",
"ugm.ac.id": "https://ugm.ac.id/?s={q_plus}",
"itb.ac.id": "https://www.itb.ac.id/search?q={q_plus}",
"unhas.ac.id": "https://unhas.ac.id/?s={q_plus}",
"youtube.com": "https://www.youtube.com/results?search_query={q_plus}",
"facebook.com": "https://www.facebook.com/search/top/?q={q_plus}",
"x.com": "https://x.com/search?q={q_plus}",
"tiktok.com": "https://www.tiktok.com/search?q={q_plus}",
"wikipedia.org": "https://en.wikipedia.org/w/index.php?search={q_plus}",
"scholar.google.com": "https://scholar.google.com/scholar?q={q_plus}",
"xnxx.com": "https://www.xnxx.com/search/{q_path}",
"xvideos.com": "https://www.xvideos.com/?k={q_plus}",
"pornhub.com": "https://www.pornhub.com/video/search?search={q_plus}",
}

def cek_langsung(url, query):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as r:
            html = r.read().decode('utf-8', errors='ignore').lower()
            qlow = query.lower()
            # JIKA ADA KATA TIDAK DITEMUKAN = JANGAN TAMPILKAN
            if "tidak ditemukan" in html or "data tidak ditemukan" in html or "no results" in html or "no video" in html:
                return False
            # JIKA NAMA ADA DI HTML = TAMPILKAN HIJAU
            if qlow in html:
                return True
            return False
    except:
        return False

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('q',[''])[0].strip()
        self.send_response(200)
        self.send_header('Content-type','application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        if not q:
            self.wfile.write(b'{"results":[]}'); return
        q_plus = urllib.parse.quote_plus(q)
        q_path = urllib.parse.quote(q) # aprilia%20sbrfk
        valid_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(cek_langsung, tpl.replace("{q_plus}", q_plus).replace("{q_path}", q_path), q): (domain, tpl.replace("{q_plus}", q_plus).replace("{q_path}", q_path)) for domain, tpl in TEMPLATES.items()}
            for f in concurrent.futures.as_completed(futures):
                domain, url = futures[f]
                if f.result():
                    valid_results.append({"title": f"{q} di {domain}", "url": url, "source": domain, "valid": True, "status_text": "✓ DITEMUKAN"})
        self.wfile.write(json.dumps({"query": q, "results": valid_results}, ensure_ascii=False).encode())
