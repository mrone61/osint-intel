from http.server import BaseHTTPRequestHandler
import urllib.parse, json

DOMAINS = [
"detik.com","kompas.com","cnnindonesia.com","liputan6.com","tribunnews.com","antaranews.com","tempo.co","kumparan.com","okezone.com","viva.co.id","jpnn.com","merdeka.com","suara.com","republika.co.id","beritasatu.com","kompas.tv","metrotvnews.com","tvonenews.com","idntimes.com","popbela.com",
"go.id","kemendagri.go.id","kemdikbud.go.id","pddikti.kemdikbud.go.id","bkn.go.id","polri.go.id","tni.mil.id","kpu.go.id","mkri.id","dpr.go.id",
"ac.id","ui.ac.id","ugm.ac.id","itb.ac.id","unhas.ac.id","uncen.ac.id","unpad.ac.id","undip.ac.id","its.ac.id","ipb.ac.id","unair.ac.id","ub.ac.id","unsri.ac.id","unsyiah.ac.id",
"wikipedia.org","wikidata.org","youtube.com","facebook.com","instagram.com","twitter.com","x.com","tiktok.com","linkedin.com","threads.net",
"medium.com","blogspot.com","wordpress.com","kompasiana.com","kaskus.co.id","reddit.com","github.com","sinta.kemdikbud.go.id","garuda.kemdikbud.go.id","scholar.google.com","researchgate.net","academia.edu",
"shutterstock.com","gettyimages.com","tokopedia.com","bukalapak.com","shopee.co.id","lazada.co.id"
]

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('q',[''])[0].strip()
        self.send_response(200)
        self.send_header('Content-type','application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        if not q:
            self.wfile.write(b'{"error":"need ?q=nama"}')
            return
        
        results = []
        q_enc = urllib.parse.quote_plus(q)
        for d in DOMAINS:
            results.append({
                "title": f"{q} - site:{d}",
                "url": f"https://www.google.com/search?q=site%3A{d}+%22{q_enc}%22",
                "source": d
            })
        
        # Tambah variasi search engine biar jadi ratusan
        results.append({"title": f"{q} DuckDuckGo","url": f"https://duckduckgo.com/?q={q_enc}","source": "duckduckgo.com"})
        results.append({"title": f"{q} Bing","url": f"https://www.bing.com/search?q={q_enc}","source": "bing.com"})
        results.append({"title": f"{q} Yandex","url": f"https://yandex.com/search/?text={q_enc}","source": "yandex.com"})
        
        data = {"query": q, "total_found": len(results), "results": results}
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
