import re
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

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

# Cache for Delta data to avoid duplicate API calls
_delta_products_cache = None
_delta_tickers_cache = None
_delta_cache_time = None
CACHE_DURATION = 300  # 5 minutes cache


def _get_delta_data():
    """
    Fetch Delta Exchange data with caching to avoid duplicate API calls.
    Returns (products, tickers, errors) tuple.
    """
    global _delta_products_cache, _delta_tickers_cache, _delta_cache_time
    
    current_time = datetime.now(timezone.utc)
    
    # Return cached data if still valid
    if (_delta_cache_time and 
        (current_time - _delta_cache_time).total_seconds() < CACHE_DURATION and
        _delta_products_cache is not None and
        _delta_tickers_cache is not None):
        return _delta_products_cache, _delta_tickers_cache, []
    
    errors = []
    items = []
    tickers = {}
    
    # Fetch products with reduced pagination (1 iteration instead of 2)
    params = {
        "contract_types": "perpetual_futures",
        "states": "live",
        "page_size": 50,  # Reduced page size
    }
    
    try:
        payload = get_json(f"{DELTA_BASE}/products", params=params, timeout=8)  # Further reduced timeout
        items = payload.get("result") or []
    except Exception as exc:
        errors.append(f"Delta India products: {exc}")
    
    # Fetch tickers with reduced timeout
    try:
        ticker_params = {
            "contract_types": "perpetual_futures",
        }
        ticker_payload = get_json(f"{DELTA_BASE}/tickers", params=ticker_params, timeout=8)  # Further reduced timeout
        tickers = {t.get("symbol"): t for t in ticker_payload.get("result") or []}
    except Exception as exc:
        errors.append(f"Delta India tickers: {exc}")
    
    # Update cache
    _delta_products_cache = items
    _delta_tickers_cache = tickers
    _delta_cache_time = current_time
    
    return items, tickers, errors


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
    """
    Fetch Delta Exchange India listings, filtering to only products created in the last 7 days.
    Uses Delta's actual created_at timestamp for dynamic filtering.
    Uses cached data to avoid duplicate API calls.
    """
    errors = []
    
    # Calculate 7-day window from current time (UTC)
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    
    # Use cached Delta data
    items, _, delta_errors = _get_delta_data()
    errors.extend(delta_errors)

    ranked = []
    for product in items:
        underlying = product.get("underlying_asset") or {}
        symbol = str(underlying.get("symbol") or "").upper()
        name = underlying.get("name") or product.get("description") or symbol
        
        # Skip major symbols and invalid symbols
        if symbol in MAJOR_SYMBOLS or not SYMBOL_RE.match(symbol) or not name:
            continue
        
        # Use created_at timestamp for 7-day filtering
        created_at = product.get("created_at")
        if created_at:
            try:
                # Parse ISO timestamp and convert to UTC
                created_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                if created_time.tzinfo is None:
                    created_time = created_time.replace(tzinfo=timezone.utc)
                else:
                    created_time = created_time.astimezone(timezone.utc)
                
                # Only include products from the last 7 days
                if created_time < seven_days_ago:
                    continue
            except (ValueError, TypeError):
                # If we can't parse the timestamp, skip this product
                continue
        
        ranked.append(
            (
                created_at or product.get("launch_time") or "",
                _listing(
                    name,
                    symbol,
                    _iso_day(created_at or product.get("launch_time")),
                    "Delta India",
                    f"https://www.delta.exchange/app/futures/trade/{product.get('symbol')}",
                    extra_note=(
                        f"Listed on Delta India - {_iso_day(created_at or product.get('launch_time'))}"
                        if (created_at or product.get("launch_time"))
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
                timeout=10  # Reduced timeout
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
                timeout=10  # Reduced timeout
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
            timeout=10  # Reduced timeout
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
        coins = get_json(COINPAPRIKA_COINS_URL, timeout=10)  # Reduced timeout
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
    for coin in newest[:8]:  # Reduced from 12 to 8 for performance
        added_at = None
        try:
            detail = get_json(COINPAPRIKA_COIN_URL.format(coin_id=coin["id"]), timeout=8)  # Reduced timeout
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


def fetch_trending_coins():
    """
    Fetch trending coins from Delta Exchange India based on market activity.
    Trending score is calculated using:
    - 24h price change (volatility)
    - Trading volume (liquidity)
    - Normalized combination of both factors
    
    Uses cached Delta data to avoid duplicate API calls.
    
    Returns a ranked list of trending coins with their metrics.
    """
    errors = []
    
    try:
        # Use cached Delta data
        items, tickers, delta_errors = _get_delta_data()
        errors.extend(delta_errors)
        
        trending = []
        for product in items:
            product_symbol = product.get("symbol")
            if not product_symbol:
                continue
                
            underlying = product.get("underlying_asset") or {}
            symbol = str(underlying.get("symbol") or "").upper()
            name = underlying.get("name") or product.get("description") or symbol
            
            # Skip major symbols and invalid symbols
            if symbol in MAJOR_SYMBOLS or not SYMBOL_RE.match(symbol) or not name:
                continue
            
            # Get ticker data for this product
            ticker = tickers.get(product_symbol)
            if not ticker:
                continue
            
            # Extract metrics
            price = to_float(ticker.get("spot_price")) or to_float(ticker.get("mark_price"))
            change_24h = to_float(ticker.get("mark_change_24h")) or to_float(ticker.get("ltp_change_24h")) or 0
            volume = to_float(ticker.get("turnover_usd")) or 0
            
            if price is None or volume == 0:
                continue
            
            # Calculate trending score
            # Score combines absolute price change (volatility) and volume (liquidity)
            # Higher volume with significant price changes = more trending
            change_score = abs(change_24h)  # Absolute 24h change
            volume_score = min(volume / 1_000_000, 10)  # Normalize volume (cap at 10M for score)
            trending_score = (change_score * 2) + volume_score  # Weight change more heavily
            
            trending.append({
                "symbol": symbol,
                "name": name,
                "price": price,
                "change_24h": change_24h,
                "volume": volume,
                "trending_score": round(trending_score, 2),
                "contract": product_symbol,
                "url": f"https://www.delta.exchange/app/futures/trade/{product_symbol}",
                "source": "Delta India"
            })
        
        # Sort by trending score (descending) and take top 8
        trending.sort(key=lambda x: x["trending_score"], reverse=True)
        return trending[:8], []
        
    except Exception as exc:
        return [], [f"Delta trending coins: {exc}"]


def fetch_listings(fast=False):
    delta, delta_errors = fetch_delta_listings()
    if fast:
        # Skip CMC and CoinPaprika for live dashboard to improve performance
        cmc, cmc_errors = [], []
        paprika, paprika_errors = [], []
    else:
        cmc, cmc_errors = fetch_cmc_listings()
        paprika, paprika_errors = fetch_paprika_listings()
    errors = delta_errors + cmc_errors + paprika_errors
    listings = merge_listings(delta, cmc, paprika)
    if not listings:
        return None, errors or ["no listings from any source"]
    return listings, errors
