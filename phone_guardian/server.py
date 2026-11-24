#!/usr/bin/env python3
"""Local dashboard for Peace Unity Phone Guardian. Loopback only, with Host/Origin checks and a request header
requirement (blocks other web pages from poking the API) plus strict security headers."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json, os, webbrowser
import guardian

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
PORT = int(os.environ.get("GUARDIAN_PORT", "8765"))
ALLOWED_HOSTS = {f"127.0.0.1:{PORT}", f"localhost:{PORT}"}
MAX_BODY = 20_000
CSP = "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"

class Handler(SimpleHTTPRequestHandler):
    server_version = "Guardian"
    sys_version = ""

    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(WEB), **k)

    def log_message(self, *a):          # keep the terminal quiet and avoid logging URLs that may contain pasted links
        pass

    def end_headers(self):
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        super().end_headers()

    def _host_ok(self):
        if self.headers.get("Host", "") not in ALLOWED_HOSTS:
            self.send_error(403, "Bad host"); return False
        return True

    def _json(self, data, code=200):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)

    def list_directory(self, path):
        self.send_error(404); return None

    def do_GET(self):
        if not self._host_ok(): return
        if self.path == "/api/status":
            return self._json({"name": guardian.APP, "version": guardian.VERSION, "platform": guardian.detect_platform()})
        if self.path == "/api/history":
            return self._json(guardian.history())
        if self.path == "/api/report.html":
            p = guardian.REPORTS / "latest-report.html"
            if not p.exists(): return self.send_error(404)
            b = p.read_bytes(); self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(b)))
            self.send_header("Content-Disposition", "attachment; filename=guardian-report.html"); self.end_headers(); self.wfile.write(b); return
        return super().do_GET()

    def do_POST(self):
        if not self._host_ok(): return
        origin = self.headers.get("Origin")
        if origin and origin.replace("http://", "") not in ALLOWED_HOSTS:
            return self.send_error(403, "Bad origin")
        if self.headers.get("X-Guardian") != "1":
            return self.send_error(403, "Missing header")
        try: n = int(self.headers.get("Content-Length", "0"))
        except ValueError: n = 0
        if n > MAX_BODY: return self.send_error(413)
        try: body = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError: return self._json({"error": "bad json"}, 400)
        try:
            if self.path == "/api/scan":
                d = guardian.run_scan(offline=bool(body.get("offline")))
                d["report_path"] = str(guardian.save_report(d)); return self._json(d)
            if self.path == "/api/clean": return self._json(guardian.safe_cleanup())
            if self.path == "/api/adblock": return self._json(guardian.adblock_test())
            if self.path == "/api/check-url": return self._json(guardian.scan_url(str(body.get("url", ""))))
            if self.path == "/api/check-text": return self._json(guardian.scan_text(str(body.get("text", ""))[:5000]))
        except Exception as e:
            return self._json({"error": str(e)[:200]}, 500)
        self.send_error(404)

if __name__ == "__main__":
    print(f"{guardian.APP} dashboard\nOpen http://127.0.0.1:{PORT}\nLocal-only: not reachable from your Wi-Fi.  Press Ctrl+C to stop.")
    try: webbrowser.open(f"http://127.0.0.1:{PORT}")
    except Exception: pass
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
