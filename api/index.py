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

NO_RESULT = ["tidak ditemukan","tidak ada hasil","data tidak ditemukan","no results found","nothing found","no posts found","pencarian tidak ditemukan","berita tidak ditemukan","hasil tidak ditemukan","did not match any documents","sorry, but nothing matched","oops","artikel tidak ditemukan","belum ada artikel","tidak ada berita"]

def is_angka_ngarang(q):
    q = q.strip()
    # Kalau cuma angka atau 1 kata pendek = anggap ngarang
    if q.isdigit(): return True
    if len(q.split()) == 1 and len(q) < 15: 
        # bisa jadi NIM, tapi kita cek ketat nanti
        return False
    return False

def cek_pddikti_fix(query):
    q_plus = urllib.parse.quote_plus(query)
    q_lower = query.lower()
    # 5 endpoint yang dipakai frontend PDDIKTI terbaru
    urls = [
        f"https://pddikti.kemdiktisaintek.go.id/api/search/mahasiswa?keyword={q_plus}",
        f"https://pddikti.kemdiktisaintek.go.id/api/search/dosen?keyword={q_plus}",
        f"https://pddikti.kemdiktisaintek.go.id/api/search/dosen?nama={q_plus}",
        f"https://api-frontend.kemdikbud.go.id/search_mhs/{q_plus}",
        f"https://api-frontend.kemdikbud.go.id/search_dosen/{q_plus}",
        f"https://sinta.kemdiktisaintek.go.id/authors?q={q_plus}", # BACKUP: dosen pasti ada di SINTA
    ]
    for api_url in urls:
        try:
            req = urllib.request.Request(api_url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Referer": "https://pddikti.kemdiktisaintek.go.id/",
                "Accept": "application/json, text/html, */*"
            })
            with urllib.request.urlopen(req, timeout=10) as r:
                raw = r.read().decode('utf-8', errors='ignore')
                low = raw.lower()
                if len(raw) < 40: continue
                if '"total":0' in low or '"data":[]' in low or '"count":0' in low: 
                    continue
                # Kalau nama ada di response
                if q_lower in low:
                    # Pastikan bukan cuma echo keyword kosong
                    if "mahasiswa" in low or "dosen" in low or "author" in low or "nidn" in low or "ptk" in low or "sinta" in low:
                        return True
        except:
            continue
    return False

def cek_valid(url, query, domain):
    qlow = query.lower().strip()
    if "pddikti" in domain:
        return cek_pddikti_fix(query)

    # Angka ngarang harus super ketat
    is_random_number = query.strip().isdigit()

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            raw = r.read().decode('utf-8', errors='ignore')
            low = raw.lower()

            # 1. Cek frasa gagal
            for p in NO_RESULT:
                if p in low:
                    # Untuk berita, kalau ada frasa gagal = langsung invalid
                    if any(x in domain for x in ["cnnindonesia","tribunnews","detik","kompas"]):
                        # tapi cek dulu apakah ada artikel real yang mengandung query
                        arts = re.findall(r'<h3.*?</h3>|<h2.*?</h2>|<article.*?</article>', low, flags=re.DOTALL)
                        real = False
                        for a in arts:
                            clean = re.sub(r'<.*?>',' ',a).lower()
                            if qlow in clean and 'search' not in clean and 'pencarian' not in clean and len(clean)>20:
                                real = True
                                break
                        if not real:
                            return False

            # 2. Bersihkan jebakan header search
            cleaned = re.sub(r'search results for.*?<|hasil pencarian untuk.*?<', ' <', low)
            cleaned = re.sub(r'<title.*?</title>', ' ', cleaned, flags=re.DOTALL)
            cleaned = re.sub(r'<input[^>]*>', ' ', cleaned)

            if qlow not in cleaned:
                return False

            # 3. YOUTUBE - harus ada di judul video
            if "youtube.com" in domain:
                if is_random_number: return False
                titles = re.findall(r'"title":\{"runs":\[\{"text":"(.*?)"', low)
                if not titles:
                    titles = re.findall(r'"title":{"simpleText":"(.*?)"', low)
                if not titles: return False
                for t in titles[:15]:
                    if qlow in t.lower():
                        return True
                return False

            # 4. BERITA - harus ada di judul berita
            if any(x in domain for x in ["cnnindonesia","tribunnews","detik","kompas"]):
                if is_random_number: return False # angka ngarang auto invalid di berita
                # cari judul
                hits = re.findall(r'<h3[^>]*>(.*?)</h3>|<h2[^>]*>(.*?)</h2>|<article[^>]*>(.*?)</article>', low, flags=re.DOTALL)
                for group in hits:
                    for h in group:
                        if not h: continue
                        clean = re.sub(r'<.*?>',' ',h).lower()
                        if qlow in clean and len(clean)>15 and 'search' not in clean:
                            return True
                return False

            # 5. KAMPUS & SINTA & GARUDA - ini yang bikin dosen muncul
            # Untuk dosen, cukup ada di halaman (bukan cuma di header)
            if domain.endswith('.ac.id') or 'sinta' in domain or 'garuda' in domain:
                # hitung kemunculan setelah header dihapus
                count = cleaned.count(qlow)
                if count >= 1:
                    return True
                return False

            # 6. GOOGLE & WIKIPEDIA
            return qlow in cleaned

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
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
            futs = {}
            for domain, tpl in TEMPLATES.items():
                url = tpl.replace("{q_plus}", q_plus).replace("{q_path}", q_path)
                futs[ex.submit(cek_valid, url, q, domain)] = (domain, url)
            for f in concurrent.futures.as_completed(futs):
                domain, url = futs[f]
                if f.result():
                    valid.append({"title": f"{q} di {domain}", "url": url, "source": domain, "valid": True})
        self.wfile.write(json.dumps({"query": q, "results": valid}, ensure_ascii=False).encode())
