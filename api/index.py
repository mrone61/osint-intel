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

NO_RESULT = [
"tidak ditemukan","tidak ada hasil","data tidak ditemukan",
"no results found","0 results","nothing found","no posts found",
"pencarian tidak ditemukan","berita tidak ditemukan","tidak ada artikel",
"tidak ada yang cocok","hasil tidak ditemukan","maaf, tidak ada",
"your search -","did not match any documents","tidak ada yang ditemukan",
"sorry, but nothing matched","oops","artikel tidak ditemukan","belum ada artikel",
"tidak ada berita","pencarian anda tidak ditemukan"
]

def cek_pddikti_comprehensive(query):
    """Cek Mahasiswa + Dosen sekaligus"""
    q_plus = urllib.parse.quote_plus(query)
    endpoints = [
        f"https://pddikti.kemdiktisaintek.go.id/api/search/mahasiswa?keyword={q_plus}",
        f"https://pddikti.kemdiktisaintek.go.id/api/search/dosen?keyword={q_plus}",
        f"https://pddikti.kemdiktisaintek.go.id/api/search/ptk?keyword={q_plus}",
    ]
    for api_url in endpoints:
        try:
            req = urllib.request.Request(api_url, headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://pddikti.kemdiktisaintek.go.id/",
                "Accept": "application/json"
            })
            with urllib.request.urlopen(req, timeout=8) as r:
                raw = r.read().decode('utf-8', errors='ignore').lower()
                if '"total":0' in raw or '"data":[]' in raw or raw.strip() == '[]':
                    continue
                # Kalau ada data dan nama cocok
                if query.lower() in raw and len(raw) > 100:
                    return True
        except:
            continue
    return False

def cek_youtube_valid(low, qlow):
    # YouTube render via ytInitialData JSON
    # Harus ada videoRenderer dan judul mengandung query
    if "ytInitialData" not in low:
        return False
    # Cari judul video di JSON
    titles = re.findall(r'"title":\{"runs":\[\{"text":"(.*?)"', low)
    if not titles:
        titles = re.findall(r'"title":{"simpleText":"(.*?)"', low)
    # Kalau tidak ada video sama sekali = invalid
    if len(titles) == 0:
        return False
    # Harus ada minimal 1 judul yang mengandung kata kunci (bukan angka ngarang)
    for t in titles[:10]: # cek 10 teratas
        if qlow in t.lower() or all(word in t.lower() for word in qlow.split() if len(word) > 2):
            return True
    # Untuk angka ngarang 1029393, judul video tidak akan mengandung itu = return False
    return False

def cek_berita_valid(low, qlow, domain):
    # Hapus header jebakan
    temp = re.sub(r'<title.*?</title>', ' ', low, flags=re.DOTALL)
    temp = re.sub(r'search.*?for[^<]*', ' ', temp)
    temp = re.sub(r'pencarian.*?untuk[^<]*', ' ', temp)
    
    # Cek frasa gagal dulu
    for phrase in NO_RESULT:
        if phrase in low:
            # Tapi pastikan frasa gagal itu bukan bagian dari artikel yang memang mengandung query
            # Kalau ada frasa gagal = langsung invalid
            if "tidak ditemukan" in low or "no results" in low or "nothing found" in low or "oops" in low:
                # Double check: apakah ada artikel dengan query?
                articles = re.findall(r'<h3[^>]*>(.*?)</h3>|<h2[^>]*>(.*?)</h2>', low, flags=re.DOTALL)
                found = False
                for a in articles:
                    txt = ''.join(a).lower()
                    if qlow in txt and len(txt) > 10 and 'search' not in txt and 'pencarian' not in txt:
                        found = True
                        break
                if not found:
                    return False

    # Parser khusus per domain
    if "cnnindonesia" in domain:
        # CNN struktur: <h3 class="...">Judul Artikel</h3>
        hits = re.findall(r'<article.*?</article>', low, flags=re.DOTALL)
        for h in hits:
            if qlow in h.lower():
                return True
        return False
    
    if "tribunnews" in domain:
        hits = re.findall(r'<h3.*?</h3>', low, flags=re.DOTALL)
        for h in hits:
            clean_h = re.sub(r'<.*?>', ' ', h).lower()
            if qlow in clean_h and len(clean_h) > 15:
                return True
        return False

    if "detik.com" in domain or "kompas.com" in domain:
        hits = re.findall(r'<article.*?</article>|<h3.*?</h3>|<h2.*?</h2>', low, flags=re.DOTALL)
        for h in hits:
            clean_h = re.sub(r'<.*?>', ' ', h).lower()
            if qlow in clean_h and 'search' not in clean_h and 'pencarian' not in clean_h:
                return True
        return False

    return False

def cek_valid(url, query, domain):
    qlow = query.lower().strip()
    if "pddikti" in domain:
        return cek_pddikti_comprehensive(query)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
        with urllib.request.urlopen(req, timeout=8) as r:
            raw = r.read().decode('utf-8', errors='ignore')
            low = raw.lower()

            if "youtube.com" in domain:
                return cek_youtube_valid(low, qlow)

            if any(x in domain for x in ["cnnindonesia", "tribunnews", "detik.com", "kompas.com"]):
                return cek_berita_valid(low, qlow, domain)

            # Untuk kampus .ac.id + sinta + garuda
            for phrase in NO_RESULT:
                if phrase in low:
                    return False

            # Harus ada di article/link/h2 yang real, bukan header search
            articles = re.findall(r'<article[^>]*>(.*?)</article>', low, flags=re.DOTALL)
            links = re.findall(r'<a[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</a>|<a[^>]*class="[^"]*entry[^"]*"[^>]*>(.*?)</a>|<h2[^>]*>(.*?)</h2>|<h3[^>]*>(.*?)</h3>', low, flags=re.DOTALL)
            
            found = False
            for block in articles:
                clean = re.sub(r'<.*?>', ' ', block).lower()
                if qlow in clean and len(clean) > 20 and 'search results for' not in clean:
                    found = True
                    break
            
            if not found:
                for group in links:
                    for txt in group:
                        clean = re.sub(r'<.*?>', ' ', txt).lower().strip()
                        if qlow in clean and len(clean) > 10 and 'search' not in clean and 'hasil pencarian' not in clean:
                            found = True
                            break
                    if found:
                        break
            
            return found

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
