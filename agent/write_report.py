import json
from datetime import datetime, timezone
from pathlib import Path

from config import FRONTEND_REPORT_PATH, REPORT_PATH

PLACEHOLDER = {
    "news": [],
    "listings": [],
    "trending": [],
    "metals": [],
    "commodities_forex": [],
    "crypto_full": [],
    "setups": [],
    "top_setup": None,
    "ai_briefing": {
        "morning_summary": "AI briefing not available",
        "market_sentiment": "unknown",
        "things_to_watch": []
    }
}


def _load_existing(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, ValueError):
        return {}


def write_report(
    markets=None,
    news=None,
    listings=None,
    trending=None,
    metals=None,
    commodities_forex=None,
    crypto_full=None,
    ai_briefing=None,
    setups=None,
    top_setup=None,
    errors=None,
):
    existing = _load_existing(REPORT_PATH) or _load_existing(FRONTEND_REPORT_PATH)

    # Default top_setup if not provided
    if top_setup is None and setups:
        for s in setups:
            if s.get("direction") != "NO_TRADE" and s.get("score", 0) >= 60:
                top_setup = s
                break
        if top_setup is None:
            top_setup = {"note": "no high-quality setup right now"}

    report = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "markets": markets
        if markets is not None
        else existing.get("markets", []),
        "news": news if news is not None else existing.get("news", PLACEHOLDER["news"]),
        "listings": listings
        if listings is not None
        else existing.get("listings", PLACEHOLDER["listings"]),
        "trending": trending
        if trending is not None
        else existing.get("trending", PLACEHOLDER["trending"]),
        "metals": metals
        if metals is not None
        else existing.get("metals", PLACEHOLDER["metals"]),
        "commodities_forex": commodities_forex
        if commodities_forex is not None
        else existing.get("commodities_forex", PLACEHOLDER["commodities_forex"]),
        "crypto_full": crypto_full
        if crypto_full is not None
        else existing.get("crypto_full", PLACEHOLDER["crypto_full"]),
        "setups": setups if setups is not None else existing.get("setups", PLACEHOLDER["setups"]),
        "top_setup": top_setup if top_setup is not None else existing.get("top_setup", PLACEHOLDER["top_setup"]),
        "ai_briefing": ai_briefing if ai_briefing is not None else existing.get("ai_briefing", PLACEHOLDER["ai_briefing"]),
        "errors": {
            "markets": [],
            "news": [],
            "listings": [],
            "trending": [],
            "metals": [],
            "commodities_forex": [],
            "crypto_full": [],
            **(errors if errors is not None else existing.get("errors", {})),
        },
    }
    payload = json.dumps(report, indent=2) + "\n"

    for path in (REPORT_PATH, FRONTEND_REPORT_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")

    return REPORT_PATH
