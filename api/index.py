from http.server import BaseHTTPRequestHandler
import urllib.parse, json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed.query)
            query = (qs.get('q') or qs.get('u') or qs.get('name') or [None])[0]

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            if not query:
                self.wfile.write(json.dumps({"error": "need ?q=nama", "contoh": "/api/index?q=Prabowo Subianto"}).encode())
                return

            q = query.strip()
            q_enc = urllib.parse.quote_plus(q)
            q_enc_plus = q.replace(' ', '+')

            # SEMUA SUMBER TERBUKA - kita kasih link search langsung, anti blokir
            results = [
                {"title": f"Google - {q}", "url": f"https://www.google.com/search?q={q_enc}", "source": "google"},
                {"title": f"Google News - {q}", "url": f"https://news.google.com/search?q={q_enc}", "source": "gnews"},
                {"title": f"Wikipedia - {q}", "url": f"https://id.wikipedia.org/w/index.php?search={q_enc}", "source": "wikipedia"},
                {"title": f"Twitter / X - {q}", "url": f"https://x.com/search?q={q_enc}", "source": "twitter"},
                {"title": f"YouTube - {q}", "url": f"https://www.youtube.com/results?search_query={q_enc}", "source": "youtube"},
                {"title": f"TikTok - {q}", "url": f"https://www.tiktok.com/search?q={q_enc}", "source": "tiktok"},
                {"title": f"Instagram - {q}", "url": f"https://www.google.com/search?q=site%3Ainstagram.com+{q_enc}", "source": "instagram"},
                {"title": f"Facebook - {q}", "url": f"https://www.facebook.com/search/top/?q={q_enc}", "source": "facebook"},
                {"title": f"Detik.com - {q}", "url": f"https://www.detik.com/search/searchall?query={q_enc}", "source": "detik"},
                {"title": f"Kompas.com - {q}", "url": f"https://search.kompas.com/search?q={q_enc}", "source": "kompas"},
                {"title": f"CNN Indonesia - {q}", "url": f"https://www.cnnindonesia.com/search/?query={q_enc}", "source": "cnn"},
                {"title": f"PDDikti - {q}", "url": f"https://pddikti.kemdikbud.go.id/search/{q_enc}", "source": "pddikti"},
                {"title": f"LinkedIn - {q}", "url": f"https://www.linkedin.com/search/results/all/?keywords={q_enc}", "source": "linkedin"},
                {"title": f"GitHub - {q}", "url": f"https://github.com/search?q={q_enc}", "source": "github"},
                {"title": f"Google Maps - {q}", "url": f"https://www.google.com/maps/search/{q_enc}", "source": "maps"},
            ]

            data = {
                "query": q,
                "total": len(results),
                "results": results,
                "note": "PAPUA THREAT INTELLIGENCE - LEGAL PUBLIC OSINT"
            }
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

        except Exception as e:
            # INI PENTING: kalau error pun tetap balikin JSON, bukan HTML
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e), "query": ""}).encode())
