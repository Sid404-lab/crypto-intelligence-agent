"""
serve.py — serve the frontend over HTTP from the project root.

Run from the project root:
    py -3 serve.py

Opens http://localhost:8080 and serves frontend/ as the web root,
so ./data/latest-report.json resolves correctly inside app.js.
"""
import http.server
import os
from pathlib import Path

PORT = 8080
FRONTEND = Path(__file__).resolve().parent / "frontend"

os.chdir(FRONTEND)

handler = http.server.SimpleHTTPRequestHandler
httpd = http.server.HTTPServer(("", PORT), handler)
print(f"Serving frontend/ at http://localhost:{PORT}")
print("Press Ctrl+C to stop.")
httpd.serve_forever()
