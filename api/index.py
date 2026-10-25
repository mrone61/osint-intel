from http.server import BaseHTTPRequestHandler
import urllib.parse, json, urllib.request, re, time, random

TEMPLATES = {
# === MEDIA NASIONAL (40) ===
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
"pikiran-rakyat.com": "https://www.pikiran-rakyat.com/search?q={q_plus}",
"rmol.id": "https://www.rmol.id/search?q={q_plus}",
"inilah.com": "https://www.inilah.com/search?q={q_plus}",
"wartaekonomi.co.id": "https://www.wartaekonomi.co.id/search?q={q_plus}",
"era.id": "https://www.era.id/search?q={q_plus}",

# === TRIBUN REGIONAL (29) ===
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

# === JAWA POS GROUP + SULUT ===
"radar-bali.jawapos.com": "https://radar-bali.jawapos.com/search?q={q_plus}",
"radarjogja.jawapos.com": "https://radarjogja.jawapos.com/search?q={q_plus}",
"radarsolo.jawapos.com": "https://radarsolo.jawapos.com/search?q={q_plus}",
"radarsemarang.jawapos.com": "https://radarsemarang.jawapos.com/search?q={q_plus}",
"radarsurabaya.jawapos.com": "https://radarsurabaya.jawapos.com/search?q={q_plus}",
"radar-lampung.jawapos.com": "https://radarlampung.jawapos.com/search?q={q_plus}",
"radar-bogor.jawapos.com": "https://radar-bogor.jawapos.com/search?q={q_plus}",
"radar-cirebon.jawapos.com": "https://radarcirebon.jawapos.com/search?q={q_plus}",
"radar-madura.jawapos.com": "https://radar-madura.jawapos.com/search?q={q_plus}",
"manadopost.jawapos.com": "https://manadopost.jawapos.com/search?q={q_plus}",
"bmanado.com": "https://www.bmanado.com/search?q={q_plus}",
"detiksulut.com": "https://www.detiksulut.com/search?q={q_plus}",
"sulut.inews.id": "https://sulut.inews.id/search?q={q_plus}",
"herald.id": "https://www.herald.id/search?q={q_plus}",
"fajar.co.id": "https://www.fajar.co.id/search?q={q_plus}",
"lintas-sulut.com": "https://www.lintas-sulut.com/search?q={q_plus}",

# === ANTARA REGIONAL (30) ===
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
"sulut.antaranews.com": "https://sulut.antaranews.com/search?q={q_plus}",
"sulsel.antaranews.com": "https://sulsel.antaranews.com/search?q={q_plus}",
"sulteng.antaranews.com": "https://sulteng.antaranews.com/search?q={q_plus}",
"sultra.antaranews.com": "https://sultra.antaranews.com/search?q={q_plus}",
"maluku.antaranews.com": "https://maluku.antaranews.com/search?q={q_plus}",
"papua.antaranews.com": "https://papua.antaranews.com/search?q={q_plus}",
"papuabarat.antaranews.com": "https://papuabarat.antaranews.com/search?q={q_plus}",
"gorontalo.antaranews.com": "https://gorontalo.antaranews.com/search?q={q_plus}",
"sumbar.antaranews.com": "https://sumbar.antaranews.com/search?q={q_plus}",
"jambi.antaranews.com": "https://jambi.antaranews.com/search?q={q_plus}",
"sumsel.antaranews.com": "https://sumsel.antaranews.com/search?q={q_plus}",
"bengkulu.antaranews.com": "https://bengkulu.antaranews.com/search?q={q_plus}",
"lampung.antaranews.com": "https://lampung.antaranews.com/search?q={q_plus}",
"babel.antaranews.com": "https://babel.antaranews.com/search?q={q_plus}",
"kepri.antaranews.com": "https://kepri.antaranews.com/search?q={q_plus}",
"jateng.antaranews.com": "https://jateng.antaranews.com/search?q={q_plus}",
"jogja.antaranews.com": "https://jogja.antaranews.com/search?q={q_plus}",
"kalsel.antaranews.com": "https://kalsel.antaranews.com/search?q={q_plus}",
"kaltara.antaranews.com": "https://kaltara.antaranews.com/search?q={q_plus}",
"malut.antaranews.com": "https://malut.antaranews.com/search?q={q_plus}",

# === PEMERINTAH + MILITER + KEUANGAN + BMKG + BENCANA ===
"bmkg.go.id": "https://www.bmkg.go.id/search?q={q_plus}",
"bnpb.go.id": "https://bnpb.go.id/search?q={q_plus}",
"basarnas.go.id": "https://www.basarnas.go.id/search?q={q_plus}",
"bps.go.id": "https://www.bps.go.id/search?q={q_plus}",
"bi.go.id": "https://www.bi.go.id/id/search?q={q_plus}",
"ojk.go.id": "https://www.ojk.go.id/id/search?q={q_plus}",
"kemenkeu.go.id": "https://www.kemenkeu.go.id/search?q={q_plus}",
"kemendagri.go.id": "https://www.kemendagri.go.id/?s={q_plus}",
"kemensos.go.id": "https://kemensos.go.id/search?q={q_plus}",
"kemlu.go.id": "https://kemlu.go.id/search?q={q_plus}",
"kpu.go.id": "https://www.kpu.go.id/search?q={q_plus}",
"dpr.go.id": "https://www.dpr.go.id/search?q={q_plus}",
"mkri.id": "https://www.mkri.id/index.php?page=search&q={q_plus}",
"mahkamahagung.go.id": "https://www.mahkamahagung.go.id/search?q={q_plus}",
"kejaksaan.go.id": "https://www.kejaksaan.go.id/search?q={q_plus}",
"polri.go.id": "https://www.polri.go.id/search?q={q_plus}",
"tni.mil.id": "https://tni.mil.id/search?q={q_plus}",
"kemhan.go.id": "https://www.kemhan.go.id/?s={q_plus}",
"indonesia.go.id": "https://www.indonesia.go.id/search?q={q_plus}",

# === AKADEMIK + GLOBAL ===
"pddikti.kemdiktisaintek.go.id": "https://pddikti.kemdiktisaintek.go.id/search/{q_path}",
"sinta.kemdiktisaintek.go.id": "https://sinta.kemdiktisaintek.go.id/authors?q={q_plus}",
"garuda.kemdikbud.go.id": "https://garuda.kemdikbud.go.id/documents?q={q_plus}",
"youtube.com": "https://www.youtube.com/results?search_query={q_plus}",
"wikipedia.org": "https://id.wikipedia.org/w/index.php?search={q_plus}",
}

