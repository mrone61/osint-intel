from http.server import BaseHTTPRequestHandler
import urllib.parse, json, urllib.request, concurrent.futures, re

NO_RESULT = ["did not match any documents","tidak menemukan hasil"]
JEBAKAN = ["search results for","hasil pencarian untuk"]

MEDIA_COM_ID = [
    "detik.com", "kompas.com", "liputan6.com", "cnnindonesia.com",
    "tribunnews.com", "antaranews.com", "kumparan.com", "okezone.com",
    "sindonews.com", "tempo.co", "jpnn.com", "merdeka.com"
]

def is_angka(q): return q.strip().isdigit()

def get_links_from_google(query):
    if is_angka(query): return []
    # JANGAN pakai petik untuk nama terkenal biar hasil banyak
    q_plus = urllib.parse.quote_plus(query)
    # QUERY SIMPEL TANPA 20 OR BIAR GOOGLE GAK BLOCK
    url = f"https://www.google.com/search?q={q_plus}&num=25&hl=id&lr=lang_id"
    
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.google.co.id/"
        })
        with urllib.request.urlopen(req, timeout=12) as r:
            raw = r.read().decode('utf-8','ignore')
            low = raw.lower()
            # Jangan langsung return [] kalau ada NO_RESULT, cek dulu linknya ada gak
            links = re.findall(r'/url\?q=(https?://[^&]+)', raw)
            if not links:
                # Fallback parser kalau Google ganti format
                links = re.findall(r'"(https?://[^"]+\.(?:id|com)[^"]+)"', raw)
            
            clean_links = []
            for l in links:
                l = urllib.parse.unquote(l).split('&')[0]
                if "google.com" in l: continue
                if "google.co" in l: continue
                if "gstatic.com" in l: continue
                if "youtube.com" in l: continue
                # FILTER: Harus .id ATAU media .com Indonesia ATAU .go.id .ac.id
                parsed = urllib.parse.urlparse(l)
                netloc = parsed.netloc.lower()
                is_id_domain = netloc.endswith(".id")
                is_media_com = any(m in netloc for m in MEDIA_COM_ID)
                # Izinkan juga yang .id nya di path kayak blogspot
                if is_id_domain or is_media_com or ".go.id" in l or ".ac.id" in l:
                    clean_links.append(l)
            
            # Kalau filter terlalu ketat dan hasilnya 0, kasih semua link Indonesia aja
            if not clean_links:
                for l in links:
                    l = urllib.parse.unquote(l).split('&')[0]
                    if ".id" in l or "detik.com" in l or "kompas.com" in l:
                        clean_links.append(l)

            return list(dict.fromkeys(clean_links))[:20]
    except Exception as e:
        print(f"Google error: {e}")
        return []

def cek_valid_url(url, query):
    try:
        qlow = query.lower().strip()
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 Chrome/122"})
        with urllib.request.urlopen(req, timeout=7) as r:
            raw = r.read().decode('utf-8','ignore')
            low = raw.lower()
            if any(k in low for k in NO_RESULT) and qlow not in low:
                return False
            
            clean = re.sub(r'<script.*?</script>',' ',low, flags=re.DOTALL)
            clean = re.sub(r'<style.*?</style>',' ',clean, flags=re.DOTALL)
            for j in JEBAKAN:
                clean = clean.replace(j,' ')

            if qlow not in clean:
                return False

            score = 0
            titles = re.findall(r'<title[^>]*>(.*?)</title>', clean)
            for t in titles:
                if qlow in t.lower(): score += 100

            headings = re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', clean)
            for h in headings:
                txt = re.sub(r'<.*?>',' ',h).lower()
                if qlow in txt: score += 80

            # Paragraf sekarang 40 poin biar gak kelolosan
            if qlow in clean:
                score += 40

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
            self.wfile.write(json.dumps({
                "query": q, "results": [], 
                "status": "GOOGLE_EMPTY_OR_BLOCKED", 
                "hint": "Coba lagi, Google kadang block Vercel"
            }, ensure_ascii=False).encode())
            return

        valid = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
            futs = {ex.submit(cek_valid_url, url, q): url for url in google_links}
            for f in concurrent.futures.as_completed(futs):
                url = futs[f]
                try:
                    if f.result():
                        domain = urllib.parse.urlparse(url).netloc
                        valid.append({
                            "title": f"{q} di {domain}",
                            "url": url,
                            "source": domain,
                            "valid": True
                        })
                except:
                    pass

        self.wfile.write(json.dumps({
            "query": q, 
            "results": valid, 
            "google_found": len(google_links),
            "coverage": "ALL .id + MEDIA .COM INDONESIA - FIXED"
        }, ensure_ascii=False).encode())
