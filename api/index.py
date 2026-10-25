from http.server import BaseHTTPRequestHandler
import urllib.parse, json, urllib.request, concurrent.futures, re

TEMPLATES = {
# --- AKADEMIK ---
"pddikti.kemdiktisaintek.go.id": "https://pddikti.kemdiktisaintek.go.id/search/{q_path}",
"sinta.kemdiktisaintek.go.id": "https://sinta.kemdiktisaintek.go.id/authors?q={q_plus}",
"garuda.kemdikbud.go.id": "https://garuda.kemdikbud.go.id/documents?q={q_plus}",

# --- NASIONAL SUPER ---
"detik.com": "https://www.detik.com/search/searchall?query={q_plus}",
"kompas.com": "https://www.kompas.com/search?q={q_plus}",
"kompasiana.com": "https://www.kompasiana.com/search?q={q_plus}",
"kompas.tv": "https://www.kompas.tv/search?q={q_plus}",
"cnnindonesia.com": "https://www.cnnindonesia.com/search?query={q_plus}",
"cnbcindonesia.com": "https://www.cnbcindonesia.com/search?q={q_plus}",
"liputan6.com": "https://www.liputan6.com/search?q={q_plus}",
"tribunnews.com": "https://www.tribunnews.com/search?q={q_plus}",
"okezone.com": "https://www.okezone.com/search?q={q_plus}",
"sindonews.com": "https://www.sindonews.com/search?q={q_plus}",
"inews.id": "https://www.inews.id/search/{q_plus}",
"viva.co.id": "https://www.viva.co.id/search?q={q_plus}",
"tvonenews.com": "https://www.tvonenews.com/search?q={q_plus}",
"merdeka.com": "https://www.merdeka.com/search?q={q_plus}",
"kumparan.com": "https://www.kumparan.com/search?q={q_plus}",
"antaranews.com": "https://www.antaranews.com/search/{q_path}",
"tempo.co": "https://www.tempo.co/search?q={q_plus}",
"republika.co.id": "https://www.republika.co.id/search/{q_plus}",
"beritasatu.com": "https://www.beritasatu.com/search?q={q_plus}",
"metrotvnews.com": "https://www.metrotvnews.com/search/{q_plus}",
"medcom.id": "https://www.medcom.id/search?q={q_plus}",
"jpnn.com": "https://www.jpnn.com/search?q={q_plus}",
"jawapos.com": "https://www.jawapos.com/search?q={q_plus}",
"idntimes.com": "https://www.idntimes.com/search?q={q_plus}",
"suara.com": "https://www.suara.com/search?q={q_plus}",
"grid.id": "https://www.grid.id/search?q={q_plus}",
"bisnis.com": "https://www.bisnis.com/search?q={q_plus}",
"kontan.co.id": "https://www.kontan.co.id/search?q={q_plus}",
"idxchannel.com": "https://www.idxchannel.com/search?q={q_plus}",
"katadata.co.id": "https://www.katadata.co.id/search?q={q_plus}",
"tirto.id": "https://www.tirto.id/search?q={q_plus}",
"voi.id": "https://www.voi.id/search?q={q_plus}",
"akurat.co": "https://www.akurat.co/search?q={q_plus}",
"mongabay.co.id": "https://www.mongabay.co.id/search/?s={q_plus}",
"narasi.tv": "https://www.narasi.tv/search?q={q_plus}",

# --- TRIBUN NETWORK SABANG - MERAUKE ---
"aceh.tribunnews.com": "https://aceh.tribunnews.com/search?q={q_plus}",
"medan.tribunnews.com": "https://medan.tribunnews.com/search?q={q_plus}",
"batam.tribunnews.com": "https://batam.tribunnews.com/search?q={q_plus}",
"padang.tribunnews.com": "https://padang.tribunnews.com/search?q={q_plus}",
"pekanbaru.tribunnews.com": "https://pekanbaru.tribunnews.com/search?q={q_plus}",
"jambi.tribunnews.com": "https://jambi.tribunnews.com/search?q={q_plus}",
"palembang.tribunnews.com": "https://palembang.tribunnews.com/search?q={q_plus}",
"bangka.tribunnews.com": "https://bangka.tribunnews.com/search?q={q_plus}",
"bengkulu.tribunnews.com": "https://bengkulu.tribunnews.com/search?q={q_plus}",
"lampung.tribunnews.com": "https://lampung.tribunnews.com/search?q={q_plus}",
"jakarta.tribunnews.com": "https://jakarta.tribunnews.com/search?q={q_plus}",
"jabar.tribunnews.com": "https://jabar.tribunnews.com/search?q={q_plus}",
"jateng.tribunnews.com": "https://jateng.tribunnews.com/search?q={q_plus}",
"jogja.tribunnews.com": "https://jogja.tribunnews.com/search?q={q_plus}",
"jatim.tribunnews.com": "https://jatim.tribunnews.com/search?q={q_plus}",
"bali.tribunnews.com": "https://bali.tribunnews.com/search?q={q_plus}",
"lombok.tribunnews.com": "https://lombok.tribunnews.com/search?q={q_plus}",
"pontianak.tribunnews.com": "https://pontianak.tribunnews.com/search?q={q_plus}",
"banjarmasin.tribunnews.com": "https://banjarmasin.tribunnews.com/search?q={q_plus}",
"palangkaraya.tribunnews.com": "https://palangkaraya.tribunnews.com/search?q={q_plus}",
"samarinda.tribunnews.com": "https://kaltim.tribunnews.com/search?q={q_plus}",
"manado.tribunnews.com": "https://manado.tribunnews.com/search?q={q_plus}",
"palu.tribunnews.com": "https://palu.tribunnews.com/search?q={q_plus}",
"makassar.tribunnews.com": "https://makassar.tribunnews.com/search?q={q_plus}",
"kendari.tribunnews.com": "https://kendari.tribunnews.com/search?q={q_plus}",
"ambon.tribunnews.com": "https://ambon.tribunnews.com/search?q={q_plus}",
"ternate.tribunnews.com": "https://ternate.tribunnews.com/search?q={q_plus}",
"papua.tribunnews.com": "https://papua.tribunnews.com/search?q={q_plus}",
"sorong.tribunnews.com": "https://sorong.tribunnews.com/search?q={q_plus}",

# --- JAWA POS / RADAR NETWORK ---
"radar-bali.jawapos.com": "https://radar-bali.jawapos.com/search?q={q_plus}",
"radarjogja.jawapos.com": "https://radarjogja.jawapos.com/search?q={q_plus}",
"radarsolo.jawapos.com": "https://radarsolo.jawapos.com/search?q={q_plus}",
"radarsemarang.jawapos.com": "https://radarsemarang.jawapos.com/search?q={q_plus}",
"radarsurabaya.jawapos.com": "https://radarsurabaya.jawapos.com/search?q={q_plus}",
"radar-lampung.jawapos.com": "https://radarlampung.jawapos.com/search?q={q_plus}",
"radar-bogor.jawapos.com": "https://radar-bogor.jawapos.com/search?q={q_plus}",
"radar-cirebon.jawapos.com": "https://radarcirebon.jawapos.com/search?q={q_plus}",
"radar-madura.jawapos.com": "https://radar-madura.jawapos.com/search?q={q_plus}",

# --- REGIONAL SULAWESI & INDONESIA TIMUR ---
"herald.id": "https://www.herald.id/search?q={q_plus}",
"fajar.co.id": "https://www.fajar.co.id/search?q={q_plus}",
"saibetik.com": "https://www.saibetik.com/search?q={q_plus}",
"lintas-sulut.com": "https://www.lintas-sulut.com/search?q={q_plus}",
"manadopost.jawapos.com": "https://manadopost.jawapos.com/search?q={q_plus}",
"bmanado.com": "https://www.bmanado.com/search?q={q_plus}",
"detiksulut.com": "https://www.detiksulut.com/search?q={q_plus}",
"sulut.inews.id": "https://sulut.inews.id/search?q={q_plus}",
"sulut.antaranews.com": "https://sulut.antaranews.com/search?q={q_plus}",
"gorontalo.antaranews.com": "https://gorontalo.antaranews.com/search?q={q_plus}",
"sulsel.antaranews.com": "https://sulsel.antaranews.com/search?q={q_plus}",
"sulteng.antaranews.com": "https://sulteng.antaranews.com/search?q={q_plus}",
"sultra.antaranews.com": "https://sultra.antaranews.com/search?q={q_plus}",
"maluku.antaranews.com": "https://maluku.antaranews.com/search?q={q_plus}",
"papua.antaranews.com": "https://papua.antaranews.com/search?q={q_plus}",
"papuabarat.antaranews.com": "https://papuabarat.antaranews.com/search?q={q_plus}",
"aceh.antaranews.com": "https://aceh.antaranews.com/search?q={q_plus}",
"sumut.antaranews.com": "https://sumut.antaranews.com/search?q={q_plus}",
"riau.antaranews.com": "https://riau.antaranews.com/search?q={q_plus}",
"jabar.antaranews.com": "https://jabar.antaranews.com/search?q={q_plus}",
"jatim.antaranews.com": "https://jatim.antaranews.com/search?q={q_plus}",
"bali.antaranews.com": "https://bali.antaranews.com/search?q={q_plus}",
"ntb.antaranews.com": "https://ntb.antaranews.com/search?q={q_plus}",
"ntt.antaranews.com": "https://ntt.antaranews.com/search?q={q_plus}",
"kalbar.antaranews.com": "https://kalbar.antaranews.com/search?q={q_plus}",
"kaltim.antaranews.com": "https://kaltim.antaranews.com/search?q={q_plus}",

# --- LAINNYA ---
"pikiran-rakyat.com": "https://www.pikiran-rakyat.com/search?q={q_plus}",
"rmol.id": "https://www.rmol.id/search?q={q_plus}",
"inilah.com": "https://www.inilah.com/search?q={q_plus}",
"wartaekonomi.co.id": "https://www.wartaekonomi.co.id/search?q={q_plus}",
"era.id": "https://www.era.id/search?q={q_plus}",
"bloombergtechnoz.com": "https://www.bloombergtechnoz.com/search?q={q_plus}",
"disway.id": "https://www.disway.id/search?q={q_plus}",
"youtube.com": "https://www.youtube.com/results?search_query={q_plus}",
"wikipedia.org": "https://id.wikipedia.org/w/index.php?search={q_plus}",
}

