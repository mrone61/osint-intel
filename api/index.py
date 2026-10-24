from http.server import BaseHTTPRequestHandler
import urllib.parse, json, urllib.request, re, concurrent.futures

TEMPLATES = {
"detik.com": "https://www.detik.com/search/searchall?query={q}",
"kompas.com": "https://www.kompas.com/search?q={q}",
"cnnindonesia.com": "https://www.cnnindonesia.com/search?query={q}",
"tribunnews.com": "https://www.tribunnews.com/search?q={q}",
"tempo.co": "https://www.tempo.co/search?q={q}",
"pddikti.kemdiktisaintek.go.id": "https://pddikti.kemdiktisaintek.go.id/search/{q}",
"sinta.kemdiktisaintek.go.id": "https://sinta.kemdiktisaintek.go.id/authors?q={q}",
"garuda.kemdikbud.go.id": "https://garuda.kemdikbud.go.id/documents?q={q}",
"wikipedia.org": "https://en.wikipedia.org/w/index.php?search={q}",
"youtube.com": "https://www.youtube.com/results?search_query={q}",
"scholar.google.com": "https://scholar.google.com/scholar?q={q}",
}

def validate_url(url, query):
    """Cek langsung ke situsnya, apakah nama ada"""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as r:
            html = r.read().decode('utf-8', errors='ignore')
            html_low = html.lower()
            q_low = query.lower()
            
            # Untuk PDDIKTI / SINTA - kalau ada tulisan hasil / ditemukan = HIJAU
            # PDDIKTI kalau gak ketemu biasanya ada kata "tidak ditemukan" / "data tidak ditemukan"
            if "pddikti" in url or "sinta" in url or "garuda" in url:
                if "tidak ditemukan" in html_low or "data tidak ditemukan" in html_low or "no result" in html_low or "0 results" in html_low:
                    return False
                # kalau ada nama itu di HTML atau ada tabel hasil
                if q_low in html_low or "mahasiswa" in html_low or "author" in html_low:
                    return True
                return True # PDDIKTI sering load via JS, kalau bisa diakses anggap HIJAU biar lu cek manual
            
            # Untuk berita - cek apakah query muncul di hasil search
            if q_low in html_low:
                return True
            return False
    except Exception as e:
        # Kalau diblock / error, jangan langsung MERAH, anggap BUTUH CEK MANUAL = HIJAU
        # Biar lu tetap bisa klik
        return True

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('q',[''])[0].strip()
        self.send_response(200)
        self.send_header('Content-type','application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        if not q:
            self.wfile.write(b'{"error":"need ?q"}'); return
        
        q_enc = urllib.parse.quote_plus(q)
        
        # Buat semua URL dulu
        urls = []
        for domain, tpl in TEMPLATES.items():
            url = tpl.replace("{q}", q_enc)
            urls.append((domain, url))
        
        # Validasi parallel 8 detik max
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            future_to_domain = {executor.submit(validate_url, url, q): (domain, url) for domain, url in urls}
            for future in concurrent.futures.as_completed(future_to_domain):
                domain, url = future_to_domain[future]
                try:
                    is_green = future.result()
                except:
                    is_green = True
                results.append({
                    "title": f"Cari '{q}' di {domain}",
                    "url": url,
                    "source": domain,
                    "valid": is_green,
                    "status_text": "✓ TERDETEKSI / CEK MANUAL" if is_green else "✗ TIDAK DITEMUKAN DI SITUS ITU"
                })
        
        self.wfile.write(json.dumps({"query": q, "results": results}, ensure_ascii=False).encode())
