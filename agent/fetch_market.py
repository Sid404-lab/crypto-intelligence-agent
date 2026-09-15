from config import COINGECKO_MARKETS_URL, COINS, DELTA_BASE, MAJOR_SYMBOLS, coingecko_api_key
from http_util import get_json, to_float


def _coingecko_rows(payload):
    rows = {}
    for item in payload:
        symbol = str(item.get("symbol") or "").upper()
        price = to_float(item.get("current_price"))
        if not symbol or price is None:
            continue
        rows[symbol] = {
            "price": price,
            "change_24h": to_float(item.get("price_change_percentage_24h")),
            "volume": to_float(item.get("total_volume")),
            "market_cap": to_float(item.get("market_cap")),
            "source": "CoinGecko",
        }
    return rows


def fetch_coingecko_quotes():
    key = coingecko_api_key()
    headers = {"x-cg-demo-api-key": key} if key else {}
    try:
        payload = get_json(
            COINGECKO_MARKETS_URL,
            params={"vs_currency": "usd", "order": "market_cap_desc", "per_page": 200, "page": 1},
            extra_headers=headers or None,
            timeout=8,
        )
        return _coingecko_rows(payload), []
    except Exception as exc:
        return {}, [f"CoinGecko quotes: {exc}"]


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
        cmc, cmc_errors = {}, []
    else:
        cmc, cmc_errors = fetch_coingecko_quotes()
    paprika, paprika_errors = fetch_paprika_quotes()
    delta, delta_errors = fetch_delta_quotes()
    errors.extend(cmc_errors + paprika_errors + delta_errors)

    markets = []
    for coin in COINS:
        symbol = coin["symbol"]
        cmc_row = cmc.get(symbol)
        paprika_row = paprika.get(symbol)
        delta_row = delta.get(symbol)
        # Prioritize Delta India for crypto majors (per task: crypto only → Delta, metals/forex stay on Yahoo)
        # If Delta has no market for this coin, note as limitation and fall back to other sources (next phase will replace full list)
        if not delta_row and symbol in MAJOR_SYMBOLS:
            # Limitation: Delta India has no perpetual for this coin — will be handled in next phase
            errors.append(f"{symbol}: no Delta India market (limitation — using fallback)")
        primary = delta_row or cmc_row or paprika_row
        if not primary:
            errors.append(f"{symbol}: no market data from any source")
            continue
        sources = [
            name
            for name, row in (
                ("Delta India", delta_row),
                ("CoinGecko", cmc_row),
                ("CoinPaprika", paprika_row),
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