NO_RESULT = ["tidak ditemukan","tidak ada hasil","data tidak ditemukan","no results found","nothing found","no posts found","pencarian tidak ditemukan","berita tidak ditemukan","hasil tidak ditemukan","did not match any documents"]
JEBAKAN_SEARCH = ["hasil pencarian untuk","search results for","hasil cari","pencarian untuk"]

def is_angka(q): return q.strip().isdigit()
def cek_pddikti_gate(query):
    if is_angka(query): return False
    q_plus = urllib.parse.quote_plus(query)
    endpoints = [
        f"https://pddikti.kemdiktisaintek.go.id/api/search/dosen?keyword={q_plus}",
        f"https://sinta.kemdiktisaintek.go.id/authors?q={q_plus}",
    ]
    for api_url in endpoints:
        try:
            req = urllib.request.Request(api_url, headers={"User-Agent":"Mozilla/5.0","Referer":"https://pddikti.kemdiktisaintek.go.id/"})
            with urllib.request.urlopen(req, timeout=8) as r:
                raw = r.read().decode('utf-8','ignore')
                low = raw.lower()
                if len(raw)<100: continue
                if '"total":0' in low or '"data":[]' in low: continue
                if any(k in low for k in NO_RESULT): continue
                if query.lower().split()[0] in low and query.lower().split()[-1] in low: return True
        except: continue
    try:
        url = f"https://www.google.com/search?q={q_plus}+site%3Asinta.kemdiktisaintek.go.id+OR+site%3Apddikti.kemdiktisaintek.go.id"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read().decode('utf-8','ignore').lower()
            if "sinta.kemdiktisaintek.go.id" in raw or "pddikti.kemdiktisaintek.go.id" in raw: return True
    except: pass
    return False

