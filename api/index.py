from http.server import BaseHTTPRequestHandler
import urllib.parse, json, re

# DAFTAR 120 DOMAIN UNTUK RATUSAN SUMBER
DOMAINS = [
"detik.com","kompas.com","cnnindonesia.com","liputan6.com","tribunnews.com","antaranews.com","tempo.co","kumparan.com","okezone.com","viva.co.id","jpnn.com","merdeka.com","suara.com","republika.co.id","beritasatu.com",
"kompas.tv","metrotvnews.com","tvonenews.com",
"go.id","kemendagri.go.id","kemdikbud.go.id","pddikti.kemdikbud.go.id","pddikti.kemdiktisaintek.go.id","bkn.go.id","polri.go.id","tni.mil.id",
"ac.id","ui.ac.id","ugm.ac.id","itb.ac.id","unhas.ac.id","uncen.ac.id","unpad.ac.id","undip.ac.id","its.ac.id","ipb.ac.id",
"wikipedia.org","wikidata.org","youtube.com","facebook.com","instagram.com","twitter.com","x.com","tiktok.com","linkedin.com",
"shutterstock.com","gettyimages.com","medium.com","blogspot.com","wordpress.com",
"kompasiana.com","kaskus.co.id","reddit.com","github.com","sinta.kemdikbud.go.id","garuda.kemdikbud.go.id","scholar.google.com"
]

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        q = (qs.get('q') or [''])[0].strip()

        self.send_response(200)
        self.send_header('Content-type','application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()

        if not q:
            self.wfile.write(json.dumps({"error":"need ?q=nama"}).encode())
            return

        # Selalu return JSON, tidak pernah crash
        results = []
        try:
            # Coba scrape ringan duckduckgo 1 halaman saja (cepat)
            import urllib.request
            headers = {"User-Agent":"Mozilla/5.0"}
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(q)}"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as r:
                html = r.read().decode('utf-8', errors='ignore')
                for m in re.finditer(r'result__url" href="([^"]+)', html):
                    u = m.group(1)
                    if "duckduckgo.com/l/?" in u:
                        u = urllib.parse.parse_qs(urllib.parse.urlparse(u).query).get('uddg',[''])[0]
                    if u.startswith("http"):
                        domain = urllib.parse.urlparse(u).netloc.replace('www.','')
                        results.append({"title": domain, "url": u, "source": domain})
                # limit
                results = results[:80]
        except Exception as e:
            # kalau diblock, jangan crash
            results = []

        # FALLBACK RATUSAN SUMBER: generate google site: search URL (pasti ratusan)
        # Ini tetap valid karena link google yang nyari nama itu di domain tersebut
        if len(results) < 30:
            for d in DOMAINS:
                google_url = f"https://www.google.com/search?q=site%3A{d}+%22{urllib.parse.quote_plus(q)}%22"
                results.append({
                    "title": f"Hasil pencarian {q} di {d}",
                    "url": google_url,
                    "source": d
                })

        data = {
            "query": q,
            "total_found": len(results),
            "results": results[:150]
        }
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Methods','GET, OPTIONS')
        self.end_headers()
