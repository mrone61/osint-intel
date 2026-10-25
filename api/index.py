from http.server import BaseHTTPRequestHandler
import urllib.parse, json, urllib.request, concurrent.futures, re

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
"ui.ac.id": "https://www.ui.ac.id/?s={q_plus}",
"ugm.ac.id": "https://ugm.ac.id/?s={q_plus}",
"itb.ac.id": "https://www.itb.ac.id/search?q={q_plus}",
"ipb.ac.id": "https://www.ipb.ac.id/?s={q_plus}",
"its.ac.id": "https://www.its.ac.id/?s={q_plus}",
"detik.com": "https://www.detik.com/search/searchall?query={q_plus}",
"kompas.com": "https://www.kompas.com/search?q={q_plus}",
"cnnindonesia.com": "https://www.cnnindonesia.com/search?query={q_plus}",
"tribunnews.com": "https://www.tribunnews.com/search?q={q_plus}",
"youtube.com": "https://www.youtube.com/results?search_query={q_plus}",
"wikipedia.org": "https://en.wikipedia.org/w/index.php?search={q_plus}",
}

FORCE_ALWAYS = ["google.com"] # PDDIKTI DIHAPUS DARI SINI

NO_RESULT = [
"tidak ditemukan","tidak ada hasil","data tidak ditemukan",
"no results found","0 results","nothing found","no posts found",
"pencarian tidak ditemukan","berita tidak ditemukan","tidak ada artikel",
"tidak ada yang cocok","hasil tidak ditemukan","maaf, tidak ada"
]

def cek_pddikti_valid(query):
    # PDDIKTI validasi via API frontend-nya, bukan HTML search-nya
    try:
        q_plus = urllib.parse.quote_plus(query)
        # Ini endpoint search mahasiswa yang dipakai frontend PDDIKTI
        api_url = f"https://pddikti.kemdiktisaintek.go.id/api/search/mahasiswa?keyword={q_plus}"
        req = urllib.request.Request(api_url, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://pddikti.kemdiktisaintek.go.id/",
            "Accept": "application/json"
        })
        with urllib.request.urlopen(req, timeout=8) as r:
            raw = r.read().decode('utf-8', errors='ignore')
            # Kalau API return array kosong atau count 0 = tidak valid
            if '"total":0' in raw or '"data":[]' in raw or raw.strip() == '[]' or len(raw) < 50:
                return False
            # Kalau nama ada di json response = valid
            if query.lower() in raw.lower():
                return True
            return False
    except:
        # Fallback: coba endpoint kedua (versi lama)
        try:
            api_url2 = f"https://api-frontend.kemdikbud.go.id/search_mhs/{urllib.parse.quote(query)}"
            req2 = urllib.request.Request(api_url2, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req2, timeout=8) as r2:
                raw2 = r2.read().decode('utf-8', errors='ignore')
                if query.lower() in raw2.lower() and len(raw2) > 100:
                    return True
            return False
        except:
            return False

def cek_valid(url, query, domain):
    # Handler khusus PDDIKTI
    if "pddikti" in domain:
        return cek_pddikti_valid(query)

    if domain in FORCE_ALWAYS:
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=7) as r:
            raw = r.read().decode('utf-8', errors='ignore')
            low = raw.lower()
            qlow = query.lower().strip()

            for k in NO_RESULT:
                if k in low:
                    return False

            # Bersihkan tag yang mengecoh
            clean = re.sub(r'<input[^>]*>', ' ', low)
            clean = re.sub(r'<title[^>]*>.*?</title>', ' ', clean)
            clean = re.sub(r'<meta[^>]*>', ' ', clean)
            clean = re.sub(r'<script.*?</script>', ' ', clean, flags=re.DOTALL)
            clean = re.sub(r'<style.*?</style>', ' ', clean, flags=re.DOTALL)

            if qlow not in clean:
                return False

            # Validasi ketat untuk portal berita & kampus
            links = re.findall(r'<a[^>]*>(.*?)</a>', clean)
            found_in_link = any(qlow in lt.lower() for lt in links if lt.strip())
            
            if not found_in_link:
                headings = re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', clean)
                found_in_link = any(qlow in h.lower() for h in headings)

            if domain.endswith('.ac.id') or any(x in domain for x in ['cnn','detik','kompas','tribun','sinta','garuda']):
                if not found_in_link:
                    return False

            return True
    except Exception:
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
                futs[ex.submit(cek_valid, url, q, domain)] = (domain, url)
            for f in concurrent.futures.as_completed(futs):
                domain, url = futs[f]
                if f.result():
                    valid.append({"title": f"{q} di {domain}", "url": url, "source": domain, "valid": True})
        self.wfile.write(json.dumps({"query": q, "results": valid}, ensure_ascii=False).encode())
