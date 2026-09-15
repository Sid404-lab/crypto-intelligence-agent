"""
New & Trending — lightweight momentum signals for coins that don't have
enough history for the full ATR/ADX/RSI/MACD strategy (20-50+ candles).

Reuses:
- Trending detection: Delta's ticker data (already fetched in fetch_trending_coins)
  → high volume or largest % moves
- New listing detection: day-over-day comparison already used for New Prints
  → fetch_delta_listings (products created in last 7 days)

For each candidate we fetch a short history (15m or 1h, 20 candles) and compute
only: 5-10 candle % change, volume spike vs recent avg, price vs EMA9.
No R:R targets — not enough data for reliable stops.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed

from http_util import to_float
from indicators import ema
from fetch_candles import fetch_candles


def _momentum_direction(closes):
    """Return LONG/SHORT/NEUTRAL based on price vs EMA9 and recent momentum."""
    if len(closes) < 10:
        return "NEUTRAL"
    e9 = ema(closes, 9)
    # ema returns list same length, with None for early values
    last_ema = e9[-1] if e9 and e9[-1] is not None else None
    if last_ema is None:
        return "NEUTRAL"
    price = closes[-1]
    # 5-candle momentum
    if len(closes) >= 6:
        mom5 = ((closes[-1] - closes[-6]) / closes[-6] * 100) if closes[-6] != 0 else 0
    else:
        mom5 = 0
    # Decide direction: price above EMA9 + positive momentum => LONG, opposite => SHORT
    if price > last_ema and mom5 > 1:
        return "LONG"
    if price < last_ema and mom5 < -1:
        return "SHORT"
    # Weaker signals
    if price > last_ema:
        return "LONG"
    if price < last_ema:
        return "SHORT"
    return "NEUTRAL"


def _strength_label(mom_pct, vol_spike):
    """Simple strength based on momentum % and volume spike."""
    abs_mom = abs(mom_pct) if mom_pct is not None else 0
    spike = vol_spike if vol_spike is not None else 1
    # Strong: large momentum (>5%) and volume spike (>1.5x)
    if abs_mom >= 5 and spike >= 1.5:
        return "Strong"
    if abs_mom >= 3 and spike >= 1.2:
        return "Moderate"
    if abs_mom >= 1.5:
        return "Weak"
    return "Early Signal"


def _compute_lightweight(candles):
    """Compute 5-candle momentum, volume spike, EMA9 relation."""
    if not candles or len(candles) < 5:
        return None
    closes = [c["close"] for c in candles]
    volumes = [c["volume"] for c in candles]
    # 5-candle % change (or available)
    if len(closes) >= 6:
        mom5 = ((closes[-1] - closes[-6]) / closes[-6] * 100) if closes[-6] != 0 else 0
    else:
        mom5 = ((closes[-1] - closes[0]) / closes[0] * 100) if closes[0] != 0 else 0
    # Volume spike vs recent average (last 10 avg)
    if len(volumes) >= 10:
        avg_vol = sum(volumes[-11:-1]) / 10 if sum(volumes[-11:-1]) != 0 else None
        vol_spike = (volumes[-1] / avg_vol) if avg_vol and avg_vol != 0 else 1
    elif len(volumes) >= 2:
        avg_vol = sum(volumes[:-1]) / (len(volumes)-1) if sum(volumes[:-1]) != 0 else None
        vol_spike = (volumes[-1] / avg_vol) if avg_vol else 1
    else:
        vol_spike = 1
    # EMA9
    direction = _momentum_direction(closes)
    strength = _strength_label(mom5, vol_spike)
    return {
        "momentum_pct": round(mom5, 2),
        "volume_spike": round(vol_spike, 2),
        "direction": direction,
        "strength": strength,
    }


def generate_new_trending(trending, listings, max_items=12):
    """
    Generate New & Trending signals.

    Args:
        trending: list from fetch_trending_coins (already has symbol, name, price, change_24h, volume, trending_score)
        listings: list from fetch_delta_listings (new in last 7 days, has symbol, name)
        max_items: max number to return

    Returns:
        (new_trending_list, errors)

    Each item: {
        symbol, name, price, change_24h, volume,
        why, momentum_direction, strength, momentum_pct, volume_spike,
        badge: "Momentum" or "Early Signal",
        note: "Less data available — early signal" etc.
    }
    """
    errors = []
    # Build lookup for listings (new)
    new_symbols = {item["symbol"].upper(): item for item in (listings or [])}
    # Build lookup for trending
    trending_by_symbol = {t["symbol"].upper(): t for t in (trending or [])}

    # Union candidates: all trending + all new listings (deduplicated)
    candidates = {}
    for t in trending or []:
        sym = t["symbol"].upper()
        candidates[sym] = {"source": "trending", "data": t}
    for item in listings or []:
        sym = item["symbol"].upper()
        # If already in trending, mark as both
        if sym in candidates:
            candidates[sym]["source"] = "both"
            candidates[sym]["listing"] = item
        else:
            candidates[sym] = {"source": "new", "data": item, "listing": item}

    # Prefetch candles for all candidates concurrently (speed)
    # Build contract map first
    contract_map = {}
    for symbol, info in candidates.items():
        trending_entry = trending_by_symbol.get(symbol)
        contract = None
        if trending_entry and trending_entry.get("contract"):
            contract = trending_entry["contract"]
        elif info.get("listing") and info["listing"].get("url"):
            url = info["listing"]["url"]
            try:
                contract = url.rstrip("/").split("/")[-1]
            except:
                contract = f"{symbol}USD"
        else:
            contract = f"{symbol}USD"
        contract_map[symbol] = contract

    def _fetch_for(sym):
        contract = contract_map[sym]
        for res in ["15m", "1h"]:
            c, err = fetch_candles(contract, res, count=15)
            if c and len(c) >= 5:
                return c, contract
        if contract != f"{sym}USD":
            c, err = fetch_candles(f"{sym}USD", "15m", count=15)
            if c and len(c) >= 5:
                return c, f"{sym}USD"
        return [], contract

    candles_map = {}
    contract_final_map = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_sym = {executor.submit(_fetch_for, sym): sym for sym in candidates}
        for future in as_completed(future_to_sym):
            sym = future_to_sym[future]
            try:
                c, final_contract = future.result()
                candles_map[sym] = c
                contract_final_map[sym] = final_contract
            except:
                candles_map[sym] = []
                contract_final_map[sym] = contract_map[sym]

    # For each candidate, determine why flagged and compute lightweight signals
    results = []
    for symbol, info in candidates.items():
        source = info["source"]
        base = info["data"]
        why_parts = []
        is_new = symbol in new_symbols
        is_trending = symbol in trending_by_symbol
        trending_entry = trending_by_symbol.get(symbol)
        if is_new:
            why_parts.append("New listing")
        if is_trending and trending_entry:
            chg = abs(trending_entry.get("change_24h") or 0)
            vol = trending_entry.get("volume") or 0
            if chg >= 5:
                why_parts.append(f"Big mover ({'+' if trending_entry['change_24h']>0 else ''}{trending_entry['change_24h']:.1f}%)")
            elif vol and vol > 5_000_000:
                why_parts.append("High volume")
            else:
                why_parts.append("Trending")
        if not why_parts:
            why_parts.append("Trending")
        why = " + ".join(why_parts)
        contract = contract_final_map.get(symbol, contract_map.get(symbol, f"{symbol}USD"))
        candles = candles_map.get(symbol, [])

        lightweight = _compute_lightweight(candles) if candles else None
        if not lightweight:
            # Not enough data — still flag as early signal with neutral
            lightweight = {
                "momentum_pct": 0,
                "volume_spike": 1,
                "direction": "NEUTRAL",
                "strength": "Early Signal",
            }
            # Add note about insufficient data
            note = "Less data available — early signal ( < 5 candles )"
        else:
            note = "Less data available — momentum only (no ATR/ADX/RSI/MACD)"
            # If strength is Early Signal, keep that, otherwise use Momentum badge
            # The strength already reflects that

        # Determine badge: Momentum vs Early Signal
        badge = "Early Signal" if lightweight["strength"] == "Early Signal" else "Momentum"

        # Price, change, volume — prefer trending data if available, else try to get from candles last close
        price = None
        change_24h = None
        volume = None
        name = base.get("name") or symbol
        if trending_entry:
            price = trending_entry.get("price")
            change_24h = trending_entry.get("change_24h")
            volume = trending_entry.get("volume")
        # Fallback to candles last close if trending missing
        if price is None and candles:
            price = candles[-1]["close"]
        if change_24h is None and lightweight:
            change_24h = lightweight["momentum_pct"]

        # If still no price, skip? But we should still include with note
        results.append({
            "symbol": symbol,
            "name": name,
            "price": price,
            "change_24h": change_24h,
            "volume": volume,
            "contract": contract,
            "why": why,
            "momentum_direction": lightweight["direction"],
            "strength": lightweight["strength"],
            "momentum_pct": lightweight["momentum_pct"],
            "volume_spike": lightweight["volume_spike"],
            "badge": badge,
            "note": note,
            "url": trending_entry.get("url") if trending_entry and trending_entry.get("url") else f"https://www.delta.exchange/app/futures/trade/{contract}",
            "source": "Delta India",
        })

    # Sort: balance new and trending — don't overly prioritize new listings
    # Use a combined score: trending_score (if any) + momentum strength + volume
    # This ensures both new listings and big movers appear
    trending_score_map = {t["symbol"].upper(): t.get("trending_score", 0) for t in (trending or [])}
    def sort_key(x):
        # Base score from trending (if trending) or from momentum
        t_score = trending_score_map.get(x["symbol"], 0) or 0
        # Strength order: Strong > Moderate > Weak > Early Signal
        strength_order = {"Strong": 3, "Moderate": 2, "Weak": 1, "Early Signal": 0}
        strength_val = strength_order.get(x["strength"], 0)
        # Combine: trending_score weighted, plus momentum, plus small bonus for new (to ensure new appear but not dominate)
        mom = abs(x.get("momentum_pct") or 0)
        vol = x.get("volume") or 0
        is_new_bonus = 2 if "New listing" in x["why"] else 0
        return (t_score * 0.3 + mom * 1.5 + strength_val * 2 + is_new_bonus, vol)

    results.sort(key=sort_key, reverse=True)
    # Ensure at least 3 new listings and 3 trending in final list if available
    # If we have many new, ensure we keep some trending-only
    # Simple: take top max_items after balanced sort (already balanced)
    return results[:max_items], errors
