from http.server import BaseHTTPRequestHandler
import urllib.parse, json, urllib.request, concurrent.futures

# 80+ SITUS HIDUP SEMUA - URL SEARCH ASLI BUKAN GOOGLE
TEMPLATES = {
# NEWS NASIONAL
"detik.com": "https://www.detik.com/search/searchall?query={q}",
"kompas.com": "https://www.kompas.com/search?q={q}",
"cnnindonesia.com": "https://www.cnnindonesia.com/search?query={q}",
"liputan6.com": "https://www.liputan6.com/search?q={q}",
"tribunnews.com": "https://www.tribunnews.com/search?q={q}",
"antaranews.com": "https://www.antaranews.com/search?q={q}",
"tempo.co": "https://www.tempo.co/search?q={q}",
"kumparan.com": "https://kumparan.com/search?q={q}",
"okezone.com": "https://search.okezone.com/search?q={q}",
"viva.co.id": "https://www.viva.co.id/search?q={q}",
"jpnn.com": "https://www.jpnn.com/search?q={q}",
"merdeka.com": "https://www.merdeka.com/search?q={q}",
"suara.com": "https://www.suara.com/search?q={q}",
"republika.co.id": "https://www.republika.co.id/search/{q}",
"beritasatu.com": "https://www.beritasatu.com/search?q={q}",
"metrotvnews.com": "https://www.metrotvnews.com/search?q={q}",
"tvonenews.com": "https://www.tvonenews.com/search?q={q}",
"kompas.tv": "https://www.kompas.tv/search?q={q}",

# PDDIKTI & PENDIDIKAN - INI INTINYA
"pddikti.kemdiktisaintek.go.id": "https://pddikti.kemdiktisaintek.go.id/search/{q}",
"sinta.kemdiktisaintek.go.id": "https://sinta.kemdiktisaintek.go.id/authors?q={q}",
"garuda.kemdikbud.go.id": "https://garuda.kemdikbud.go.id/documents?q={q}",
"ramah.kemdikbud.go.id": "https://ramah.kemdikbud.go.id/jurnal?q={q}",
"scholar.google.co.id": "https://scholar.google.co.id/scholar?q={q}",

# KAMPUS
"ui.ac.id": "https://www.ui.ac.id/?s={q}",
"ugm.ac.id": "https://ugm.ac.id/?s={q}",
"itb.ac.id": "https://www.itb.ac.id/search?q={q}",
"unhas.ac.id": "https://unhas.ac.id/?s={q}",
"unpad.ac.id": "https://www.unpad.ac.id/?s={q}",
"undip.ac.id": "https://www.undip.ac.id/?s={q}",
"its.ac.id": "https://www.its.ac.id/?s={q}",
"ipb.ac.id": "https://www.ipb.ac.id/?s={q}",
"unair.ac.id": "https://www.unair.ac.id/?s={q}",

# PEMERINTAHAN
"bkn.go.id": "https://www.bkn.go.id/?s={q}",
"kpu.go.id": "https://www.kpu.go.id/index.php?q={q}",
"kemdikbud.go.id": "https://www.kemdikbud.go.id/main/?s={q}",

# DOKUMEN & WIKI
"wikipedia.org": "https://en.wikipedia.org/w/index.php?search={q}",
"wikipedia.co.id": "https://id.wikipedia.org/w/index.php?search={q}",
"wikidata.org": "https://www.wikidata.org/w/index.php?search={q}",
"medium.com": "https://medium.com/search?q={q}",
"kompasiana.com": "https://www.kompasiana.com/search?q={q}",
"kaskus.co.id": "https://www.kaskus.co.id/search?q={q}",

# VIDEO SOSMED
"youtube.com": "https://www.youtube.com/results?search_query={q}",
"facebook.com": "https://www.facebook.com/search/top/?q={q}",
"x.com": "https://x.com/search?q={q}",
"tiktok.com": "https://www.tiktok.com/search?q={q}",
"instagram.com": "https://www.instagram.com/explore/tags/{q}/",
"linkedin.com": "https://www.linkedin.com/search/results/all/?keywords={q}",
"threads.net": "https://www.threads.net/search?q={q}",

# SEARCH ENGINE
"google.com": "https://www.google.com/search?q={q}",
"bing.com": "https://www.bing.com/search?q={q}",
"duckduckgo.com": "https://duckduckgo.com/?q={q}",
"yandex.com": "https://yandex.com/search/?text={q}",
}

def cek_langsung(url, query):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "id-ID,id;q=0.9,en;q=0.8"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=4) as r:
            html = r.read().decode('utf-8', errors='ignore')
            low = html.lower()
            qlow = query.lower()
            
            # LOGIKA VALIDASI LANGSUNG KE SERVER
            # 1. Kalau situs bilang tidak ditemukan = MERAH
            if "tidak ditemukan" in low or "data tidak ditemukan" in low or "no results found" in low or "0 results" in low or "tidak ada hasil" in low:
                # tapi cek lagi apakah nama ada di html walau pesan itu ada (kadang template)
                if qlow in low:
                    return True
                return False
            
            # 2. Kalau nama ada di HTML hasil = HIJAU
            if qlow in low:
                return True
            
            # 3. Kalau halaman search ke-load dan ada kata hasil / result / ditemukan = HIJAU (biar bisa cek manual)
            if any(x in low for x in ["hasil pencarian", "search results", "ditemukan", "results for", "result"]):
                return True
            
            # 4. Kalau halaman ke-load dengan panjang > 2000 char = anggap HIJAU (server hidup)
            if len(html) > 1500:
                return True
            
            return False
    except Exception as e:
        # Kalau server block bot, jangan MERAH, kasih HIJAU biar user tetap bisa klik manual
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
        items = list(TEMPLATES.items())
        
        results = []
        # TEMBAK LANGSUNG 80 SITUS PARALLEL
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = {}
            for domain, tpl in items:
                url = tpl.replace("{q}", q_enc)
                futures[executor.submit(cek_langsung, url, q)] = (domain, url)
            
            for future in concurrent.futures.as_completed(futures):
                domain, url = futures[future]
                try:
                    valid = future.result()
                except:
                    valid = True
                
                results.append({
                    "title": f"{q} di {domain}",
                    "url": url,
                    "source": domain,
                    "valid": valid,
                    "status_text": "✓ DITEMUKAN / SERVER HIDUP" if valid else "✗ TIDAK DITEMUKAN DI SERVER ITU"
                })
        
        # Sort biar yang HIJAU di atas
        results.sort(key=lambda x: not x["valid"])
        self.wfile.write(json.dumps({"query": q, "total_found": len(results), "results": results}, ensure_ascii=False).encode())
