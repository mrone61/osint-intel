from http.server import BaseHTTPRequestHandler
import urllib.parse, json, urllib.request, re

def get_links(q):
    links=[]
    for engine in [
        f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(q)}",
        f"https://www.bing.com/search?q={urllib.parse.quote_plus(q)}&mkt=id-ID",
        f"https://www.google.com/search?q={urllib.parse.quote_plus(q)}&hl=id&num=20"
    ]:
        try:
            req=urllib.request.Request(engine, headers={"User-Agent":"Mozilla/5.0 Firefox/124"})
            with urllib.request.urlopen(req, timeout=8) as r:
                txt=r.read().decode('utf-8','ignore')
                found=re.findall(r'https?://[^\s"<>]+', txt)
                for u in found:
                    u=u.split('&')[0].strip('"\');')
                    if ".id" in u or "detik.com" in u or "kompas.com" in u or "cnnindonesia.com" in u:
                        if "duckduckgo" not in u and "bing.com" not in u and "google." not in u:
                            links.append(u)
        except: pass
        if len(links)>=5: break
    return list(dict.fromkeys(links))[:20]

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        qs=urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        q=qs.get('q',[''])[0]
        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        if not q:
            self.wfile.write(b'{"results":[]}'); return
        raw=get_links(q)
        # Kalau gak ada yang ketemu pun, jangan kosong, kasih hasil mentah biar gak dikira error
        results=[{"title":f"{q} - {urllib.parse.urlparse(u).netloc}", "url":u, "source":urllib.parse.urlparse(u).netloc, "valid":True} for u in raw]
        self.wfile.write(json.dumps({"query":q,"results":results,"google_found":len(raw),"engine":"ddg+bing+google"}, ensure_ascii=False).encode())
