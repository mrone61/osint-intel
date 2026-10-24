from http.server import BaseHTTPRequestHandler
import urllib.parse, json, urllib.request, concurrent.futures

TEMPLATES = {
"pddikti.kemdiktisaintek.go.id": "https://pddikti.kemdiktisaintek.go.id/search/{q_path}",
"sinta.kemdiktisaintek.go.id": "https://sinta.kemdiktisaintek.go.id/authors?q={q_plus}",
"garuda.kemdikbud.go.id": "https://garuda.kemdikbud.go.id/documents?q={q_plus}",
"ustj.ac.id": "https://ustj.ac.id/?s={q_plus}",
"unhas.ac.id": "https://unhas.ac.id/?s={q_plus}",
"unm.ac.id": "https://unm.ac.id/?s={q_plus}",
"umi.ac.id": "https://umi.ac.id/?s={q_plus}",
"unismuh.ac.id": "https://unismuh.ac.id/?s={q_plus}",
"ui.ac.id": "https://www.ui.ac.id/?s={q_plus}",
"ugm.ac.id": "https://ugm.ac.id/?s={q_plus}",
"itb.ac.id": "https://www.itb.ac.id/search?q={q_plus}",
"ipb.ac.id": "https://www.ipb.ac.id/?s={q_plus}",
"its.ac.id": "https://www.its.ac.id/?s={q_plus}",
"unpad.ac.id": "https://www.unpad.ac.id/?s={q_plus}",
"undip.ac.id": "https://www.undip.ac.id/?s={q_plus}",
"unair.ac.id": "https://www.unair.ac.id/?s={q_plus}",
"detik.com": "https://www.detik.com/search/searchall?query={q_plus}",
"kompas.com": "https://www.kompas.com/search?q={q_plus}",
"youtube.com": "https://www.youtube.com/results?search_query={q_plus}",
"facebook.com": "https://www.facebook.com/search/top/?q={q_plus}",
"x.com": "https://x.com/search?q={q_plus}",
"tiktok.com": "https://www.tiktok.com/search?q={q_plus}",
"wikipedia.org": "https://en.wikipedia.org/w/index.php?search={q_plus}",
"xnxx.com": "https://www.xnxx.com/search/{q_path}",
"xvideos.com": "https://www.xvideos.com/?k={q_plus}",
"pornhub.com": "https://www.pornhub.com/video/search?search={q_plus}",
"xhamster.com": "https://xhamster.com/search/{q_path}",
}

FORCE_ALWAYS = ["pddikti.kemdiktisaintek.go.id", "sinta.kemdiktisaintek.go.id", "garuda.kemdikbud.go.id"]

def cek_valid(url, query, domain):
    if domain in FORCE_ALWAYS:
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=7) as r:
            html = r.read().decode('utf-8', errors='ignore').lower()
            qlow = query.lower()
            # harus ada nama nya persis di html web itu
            if qlow in html:
                # tapi kalau web bilang tidak ditemukan, jangan tampilkan
                if "tidak ditemukan" in html or "no results" in html or "no video found" in html:
                    if qlow not in html:
                        return False
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
        q_path = urllib.parse.quote(q)
        valid = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as ex:
            futs = {ex.submit(cek_valid, tpl.replace("{q_plus}", q_plus).replace("{q_path}", q_path), q, d): (d, tpl.replace("{q_plus}", q_plus).replace("{q_path}", q_path)) for d, tpl in TEMPLATES.items()}
            for f in concurrent.futures.as_completed(futs):
                d, url = futs[f]
                if f.result():
                    valid.append({"title": f"{q} di {d}", "url": url, "source": d, "valid": True})
        self.wfile.write(json.dumps({"query": q, "results": valid}, ensure_ascii=False).encode())
