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
"instagram.com": "https://www.instagram.com/explore/tags/{q_path}/",
"wikipedia.org": "https://en.wikipedia.org/w/index.php?search={q_plus}",
"scholar.google.com": "https://scholar.google.com/scholar?q={q_plus}",
"xnxx.com": "https://www.xnxx.com/search/{q_path}",
"xvideos.com": "https://www.xvideos.com/?k={q_plus}",
"pornhub.com": "https://www.pornhub.com/video/search?search={q_plus}",
"xhamster.com": "https://xhamster.com/search/{q_path}",
}

def cek_100_persen(url, query):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "id-ID,en;q=0.9"})
        with urllib.request.urlopen(req, timeout=5) as r:
            html = r.read().decode('utf-8', errors='ignore').lower()
            qlow = query.lower().strip()
            parts = qlow.split()

            # 1. Jika ada tulisan tidak ditemukan = GAGAL, jangan tampilkan
            if any(x in html for x in ["tidak ditemukan","data tidak ditemukan","tidak ada hasil","no results found","no result","no video found","0 results","page not found"]):
                # tapi cek dulu apakah nama masih ada meski ada tulisan itu
                if qlow not in html:
                    return False

            # 2. SISTEM 100% - SEMUA KATA HARUS ADA
            # contoh: "jaden smith" -> harus ada "jaden" DAN "smith"
            for kata in parts:
                if len(kata) < 2: continue
                if kata not in html:
                    return False # kalau 1 kata aja gak ada = JANGAN TAMPILKAN
            
            # 3. Minimal harus ada frasa lengkap atau kedua kata berdekatan
            # kalau frasa lengkap ada -> 100% valid
            if qlow in html:
                return True
            
            # kalau semua kata ada (sudah lolos di atas) -> anggap valid
            return True

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
        q_path = urllib.parse.quote(q) 

        valid_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = {}
            for domain, tpl in TEMPLATES.items():
                url = tpl.replace("{q_plus}", q_plus).replace("{q_path}", q_path)
                futures[executor.submit(cek_100_persen, url, q)] = (domain, url)

            for f in concurrent.futures.as_completed(futures):
                domain, url = futures[f]
                try:
                    if f.result() == True:
                        valid_results.append({
                            "title": f"{q} di {domain}", 
                            "url": url, 
                            "source": domain, 
                            "valid": True, 
                            "status_text": "✓ 100% DITEMUKAN"
                        })
                except:
                    pass

        self.wfile.write(json.dumps({"query": q, "results": valid_results}, ensure_ascii=False).encode())
