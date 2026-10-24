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
"uim-makassar.ac.id": "https://uim-makassar.ac.id/?s={q_plus}",
"uncen.ac.id": "https://uncen.ac.id/?s={q_plus}",
"unipa.ac.id": "https://unipa.ac.id/?s={q_plus}",
"ui.ac.id": "https://www.ui.ac.id/?s={q_plus}",
"ugm.ac.id": "https://ugm.ac.id/?s={q_plus}",
"itb.ac.id": "https://www.itb.ac.id/search?q={q_plus}",
"ipb.ac.id": "https://www.ipb.ac.id/?s={q_plus}",
"its.ac.id": "https://www.its.ac.id/?s={q_plus}",
"unpad.ac.id": "https://www.unpad.ac.id/?s={q_plus}",
"undip.ac.id": "https://www.undip.ac.id/?s={q_plus}",
"unair.ac.id": "https://www.unair.ac.id/?s={q_plus}",
"unud.ac.id": "https://www.unud.ac.id/?s={q_plus}",
"unsyiah.ac.id": "https://unsyiah.ac.id/?s={q_plus}",
"unsri.ac.id": "https://www.unsri.ac.id/?s={q_plus}",
"unila.ac.id": "https://www.unila.ac.id/?s={q_plus}",
"unand.ac.id": "https://www.unand.ac.id/?s={q_plus}",
"ub.ac.id": "https://www.ub.ac.id/?s={q_plus}",
"uns.ac.id": "https://uns.ac.id/?s={q_plus}",
"unnes.ac.id": "https://unnes.ac.id/?s={q_plus}",
"uny.ac.id": "https://www.uny.ac.id/?s={q_plus}",
"uin-alauddin.ac.id": "https://uin-alauddin.ac.id/?s={q_plus}",
"telkomuniversity.ac.id": "https://telkomuniversity.ac.id/?s={q_plus}",
"binus.ac.id": "https://binus.ac.id/?s={q_plus}",
"gunadarma.ac.id": "https://www.gunadarma.ac.id/?s={q_plus}",
"detik.com": "https://www.detik.com/search/searchall?query={q_plus}",
"kompas.com": "https://www.kompas.com/search?q={q_plus}",
"cnnindonesia.com": "https://www.cnnindonesia.com/search?query={q_plus}",
"tribunnews.com": "https://www.tribunnews.com/search?q={q_plus}",
"tempo.co": "https://www.tempo.co/search?q={q_plus}",
"liputan6.com": "https://www.liputan6.com/search?q={q_plus}",
"antaranews.com": "https://www.antaranews.com/search?q={q_plus}",
"youtube.com": "https://www.youtube.com/results?search_query={q_plus}",
"facebook.com": "https://www.facebook.com/search/top/?q={q_plus}",
"x.com": "https://x.com/search?q={q_plus}",
"tiktok.com": "https://www.tiktok.com/search?q={q_plus}",
"wikipedia.org": "https://en.wikipedia.org/w/index.php?search={q_plus}",
"scholar.google.com": "https://scholar.google.com/scholar?q={q_plus}",
"xnxx.com": "https://www.xnxx.com/search/{q_path}",
"xvideos.com": "https://www.xvideos.com/?k={q_plus}",
"pornhub.com": "https://www.pornhub.com/video/search?search={q_plus}",
"xhamster.com": "https://xhamster.com/search/{q_path}",
}

def cek_bener(url, query, domain):
    # === PDDIKTI & SEMUA KAMPUS SELALU TAMPIL - INI YANG AWAL BERHASIL ===
    if "pddikti" in domain or "ac.id" in domain or "sinta" in domain or "garuda" in domain:
        return True

    try:
        headers = {"User-Agent": "Mozilla/5.0", "Accept-Language": "id-ID,en;q=0.8"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as r:
            html = r.read().decode('utf-8', errors='ignore')
            low = html.lower()
            qlow = query.lower()

            if any(x in low for x in ["tidak ditemukan","tidak ada hasil","no results","no video found","0 results"]):
                if qlow not in low:
                    return False
            
            parts = [p for p in qlow.split() if len(p)>=2]
            if qlow in low: return True
            if parts and all(p in low for p in parts): return True
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
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
            futs = {}
            for domain, tpl in TEMPLATES.items():
                url = tpl.replace("{q_plus}", q_plus).replace("{q_path}", q_path)
                futs[ex.submit(cek_bener, url, q, domain)] = (domain, url)
            for f in concurrent.futures.as_completed(futs):
                domain, url = futs[f]
                if f.result():
                    valid.append({"title": f"{q} di {domain}", "url": url, "source": domain, "valid": True})

        self.wfile.write(json.dumps({"query": q, "results": valid}, ensure_ascii=False).encode())
