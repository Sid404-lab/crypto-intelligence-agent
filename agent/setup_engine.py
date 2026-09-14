"""
Setup scoring engine using fetch_candles and indicators modules.
"""

from indicators import ema, rsi, macd, atr, support_resistance
from fetch_candles import fetch_all_candles
from config import COINS


def _get_closes(candles):
    return [c["close"] for c in candles]


def _get_highs(candles):
    return [c["high"] for c in candles]


def _get_lows(candles):
    return [c["low"] for c in candles]


def _get_volumes(candles):
    return [c["volume"] for c in candles]


def evaluate_setup(symbol, candles_by_resolution):
    """
    Evaluate a trade setup for a symbol using 1h candles.

    Returns dict with: symbol, direction, score, reasons, entry_zone,
    stop_loss, targets, risk_reward, timeframe, invalidation
    """
    candles_1h = candles_by_resolution.get("1h", [])

    if len(candles_1h) < 50:
        return {
            "symbol": symbol,
            "direction": "NO_TRADE",
            "score": 0,
            "reasons": ["Insufficient 1h candle data"],
            "entry_zone": None,
            "stop_loss": None,
            "targets": None,
            "risk_reward": None,
            "timeframe": "1h",
            "invalidation": "N/A",
        }

    closes = _get_closes(candles_1h)
    highs = _get_highs(candles_1h)
    lows = _get_lows(candles_1h)
    volumes = _get_volumes(candles_1h)

    current_price = closes[-1]

    # === INDICATORS ===
    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)
    rsi14 = rsi(closes, 14)
    _, _, hist = macd(closes, 12, 26, 9)
    atr14 = atr(highs, lows, closes, 14)
    sr = support_resistance(candles_1h, 50)

    # Latest values (handle None)
    e20 = ema20[-1] if ema20[-1] is not None else None
    e50 = ema50[-1] if ema50[-1] is not None else None
    rsi_val = rsi14[-1] if rsi14[-1] is not None else None
    macd_hist = hist[-1] if hist[-1] is not None else None
    atr_val = atr14[-1] if atr14[-1] is not None else None

    if any(v is None for v in (e20, e50, rsi_val, macd_hist, atr_val)):
        return {
            "symbol": symbol,
            "direction": "NO_TRADE",
            "score": 0,
            "reasons": ["Insufficient indicator data"],
            "entry_zone": None,
            "stop_loss": None,
            "targets": None,
            "risk_reward": None,
            "timeframe": "1h",
            "invalidation": "N/A",
        }

    # === TREND DETERMINATION ===
    # bullish if price > EMA20 > EMA50
    # bearish if price < EMA20 < EMA50
    trend = "mixed"
    if current_price > e20 > e50:
        trend = "bullish"
    elif current_price < e20 < e50:
        trend = "bearish"

    # === SCORING ===
    # Each factor has a point value. Max per direction = 100.
    # - Trend aligned (price/EMA20/EMA50 all one direction): +25
    # - RSI in healthy range for that direction (40-70 long, 30-60 short): +15
    # - MACD histogram sign matches direction: +20
    # - Price within 3% of support (LONG) or resistance (SHORT): +20
    # - Recent volume above 20-candle average: +20

    bullish_score = 0
    bearish_score = 0
    reasons = []

    # Trend alignment
    if trend == "bullish":
        bullish_score += 25
        reasons.append("Trend aligned: price > EMA20 > EMA50")
    elif trend == "bearish":
        bearish_score += 25
        reasons.append("Trend aligned: price < EMA20 < EMA50")

    # RSI healthy range
    if 40 <= rsi_val <= 70:
        bullish_score += 15
        reasons.append(f"RSI healthy for long ({rsi_val:.1f})")
    elif 30 <= rsi_val <= 60:
        bearish_score += 15
        reasons.append(f"RSI healthy for short ({rsi_val:.1f})")

    # MACD histogram sign
    if macd_hist > 0:
        bullish_score += 20
        reasons.append("MACD histogram positive")
    elif macd_hist < 0:
        bearish_score += 20
        reasons.append("MACD histogram negative")

    # Support/Resistance proximity
    support = sr.get("support")
    resistance = sr.get("resistance")

    if support and resistance:
        dist_to_support_pct = ((current_price - support) / current_price) * 100
        dist_to_resistance_pct = ((resistance - current_price) / current_price) * 100

        if dist_to_support_pct <= 3.0:
            bullish_score += 20
            reasons.append(f"Near support ({dist_to_support_pct:.1f}% away)")
        elif dist_to_resistance_pct <= 3.0:
            bearish_score += 20
            reasons.append(f"Near resistance ({dist_to_resistance_pct:.1f}% away)")

    # Volume above average
    if len(volumes) >= 20:
        avg_vol = sum(volumes[-20:]) / 20
        if volumes[-1] > avg_vol:
            if trend == "bullish":
                bullish_score += 20
                reasons.append("Volume above 20-candle average")
            elif trend == "bearish":
                bearish_score += 20
                reasons.append("Volume above 20-candle average")

    # === DIRECTION DECISION ===
    # If both scores < 40, or within 10 points -> NO_TRADE
    if bullish_score < 40 and bearish_score < 40:
        direction = "NO_TRADE"
        score = max(bullish_score, bearish_score)
    elif abs(bullish_score - bearish_score) <= 10:
        direction = "NO_TRADE"
        score = max(bullish_score, bearish_score)
    elif bullish_score > bearish_score:
        direction = "LONG"
        score = bullish_score
    else:
        direction = "SHORT"
        score = bearish_score

    # === NON-NO_TRADE CALCULATIONS ===
    entry_zone = None
    stop_loss = None
    targets = None
    risk_reward = None
    invalidation = None

    if direction != "NO_TRADE":
        # Entry zone: current price to +/- 0.3% in trade direction
        if direction == "LONG":
            entry_zone = [round(current_price, 2), round(current_price * 1.003, 2)]
            # Stop: recent swing low minus 1x ATR
            # Use lowest low in last 10 candles as swing low proxy
            swing_low = min(lows[-10:]) if len(lows) >= 10 else min(lows)
            stop_loss = round(swing_low - atr_val, 2)

            risk_dist = entry_zone[0] - stop_loss
            if risk_dist > 0:
                # TP1 is structural: nearest resistance above entry (the
                # "room to target" the setup was scored on). It must clear
                # entry after rounding; otherwise fall back to 1x risk so
                # TP1 is never equal to (or below) entry.
                struct_tp1 = (
                    round(resistance, 2)
                    if resistance and resistance > entry_zone[0]
                    else None
                )
                if struct_tp1 is not None and struct_tp1 > entry_zone[0]:
                    tp1 = struct_tp1
                else:
                    tp1 = entry_zone[0] + risk_dist
                tp2 = entry_zone[0] + 2 * risk_dist
                tp3 = entry_zone[0] + 3 * risk_dist
                targets = [round(tp1, 2), round(tp2, 2), round(tp3, 2)]
                risk = abs(entry_zone[0] - stop_loss)
                reward = abs(targets[0] - entry_zone[0])
                rr_ratio = reward / risk if risk > 0 else 0
                risk_reward = f"1:{rr_ratio:.1f}"
            invalidation = "Price closes back below EMA20 on 1h"

        else:  # SHORT
            entry_zone = [round(current_price * 0.997, 2), round(current_price, 2)]
            # Stop: recent swing high plus 1x ATR
            swing_high = max(highs[-10:]) if len(highs) >= 10 else max(highs)
            stop_loss = round(swing_high + atr_val, 2)

            risk_dist = stop_loss - entry_zone[1]
            if risk_dist > 0:
                # TP1 is structural: nearest support below entry.
                # It must clear entry after rounding; otherwise fall back
                # to 1x risk so TP1 is never equal to (or above) entry.
                struct_tp1 = (
                    round(support, 2)
                    if support and support < entry_zone[1]
                    else None
                )
                if struct_tp1 is not None and struct_tp1 < entry_zone[1]:
                    tp1 = struct_tp1
                else:
                    tp1 = entry_zone[1] - risk_dist
                tp2 = entry_zone[1] - 2 * risk_dist
                tp3 = entry_zone[1] - 3 * risk_dist
                targets = [round(tp1, 2), round(tp2, 2), round(tp3, 2)]
                risk = abs(entry_zone[1] - stop_loss)
                reward = abs(targets[0] - entry_zone[1])
                rr_ratio = reward / risk if risk > 0 else 0
                risk_reward = f"1:{rr_ratio:.1f}"
            invalidation = "Price closes back above EMA20 on 1h"

    return {
        "symbol": symbol,
        "direction": direction,
        "score": score,
        "reasons": reasons,
        "entry_zone": entry_zone,
        "stop_loss": stop_loss,
        "targets": targets,
        "risk_reward": risk_reward,
        "timeframe": "1h",
        "invalidation": invalidation,
    }


def scan_all_setups():
    """
    Fetch candles for all coins and evaluate setups.
    Returns list sorted by score descending.
    """
    candles_data, errors = fetch_all_candles()

    setups = []
    for coin in COINS:
        symbol = coin["symbol"]
        coin_candles = candles_data.get(symbol, {})
        setup = evaluate_setup(symbol, coin_candles)
        setups.append(setup)

    # Sort by score descending
    setups.sort(key=lambda x: x["score"], reverse=True)
    return setups


if __name__ == "__main__":
    setups = scan_all_setups()
    for s in setups:
        print(f"\n--- {s['symbol']} ---")
        print(f"Direction: {s['direction']}")
        print(f"Score: {s['score']}")
        print(f"Reasons: {s['reasons']}")
        print(f"Entry: {s['entry_zone']}")
        print(f"Stop: {s['stop_loss']}")
        print(f"Targets: {s['targets']}")
        print(f"R:R: {s['risk_reward']}")
        print(f"Invalidation: {s['invalidation']}")