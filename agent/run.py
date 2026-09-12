import os

from fetch_listings import fetch_listings
from fetch_market import fetch_markets
from fetch_news import fetch_news
from groq_briefing import generate_ai_briefing
from send_telegram import send_telegram_briefing
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
    ai_briefing = generate_ai_briefing(markets, news, listings)
    errors = {
        "markets": market_errors,
        "news": news_errors,
        "listings": listing_errors,
    }
    path = write_report(
        markets,
        news=news,
        listings=listings,
        ai_briefing=ai_briefing,
        errors=errors,
    )
    print(f"Wrote {path}")
    send_telegram_briefing(ai_briefing)
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


if __name__ == "__main__":
    main()
