import re

from config import (
    CMC_LISTINGS_LATEST_PUBLIC_URL,
    CMC_LISTINGS_LATEST_URL,
    CMC_NEW_URL,
    COINPAPRIKA_COIN_URL,
    COINPAPRIKA_COINS_URL,
    DELTA_BASE,
    LISTINGS_LIMIT,
    MAJOR_SYMBOLS,
    cmc_api_key,
)
from http_util import get_json, to_float

SYMBOL_RE = re.compile(r"^[A-Z0-9]{1,15}$")


def _iso_day(value):
    if not value:
        return None
    return str(value)[:10]


def _listing(name, symbol, added_at, source, url, extra_note=None):
    symbol = str(symbol).upper()
    if extra_note:
        note = extra_note
    elif added_at:
        note = f"Added {added_at} - {source}"
    else:
        note = f"Recently added - {source}"
    return {
        "name": name,
        "symbol": symbol,
        "added_at": added_at,
        "note": note,
        "url": url,
        "source": source,
    }


def fetch_delta_listings():
    errors = []
    items = []
    params = {
        "contract_types": "perpetual_futures",
        "states": "live",
        "page_size": 100,
    }
    try:
        after = None
        for _ in range(4):
            if after:
                params["after"] = after
            payload = get_json(f"{DELTA_BASE}/products", params=params, timeout=25)
            batch = payload.get("result") or []
            items.extend(batch)
            after = (payload.get("meta") or {}).get("after")
            if not after or not batch:
                break
    except Exception as exc:
        return [], [f"Delta India products: {exc}"]

    ranked = []
    for product in items:
        underlying = product.get("underlying_asset") or {}
        symbol = str(underlying.get("symbol") or "").upper()
        name = underlying.get("name") or product.get("description") or symbol
        if symbol in MAJOR_SYMBOLS or not SYMBOL_RE.match(symbol) or not name:
            continue
        ranked.append(
            (
                product.get("launch_time") or "",
                _listing(
                    name,
                    symbol,
                    _iso_day(product.get("launch_time")),
                    "Delta India",
                    f"https://www.delta.exchange/app/futures/trade/{product.get('symbol')}",
                    extra_note=(
                        f"Listed on Delta India - {_iso_day(product.get('launch_time'))}"
                        if product.get("launch_time")
                        else "Listed on Delta India"
                    ),
                ),
            )
        )
    ranked.sort(key=lambda row: row[0], reverse=True)
    unique = []
    seen = set()
    for _, item in ranked:
        if item["symbol"] in seen:
            continue
        seen.add(item["symbol"])
        unique.append(item)
    return unique, errors


def _parse_cmc_listings(payload):
    """Extract listing items from a CMC listings/new or listings/latest response."""
    listings = []
    for item in payload.get("data") or []:
        symbol = str(item.get("symbol") or "").upper()
        name = item.get("name")
        slug = item.get("slug") or symbol.lower()
        if not name or not SYMBOL_RE.match(symbol):
            continue
        listings.append(
            _listing(
                name,
                symbol,
                _iso_day(item.get("date_added")),
                "CoinMarketCap",
                f"https://coinmarketcap.com/currencies/{slug}/",
            )
        )
    return listings


def fetch_cmc_listings():
    """
    Fetch recently-added coins from CoinMarketCap using the best available endpoint:
      1. /v1/cryptocurrency/listings/new  (requires paid API key — Basic plan+)
      2. /v1/cryptocurrency/listings/latest?sort=date_added&sort_dir=desc  (requires any API key)
      3. public-api /v1/cryptocurrency/listings/latest?sort=date_added  (keyless, best-effort)
    """
    key = cmc_api_key()
    errors = []

    # --- Tier 1: /listings/new (paid key required) ---
    if key:
        try:
            payload = get_json(
                CMC_NEW_URL,
                params={"start": 1, "limit": 20, "convert": "USD"},
                extra_headers={"X-CMC_PRO_API_KEY": key},
            )
            listings = _parse_cmc_listings(payload)
            if listings:
                return listings, []
            errors.append("CoinMarketCap /listings/new: empty response, trying fallback")
        except Exception as exc:
            errors.append(f"CoinMarketCap /listings/new: {exc}")

        # --- Tier 2: /listings/latest sorted by date_added (paid key) ---
        try:
            payload = get_json(
                CMC_LISTINGS_LATEST_URL,
                params={"start": 1, "limit": 20, "convert": "USD", "sort": "date_added", "sort_dir": "desc"},
                extra_headers={"X-CMC_PRO_API_KEY": key},
            )
            listings = _parse_cmc_listings(payload)
            if listings:
                return listings, errors
            errors.append("CoinMarketCap /listings/latest (keyed): empty response")
        except Exception as exc:
            errors.append(f"CoinMarketCap /listings/latest (keyed): {exc}")

    # --- Tier 3: public-api keyless (no key needed) ---
    try:
        payload = get_json(
            CMC_LISTINGS_LATEST_PUBLIC_URL,
            params={"start": 1, "limit": 20, "convert": "USD", "sort": "date_added", "sort_dir": "desc"},
        )
        listings = _parse_cmc_listings(payload)
        if listings:
            return listings, errors
        errors.append("CoinMarketCap public /listings/latest: empty response")
    except Exception as exc:
        errors.append(f"CoinMarketCap public /listings/latest: {exc}")

    return [], errors


def fetch_paprika_listings():
    errors = []
    try:
        coins = get_json(COINPAPRIKA_COINS_URL)
    except Exception as exc:
        return [], [f"CoinPaprika list: {exc}"]

    newest = [
        coin
        for coin in coins
        if coin.get("is_new")
        and coin.get("name")
        and coin.get("symbol")
        and SYMBOL_RE.match(str(coin["symbol"]).upper())
    ]

    listings = []
    for coin in newest[:12]:
        added_at = None
        try:
            detail = get_json(COINPAPRIKA_COIN_URL.format(coin_id=coin["id"]), timeout=15)
            added_at = _iso_day(detail.get("first_data_at"))
        except Exception as exc:
            errors.append(f"CoinPaprika {coin['symbol']}: {exc}")
        listings.append(
            _listing(
                coin["name"],
                coin["symbol"],
                added_at,
                "CoinPaprika",
                f"https://coinpaprika.com/coin/{coin['id']}/",
            )
        )
    return listings, errors


def merge_listings(*groups):
    merged = []
    seen = set()
    for group in groups:
        for item in group:
            key = item["symbol"]
            if key in seen or key in MAJOR_SYMBOLS:
                continue
            seen.add(key)
            merged.append(item)
            if len(merged) >= LISTINGS_LIMIT:
                return merged
    return merged


def fetch_listings():
    delta, delta_errors = fetch_delta_listings()
    cmc, cmc_errors = fetch_cmc_listings()
    paprika, paprika_errors = fetch_paprika_listings()
    errors = delta_errors + cmc_errors + paprika_errors
    listings = merge_listings(delta, cmc, paprika)
    if not listings:
        return None, errors or ["no listings from any source"]
    return listings, errors
