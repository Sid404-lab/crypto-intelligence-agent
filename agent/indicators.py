"""
Pure Python technical indicator implementations.
No external dependencies — only built-in operations.
"""


def ema(values, period):
    """
    Exponential Moving Average.
    Returns list of same length as input with None for first period-1 entries.
    """
    if not values or len(values) < period:
        return [None] * len(values) if values else []

    multiplier = 2.0 / (period + 1)
    result = [None] * (period - 1)

    # First EMA is SMA of first `period` values
    first_ema = sum(values[:period]) / period
    result.append(first_ema)

    for i in range(period, len(values)):
        ema_val = (values[i] - result[-1]) * multiplier + result[-1]
        result.append(ema_val)

    return result


def rsi(closes, period=14):
    """
    Relative Strength Index (Wilder's method).
    Returns list of RSI values (0-100), None where insufficient data.
    """
    if not closes or len(closes) < period + 1:
        return [None] * len(closes) if closes else []

    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]

    gains = [d if d > 0 else 0.0 for d in deltas]
    losses = [-d if d < 0 else 0.0 for d in deltas]

    # First average gain/loss (simple average)
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    result = [None] * period

    if avg_loss == 0:
        result.append(100.0)
    else:
        rs = avg_gain / avg_loss
        result.append(100.0 - (100.0 / (1.0 + rs)))

    # Subsequent values use Wilder's smoothing
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            result.append(100.0)
        else:
            rs = avg_gain / avg_loss
            result.append(100.0 - (100.0 / (1.0 + rs)))

    return result


def macd(closes, fast=12, slow=26, signal=9):
    """
    MACD (Moving Average Convergence Divergence).
    Returns tuple: (macd_line, signal_line, histogram)
    Each list same length as input.
    """
    if not closes or len(closes) < slow + signal:
        empty = [None] * len(closes) if closes else []
        return empty, empty, empty

    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)

    macd_line = [None] * len(closes)
    for i in range(len(closes)):
        if ema_fast[i] is not None and ema_slow[i] is not None:
            macd_line[i] = ema_fast[i] - ema_slow[i]

    # Signal line is EMA of MACD line
    valid_macd = [v for v in macd_line if v is not None]
    if len(valid_macd) < signal:
        return macd_line, [None] * len(closes), [None] * len(closes)

    signal_line_raw = ema(valid_macd, signal)
    # Pad with Nones to match original length
    signal_line = [None] * (len(closes) - len(signal_line_raw)) + signal_line_raw

    histogram = [None] * len(closes)
    for i in range(len(closes)):
        if macd_line[i] is not None and signal_line[i] is not None:
            histogram[i] = macd_line[i] - signal_line[i]

    return macd_line, signal_line, histogram


def atr(highs, lows, closes, period=14):
    """
    Average True Range (Wilder's method).
    Returns list of ATR values, None where insufficient data.
    """
    if not highs or len(highs) < period + 1:
        return [None] * len(highs) if highs else []

    true_ranges = [None]  # First candle has no previous close

    for i in range(1, len(highs)):
        tr1 = highs[i] - lows[i]
        tr2 = abs(highs[i] - closes[i - 1])
        tr3 = abs(lows[i] - closes[i - 1])
        true_ranges.append(max(tr1, tr2, tr3))

    # First ATR is simple average of first `period` true ranges
    result = [None] * period
    first_atr = sum(true_ranges[1:period + 1]) / period
    result.append(first_atr)

    # Subsequent ATRs use Wilder's smoothing
    for i in range(period + 1, len(true_ranges)):
        atr_val = (result[-1] * (period - 1) + true_ranges[i]) / period
        result.append(atr_val)

    return result


def support_resistance(candles, lookback=50):
    """
    Find support (lowest low) and resistance (highest high) in the last `lookback` candles.
    Returns {"support": price, "resistance": price}
    """
    if not candles or len(candles) < lookback:
        return {"support": None, "resistance": None}

    recent = candles[-lookback:]
    lows = [c["low"] for c in recent]
    highs = [c["high"] for c in recent]

    return {
        "support": min(lows) if lows else None,
        "resistance": max(highs) if highs else None,
    }


if __name__ == "__main__":
    from fetch_candles import fetch_candles

    candles_1h, err = fetch_candles("BTCUSD", "1h", count=100)
    if err:
        print(f"Error fetching candles: {err}")
    else:
        closes = [c["close"] for c in candles_1h]
        highs = [c["high"] for c in candles_1h]
        lows = [c["low"] for c in candles_1h]

        ema20 = ema(closes, 20)
        rsi14 = rsi(closes, 14)
        macd_line, signal_line, histogram = macd(closes, 12, 26, 9)
        atr14 = atr(highs, lows, closes, 14)
        sr = support_resistance(candles_1h, 50)

        print(f"Latest close: {closes[-1]:.2f}")
        print(f"EMA20: {ema20[-1]:.2f}")
        print(f"RSI14: {rsi14[-1]:.2f}")
        print(f"MACD histogram: {histogram[-1]:.6f}")
        print(f"ATR14: {atr14[-1]:.2f}")
        print(f"Support (50): {sr['support']:.2f}")
        print(f"Resistance (50): {sr['resistance']:.2f}")