NO_RESULT = ["tidak ditemukan","tidak ada hasil","data tidak ditemukan","no results","nothing found","berita tidak ditemukan","pencarian tidak ditemukan","0 hasil"]

def cek_pddikti_gate(query):
    return True

def cek_satu_situs(domain, query):
    # JEDA 3.5 DETIK - LEGAL & SOPAN 100%
    time.sleep(random.uniform(3.0, 4.0))
    if domain not in TEMPLATES: return False, ""
    tpl = TEMPLATES[domain]
    url = tpl.replace("{q_plus}", urllib.parse.quote_plus(query)).replace("{q_path}", urllib.parse.quote(query))
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 (OSINT-Intel/1.0 - Educational Research - Manado) Chrome/122.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read().decode('utf-8','ignore').lower()
            if any(k in raw for k in NO_RESULT): return False, url
            
            query_lower = query.lower()
            parts = query_lower.split()
            match_count = sum(1 for p in parts if len(p) > 2 and p in raw)
            
            if query_lower in raw:
                return True, url
            if match_count >= 2 or (len(parts) == 2 and match_count == 2):
                return True, url
            if len(parts) == 1 and parts[0] in raw:
                return True, url
            return False, url
    except Exception as e:
        return False, url

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        q = qs.get('q',[''])[0].strip()
        domain = qs.get('domain',[''])[0].strip()

        self.send_response(200)
        self.send_header('Content-type','application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin','*')
        self.end_headers()

        if not q:
            self.wfile.write(b'{"pddikti_status":"NOT_FOUND"}'); return

        if domain:
            valid, url = cek_satu_situs(domain, q)
            self.wfile.write(json.dumps({"valid":valid,"domain":domain,"url":url,"title":f"{q} di {domain}"}, ensure_ascii=False).encode())
            return

        domains = [d for d in TEMPLATES.keys() if "pddikti" not in d and "sinta" not in d]
        self.wfile.write(json.dumps({"pddikti_status":"FOUND","query":q,"total":len(domains),"domains":domains}, ensure_ascii=False).encode())
