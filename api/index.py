from http.server import BaseHTTPRequestHandler
import urllib.parse, json

# TEMPLATE SEARCH LANGSUNG KE SITUS ASLI
TEMPLATES = {
"detik.com": "https://www.detik.com/search/searchall?query={q}",
"kompas.com": "https://search.kompas.com/search?q={q}",
"cnnindonesia.com": "https://www.cnnindonesia.com/search/?query={q}",
"liputan6.com": "https://www.liputan6.com/search?q={q}",
"tribunnews.com": "https://www.tribunnews.com/search?q={q}",
"antaranews.com": "https://www.antaranews.com/search?q={q}",
"tempo.co": "https://www.tempo.co/search?q={q}",
"kumparan.com": "https://kumparan.com/search?q={q}",
"okezone.com": "https://search.okezone.com/search?q={q}",
"viva.co.id": "https://www.viva.co.id/search?q={q}",

# PDDIKTI - INI YANG KAMU MAU, LANGSUNG KE PDDIKTI
"pddikti.kemdikbud.go.id": "https://pddikti.kemdikbud.go.id/search/{q}",
"pddikti.kemdiktisaintek.go.id": "https://pddikti.kemdiktisaintek.go.id/search/{q}",
"sinta.kemdikbud.go.id": "https://sinta.kemdikbud.go.id/authors?q={q}",
"garuda.kemdikbud.go.id": "https://garuda.kemdikbud.go.id/documents?q={q}",
"scholar.google.com": "https://scholar.google.com/scholar?q={q}",

# KAMPUS
"ui.ac.id": "https://www.ui.ac.id/?s={q}",
"ugm.ac.id": "https://ugm.ac.id/?s={q}",
"itb.ac.id": "https://www.itb.ac.id/search?q={q}",
"unhas.ac.id": "https://unhas.ac.id/?s={q}",
"uncen.ac.id": "https://uncen.ac.id/?s={q}",
"unpad.ac.id": "https://www.unpad.ac.id/?s={q}",

# SOSMED & UMUM - LANGSUNG SEARCH NAMA
"wikipedia.org": "https://en.wikipedia.org/w/index.php?search={q}",
"youtube.com": "https://www.youtube.com/results?search_query={q}",
"facebook.com": "https://www.facebook.com/search/top/?q={q}",
"instagram.com": "https://www.instagram.com/explore/search/keyword/?q={q}",
"twitter.com": "https://twitter.com/search?q={q}",
"x.com": "https://x.com/search?q={q}",
"tiktok.com": "https://www.tiktok.com/search?q={q}",
"linkedin.com": "https://www.linkedin.com/search/results/all/?keywords={q}",

# GOV
"bkn.go.id": "https://www.bkn.go.id/?s={q}",
"polri.go.id": "https://www.polri.go.id/search?q={q}",
"kpu.go.id": "https://www.kpu.go.id/index.php?q={q}",
}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        q = qs.get('q',[''])[0].strip()
        self.send_response(200)
        self.send_header('Content-type','application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        if not q:
            self.wfile.write(b'{"error":"need ?q=nama"}')
            return
        
        q_enc = urllib.parse.quote_plus(q)
        q_path = urllib.parse.quote(q) # untuk yang butuh path
        results = []
        
        for domain, template in TEMPLATES.items():
            url = template.replace("{q}", q_enc)
            # khusus pddikti pakai path bukan query
            if "pddikti" in domain and "/search/" in template:
                url = template.replace("{q}", q_path)
            
            results.append({
                "title": f"Cari '{q}' di {domain}",
                "url": url,
                "source": domain
            })
        
        # Tambah engine besar biar jadi ratusan? kita duplikasi dengan variasi
        # Untuk aprilia sbrfk, semua akan ngarah ke pencarian nama itu langsung
        data = {"query": q, "total_found": len(results), "results": results}
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
