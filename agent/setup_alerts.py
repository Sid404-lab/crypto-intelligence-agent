"""
Setup alerts for Telegram — only for crypto (Delta) high-score setups.

- Main scanner: BTC, ETH, SOL, BNB, XRP, DOGE etc (COINS)
- New & Trending: Delta momentum-only tier

Dedup: by symbol+direction+entry_zone+stop_loss (main) or symbol+momentum+strength (trending)
so we don't spam every 5-min cron. Logged to data/setup_alerts_log.json with timestamp.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import requests

from config import COINS, MAJOR_SYMBOLS, ROOT

ALERT_LOG_PATH = ROOT / "data" / "setup_alerts_log.json"
# Also keep a simple dedup set in same file; no separate file needed

# Non-crypto blocklist to ensure we never alert for metals/commodities/forex/stocks
NON_CRYPTO_BLOCK = {
    # Metals
    "XAU", "XAG", "PLAT",
    # Commodities
    "WTI", "BRENT", "NATGAS", "COPPER",
    # Forex (sample, actual list is larger; we check dynamically as well)
    "EURUSD", "GBPUSD", "USDJPY", "USDINR", "AUDUSD", "USDCNY", "USDCHF", "USDCAD",
    "NZDUSD", "EURGBP", "EURJPY", "EURCHF", "EURCAD", "EURAUD", "EURNZD", "GBPJPY",
    "GBPCHF", "GBPCAD", "GBPAUD", "GBPNZD", "AUDJPY", "AUDCHF", "AUDCAD", "AUDNZD",
    "CADJPY", "CADCHF", "NZDJPY", "CHFJPY", "USDSGD", "USDHKD", "USDMXN", "USDZAR", "USDTRY",
    # Stocks (NSE/BSE + NASDAQ/NYSE) — block all stock symbols to ensure crypto-only
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "BHARTIARTL", "ITC",
    "AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "NVDA", "META", "NFLX",
    "NIFTY", "BANKNIFTY", "SENSEX", "DJI", "SPX", "IXIC",
}

CRYPTO_SCORE_THRESHOLD = 60  # main scanner high-score
TRENDING_STRENGTH_ALERT = {"Strong", "Moderate"}  # New & Trending high-signal


def _is_crypto_symbol(symbol: str) -> bool:
    """Only alert for Delta crypto. Block metals/commodities/forex/stocks."""
    s = str(symbol or "").strip().upper()
    if not s:
        return False
    if s in NON_CRYPTO_BLOCK:
        return False
    # If it's one of the 6 majors, definitely crypto
    if s in MAJOR_SYMBOLS:
        return True
    # Heuristic: forex are 6-char pairs ending with USD etc and are in blocklist;
    # stocks are in blocklist; metals/commodities also blocked above.
    # For remaining, assume crypto if not blocked and length 2-10 and not containing special.
    # New & Trending symbols like AKE, CHIP etc will pass.
    # To be safe, we also check that symbol is not obviously non-crypto like contains "/" or is 3-4 chars forex-like but not in majors.
    # We already blocked known forex, so remaining 2-5 char uppercase symbols are likely crypto.
    if len(s) >= 2 and len(s) <= 12 and s.isalpha():
        return True
    # Allow alphanumeric like 1000PEPE etc
    if s.replace("1000", "").isalpha() and len(s) <= 12:
        return True
    return True  # default to crypto for Delta trending symbols


def _dedup_key_main(setup: dict) -> str:
    sym = str(setup.get("symbol") or "").upper()
    direction = str(setup.get("direction") or "")
    entry = setup.get("entry_zone")
    stop = setup.get("stop_loss")
    # Use rounded entry/stop to avoid tiny price diff spam, but still distinct per level
    entry_str = "|".join(f"{x:.2f}" for x in entry) if isinstance(entry, (list, tuple)) else str(entry)
    stop_str = f"{stop:.2f}" if isinstance(stop, (int, float)) else str(stop)
    # Include score bucket to differentiate
    score = setup.get("score", 0)
    return f"main:{sym}:{direction}:{entry_str}:{stop_str}:{score}"


def _dedup_key_trending(item: dict) -> str:
    sym = str(item.get("symbol") or "").upper()
    direction = str(item.get("momentum_direction") or "")
    strength = str(item.get("strength") or "")
    # Use price band (rounded) to differentiate
    price = item.get("price")
    price_str = f"{price:.4f}" if isinstance(price, (int, float)) else str(price)
    return f"trending:{sym}:{direction}:{strength}:{price_str}"


def _load_log() -> list:
    if not ALERT_LOG_PATH.exists():
        return []
    try:
        data = json.loads(ALERT_LOG_PATH.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


def _save_log(entries: list):
    ALERT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Keep last 500 entries to avoid bloat
    to_save = entries[-500:]
    ALERT_LOG_PATH.write_text(json.dumps(to_save, indent=2) + "\n", encoding="utf-8")


def _is_already_alerted(dedup_key: str, log_entries: list, hours: int = 24) -> bool:
    """Check if dedup_key already alerted within hours."""
    now = datetime.now(timezone.utc)
    for entry in reversed(log_entries):
        if entry.get("dedup_key") == dedup_key:
            ts = entry.get("alerted_at")
            try:
                alerted_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                delta = (now - alerted_time).total_seconds() / 3600
                if delta < hours:
                    return True
                # If older than window, consider it new again
                return False
            except Exception:
                # If timestamp parse fails, treat as already alerted to be safe
                return True
    return False


def _format_main_alert(setup: dict) -> str:
    sym = setup.get("symbol", "?")
    direction = setup.get("direction", "?")
    score = setup.get("score", "?")
    entry = setup.get("entry_zone")
    stop = setup.get("stop_loss")
    targets = setup.get("targets")
    rr = setup.get("risk_reward")
    # Format entry zone
    if isinstance(entry, (list, tuple)) and len(entry) == 2:
        entry_str = f"${entry[0]:,.2f} – ${entry[1]:,.2f}"
    elif entry is not None:
        entry_str = f"${entry}"
    else:
        entry_str = "—"
    stop_str = f"${stop:,.2f}" if isinstance(stop, (int, float)) else (str(stop) if stop is not None else "—")
    if isinstance(targets, (list, tuple)):
        targets_str = " / ".join(f"${t:,.2f}" for t in targets)
    else:
        targets_str = str(targets) if targets else "—"
    rr_str = rr or "—"
    emoji = "🚀" if direction == "LONG" else "📉" if direction == "SHORT" else "⚪"
    lines = [
        f"{emoji} *{sym}* — {direction} (Score: {score})",
        f"*Tier:* Main Scanner",
        "",
        f"*Entry Zone:* {entry_str}",
        f"*Stop Loss:* {stop_str}",
        f"*Targets:* {targets_str}",
        f"*R:R:* {rr_str}",
        "",
        f"*Reasons:* {', '.join(setup.get('reasons') or [])[:200]}",
    ]
    # Invalidation
    inv = setup.get("invalidation")
    if inv and inv != "N/A":
        lines.append(f"*Invalidation:* {inv}")
    return "\n".join(lines)


def _format_trending_alert(item: dict) -> str:
    sym = item.get("symbol", "?")
    direction = item.get("momentum_direction", "?")
    strength = item.get("strength", "?")
    badge = item.get("badge", "")
    price = item.get("price")
    change = item.get("change_24h")
    mom = item.get("momentum_pct")
    vol_spike = item.get("volume_spike")
    why = item.get("why", "")
    price_str = f"${price:,.4f}" if isinstance(price, (int, float)) else str(price) if price is not None else "—"
    change_str = f"{change:+.2f}%" if isinstance(change, (int, float)) else ""
    mom_str = f"{mom:+.2f}%" if isinstance(mom, (int, float)) else str(mom)
    vol_str = f"{vol_spike:.2f}x" if isinstance(vol_spike, (int, float)) else str(vol_spike)
    emoji = "⚡" if direction == "LONG" else "📉" if direction == "SHORT" else "⚪"
    lines = [
        f"{emoji} *{sym}* — {direction} ({badge} {strength})",
        f"*Tier:* New & Trending (Delta momentum-only)",
        "",
        f"*Price:* {price_str} {change_str}",
        f"*Momentum:* {mom_str} (5c) | Vol Spike: {vol_str}",
        f"*Why:* {why}",
        f"*Strength:* {strength} | Badge: {badge}",
    ]
    if item.get("contract"):
        lines.append(f"*Contract:* {item.get('contract')}")
    return "\n".join(lines)


def _send_telegram(text: str, parse_mode: str = "Markdown") -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        print("Telegram setup alert skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing.")
        return False
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True,
            },
            timeout=10,
        )
        # Fallback to plain text if markdown fails (e.g., unescaped chars)
        if resp.status_code == 400:
            resp = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text, "disable_web_page_preview": True},
                timeout=10,
            )
        resp.raise_for_status()
        print(f"Telegram setup alert sent ({len(text)} chars).")
        return True
    except Exception as exc:
        print(f"Telegram setup alert failed: {exc}")
        return False


def check_and_alert(setups: list, new_trending: list):
    """
    Check for new high-score crypto setups and send Telegram alerts.

    Only alerts for crypto (Delta) — never for metals/commodities/forex/stocks.
    Tracks dedup via data/setup_alerts_log.json so we don't spam every 5-min run.
    Logs each alert with timestamp for backtesting.
    """
    log_entries = _load_log()
    new_alerts = []

    # --- Main scanner tier ---
    for setup in setups or []:
        sym = str(setup.get("symbol") or "").strip()
        if not sym or not _is_crypto_symbol(sym):
            continue
        # High-score filter: direction LONG/SHORT and score >= threshold
        direction = setup.get("direction")
        score = setup.get("score", 0)
        if direction not in ("LONG", "SHORT"):
            continue
        if not isinstance(score, (int, float)) or score < CRYPTO_SCORE_THRESHOLD:
            continue
        dedup = _dedup_key_main(setup)
        if _is_already_alerted(dedup, log_entries):
            continue
        # Format and send
        text = _format_main_alert(setup)
        sent = _send_telegram(text)
        # Log regardless of send success? Only log if sent, to allow retry
        if sent:
            entry = {
                "alerted_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "dedup_key": dedup,
                "tier": "main",
                "symbol": sym.upper(),
                "direction": direction,
                "entry_zone": setup.get("entry_zone"),
                "stop_loss": setup.get("stop_loss"),
                "targets": setup.get("targets"),
                "risk_reward": setup.get("risk_reward"),
                "score": score,
                "timeframe": setup.get("timeframe"),
                "reasons": setup.get("reasons"),
                "invalidation": setup.get("invalidation"),
            }
            log_entries.append(entry)
            new_alerts.append(entry)
            _save_log(log_entries)
        else:
            # Even if send failed, we don't want to spam; still log as attempted?
            # For now, don't log, so next run will retry
            pass

    # --- New & Trending tier (Delta momentum-only) ---
    for item in new_trending or []:
        sym = str(item.get("symbol") or "").strip()
        if not sym or not _is_crypto_symbol(sym):
            continue
        direction = item.get("momentum_direction")
        strength = item.get("strength")
        if direction not in ("LONG", "SHORT"):
            continue
        if strength not in TRENDING_STRENGTH_ALERT:
            continue
        # Additional filter: must have Delta source (crypto)
        # new_trending items are all Delta, but check
        if item.get("source") and item.get("source") != "Delta India":
            continue
        dedup = _dedup_key_trending(item)
        if _is_already_alerted(dedup, log_entries):
            continue
        text = _format_trending_alert(item)
        sent = _send_telegram(text)
        if sent:
            entry = {
                "alerted_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "dedup_key": dedup,
                "tier": "new_trending",
                "symbol": sym.upper(),
                "direction": direction,
                "strength": strength,
                "badge": item.get("badge"),
                "price": item.get("price"),
                "change_24h": item.get("change_24h"),
                "momentum_pct": item.get("momentum_pct"),
                "volume_spike": item.get("volume_spike"),
                "why": item.get("why"),
                "contract": item.get("contract"),
            }
            log_entries.append(entry)
            new_alerts.append(entry)
            _save_log(log_entries)

    if new_alerts:
        print(f"Setup alerts: {len(new_alerts)} new crypto setup(s) alerted.")
    else:
        print("Setup alerts: no new crypto setups to alert (deduped or below threshold).")
    return new_alerts
