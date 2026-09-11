from config import CMC_QUOTES_PUBLIC_URL, CMC_QUOTES_URL, COINS, DELTA_BASE, cmc_api_key
from http_util import get_json, to_float


def _usd_quote(item):
    quote = item.get("quote")
    if isinstance(quote, dict):
        return quote.get("USD") or (next(iter(quote.values())) if quote else None)
    if isinstance(quote, list):
        for row in quote:
            if str(row.get("symbol", "")).upper() == "USD":
                return row
        return quote[0] if quote else None
    return None


def _cmc_rows(payload):
    data = payload.get("data", payload)
    rows = {}
    if isinstance(data, dict):
        items = []
        for value in data.values():
            items.extend(value if isinstance(value, list) else [value])
    elif isinstance(data, list):
        items = data
    else:
        items = []
    for item in items:
        symbol = str(item.get("symbol", "")).upper()
        usd = _usd_quote(item) or item
        price = to_float(usd.get("price"))
        if not symbol or price is None:
            continue
        rows[symbol] = {
            "price": price,
            "change_24h": to_float(usd.get("percent_change_24h")),
            "volume": to_float(usd.get("volume_24h")),
            "market_cap": to_float(usd.get("market_cap")),
            "source": "CoinMarketCap",
        }
    return rows


def fetch_cmc_quotes():
    params = {"symbol": ",".join(coin["symbol"] for coin in COINS), "convert": "USD"}
    key = cmc_api_key()
    try:
        if key:
            payload = get_json(
                CMC_QUOTES_URL,
                params=params,
                extra_headers={"X-CMC_PRO_API_KEY": key},
                timeout=8  # Reduced timeout
            )
        else:
            payload = get_json(CMC_QUOTES_PUBLIC_URL, params=params, timeout=8)  # Reduced timeout
        return _cmc_rows(payload), []
    except Exception as exc:
        return {}, [f"CoinMarketCap quotes: {exc}"]


def fetch_paprika_quotes():
    rows = {}
    errors = []
    for coin in COINS:
        url = f"https://api.coinpaprika.com/v1/tickers/{coin['paprika_id']}"
        try:
            item = get_json(url, timeout=8)  # Reduced timeout
            usd = (item.get("quotes") or {}).get("USD") or {}
            price = to_float(usd.get("price"))
            if price is None:
                raise RuntimeError("missing USD price")
            rows[coin["symbol"]] = {
                "price": price,
                "change_24h": to_float(usd.get("percent_change_24h")),
                "volume": to_float(usd.get("volume_24h")),
                "market_cap": to_float(usd.get("market_cap")),
                "source": "CoinPaprika",
            }
        except Exception as exc:
            errors.append(f"CoinPaprika {coin['symbol']}: {exc}")
    return rows, errors


def fetch_delta_quotes():
    try:
        payload = get_json(
            f"{DELTA_BASE}/tickers",
            params={
                "contract_types": "perpetual_futures",
                "underlying_asset_symbols": ",".join(coin["symbol"] for coin in COINS),
            },
        )
    except Exception as exc:
        return {}, [f"Delta India tickers: {exc}"]

    rows = {}
    for item in payload.get("result") or []:
        symbol = str(item.get("underlying_asset_symbol", "")).upper()
        price = to_float(item.get("spot_price")) or to_float(item.get("mark_price"))
        if symbol in rows or price is None:
            continue
        rows[symbol] = {
            "price": price,
            "change_24h": to_float(item.get("mark_change_24h"))
            or to_float(item.get("ltp_change_24h")),
            "volume": to_float(item.get("turnover_usd")),
            "market_cap": None,
            "source": "Delta India",
            "contract": item.get("symbol"),
        }
    return rows, []


def fetch_markets(fast=False):
    errors = []
    if fast:
        # Skip CMC for live dashboard to improve response time
        cmc, cmc_errors = {}, []
    else:
        cmc, cmc_errors = fetch_cmc_quotes()
    paprika, paprika_errors = fetch_paprika_quotes()
    delta, delta_errors = fetch_delta_quotes()
    errors.extend(cmc_errors + paprika_errors + delta_errors)

    markets = []
    for coin in COINS:
        symbol = coin["symbol"]
        cmc_row = cmc.get(symbol)
        paprika_row = paprika.get(symbol)
        delta_row = delta.get(symbol)
        primary = cmc_row or paprika_row or delta_row
        if not primary:
            errors.append(f"{symbol}: no market data from any source")
            continue
        sources = [
            name
            for name, row in (
                ("CoinMarketCap", cmc_row),
                ("CoinPaprika", paprika_row),
                ("Delta India", delta_row),
            )
            if row
        ]
        row = {
            "symbol": symbol,
            "name": coin["name"],
            "price": primary["price"],
            "change_24h": primary["change_24h"] if primary["change_24h"] is not None else 0,
            "volume": primary.get("volume") or 0,
            "market_cap": primary.get("market_cap") or 0,
            "source": primary["source"],
            "sources": sources,
            "chart_url": f"https://www.tradingview.com/chart/?symbol={coin['tv']}",
        }
        if delta_row:
            row["india"] = {
                "venue": "Delta India",
                "contract": delta_row.get("contract"),
                "spot_price": delta_row["price"],
                "change_24h": delta_row["change_24h"],
                "volume": delta_row.get("volume"),
            }
        markets.append(row)

    if not markets:
        return None, errors or ["all market sources failed"]
    return markets, errors
