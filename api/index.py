from http.server import BaseHTTPRequestHandler
import urllib.parse, json, urllib.request, concurrent.futures, re

NO_RESULT = ["did not match any documents","tidak menemukan","no results found","tidak ditemukan","tidak ada hasil"]
JEBAKAN = ["search results for","hasil pencarian untuk"]

def is_angka(q): return q.strip().isdigit()

def get_links_from_google(query):
    """Ambil semua link dari SELURUH website Indonesia (.id)"""
    if is_angka(query): return []
    # KUNCI: pakai site:.id untuk scan seluruh Indonesia
    q_plus = urllib.parse.quote_plus(f'"{query}"') # pakai petik biar nama lengkap
    url = f"https://www.google.com/search?q={q_plus}+site%3A.id&num=25"
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7"
        })
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read().decode('utf-8','ignore')
            low = raw.lower()
            if any(k in low for k in NO_RESULT):
                return []
            # Ambil link asli dari Google
            links = re.findall(r'/url\?q=(https://[^&]+)', raw)
            clean_links = []
            for l in links:
                l = urllib.parse.unquote(l)
                # Filter cuma .id biar beneran Indonesia
                parsed = urllib.parse.urlparse(l)
                if parsed.netloc.endswith(".id") or ".id/" in l:
                    if "google.com" not in l and "support.google" not in l and "accounts.google" not in l:
                        clean_links.append(l)
            # Hilangin duplikat
            return list(dict.fromkeys(clean_links))[:20]
    except Exception as e:
        print(f"Google error: {e}")
        return []

def cek_valid_url(url, query):
    """Validasi apakah nama beneran ada di halaman itu"""
    try:
        qlow = query.lower().strip()
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            raw = r.read().decode('utf-8','ignore')
            low = raw.lower()
            if any(k in low for k in NO_RESULT): return False
            
            clean = re.sub(r'<script.*?</script>',' ',low, flags=re.DOTALL)
            clean = re.sub(r'<style.*?</style>',' ',clean, flags=re.DOTALL)
            clean = re.sub(r'<input[^>]*>',' ',clean)
            for j in JEBAKAN:
                clean = clean.replace(j,' ')

            if qlow not in clean:
                return False

            # SKOR
            score = 0
            if f"<title" in clean:
                titles = re.findall(r'<title[^>]*>(.*?)</title>', clean)
                for t in titles:
                    if qlow in t.lower(): score += 100

            headings = re.findall(r'<h[1-3][^>]*>(.*?)</h[1-3]>', clean)
            for h in headings:
                txt = re.sub(r'<.*?>',' ',h).lower()
                if qlow in txt: score += 80

            links = re.findall(r'<a[^>]*>(.*?)</a>', clean)
            for a in links:
                txt = re.sub(r'<.*?>',' ',a).lower()
                if qlow in txt and len(txt) > 8:
                    score += 50
                    break
            
            return score >= 50
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

        google_links = get_links_from_google(q)

        if not google_links:
            self.wfile.write(json.dumps({"query": q, "results": [], "source": "google.co.id", "status": "NOT_FOUND_IN_ALL_ID"}, ensure_ascii=False).encode())
            return

        valid = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
            futs = {ex.submit(cek_valid_url, url, q): url for url in google_links}
            for f in concurrent.futures.as_completed(futs):
                url = futs[f]
                if f.result():
                    domain = urllib.parse.urlparse(url).netloc
                    valid.append({
                        "title": f"{q} di {domain}",
                        "url": url,
                        "source": domain,
                        "valid": True
                    })

        self.wfile.write(json.dumps({"query": q, "results": valid, "google_found": len(google_links), "coverage": "ALL .id DOMAINS"}, ensure_ascii=False).encode())
