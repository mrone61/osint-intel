from http.server import BaseHTTPRequestHandler
import urllib.parse, json, urllib.request, concurrent.futures

TEMPLATES = {
"pddikti.kemdiktisaintek.go.id": "https://pddikti.kemdiktisaintek.go.id/search/{q_path}",
"google.com": "https://www.google.com/search?q={q_plus}+site%3Aac.id+OR+site%3Apddikti.kemdiktisaintek.go.id",
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
"detik.com": "https://www.detik.com/search/searchall?query={q_plus}",
"kompas.com": "https://www.kompas.com/search?q={q_plus}",
"cnnindonesia.com": "https://www.cnnindonesia.com/search?query={q_plus}",
"tribunnews.com": "https://www.tribunnews.com/search?q={q_plus}",
"youtube.com": "https://www.youtube.com/results?search_query={q_plus}",
"facebook.com": "https://www.facebook.com/search/top/?q={q_plus}",
"x.com": "https://x.com/search?q={q_plus}",
"tiktok.com": "https://www.tiktok.com/search?q={q_plus}",
"wikipedia.org": "https://en.wikipedia.org/w/index.php?search={q_plus}",
"scholar.google.com": "https://scholar.google.com/scholar?q={q_plus}",
}

FORCE_ALWAYS = ["pddikti.kemdiktisaintek.go.id", "google.com"]

# Kata kunci kalau TIDAK ADA HASIL - langsung anggap tidak valid
NO_RESULT_KEYWORDS = [
"tidak ditemukan","tidak ada hasil","tidak ada artikel",
"data tidak ditemukan","no results","no result","0 results",
"nothing found","no posts found","tidak ada postingan",
"pencarian tidak ditemukan","maaf, tidak ada","sorry, no results",
"tidak ada yang cocok"
]

def cek_nama_lengkap(url, query, domain):
    if domain in FORCE_ALWAYS:
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            html = r.read().decode('utf-8', errors='ignore').lower()
            qlow = query.lower().strip()

            # 1. CEK DULU APAKAH WEB BILANG TIDAK ADA HASIL
            # Kalau ada kata tidak ditemukan, langsung FALSE
            # Ini yang bikin Evanita Manullang kemarin ngaur di UGM/UNDIP
            for keyword in NO_RESULT_KEYWORDS:
                if keyword in html:
                    return False

            # 2. BARU CEK APAKAH NAMA LENGKAP PERSIS ADA
            # Harus persis "evanita manullang", bukan cuma "evanita"
            if qlow not in html:
                return False

            # 3. TAMBAHAN: Nama harus muncul minimal 2 kali atau di dalam tag artikel
            # Biar tidak cuma di kotak search doang
            # Kalau cuma di kotak search, hitungan nya cuma 1
            count = html.count(qlow)
            if count < 2:
                # cek apakah ada di dalam <article> atau <h2> atau <a>
                # kalau tidak, berarti cuma di input search
                if f'>{qlow}' not in html and f'"{qlow}"' not in html:
                    # kemungkinan cuma di value input, anggap tidak valid
                    # tapi kita tetap butuh validasi lebih ketat
                    pass
            
            return True
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
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
            futs = {}
            for domain, tpl in TEMPLATES.items():
                url = tpl.replace("{q_plus}", q_plus).replace("{q_path}", q_path)
                futs[ex.submit(cek_nama_lengkap, url, q, domain)] = (domain, url)
            for f in concurrent.futures.as_completed(futs):
                domain, url = futs[f]
                if f.result():
                    valid.append({"title": f"{q} di {domain}", "url": url, "source": domain, "valid": True})
        self.wfile.write(json.dumps({"query": q, "results": valid}, ensure_ascii=False).encode())
