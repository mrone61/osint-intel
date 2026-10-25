from http.server import BaseHTTPRequestHandler
import urllib.parse, json, urllib.request, concurrent.futures, re

TEMPLATES = {
"google.com": "https://www.google.com/search?q={q_plus}+site%3Aac.id+OR+site%3Adetik.com+OR+site%3Akompas.com+OR+site%3Acnnindonesia.com",
"detik.com": "https://www.detik.com/search/searchall?query={q_plus}",
"kompas.com": "https://www.kompas.com/search?q={q_plus}",
"cnnindonesia.com": "https://www.cnnindonesia.com/search?query={q_plus}",
"tribunnews.com": "https://www.tribunnews.com/search?q={q_plus}",
"antaranews.com": "https://www.antaranews.com/search?q={q_plus}",
"liputan6.com": "https://www.liputan6.com/search?q={q_plus}",
"ustj.ac.id": "https://ustj.ac.id/?s={q_plus}",
"unhas.ac.id": "https://unhas.ac.id/?s={q_plus}",
"unm.ac.id": "https://unm.ac.id/?s={q_plus}",
"umi.ac.id": "https://umi.ac.id/?s={q_plus}",
"unismuh.ac.id": "https://unismuh.ac.id/?s={q_plus}",
"uim-makassar.ac.id": "https://uim-makassar.ac.id/?s={q_plus}",
"pddikti.kemdiktisaintek.go.id": "https://pddikti.kemdiktisaintek.go.id/search/{q_path}",
"sinta.kemdiktisaintek.go.id": "https://sinta.kemdiktisaintek.go.id/authors?q={q_plus}",
}

NO_RESULT = ["tidak ditemukan","tidak ada hasil","data tidak ditemukan","no results found","nothing found","no posts found","pencarian tidak ditemukan","berita tidak ditemukan","hasil tidak ditemukan","did not match any documents","sorry, but nothing matched"]
JEBAKAN_SEARCH = ["hasil pencarian untuk","search results for","hasil cari","pencarian untuk"]

def is_angka(q): return q.strip().isdigit()

def cek_google_gate(query):
    """Gate baru: cek di Google dulu, kalau 0 ya sudah pasti gak ada di media manapun"""
    if is_angka(query): return False
    try:
        q_plus = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={q_plus}+site%3Aac.id+OR+site%3Adetik.com+OR+site%3Akompas.com+OR+site%3Acnnindonesia.com+OR+site%3Atribunnews.com"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=8) as r:
            raw = r.read().decode('utf-8','ignore').lower()
            if "did not match any documents" in raw or "tidak menemukan" in raw or "no results" in raw:
                return False
            # Minimal harus ada link .ac.id atau detik/kompas
            if any(x in raw for x in [".ac.id","detik.com","kompas.com","cnnindonesia","tribunnews"]):
                return True
            return False
    except:
        # Kalau Google diblokir Vercel, jangan matiin, anggap aja ADA biar lanjut cek manual
        return True

def cek_valid(url, query, domain):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            raw = r.read().decode('utf-8','ignore')
            low = raw.lower()
            qlow = query.lower().strip()
            if any(k in low for k in NO_RESULT): return False
            clean = re.sub(r'<input[^>]*>',' ',low)
            clean = re.sub(r'<title[^>]*>.*?</title>',' ',clean)
            clean = re.sub(r'<script.*?</script>',' ',clean, flags=re.DOTALL)
            clean = re.sub(r'<style.*?</style>',' ',clean, flags=re.DOTALL)
            for j in JEBAKAN_SEARCH:
                clean = clean.replace(j,' ')
            if qlow not in clean: return False
            
            # Validasi: harus ada di link atau heading
            links = re.findall(r'<a[^>]*>(.*?)</a>', clean)
            headings = re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', clean)
            for lst in [links, headings]:
                for item in lst:
                    txt = re.sub(r'<.*?>',' ',item).lower().strip()
                    if qlow in txt and len(txt)>8 and 'search' not in txt and 'hasil pencarian' not in txt:
                        return True
            return False
    except:
        return False

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('q',[''])[0].strip()
        self.send_response(200)
        self.send_header('Content-type','application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        if not q or is_angka(q):
            self.wfile.write(b'{"results":[]}'); return
        
        # GATE BARU: Google, bukan PDDIKTI
        if not cek_google_gate(q):
            self.wfile.write(json.dumps({"query": q, "results": [], "gate": "GOOGLE_NOT_FOUND"}, ensure_ascii=False).encode())
            return

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
        
        self.wfile.write(json.dumps({"query": q, "results": valid, "gate": "FOUND"}, ensure_ascii=False).encode())
