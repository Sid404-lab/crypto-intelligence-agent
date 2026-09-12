import os

import requests


def _format_message(ai_briefing):
    briefing = ai_briefing or {}
    summary = briefing.get("morning_summary", "AI briefing unavailable.")
    sentiment = briefing.get("market_sentiment", "unknown")
    watch_items = briefing.get("things_to_watch") or []

    lines = [
        "Pulse — Crypto Intelligence Brief",
        "",
        summary,
        "",
        f"Sentiment: {sentiment}",
    ]

    if watch_items:
        lines.append("")
        lines.append("Things to watch:")
        lines.extend(f"- {item}" for item in watch_items)

    return "\n".join(lines)


def send_telegram_briefing(ai_briefing):
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not token or not chat_id:
        print("Telegram notification skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing.")
        return

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": _format_message(ai_briefing),
                "disable_web_page_preview": True,
            },
            timeout=10,
        )
        response.raise_for_status()
        print("Telegram notification sent.")
    except Exception as exc:
        print(f"Telegram notification failed: {exc}")
