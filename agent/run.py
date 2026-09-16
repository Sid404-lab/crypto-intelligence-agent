import os
from fetch_crypto_full import fetch_crypto_full
from fetch_listings import fetch_listings, fetch_trending_coins
from fetch_market import fetch_markets
from fetch_metals import fetch_commodities_forex, fetch_metals
from fetch_news import fetch_news
from groq_briefing import generate_ai_briefing
from new_trending import generate_new_trending
from send_telegram import send_telegram_briefing
from setup_alerts import check_and_alert
from setup_engine import scan_all_setups
from write_report import write_report


def _safe(text):
    return str(text).encode("ascii", "replace").decode("ascii")


def main():
    if not os.getenv("GROQ_API_KEY", "").strip():
        print(
            "Warning: GROQ_API_KEY is not set. "
            "The pipeline will continue, but the AI briefing will be unavailable."
        )

    markets, market_errors = fetch_markets()
    news, news_errors = fetch_news()
    listings, listing_errors = fetch_listings()
    trending, trending_errors = fetch_trending_coins()
    metals, metals_errors = fetch_metals()
    commodities_forex, commodities_forex_errors = fetch_commodities_forex()
    crypto_full, crypto_full_errors = fetch_crypto_full()
    ai_briefing = generate_ai_briefing(markets, news, listings)
    setups = scan_all_setups()
    new_trending, new_trending_errors = generate_new_trending(trending, listings)

    # Determine top setup: first with direction != NO_TRADE and score >= 60
    top_setup = None
    for s in setups:
        if s.get("direction") != "NO_TRADE" and s.get("score", 0) >= 60:
            top_setup = s
            break

    errors = {
        "markets": market_errors,
        "news": news_errors,
        "listings": listing_errors,
        "trending": trending_errors,
        "metals": metals_errors,
        "commodities_forex": commodities_forex_errors,
        "crypto_full": crypto_full_errors,
        "new_trending": new_trending_errors,
    }
    path = write_report(
        markets,
        news=news,
        listings=listings,
        trending=trending,
        metals=metals,
        commodities_forex=commodities_forex,
        crypto_full=crypto_full,
        ai_briefing=ai_briefing,
        setups=setups,
        top_setup=top_setup,
        new_trending=new_trending,
        errors=errors,
    )
    print(f"Wrote {path}")
    send_telegram_briefing(ai_briefing)
    # --- Setup alerts: only crypto, deduped, logged ---
    try:
        check_and_alert(setups, new_trending)
    except Exception as e:
        print(f"Setup alert error: {e}")
    if markets is None:
        print("Markets: kept previous items (all sources failed)")
    else:
        for market in markets:
            print(
                f"{market['symbol']}: {market['price']} "
                f"({market['change_24h']:+.2f}%) "
                f"[{market.get('source')}]"
            )
    for error in market_errors:
        print(f"Market warning: {_safe(error)}")
    if news is None:
        print("News: kept previous items (all feeds failed)")
    else:
        print(f"News items: {len(news)}")
    for error in news_errors:
        print(f"News warning: {_safe(error)}")
    if listings is None:
        print("Listings: kept previous items (all sources failed)")
    else:
        print(f"Listings: {len(listings)}")
        for item in listings:
            print(_safe(f"  {item['symbol']} {item['name']} ({item['note']})"))
    for error in listing_errors:
        print(f"Listings warning: {_safe(error)}")
    if trending is None:
        print("Trending: kept previous items (all sources failed)")
    else:
        print(f"Trending: {len(trending)}")
    for error in trending_errors:
        print(f"Trending warning: {_safe(error)}")
    if metals is None:
        print("Metals: kept previous items (all sources failed)")
    else:
        print(f"Metals: {len(metals)}")
        for metal in metals:
            print(
                f"{metal['symbol']}: {metal['price']} "
                f"({metal['change_24h']:+.2f}%) "
                f"[{metal.get('source')}]"
            )
    for error in metals_errors:
        print(f"Metals warning: {_safe(error)}")
    if commodities_forex is None:
        print("Commodities/Forex: kept previous items (all sources failed)")
    else:
        print(f"Commodities/Forex: {len(commodities_forex)}")
        for item in commodities_forex:
            print(
                f"{item['symbol']}: {item['price']} "
                f"({item['change_pct']:+.2f}%) "
                f"[{item.get('source')}]"
            )
    for error in commodities_forex_errors:
        print(f"Commodities/Forex warning: {_safe(error)}")
    if not crypto_full:
        print("Crypto full: kept previous items (fetch failed)")
    else:
        print(f"Crypto full: {len(crypto_full)}")
        for coin in crypto_full[:5]:
            print(_safe(f"  {coin['symbol']} {coin['name']}: {coin['price']}"))
        if len(crypto_full) > 5:
            print(f"  ... and {len(crypto_full) - 5} more")
    for error in crypto_full_errors:
        print(f"Crypto full warning: {_safe(error)}")
    if not new_trending:
        print("New & Trending: none (no candidates or fetch failed)")
    else:
        print(f"New & Trending: {len(new_trending)}")
        for coin in new_trending[:5]:
            print(_safe(f"  {coin['symbol']} {coin['badge']} {coin['momentum_direction']} ({coin['why']}) mom {coin['momentum_pct']}% vol x{coin['volume_spike']}"))
        if len(new_trending) > 5:
            print(f"  ... and {len(new_trending) - 5} more")
    for error in new_trending_errors:
        print(f"New & Trending warning: {_safe(error)}")
    print("\n=== SETUP SCAN RESULTS ===")
    for setup in setups:
        print(f"{setup['symbol']}: {setup['direction']} (score {setup['score']})")


if __name__ == "__main__":
    main()
