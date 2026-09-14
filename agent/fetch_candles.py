import time
from http_util import get_json, to_float
from config import DELTA_BASE, COINS


RESOLUTION_SECONDS = {
    "5m": 300,
    "15m": 900,
    "1h": 3600,
    "4h": 14400,
}


def fetch_candles(symbol_contract, resolution, count=100):
    """
    Fetch OHLCV candle data from Delta Exchange India.

    Args:
        symbol_contract: Delta contract symbol (e.g., "BTCUSD")
        resolution: One of "5m", "15m", "1h", "4h"
        count: Number of candles to fetch (default 100)

    Returns:
        (candles_list, error_string) tuple
        candles_list: list of {"time", "open", "high", "low", "close", "volume"} dicts, oldest first
        error_string: None on success, error message on failure
    """
    if resolution not in RESOLUTION_SECONDS:
        return [], f"Invalid resolution: {resolution}"

    try:
        end_time = int(time.time())
        start_time = end_time - (RESOLUTION_SECONDS[resolution] * count * 2)

        params = {
            "resolution": resolution,
            "symbol": symbol_contract,
            "start": start_time,
            "end": end_time,
        }

        response = get_json(f"{DELTA_BASE}/history/candles", params=params, timeout=15)

        candles_data = response.get("result") or []
        if not candles_data:
            return [], f"No candle data returned for {symbol_contract} {resolution}"

        candles = []
        for c in candles_data:
            try:
                o = to_float(c.get("open"))
                h = to_float(c.get("high"))
                l = to_float(c.get("low"))
                cl = to_float(c.get("close"))
                v = to_float(c.get("volume"))
                t = int(c.get("time", 0))

                if None in (o, h, l, cl, v) or t == 0:
                    continue

                candles.append({
                    "time": t,
                    "open": o,
                    "high": h,
                    "low": l,
                    "close": cl,
                    "volume": v,
                })
            except (ValueError, TypeError):
                continue

        candles.sort(key=lambda x: x["time"])
        return candles[-count:], None

    except Exception as exc:
        return [], f"Delta candles {symbol_contract} {resolution}: {exc}"


def fetch_all_candles():
    """
    Fetch candles for all configured coins at all resolutions.

    Returns:
        (candles_dict, errors_list) tuple
        candles_dict: {symbol: {resolution: [candles]}}
        errors_list: list of error strings
    """
    resolutions = ["5m", "15m", "1h", "4h"]
    all_candles = {}
    errors = []

    for coin in COINS:
        symbol = coin["symbol"]
        contract = coin["tv"]

        all_candles[symbol] = {}
        for res in resolutions:
            candles, err = fetch_candles(contract, res, count=100)
            if err:
                errors.append(f"{symbol} {res}: {err}")
            else:
                all_candles[symbol][res] = candles

    return all_candles, errors


if __name__ == "__main__":
    btc_candles = {}
    btc_errors = []
    for res in ["5m", "15m", "1h", "4h"]:
        candles, err = fetch_candles("BTCUSD", res, count=100)
        if err:
            btc_errors.append(f"{res}: {err}")
        else:
            btc_candles[res] = candles
        print(f"BTC {res}: {len(candles)} candles")

    if btc_errors:
        print("Errors:", btc_errors)