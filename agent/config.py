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
    {"symbol": "BNB", "name": "BNB", "paprika_id": "bnb-binance-coin", "tv": "BNBUSD"},
    {"symbol": "XRP", "name": "XRP", "paprika_id": "xrp-xrp", "tv": "XRPUSD"},
    {"symbol": "DOGE", "name": "Dogecoin", "paprika_id": "doge-dogecoin", "tv": "DOGEUSD"},
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
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3/"
COINGECKO_MARKETS_URL = COINGECKO_BASE_URL + "coins/markets"
COINGECKO_TRENDING_URL = COINGECKO_BASE_URL + "search/trending"

LISTINGS_LIMIT = 12


def coingecko_api_key():
    return os.getenv("COINGECKO_API_KEY", "").strip()
