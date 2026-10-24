from http.server import BaseHTTPRequestHandler
import urllib.parse, json, urllib.request, concurrent.futures

TEMPLATES = {
# NEWS
"detik.com": "https://www.detik.com/search/searchall?query={q_plus}",
"kompas.com": "https://www.kompas.com/search?q={q_plus}",
"cnnindonesia.com": "https://www.cnnindonesia.com/search?query={q_plus}",
"tribunnews.com": "https://www.tribunnews.com/search?q={q_plus}",
"tempo.co": "https://www.tempo.co/search?q={q_plus}",
"liputan6.com": "https://www.liputan6.com/search?q={q_plus}",
"antaranews.com": "https://www.antaranews.com/search?q={q_plus}",
"kumparan.com": "https://kumparan.com/search?q={q_plus}",
"okezone.com": "https://search.okezone.com/search?q={q_plus}",
"jpnn.com": "https://www.jpnn.com/search?q={q_plus}",
"merdeka.com": "https://www.merdeka.com/search?q={q_plus}",
"suara.com": "https://www.suara.com/search?q={q_plus}",

# PDDIKTI - PAKAI %20
"pddikti.kemdiktisaintek.go.id": "https://pddikti.kemdiktisaintek.go.id/search/{q_path}",
"sinta.kemdiktisaintek.go.id": "https://sinta.kemdiktisaintek.go.id/authors?q={q_plus}",
"garuda.kemdikbud.go.id": "https://garuda.kemdikbud.go.id/documents?q={q_plus}",

# KAMPUS
"ui.ac.id": "https://www.ui.ac.id/?s={q_plus}",
"ugm.ac.id": "https://ugm.ac.id/?s={q_plus}",
"itb.ac.id": "https://www.itb.ac.id/search?q={q_plus}",
"unhas.ac.id": "https://unhas.ac.id/?s={q_plus}",
"ipb.ac.id": "https://www.ipb.ac.id/?s={q_plus}",
"its.ac.id": "https://www.its.ac.id/?s={q_plus}",

# SOSMED
"youtube.com": "https://www.youtube.com/results?search_query={q_plus}",
"facebook.com": "https://www.facebook.com/search/top/?q={q_plus}",
"x.com": "https://x.com/search?q={q_plus}",
"tiktok.com": "https://www.tiktok.com/search?q={q_plus}",
"instagram.com": "https://www.instagram.com/explore/tags/{q_path}/",
"linkedin.com": "https://www.linkedin.com/search/results/all/?keywords={q_plus}",

# DOKUMEN
"wikipedia.org": "https://en.wikipedia.org/w/index.php?search={q_plus}",
"scholar.google.com": "https://scholar.google.com/scholar?q={q_plus}",
"google.com": "https://www.google.com/search?q={q_plus}",
"bing.com": "https://www.bing.com/search?q={q_plus}",

# DEWASA - MASUK OSINT JUGA
"xnxx.com": "https://www.xnxx.com/search/{q_path}",
"xvideos.com": "https://www.xvideos.com/?k={q_plus}",
"pornhub.com": "https://www.pornhub.com/video/search?search={q_plus}",
"xhamster.com": "https://xhamster.com/search/{q_path}",
"redtube.com": "https://www.redtube.com/?search={q_plus}",
"youporn.com": "https://www.youporn.com/search/?query={q_plus}",
"spankbang.com": "https://spankbang.com/s/{q_path}/",
"onlyfans.com": "https://onlyfans.com/search/{q_path}",
}

def cek_langsung(url, query):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as r:
            html = r.read().decode('utf-8', errors='ignore').lower()
            qlow = query.lower()
            if "tidak ditemukan" in html or "data tidak ditemukan" in html or "no results" in html or "no video" in html or "0 results" in html or "no result" in html:
                return False if qlow not in html else True
            if qlow in html:
                return True
            return len(html) > 2000
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
            self.wfile.write(b'{"error":"need ?q"}'); return
        q_plus = urllib.parse.quote_plus(q)
        q_path = urllib.parse.quote(q)
        items = list(TEMPLATES.items())
        valid_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(cek_langsung, tpl.replace("{q_plus}", q_plus).replace("{q_path}", q_path), q): (domain, tpl.replace("{q_plus}", q_plus).replace("{q_path}", q_path)) for domain, tpl in items}
            for future in concurrent.futures.as_completed(futures):
                domain, url = futures[future]
                try:
                    if future.result():
                        valid_results.append({"title": f"{q} di {domain}", "url": url, "source": domain, "valid": True, "status_text": "✓ DITEMUKAN"})
                except:
                    pass
        self.wfile.write(json.dumps({"query": q, "total_found": len(valid_results), "results": valid_results}, ensure_ascii=False).encode())
