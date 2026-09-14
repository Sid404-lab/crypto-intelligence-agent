from http_util import get_json, to_float

COINGECKO_MARKETS_URL = "https://api.coingecko.com/api/v3/coins/markets"
BINANCE_EXCHANGE_INFO_URL = "https://api.binance.com/api/v3/exchangeInfo"


def fetch_binance_spot_usdt():
    """
    Fetch Binance's public exchangeInfo once and build the set of valid
    TRADING spot symbols (e.g. BTCUSDT). No key needed.

    Returns (symbols_set, errors). On failure returns (empty set, [error])
    so callers can still proceed with chart_symbol=None everywhere.
    """
    try:
        data = get_json(BINANCE_EXCHANGE_INFO_URL, timeout=30)
    except Exception as exc:
        return set(), [f"Binance exchangeInfo: {exc}"]

    symbols = set()
    try:
        for entry in data.get("symbols", []):
            if entry.get("status") != "TRADING":
                continue
            if not entry.get("isSpotTradingAllowed"):
                continue
            permission_sets = entry.get("permissionSets") or []
            if not any("SPOT" in ps for ps in permission_sets):
                continue
            if entry.get("symbol"):
                symbols.add(entry["symbol"])
    except Exception as exc:
        return set(), [f"Binance exchangeInfo: unexpected format ({exc})"]
    return symbols, []


def fetch_crypto_full():
    """
    Fetch the top 250 cryptocurrencies by market cap from CoinGecko's
    free public API (no key needed). One call per run — well within the
    free-tier rate limit (~10-30 calls/min).

    Returns (coins, errors): coins is a list of
    {symbol, name, price, change_24h_pct, volume, market_cap, chart_symbol}
    dicts, or None on failure so the previous report data is kept.
    On failure returns (None, [error]) so report generation continues.

    chart_symbol is "BINANCE:{SYMBOL}USDT" only when that pair is confirmed
    present in Binance exchangeInfo; otherwise None (never guessed).
    """
    valid_binance = set()
    binance_errors = []
    try:
        valid_binance, binance_errors = fetch_binance_spot_usdt()
    except Exception as exc:
        binance_errors = [f"Binance exchangeInfo: {exc}"]
    errors = list(binance_errors)
    try:
        data = get_json(
            COINGECKO_MARKETS_URL,
            params={
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": 250,
                "page": 1,
            },
            timeout=30,
        )
    except Exception as exc:
        return None, errors + [f"CoinGecko markets: {exc}"]

    if not isinstance(data, list) or not data:
        return None, errors + ["CoinGecko markets: empty response"]

    coins = []
    for coin in data:
        price = to_float(coin.get("current_price"))
        if price is None:
            continue
        symbol = str(coin.get("symbol") or "").upper()
        pair = f"{symbol}USDT"
        coins.append(
            {
                "symbol": symbol,
                "name": coin.get("name"),
                "price": price,
                "change_24h_pct": to_float(coin.get("price_change_percentage_24h")),
                "volume": to_float(coin.get("total_volume")),
                "market_cap": to_float(coin.get("market_cap")),
                "chart_symbol": f"BINANCE:{pair}" if pair in valid_binance else None,
            }
        )

    if not coins:
        return None, errors + ["CoinGecko markets: no usable entries"]
    return coins, errors
