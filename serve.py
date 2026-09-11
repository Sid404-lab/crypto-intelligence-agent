"""
serve.py — Dynamic crypto intelligence dashboard server.

Run from the project root:
    py -3 serve.py

Opens:
    http://127.0.0.1:8080

Serves:
- Static frontend files from frontend/
- /api/health
- /api/report
"""

import http.server
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parent
AGENT_DIR = ROOT / "agent"
FRONTEND = ROOT / "frontend"

# Allow imports from agent/
sys.path.insert(0, str(AGENT_DIR))


# ============================================================
# AGENT IMPORTS
# ============================================================

from fetch_listings import fetch_listings, fetch_trending_coins
from fetch_market import fetch_markets
from fetch_news import fetch_news
from groq_briefing import generate_ai_briefing


# ============================================================
# SERVER CONFIG
# ============================================================

HOST = "127.0.0.1"
PORT = 8080


# ============================================================
# REQUEST HANDLER
# ============================================================

class APIHandler(http.server.SimpleHTTPRequestHandler):
    """
    Handles both:
    - Static frontend files
    - Dynamic API endpoints
    """

    def __init__(self, *args, directory=None, **kwargs):
        if directory is None:
            directory = str(FRONTEND)

        super().__init__(
            *args,
            directory=directory,
            **kwargs
        )

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    def do_GET(self):
        """Handle GET requests."""

        parsed_path = urlparse(self.path)

        if parsed_path.path.startswith("/api/"):
            self.handle_api_request(parsed_path)
        else:
            # Serve frontend files
            super().do_GET()

    # --------------------------------------------------------
    # OPTIONS
    # --------------------------------------------------------

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""

        self.send_response(204)

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, OPTIONS"
        )

        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )

        self.send_header(
            "Content-Length",
            "0"
        )

        self.end_headers()

    # --------------------------------------------------------
    # API ROUTER
    # --------------------------------------------------------

    def handle_api_request(self, parsed_path):
        """Route API requests."""

        path = parsed_path.path

        try:

            if path == "/api/health":
                self.handle_health()

            elif path == "/api/report":
                self.handle_live_report()

            else:
                self.send_json(
                    {
                        "error": "API endpoint not found",
                        "path": path
                    },
                    status=404
                )

        except Exception as exc:

            print(
                f"[API ERROR] {path}: {exc}",
                file=sys.stderr
            )

            self.send_json(
                {
                    "error": "Internal server error",
                    "message": str(exc)
                },
                status=500
            )

    # --------------------------------------------------------
    # HEALTH
    # --------------------------------------------------------

    def handle_health(self):
        """Return a lightweight health response."""

        health = {
            "status": "healthy",
            "timestamp": datetime.now(
                timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "version": "2.0.0"
        }

        self.send_json(
            health,
            status=200
        )

    # --------------------------------------------------------
    # LIVE REPORT
    # --------------------------------------------------------

    def handle_live_report(self):
        """
        Fetch fresh market/news/listing data concurrently
        and generate a fresh AI briefing.
        """

        # ----------------------------------------------------
        # Timestamp when this request started
        # ----------------------------------------------------

        generated_at = datetime.now(
            timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

        print(
            f"[REPORT] Generating live report at {generated_at}"
        )

        # ----------------------------------------------------
        # Concurrent data fetching
        # ----------------------------------------------------

        def fetch_markets_safe():
            try:
                return fetch_markets(fast=True)
            except Exception as exc:
                return None, [f"Market fetch failed: {exc}"]

        def fetch_news_safe():
            try:
                return fetch_news()
            except Exception as exc:
                return None, [f"News fetch failed: {exc}"]

        def fetch_listings_safe():
            try:
                return fetch_listings(fast=True)
            except Exception as exc:
                return None, [f"Listings fetch failed: {exc}"]

        def fetch_trending_safe():
            try:
                return fetch_trending_coins()
            except Exception as exc:
                return None, [f"Trending fetch failed: {exc}"]

        # Run all data fetches concurrently with individual timeouts
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(fetch_markets_safe): "markets",
                executor.submit(fetch_news_safe): "news",
                executor.submit(fetch_listings_safe): "listings",
                executor.submit(fetch_trending_safe): "trending"
            }
            
            results = {}
            # Wait for each future individually with shorter timeout
            for future in futures:
                try:
                    key = futures[future]
                    results[key] = future.result(timeout=8)  # 8s timeout per individual call
                except Exception as exc:
                    key = futures[future]
                    results[key] = (None, [f"{key} fetch failed: {exc}"])

        # Extract results
        markets, market_errors = results.get("markets", (None, []))
        news, news_errors = results.get("news", (None, []))
        listings, listing_errors = results.get("listings", (None, []))
        trending, trending_errors = results.get("trending", (None, []))

        # ----------------------------------------------------
        # AI Briefing
        # ----------------------------------------------------

        try:
            ai_briefing = generate_ai_briefing(
                markets,
                news,
                listings
            )

        except Exception as exc:
            ai_briefing = {
                "morning_summary": "AI briefing unavailable.",
                "market_sentiment": "unknown",
                "things_to_watch": ["AI briefing generation failed"],
                "error": str(exc)
            }

        # ----------------------------------------------------
        # Final report
        # ----------------------------------------------------

        report = {
            "generated_at": generated_at,

            "markets": (
                markets
                if markets is not None
                else []
            ),

            "summary": (
                "Live market intelligence - "
                "data fetched in real-time"
            ),

            "watch": [],

            "news": (
                news
                if news is not None
                else []
            ),

            "listings": (
                listings
                if listings is not None
                else []
            ),

            "trending": (
                trending
                if trending is not None
                else []
            ),

            "ai_briefing": ai_briefing,

            "errors": {
                "markets": market_errors,
                "news": news_errors,
                "listings": listing_errors,
                "trending": trending_errors
            }
        }

        print(
            "[REPORT] Live report generated successfully"
        )

        self.send_json(
            report,
            status=200
        )

    # --------------------------------------------------------
    # JSON RESPONSE HELPER
    # --------------------------------------------------------

    def send_json(self, data, status=200):
        """
        Send a proper JSON HTTP response.

        Content-Length is explicitly provided so the
        client knows exactly how many bytes to read.
        """

        response = json.dumps(
            data,
            indent=2,
            ensure_ascii=False
        ).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.send_header(
            "Content-Length",
            str(len(response))
        )

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, OPTIONS"
        )

        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )

        self.end_headers()

        self.wfile.write(response)

    # --------------------------------------------------------
    # LOGGING
    # --------------------------------------------------------

    def log_message(self, format, *args):
        """
        Reduce static-file noise.

        API requests and errors are still logged.
        """

        path = self.path

        is_api = path.startswith("/api/")

        status_code = None

        if len(args) >= 2:
            try:
                status_code = int(args[1])
            except (ValueError, TypeError):
                pass

        is_error = (
            status_code is not None
            and status_code >= 400
        )

        if is_api or is_error:
            super().log_message(
                format,
                *args
            )


# ============================================================
# SERVER START
# ============================================================

def main():
    """Start the development server."""

    print(
        "Crypto Intelligence Dashboard"
    )

    print(
        f"Serving at http://{HOST}:{PORT}"
    )

    print(
        f"Static files from: {FRONTEND}"
    )

    print(
        "API endpoints:"
    )

    print(
        f"  http://{HOST}:{PORT}/api/health"
    )

    print(
        f"  http://{HOST}:{PORT}/api/report"
    )

    print(
        "Press Ctrl+C to stop."
    )

    try:

        httpd = http.server.ThreadingHTTPServer(
            (HOST, PORT),
            APIHandler
        )

        # Keep frontend directory independent from cwd.
        # SimpleHTTPRequestHandler receives it through
        # the directory parameter above.

        httpd.serve_forever()

    except KeyboardInterrupt:

        print(
            "\nServer stopped."
        )

    except OSError as exc:

        print(
            f"Error starting server: {exc}"
        )

        print(
            f"Port {PORT} may be in use."
        )

    finally:

        try:
            httpd.server_close()
        except (NameError, AttributeError):
            pass


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()