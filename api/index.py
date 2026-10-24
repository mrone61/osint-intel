from http.server import BaseHTTPRequestHandler
import urllib.parse, json, urllib.request, concurrent.futures

TEMPLATES = {
"pddikti.kemdiktisaintek.go.id": "https://pddikti.kemdiktisaintek.go.id/search/{q_path}",
"sinta.kemdiktisaintek.go.id": "https://sinta.kemdiktisaintek.go.id/authors?q={q_plus}",
"garuda.kemdikbud.go.id": "https://garuda.kemdikbud.go.id/documents?q={q_plus}",
"detik.com": "https://www.detik.com/search/searchall?query={q_plus}",
"kompas.com": "https://www.kompas.com/search?q={q_plus}",
"cnnindonesia.com": "https://www.cnnindonesia.com/search?query={q_plus}",
"tribunnews.com": "https://www.tribunnews.com/search?q={q_plus}",
"tempo.co": "https://www.tempo.co/search?q={q_plus}",
"liputan6.com": "https://www.liputan6.com/search?q={q_plus}",
"antaranews.com": "https://www.antaranews.com/search?q={q_plus}",
"ui.ac.id": "https://www.ui.ac.id/?s={q_plus}",
"ugm.ac.id": "https://ugm.ac.id/?s={q_plus}",
"itb.ac.id": "https://www.itb.ac.id/search?q={q_plus}",
"unhas.ac.id": "https://unhas.ac.id/?s={q_plus}",
"ipb.ac.id": "https://www.ipb.ac.id/?s={q_plus}",
"its.ac.id": "https://www.its.ac.id/?s={q_plus}",
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
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as r:
            html = r.read().decode('utf-8', errors='ignore')
            html_low = html.lower()
            qlow = query.lower()

            # === SISTEM PDDIKTI ASLI YANG SUDAH BERHASIL - BERLAKU SEMUA SITUS ===
            # 1. Jika server bilang TIDAK DITEMUKAN -> JANGAN TAMPILKAN (ini yang bener)
            if "pddikti" in domain:
                if "tidak ditemukan" in html_low or "mahasiswa tidak ditemukan" in html_low or "data tidak ditemukan" in html_low:
                    return False
                # Jika tidak ada tulisan tidak ditemukan, ANGGAP ADA - TAMPILKAN
                # Karena PDDIKTI pakai JS, HTML tidak ada namanya tapi di browser ada
                return True
            
            # 2. UNTUK SEMUA SITUS LAIN - LOGIKA SAMA PERSIS KAYAK PDDIKTI AWAL
            # Cek apakah ada tulisan tidak ditemukan KHUSUS situs itu
            not_found_id = ["tidak ditemukan", "tidak ada hasil", "data tidak ditemukan"]
            not_found_en = ["no results found", "no results", "no video found", "0 results", "no videos found"]
            
            # Jika ada tulisan tidak ditemukan
            if any(x in html_low for x in not_found_id + not_found_en):
                # Tapi kalau nama masih ada di HTML, tetap tampilkan (kadang web nulis no results tapi tetap ada hasil)
                if qlow in html_low:
                    return True
                # Jika benar-benar tidak ada nama + ada tulisan tidak ditemukan = JANGAN TAMPILKAN
                return False
            
            # Jika tidak ada tulisan tidak ditemukan, cek apakah nama ada 100%
            # Contoh jaden smith -> harus ada jaden dan smith
            parts = [p for p in qlow.split() if len(p) >=2]
            if qlow in html_low:
                return True
            if parts and all(p in html_low for p in parts):
                return True
            
            # Jika tidak ada tulisan tidak ditemukan tapi juga tidak ada nama -> JANGAN TAMPILKAN
            # Biar tidak ngaur
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

        valid = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as ex:
            futs = {}
            for domain, tpl in TEMPLATES.items():
                url = tpl.replace("{q_plus}", q_plus).replace("{q_path}", q_path)
                futs[ex.submit(cek_bener, url, q, domain)] = (domain, url)
            for f in concurrent.futures.as_completed(futs):
                domain, url = futs[f]
                if f.result():
                    valid.append({"title": f"{q} di {domain}", "url": url, "source": domain, "valid": True, "status_text": "✓ DITEMUKAN"})

        self.wfile.write(json.dumps({"query": q, "results": valid}, ensure_ascii=False).encode())
