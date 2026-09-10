import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

REPORT_PATH = ROOT / "data" / "latest-report.json"
FRONTEND_REPORT_PATH = ROOT / "frontend" / "data" / "latest-report.json"

COINS = (
    {"symbol": "BTC", "name": "Bitcoin", "paprika_id": "btc-bitcoin", "tv": "BTCUSD"},
    {"symbol": "ETH", "name": "Ethereum", "paprika_id": "eth-ethereum", "tv": "ETHUSD"},
    {"symbol": "SOL", "name": "Solana", "paprika_id": "sol-solana", "tv": "SOLUSD"},
)
MAJOR_SYMBOLS = {coin["symbol"] for coin in COINS}

NEWS_LIMIT = 12
NEWS_FEEDS = (
    {"source": "CoinDesk", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
    {"source": "Cointelegraph", "url": "https://cointelegraph.com/rss"},
    {"source": "Decrypt", "url": "https://decrypt.co/feed"},
)

DELTA_BASE = "https://api.india.delta.exchange/v2"
COINPAPRIKA_COINS_URL = "https://api.coinpaprika.com/v1/coins"
COINPAPRIKA_COIN_URL = "https://api.coinpaprika.com/v1/coins/{coin_id}"
COINPAPRIKA_TICKER_URL = "https://api.coinpaprika.com/v1/tickers/{coin_id}"
CMC_QUOTES_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
CMC_QUOTES_PUBLIC_URL = "https://pro-api.coinmarketcap.com/public-api/v1/cryptocurrency/quotes/latest"
CMC_NEW_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/new"
CMC_LISTINGS_LATEST_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
CMC_LISTINGS_LATEST_PUBLIC_URL = "https://pro-api.coinmarketcap.com/public-api/v1/cryptocurrency/listings/latest"

LISTINGS_LIMIT = 12


def cmc_api_key():
    return os.getenv("CMC_API_KEY", "").strip()
