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

NO_RESULT = ["tidak ditemukan","tidak ada hasil","data tidak ditemukan","no results found","nothing found","no posts found","pencarian tidak ditemukan","berita tidak ditemukan","hasil tidak ditemukan","did not match any documents","sorry, but nothing matched","oops","belum ada artikel","tidak ada berita","no results matching"]

def is_digits(q): return q.strip().isdigit()

def has_no_result(low):
    for p in NO_RESULT:
        if p in low: return True
    return False

def cek_sinta_real(query):
    """Cek SINTA beneran ada author card, bukan cuma search box"""
    if is_digits(query): return False
    q_plus = urllib.parse.quote_plus(query)
    try:
        url = f"https://sinta.kemdiktisaintek.go.id/authors?q={q_plus}"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read().decode('utf-8','ignore')
            low = raw.lower()
            if has_no_result(low): return False
            # SINTA kalau ada hasil pasti ada class ini
            if 'profile-name' in low or 'au-name' in low or 'author-item' in low or 'sinta-profile' in low:
                if query.lower() in low:
                    return True
            # Fallback lenient tapi aman: kalau ada minimal 2 kemunculan nama (bukan cuma di input)
            clean = re.sub(r'<input[^>]*>', ' ', low)
            clean = re.sub(r'<title.*?</title>',' ', clean, flags=re.DOTALL)
            if clean.count(query.lower()) >= 2:
                return True
            # Kalau cuma 1 tapi ada di dalam <a> atau <h3>
            links = re.findall(r'<a[^>]*>(.*?)</a>', low, flags=re.DOTALL)
            for l in links:
                txt = re.sub(r'<.*?>',' ',l).lower()
                if query.lower() in txt and len(txt)>5:
                    return True
            return False
    except:
        return False

def cek_pddikti_real(query):
    if is_digits(query): return False
    q_plus = urllib.parse.quote_plus(query)
    endpoints = [
        f"https://pddikti.kemdiktisaintek.go.id/api/search/mahasiswa?keyword={q_plus}",
        f"https://pddikti.kemdiktisaintek.go.id/api/search/dosen?keyword={q_plus}",
    ]
    for api_url in endpoints:
        try:
            req = urllib.request.Request(api_url, headers={
                "User-Agent":"Mozilla/5.0",
                "Referer":"https://pddikti.kemdiktisaintek.go.id/",
                "Accept":"application/json"
            })
            with urllib.request.urlopen(req, timeout=8) as r:
                raw = r.read().decode('utf-8','ignore')
                low = raw.lower()
                if '"total":0' in low or '"data":[]' in low or len(raw)<80: continue
                if query.lower() in low and ("nidn" in low or "nim" in low or "nama" in low):
                    return True
        except:
            continue
    # === BYPASS: Kalau API PDDIKTI ke-block Vercel, cek SINTA. Dosen pasti ada di SINTA ===
    if cek_sinta_real(query):
        return True
    return False

def cek_kampus_real(url, query, low):
    """Kampus .ac.id valid kalau ada artikel/profil yang mengandung nama"""
    if is_digits(query): return False
    qlow = query.lower()
    if has_no_result(low): return False
    # Bersihkan header jebakan
    clean = re.sub(r'search results for.*?<|hasil pencarian untuk.*?<', ' <', low)
    clean = re.sub(r'<title.*?</title>',' ', clean, flags=re.DOTALL)
    clean = re.sub(r'<input[^>]*>',' ', clean)
    # Harus ada minimal di link/h2/h3 yang bukan header search
    candidates = re.findall(r'<a[^>]*>(.*?)</a>|<h2[^>]*>(.*?)</h2>|<h3[^>]*>(.*?)</h3>|<article[^>]*>(.*?)</article>', clean, flags=re.DOTALL)
    for groups in candidates:
        for g in groups:
            if not g: continue
            txt = re.sub(r'<.*?>',' ',g).lower().strip()
            if len(txt)<8: continue
            if 'search' in txt or 'hasil pencarian' in txt: continue
            if qlow in txt:
                return True
    # Fallback kedua: kalau ada di body 2x (bukan cuma 1x di header)
    if clean.count(qlow) >= 2:
        return True
    return False

def cek_valid(url, query, domain):
    qlow = query.lower()
    if "pddikti" in domain:
        return cek_pddikti_real(query)
    if "sinta" in domain:
        return cek_sinta_real(query)

    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read().decode('utf-8','ignore')
            low = raw.lower()

            if is_digits(query):
                # Angka ngarang = auto invalid untuk semua kecuali google/wikipedia yang ketat
                if "google.com" in domain or "wikipedia.org" in domain:
                    # Google wiki angka masih mungkin valid kalau memang NIM? tapi kita block juga biar aman
                    if has_no_result(low): return False
                    # Harus ada entry-title
                    entries = re.findall(r'<h2.*?</h2>|<h3.*?</h3>|class="entry-title"', low)
                    if not entries: return False
                    return False # angka tetap invalid
                return False

            if "youtube.com" in domain:
                titles = re.findall(r'"title":\{"runs":\[\{"text":"(.*?)"', low)
                if not titles: titles = re.findall(r'"title":{"simpleText":"(.*?)"', low)
                if not titles: return False
                return any(qlow in t.lower() for t in titles[:10])

            if any(x in domain for x in ["cnnindonesia","tribunnews","detik","kompas"]):
                if has_no_result(low): return False
                hits = re.findall(r'<h3[^>]*>(.*?)</h3>|<h2[^>]*>(.*?)</h2>', low, flags=re.DOTALL)
                for group in hits:
                    for h in group:
                        if not h: continue
                        txt = re.sub(r'<.*?>',' ',h).lower()
                        if qlow in txt and len(txt)>15:
                            return True
                return False

            if domain.endswith('.ac.id') or 'garuda' in domain:
                return cek_kampus_real(url, query, low)

            # google & wikipedia
            if has_no_result(low): return False
            clean = re.sub(r'<input[^>]*>',' ', low)
            clean = re.sub(r'<title.*?</title>',' ', clean, flags=re.DOTALL)
            return qlow in clean

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
