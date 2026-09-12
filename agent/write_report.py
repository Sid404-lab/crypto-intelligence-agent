import json
from datetime import datetime, timezone
from pathlib import Path

from config import FRONTEND_REPORT_PATH, REPORT_PATH

PLACEHOLDER = {
    "summary": "Market data is live. The AI morning brief will be added in a later step.",
    "watch": [],
    "news": [],
    "listings": [],
    "ai_briefing": {
        "morning_summary": "AI briefing not available",
        "market_sentiment": "unknown",
        "things_to_watch": []
    }
}


def _load_existing(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_report(
    markets=None,
    news=None,
    listings=None,
    ai_briefing=None,
    errors=None,
):
    existing = _load_existing(REPORT_PATH) or _load_existing(FRONTEND_REPORT_PATH)
    report = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "markets": markets
        if markets is not None
        else existing.get("markets", []),
        "summary": existing.get("summary", PLACEHOLDER["summary"]),
        "watch": existing.get("watch", PLACEHOLDER["watch"]),
        "news": news if news is not None else existing.get("news", PLACEHOLDER["news"]),
        "listings": listings
        if listings is not None
        else existing.get("listings", PLACEHOLDER["listings"]),
        "ai_briefing": ai_briefing if ai_briefing is not None else existing.get("ai_briefing", PLACEHOLDER["ai_briefing"]),
        "errors": errors if errors is not None else existing.get("errors", {}),
    }
    payload = json.dumps(report, indent=2) + "\n"

    for path in (REPORT_PATH, FRONTEND_REPORT_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")

    return REPORT_PATH
