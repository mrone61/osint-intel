from http.server import BaseHTTPRequestHandler
import urllib.parse, json, re, urllib.request

TEMPLATES = {
"detik.com": "https://www.detik.com/search/searchall?query={q}",
"kompas.com": "https://www.kompas.com/search?q={q}",
"cnnindonesia.com": "https://www.cnnindonesia.com/search?query={q}",
"tribunnews.com": "https://www.tribunnews.com/search?q={q}",
"tempo.co": "https://www.tempo.co/search?q={q}",
"pddikti.kemdiktisaintek.go.id": "https://pddikti.kemdiktisaintek.go.id/search/{q}",
"sinta.kemdiktisaintek.go.id": "https://sinta.kemdiktisaintek.go.id/authors?q={q}",
"wikipedia.org": "https://en.wikipedia.org/w/index.php?search={q}",
"youtube.com": "https://www.youtube.com/results?search_query={q}",
"facebook.com": "https://www.facebook.com/search/top/?q={q}",
"x.com": "https://x.com/search?q={q}",
"tiktok.com": "https://www.tiktok.com/search?q={q}",
"linkedin.com": "https://www.linkedin.com/search/results/all/?keywords={q}",
"scholar.google.com": "https://scholar.google.com/scholar?q={q}",
}

def check_mentions(query):
    found=set()
    try:
        url=f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(query)}"
        req=urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            html=r.read().decode('utf-8', errors='ignore').lower()
            for m in re.finditer(r'//([a-z0-9\.\-]+\.[a-z]{2,})', html):
                found.add(m.group(1).replace('www.',''))
    except: pass
    return found

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        q=urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('q',[''])[0].strip()
        self.send_response(200)
        self.send_header('Content-type','application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        if not q:
            self.wfile.write(b'{"error":"need ?q"}'); return
        q_enc=urllib.parse.quote_plus(q)
        mentioned=check_mentions(q)
        has_any=len(mentioned)>0
        results=[]
        for domain,tpl in TEMPLATES.items():
            is_green=any(domain in md or md in domain for md in mentioned) if has_any else False
            results.append({"title":f"Cari '{q}' di {domain}","url":tpl.replace("{q}",q_enc),"source":domain,"valid":is_green,"status_text":"✓ TERSEBUT DI INTERNET" if is_green else "✗ TIDAK DITEMUKAN / TIDAK DISEBUT"})
        self.wfile.write(json.dumps({"query":q,"results":results}, ensure_ascii=False).encode())
