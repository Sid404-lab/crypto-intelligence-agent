from config import DELTA_BASE
from http_util import get_json, to_float


def fetch_crypto_full():
    """
    Fetch the full list of crypto markets available on Delta Exchange India
    using the public products/tickers endpoint — no API key needed.

    Uses Delta's public REST: GET /v2/tickers?contract_types=perpetual_futures
    and filters for crypto (top_tag == "crypto") to exclude tradfi stock tokens.
    Returns data in the same shape as the previous CoinGecko top-250 so the
    frontend's ALL/TOP GAINERS/TOP LOSERS/LARGE-CAP filters and search keep
    working unchanged (just backed by Delta's actual tradable universe).

    If Delta has fewer coins than 250 (expected — Delta only lists what it trades),
    we return whatever is available without padding.

    Returns (coins, errors): coins is a list of
    {symbol, name, price, change_24h_pct, volume, market_cap, chart_symbol}
    dicts, or None on failure so the previous report data is kept.
    On failure returns (None, [error]) so report generation continues.

    chart_symbol is None for now — Delta's perpetuals don't map 1:1 to
    Binance spot pairs. Majors (BTC/ETH etc) already have chart_url via
    report.markets; for the full list we note chart unavailable rather than
    guessing. Next phase could add DELTA:BTCUSD TradingView mapping if needed.
    """
    try:
        data = get_json(
            f"{DELTA_BASE}/tickers",
            params={"contract_types": "perpetual_futures"},
            timeout=30,
        )
    except Exception as exc:
        return None, [f"Delta tickers: {exc}"]

    tickers = data.get("result") or []
    if not isinstance(tickers, list) or not tickers:
        return None, ["Delta tickers: empty response"]

    coins = []
    for item in tickers:
        # Only crypto perpetuals — exclude tradfi stock tokens (AAPL xStock etc)
        if item.get("top_tag") != "crypto":
            continue
        symbol = str(item.get("underlying_asset_symbol") or "").upper()
        if not symbol:
            continue
        # Delta's ticker provides mark_price / close / spot_price; prefer mark_price for perpetuals
        price = to_float(item.get("mark_price") or item.get("close") or item.get("spot_price"))
        if price is None:
            continue
        # 24h % change — Delta provides string like "-1.3925"
        change = to_float(item.get("mark_change_24h") or item.get("ltp_change_24h"))
        # volume in USD — use turnover_usd if available, else volume
        volume = to_float(item.get("turnover_usd") or item.get("volume"))
        # market_cap not available for perpetuals — keep None so LARGE-CAP filter will be empty (expected)
        # name — use description like "Bitcoin Perpetual" or fallback to symbol
        name = item.get("description") or symbol
        # Strip " Perpetual" suffix for cleaner display? Keep as is for now to preserve Delta's naming.
        # Chart — leave None; mdChartSymbol will handle fallback and show "Chart unavailable" if needed.
        # For majors, chart is already available via report.markets; for full list we don't guess.
        coins.append(
            {
                "symbol": symbol,
                "name": name,
                "price": price,
                "change_24h_pct": change,
                "volume": volume,
                "market_cap": None,
                "chart_symbol": None,
            }
        )

    if not coins:
        return None, ["Delta tickers: no crypto perpetuals found"]

    # Sort by volume descending so most traded appear first (similar to market-cap order)
    try:
        coins.sort(key=lambda c: (c.get("volume") or 0), reverse=True)
    except Exception:
        pass

    return coins, []
