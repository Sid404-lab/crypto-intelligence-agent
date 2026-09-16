import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

try:
    from zoneinfo import ZoneInfo

    IST = ZoneInfo("Asia/Kolkata")
except Exception:
    IST = timezone(timedelta(hours=5, minutes=30))

BRIEFING_TIMES_IST = [(9, 0), (18, 0)]  # 9 AM and 6 PM IST
BRIEFING_WINDOW_MINUTES = 15  # cron every 5 min, so 15 min window ensures we catch it
BRIEFING_STATE_PATH = Path(__file__).resolve().parent.parent / "data" / "last_briefing_sent.json"


def _get_ist_now() -> datetime:
    return datetime.now(timezone.utc).astimezone(IST)


def _get_current_briefing_slot(now_ist: datetime):
    """If now_ist is within BRIEFING_WINDOW of a scheduled time, return slot key like '09:00' else None."""
    for hour, minute in BRIEFING_TIMES_IST:
        slot_start = now_ist.replace(hour=hour, minute=minute, second=0, microsecond=0)
        slot_end = slot_start + timedelta(minutes=BRIEFING_WINDOW_MINUTES)
        if slot_start <= now_ist < slot_end:
            return f"{hour:02d}:{minute:02d}"
    return None


def _load_briefing_state() -> dict:
    if not BRIEFING_STATE_PATH.exists():
        return {}
    try:
        data = json.loads(BRIEFING_STATE_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
        return {}
    except Exception:
        return {}


def _save_briefing_state(state: dict):
    BRIEFING_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BRIEFING_STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def _should_send_briefing(now_ist: datetime = None) -> tuple[bool, str]:
    """Check if we are in a briefing window and haven't already sent for that slot today."""
    if now_ist is None:
        now_ist = _get_ist_now()
    slot = _get_current_briefing_slot(now_ist)
    if not slot:
        return False, ""
    date_str = now_ist.strftime("%Y-%m-%d")
    key = f"{date_str} {slot}"
    state = _load_briefing_state()
    if key in state:
        return False, key
    return True, key


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


def send_telegram_briefing(ai_briefing, force: bool = False, now_ist: datetime = None):
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not token or not chat_id:
        print("Telegram notification skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing.")
        return

    # Schedule check: only twice a day at 09:00 and 18:00 IST, with dedup via state file
    if not force:
        if now_ist is None:
            now_ist = _get_ist_now()
        should_send, slot_key = _should_send_briefing(now_ist)
        if not should_send:
            # Determine reason for skipping
            current_slot = _get_current_briefing_slot(now_ist)
            if not current_slot:
                print(
                    f"Telegram briefing skipped: not in briefing window "
                    f"(09:00 or 18:00 IST, {BRIEFING_WINDOW_MINUTES}min window) — current IST {now_ist.strftime('%Y-%m-%d %H:%M %Z')}"
                )
            else:
                print(f"Telegram briefing skipped: already sent for {slot_key} (deduped).")
            return
        # slot_key is like "2026-09-16 09:00"
        target_slot = slot_key
    else:
        target_slot = None

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
        if not force and target_slot:
            # Mark this slot as sent
            state = _load_briefing_state()
            state[target_slot] = datetime.now(timezone.utc).isoformat()
            # Also keep a simple last_sent for debugging
            state["last_sent"] = target_slot
            state["last_sent_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            _save_briefing_state(state)
    except Exception as exc:
        print(f"Telegram notification failed: {exc}")
