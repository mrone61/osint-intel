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

NO_RESULT = ["tidak ditemukan","tidak ada hasil","data tidak ditemukan","no results found","nothing found","no posts found","pencarian tidak ditemukan","berita tidak ditemukan","hasil tidak ditemukan","did not match any documents","sorry, but nothing matched","oops","belum ada artikel","tidak ada berita","your search did not match","tidak ada yang ditemukan","no results matching"]

def is_all_digits(q):
    return q.strip().isdigit()

def has_no_result_text(low):
    for p in NO_RESULT:
        if p in low:
            return True
    return False

def cek_pddikti_real(query):
    """PDDIKTI hanya valid kalau API beneran balikin data mahasiswa/dosen"""
    q_plus = urllib.parse.quote_plus(query)
    # Kalau angka semua, langsung invalid di PDDIKTI
    if is_all_digits(query):
        return False
    
    endpoints = [
        f"https://pddikti.kemdiktisaintek.go.id/api/search/mahasiswa?keyword={q_plus}",
        f"https://pddikti.kemdiktisaintek.go.id/api/search/dosen?keyword={q_plus}",
    ]
    for api_url in endpoints:
        try:
            req = urllib.request.Request(api_url, headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://pddikti.kemdiktisaintek.go.id/",
                "Accept": "application/json"
            })
            with urllib.request.urlopen(req, timeout=8) as r:
                raw = r.read().decode('utf-8','ignore')
                low = raw.lower()
                if '"total":0' in low or '"data":[]' in low or len(raw)<80:
                    continue
                # Harus ada field spesifik dosen/mhs dan nama query di dalamnya
                if query.lower() in low and ("nidn" in low or "nim" in low or "nama" in low or "pt" in low):
                    return True
        except:
            continue
    return False

def cek_valid(url, query, domain):
    qlow = query.lower().strip()
    # RULE 1: Angka ngarang auto invalid di PDDIKTI, berita, youtube
    if is_all_digits(query):
        if any(x in domain for x in ["pddikti","cnnindonesia","tribunnews","detik","kompas","youtube","sinta","garuda"]):
            return False
        # untuk .ac.id dan google, lanjut tapi harus super ketat

    if "pddikti" in domain:
        return cek_pddikti_real(query)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            raw = r.read().decode('utf-8','ignore')
            low = raw.lower()

            # RULE 2: Kalau ada teks no result = langsung INVALID
            if has_no_result_text(low):
                return False

            # RULE 3: Bersihkan search header yang nipu
            clean_low = re.sub(r'<title.*?</title>', ' ', low, flags=re.DOTALL)
            clean_low = re.sub(r'<input[^>]*>', ' ', clean_low)

            # YOUTUBE
            if "youtube.com" in domain:
                if is_all_digits(query): return False
                titles = re.findall(r'"title":\{"runs":\[\{"text":"(.*?)"', low)
                if not titles: titles = re.findall(r'"title":{"simpleText":"(.*?)"', low)
                if not titles: return False
                return any(qlow in t.lower() for t in titles[:10])

            # BERITA
            if any(x in domain for x in ["cnnindonesia","tribunnews","detik","kompas"]):
                if is_all_digits(query): return False
                articles = re.findall(r'<h3[^>]*>(.*?)</h3>|<h2[^>]*>(.*?)</h2>', low, flags=re.DOTALL)
                for art in articles:
                    for a in art:
                        if not a: continue
                        txt = re.sub(r'<.*?>',' ',a).lower().strip()
                        if qlow in txt and len(txt)>15 and 'search' not in txt and 'hasil' not in txt:
                            return True
                return False

            # SINTA & GARUDA - harus ada author card
            if "sinta" in domain:
                if is_all_digits(query): return False
                # SINTA punya class profile name
                cards = re.findall(r'<div class=".*?au-name.*?>(.*?)</div>|<a class=".*?author-name.*?>(.*?)</a>|<h3.*?</h3>', low, flags=re.DOTALL)
                for c in cards:
                    for part in c:
                        if not part: continue
                        txt = re.sub(r'<.*?>',' ',part).lower()
                        if qlow in txt:
                            return True
                return False

            if "garuda" in domain:
                if is_all_digits(query): return False
                titles = re.findall(r'<h3.*?</h3>|<h2.*?</h2>', low, flags=re.DOTALL)
                for t in titles:
                    txt = re.sub(r'<.*?>',' ',t).lower()
                    if qlow in txt:
                        return True
                return False

            # .AC.ID, GOOGLE, WIKIPEDIA
            # Harus ada entry-title / result-title yang mengandung query, bukan cuma di body
            entry_patterns = re.findall(
                r'class="[^"]*entry-title[^"]*"[^>]*>(.*?)</|class="[^"]*result-title[^"]*"[^>]*>(.*?)</|<article[^>]*>.*?<h[2-3][^>]*>(.*?)</h[2-3]>|<h2[^>]*>(.*?)</h2>|<h3[^>]*>(.*?)</h3>',
                low, flags=re.DOTALL
            )
            if not entry_patterns:
                return False # Tidak ada hasil sama sekali
            
            found = False
            for groups in entry_patterns:
                for g in groups:
                    if not g: continue
                    txt = re.sub(r'<.*?>',' ',g).lower().strip()
                    if not txt: continue
                    if 'search results for' in txt or 'hasil pencarian' in txt:
                        continue
                    if qlow in txt and len(txt) > 8:
                        found = True
                        break
                if found: break
            
            return found

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
                futs[ex.submit(cek_valid, url, q, domain)] = (domain, url)
            for f in concurrent.futures.as_completed(futs):
                domain, url = futs[f]
                if f.result():
                    valid.append({"title": f"{q} di {domain}", "url": url, "source": domain, "valid": True})
        self.wfile.write(json.dumps({"query": q, "results": valid}, ensure_ascii=False).encode())
