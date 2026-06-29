"""Serveur statique de DEV qui désactive le cache navigateur.

Évite de devoir faire Ctrl+Shift+R après chaque modif (les fichiers sont
toujours re-téléchargés). À ne PAS utiliser en production.

Lancer :  python scripts/serve.py [port]      # port par défaut : 8531
"""

import http.server
import os
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8531
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.chdir(ROOT)


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Pragma", "no-cache")
        super().end_headers()

    def log_message(self, *args):
        pass  # silencieux


# ThreadingHTTPServer : l'app charge plusieurs fichiers en parallèle, un serveur
# mono-thread se bloquerait.
with http.server.ThreadingHTTPServer(("0.0.0.0", PORT), NoCacheHandler) as httpd:
    print(f"Dev (sans cache) -> http://localhost:{PORT}")
    httpd.serve_forever()
