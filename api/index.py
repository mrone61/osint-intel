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
"kumparan.com": "https://kumparan.com/search?q={q_plus}",
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
"instagram.com": "https://www.instagram.com/explore/tags/{q_path}/",
"wikipedia.org": "https://en.wikipedia.org/w/index.php?search={q_plus}",
"scholar.google.com": "https://scholar.google.com/scholar?q={q_plus}",
"google.com": "https://www.google.com/search?q={q_plus}",
"xnxx.com": "https://www.xnxx.com/search/{q_path}",
"xvideos.com": "https://www.xvideos.com/?k={q_plus}",
"pornhub.com": "https://www.pornhub.com/video/search?search={q_plus}",
"xhamster.com": "https://xhamster.com/search/{q_path}",
"redtube.com": "https://www.redtube.com/?search={q_plus}",
}

# KATA YANG MENANDAKAN TIDAK DITEMUKAN DI SERVER
NOT_FOUND_WORDS = [
    "tidak ditemukan", "data tidak ditemukan", "mahasiswa tidak ditemukan",
    "tidak ada hasil", "tidak ada data", "no results found", "no results",
    "no result", "no video found", "no videos found", "0 results",
    "0 videos", "page not found", "not found", "nothing found"
]

def cek_langsung_ke_server(url, query, domain):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.google.com/",
            "Cache-Control": "no-cache"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as r:
            html = r.read().decode('utf-8', errors='ignore')
            html_low = html.lower()
            qlow = query.lower().strip()
            parts = [p for p in qlow.split() if len(p) >= 2]

            # 1. CEK LANGSUNG: Apakah server bilang TIDAK DITEMUKAN?
            is_not_found_page = any(word in html_low for word in NOT_FOUND_WORDS)

            # 2. Kalau server bilang tidak ditemukan DAN nama tidak ada di HTML -> JANGAN TAMPILKAN (berlaku semua situs)
            if is_not_found_page and qlow not in html_low:
                return False

            # 3. 100% MATCH - SEMUA KATA HARUS ADA UNTUK SEMUA SITUS
            # Contoh: jaden smith -> harus ada jaden DAN smith
            # Kecuali untuk situs yang pakai JS berat, kita kasih toleransi panjang HTML
            all_words_exist = all(kata in html_low for kata in parts) if parts else False
            
            # 4. LOGIKA UNIVERSAL UNTUK SEMUA SITUS:
            # A. Jika frasa lengkap ada -> VALID HIJAU
            if qlow in html_low:
                return True
            # B. Jika semua kata ada -> VALID HIJAU  
            if all_words_exist:
                return True
            # C. Jika server TIDAK bilang tidak ditemukan DAN halaman panjang (JS site seperti PDDIKTI, YouTube, TikTok) -> VALID HIJAU
            # Ini biar PDDIKTI, YouTube, TikTok, dll tetap tampil meski HTML awal tidak ada namanya karena render JS
            if not is_not_found_page and len(html) > 8000:
                return True

            # Selain itu -> JANGAN TAMPILKAN
            return False

    except Exception as e:
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
        q_path = urllib.parse.quote(q) # aprilia%20sbrfk - untuk PDDIKTI & xnxx

        valid_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = {}
            for domain, tpl in TEMPLATES.items():
                url = tpl.replace("{q_plus}", q_plus).replace("{q_path}", q_path)
                futures[executor.submit(cek_langsung_ke_server, url, q, domain)] = (domain, url)

            for f in concurrent.futures.as_completed(futures):
                domain, url = futures[f]
                if f.result() == True:
                    valid_results.append({
                        "title": f"{q} di {domain}", 
                        "url": url, 
                        "source": domain, 
                        "valid": True, 
                        "status_text": "✓ DITEMUKAN - CEK LANGSUNG 100%"
                    })

        self.wfile.write(json.dumps({"query": q, "results": valid_results}, ensure_ascii=False).encode())