def cek_valid(url, query, domain):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            raw = r.read().decode('utf-8', errors='ignore').lower()
            qlow = query.lower().strip()
            for k in NO_RESULT:
                if k in raw: return False
            clean = re.sub(r'<script.*?</script>', ' ', raw, flags=re.DOTALL)
            clean = re.sub(r'<style.*?</style>', ' ', clean, flags=re.DOTALL)
            for j in JEBAKAN_SEARCH:
                clean = clean.replace(f"{j}: {qlow}", " ").replace(f"{j} {qlow}", " ").replace(j, " ")
            if qlow not in clean: return False
            links = re.findall(r'<a[^>]*>(.*?)</a>', clean)
            if not any(qlow in lt.lower() for lt in links):
                h = re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>', clean)
                if not any(qlow in x.lower() for x in h): return False
            return True
    except: return False

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('q',[''])[0].strip()
        self.send_response(200)
        self.send_header('Content-type','application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()
        if not q:
            self.wfile.write(b'{"results":[]}'); return
        if not cek_pddikti_gate(q):
            self.wfile.write(json.dumps({"query": q, "results": [], "pddikti_status": "NOT_FOUND"}, ensure_ascii=False).encode()); return
        q_plus = urllib.parse.quote_plus(q)
        q_path = urllib.parse.quote(q)
        valid = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as ex:
            futs = {}
            for domain, tpl in TEMPLATES.items():
                url = tpl.replace("{q_plus}", q_plus).replace("{q_path}", q_path)
                if "pddikti" in domain:
                    valid.append({"title": f"{q} di {domain}", "url": url, "source": domain, "valid": True}); continue
                futs[ex.submit(cek_valid, url, q, domain)] = (domain, url)
            for f in concurrent.futures.as_completed(futs):
                domain, url = futs[f]
                if f.result():
                    valid.append({"title": f"{q} di {domain}", "url": url, "source": domain, "valid": True})
        self.wfile.write(json.dumps({"query": q, "results": valid, "pddikti_status": "FOUND"}, ensure_ascii=False).encode())
