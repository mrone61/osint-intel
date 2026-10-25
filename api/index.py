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

NO_RESULT = ["tidak ditemukan","tidak ada hasil","data tidak ditemukan","no results found","nothing found","no posts found","pencarian tidak ditemukan","berita tidak ditemukan","hasil tidak ditemukan","did not match any documents","sorry, but nothing matched"]

JEBAKAN_SEARCH = ["hasil pencarian untuk","search results for","search result for","hasil cari","pencarian untuk","menampilkan hasil untuk"]

def is_angka(q): return q.strip().isdigit()

def cek_google_saksi(query):
    """Kalau PDDIKTI diblokir Vercel, tanya Google apakah nama ini ada di SINTA/PDDIKTI"""
    if is_angka(query): return False
    try:
        q_plus = urllib.parse.quote_plus(query)
        # Tanya Google: apakah nama ini ada di SINTA atau PDDIKTI?
        url = f"https://www.google.com/search?q={q_plus}+site%3Asinta.kemdiktisaintek.go.id+OR+site%3Apddikti.kemdiktisaintek.go.id+OR+site%3Agaruda.kemdikbud.go.id"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read().decode('utf-8','ignore').lower()
            if "did not match any documents" in raw or "tidak menemukan" in raw:
                return False
            # Kalau Google nemu link sinta/pddikti/garuda = berarti dosen asli
            if "sinta.kemdiktisaintek.go.id" in raw or "pddikti.kemdiktisaintek.go.id" in raw or "garuda.kemdikbud.go.id" in raw:
                return True
            return False
    except:
        return False

def cek_pddikti_gate(query):
    if is_angka(query): return False
    q_plus = urllib.parse.quote_plus(query)
    # 1. Coba API PDDIKTI langsung
    endpoints = [
        f"https://pddikti.kemdiktisaintek.go.id/api/search/mahasiswa?keyword={q_plus}",
        f"https://pddikti.kemdiktisaintek.go.id/api/search/dosen?keyword={q_plus}",
        f"https://sinta.kemdiktisaintek.go.id/authors?q={q_plus}",
    ]
    for api_url in endpoints:
        try:
            req = urllib.request.Request(api_url, headers={"User-Agent":"Mozilla/5.0","Referer":"https://pddikti.kemdiktisaintek.go.id/","Accept":"application/json, text/html, */*"})
            with urllib.request.urlopen(req, timeout=8) as r:
                raw = r.read().decode('utf-8','ignore')
                low = raw.lower()
                if len(raw)<100: continue
                if '"total":0' in low or '"data":[]' in low: continue
                if any(k in low for k in NO_RESULT): continue
                if query.lower().split()[0] in low and query.lower().split()[-1] in low: # cek nama depan & belakang aja
                    return True
        except:
            continue
    # 2. Kalau semua diblokir Vercel, pakai Google sebagai saksi
    if cek_google_saksi(query):
        return True
    return False

def cek_valid(url, query, domain):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=7) as r:
            raw = r.read().decode('utf-8', errors='ignore')
            low = raw.lower()
            qlow = query.lower().strip()
            for k in NO_RESULT:
                if k in low: return False
            clean = re.sub(r'<input[^>]*>', ' ', low)
            clean = re.sub(r'<title[^>]*>.*?</title>', ' ', clean)
            clean = re.sub(r'<meta[^>]*>', ' ', clean)
            clean = re.sub(r'<script.*?</script>', ' ', clean, flags=re.DOTALL)
            clean = re.sub(r'<style.*?</style>', ' ', clean, flags=re.DOTALL)
            for j in JEBAKAN_SEARCH:
                clean = clean.replace(f"{j}: {qlow}", " ")
                clean = clean.replace(f"{j} {qlow}", " ")
                clean = clean.replace(f"{j}:", " ")
                clean = clean.replace(j, " ")
            clean = clean.replace(f'"{qlow}"', ' ').replace(f"'{qlow}'", ' ')
            if qlow not in clean: return False
            links = re.findall(r'<a[^>]*>(.*?)</a>', clean)
            found_in_link = any(qlow in lt.lower() for lt in links)
            if domain.endswith('.ac.id') or any(x in domain for x in ['cnn','detik','kompas','tribun','sinta','garuda']):
                if not found_in_link:
                    headings = re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', clean)
                    for h in headings:
                        if qlow in h.lower():
                            found_in_link = True
                            break
                if not found_in_link: return False
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
        
        # GATE UTAMA
        pddikti_ada = cek_pddikti_gate(q)
        if not pddikti_ada:
            self.wfile.write(json.dumps({"query": q, "results": [], "pddikti_status": "NOT_FOUND"}, ensure_ascii=False).encode())
            return

        q_plus = urllib.parse.quote_plus(q)
        q_path = urllib.parse.quote(q)
        valid = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
            futs = {}
            for domain, tpl in TEMPLATES.items():
                url = tpl.replace("{q_plus}", q_plus).replace("{q_path}", q_path)
                if "pddikti" in domain:
                    valid.append({"title": f"{q} di {domain}", "url": url, "source": domain, "valid": True})
                    continue
                futs[ex.submit(cek_valid, url, q, domain)] = (domain, url)
            for f in concurrent.futures.as_completed(futs):
                domain, url = futs[f]
                if f.result():
                    valid.append({"title": f"{q} di {domain}", "url": url, "source": domain, "valid": True})
        
        self.wfile.write(json.dumps({"query": q, "results": valid, "pddikti_status": "FOUND"}, ensure_ascii=False).encode())
