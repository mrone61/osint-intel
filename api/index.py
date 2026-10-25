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

FORCE_ALWAYS = [] # KOSONGKAN, SEMUA WAJIB VALIDASI KETAT

NO_RESULT_PHRASES = [
"tidak ditemukan","tidak ada hasil","data tidak ditemukan",
"no results found","0 results","nothing found","no posts found",
"pencarian tidak ditemukan","berita tidak ditemukan","tidak ada artikel",
"tidak ada yang cocok","hasil tidak ditemukan","maaf, tidak ada",
"your search -","did not match any documents","tidak ada yang ditemukan",
"maaf, tidak ada hasil","sorry, but nothing matched","no results matching"
]

def cek_pddikti_valid(query):
    try:
        q_plus = urllib.parse.quote_plus(query)
        api_url = f"https://pddikti.kemdiktisaintek.go.id/api/search/mahasiswa?keyword={q_plus}"
        req = urllib.request.Request(api_url, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://pddikti.kemdiktisaintek.go.id/",
            "Accept": "application/json"
        })
        with urllib.request.urlopen(req, timeout=8) as r:
            raw = r.read().decode('utf-8', errors='ignore')
            if '"total":0' in raw or '"data":[]' in raw or raw.strip() == '[]' or len(raw) < 60:
                return False
            if query.lower() in raw.lower():
                return True
            return False
    except:
        return False

def cek_google_valid(low_text, qlow):
    # Google kalau zonk ada frasa ini
    if "did not match any documents" in low_text or "tidak menemukan hasil" in low_text or "no results found" in low_text:
        return False
    # Kalau cuma ada di search box, bukan hasil
    if f'id="result-stats"' not in low_text and 'id="search"' not in low_text and 'data-ved' not in low_text:
        # Google blokir bot / captcha
        return False
    return True

def cek_valid(url, query, domain):
    if "pddikti" in domain:
        return cek_pddikti_valid(query)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=7) as r:
            raw = r.read().decode('utf-8', errors='ignore')
            low = raw.lower()
            qlow = query.lower().strip()

            # 1. Cek frasa gagal dulu (paling penting)
            for phrase in NO_RESULT_PHRASES:
                if phrase in low:
                    return False

            # 2. Bersihkan jebakan search header
            # Hapus semua "Search Results for: Manfret Nando Kambu"
            clean_for_check = re.sub(r'search results for[^<]{0,100}', ' ', low)
            clean_for_check = re.sub(r'hasil pencarian untuk[^<]{0,100}', ' ', clean_for_check)
            clean_for_check = re.sub(r'search result for[^<]{0,100}', ' ', clean_for_check)
            clean_for_check = re.sub(r'<title.*?</title>', ' ', clean_for_check, flags=re.DOTALL)
            clean_for_check = re.sub(r'<input[^>]*>', ' ', clean_for_check)

            if qlow not in clean_for_check:
                return False

            # 3. Validasi khusus Google
            if "google.com" in domain:
                return cek_google_valid(low, qlow)

            # 4. Validasi ketat untuk kampus & berita
            # Harus ada di dalam <a> atau <article> atau <h2>/h3 yang BUKAN header search
            articles = re.findall(r'<article[^>]*>(.*?)</article>', low, flags=re.DOTALL)
            links = re.findall(r'<a[^>]*>(.*?)</a>', low, flags=re.DOTALL)
            headings = re.findall(r'<h2[^>]*>(.*?)</h2>|<h3[^>]*>(.*?)</h3>', low, flags=re.DOTALL)
            
            # Gabungkan semua konten yang dianggap hasil
            real_results = []
            for a in articles:
                real_results.append(a)
            for l in links:
                # Abaikan link menu/navigasi pendek
                if len(l.strip()) > 10:
                    real_results.append(l)
            for h in headings:
                # h adalah tuple karena ada 2 grup
                text = ''.join(h)
                if 'search results for' not in text and 'hasil pencarian' not in text:
                    real_results.append(text)

            found_real = False
            for res in real_results:
                if qlow in res.lower():
                    found_real = True
                    break
            
            if domain.endswith('.ac.id') or 'sinta' in domain or 'garuda' in domain:
                return found_real
            
            return found_real or (qlow in clean_for_check)

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
