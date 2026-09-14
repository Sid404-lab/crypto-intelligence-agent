import requests
from http_util import to_float

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; pulse-crypto-intelligence/1.0)"}

METALS = (
    {"ticker": "GC=F", "symbol": "XAU", "name": "Gold", "tv": "OANDA:XAUUSD"},
    {"ticker": "SI=F", "symbol": "XAG", "name": "Silver", "tv": "TVC:SILVER"},
)

COMMODITIES_FOREX = (
    # Commodities (Yahoo futures)
    {"ticker": "CL=F", "symbol": "WTI", "name": "WTI Crude Oil", "group": "commodities"},
    {"ticker": "BZ=F", "symbol": "BRENT", "name": "Brent Crude", "group": "commodities"},
    {"ticker": "NG=F", "symbol": "NATGAS", "name": "Natural Gas", "group": "commodities"},
    {"ticker": "HG=F", "symbol": "COPPER", "name": "Copper", "group": "commodities"},
    {"ticker": "PL=F", "symbol": "PLAT", "name": "Platinum", "group": "commodities"},
    # Forex (Yahoo FX)
    {"ticker": "EURUSD=X", "symbol": "EURUSD", "name": "Euro / US Dollar", "group": "forex"},
    {"ticker": "GBPUSD=X", "symbol": "GBPUSD", "name": "British Pound / US Dollar", "group": "forex"},
    {"ticker": "USDJPY=X", "symbol": "USDJPY", "name": "US Dollar / Japanese Yen", "group": "forex"},
    {"ticker": "USDINR=X", "symbol": "USDINR", "name": "US Dollar / Indian Rupee", "group": "forex"},
    {"ticker": "AUDUSD=X", "symbol": "AUDUSD", "name": "Australian Dollar / US Dollar", "group": "forex"},
    {"ticker": "USDCNY=X", "symbol": "USDCNY", "name": "US Dollar / Chinese Yuan", "group": "forex"},
    {"ticker": "USDCHF=X", "symbol": "USDCHF", "name": "US Dollar / Swiss Franc", "group": "forex"},
    {"ticker": "USDCAD=X", "symbol": "USDCAD", "name": "US Dollar / Canadian Dollar", "group": "forex"},
    {"ticker": "NZDUSD=X", "symbol": "NZDUSD", "name": "New Zealand Dollar / US Dollar", "group": "forex"},
    {"ticker": "EURGBP=X", "symbol": "EURGBP", "name": "Euro / British Pound", "group": "forex"},
    {"ticker": "EURJPY=X", "symbol": "EURJPY", "name": "Euro / Japanese Yen", "group": "forex"},
    {"ticker": "EURCHF=X", "symbol": "EURCHF", "name": "Euro / Swiss Franc", "group": "forex"},
    {"ticker": "EURCAD=X", "symbol": "EURCAD", "name": "Euro / Canadian Dollar", "group": "forex"},
    {"ticker": "EURAUD=X", "symbol": "EURAUD", "name": "Euro / Australian Dollar", "group": "forex"},
    {"ticker": "EURNZD=X", "symbol": "EURNZD", "name": "Euro / New Zealand Dollar", "group": "forex"},
    {"ticker": "GBPJPY=X", "symbol": "GBPJPY", "name": "British Pound / Japanese Yen", "group": "forex"},
    {"ticker": "GBPCHF=X", "symbol": "GBPCHF", "name": "British Pound / Swiss Franc", "group": "forex"},
    {"ticker": "GBPCAD=X", "symbol": "GBPCAD", "name": "British Pound / Canadian Dollar", "group": "forex"},
    {"ticker": "GBPAUD=X", "symbol": "GBPAUD", "name": "British Pound / Australian Dollar", "group": "forex"},
    {"ticker": "GBPNZD=X", "symbol": "GBPNZD", "name": "British Pound / New Zealand Dollar", "group": "forex"},
    {"ticker": "AUDJPY=X", "symbol": "AUDJPY", "name": "Australian Dollar / Japanese Yen", "group": "forex"},
    {"ticker": "AUDCHF=X", "symbol": "AUDCHF", "name": "Australian Dollar / Swiss Franc", "group": "forex"},
    {"ticker": "AUDCAD=X", "symbol": "AUDCAD", "name": "Australian Dollar / Canadian Dollar", "group": "forex"},
    {"ticker": "AUDNZD=X", "symbol": "AUDNZD", "name": "Australian Dollar / New Zealand Dollar", "group": "forex"},
    {"ticker": "CADJPY=X", "symbol": "CADJPY", "name": "Canadian Dollar / Japanese Yen", "group": "forex"},
    {"ticker": "CADCHF=X", "symbol": "CADCHF", "name": "Canadian Dollar / Swiss Franc", "group": "forex"},
    {"ticker": "NZDJPY=X", "symbol": "NZDJPY", "name": "New Zealand Dollar / Japanese Yen", "group": "forex"},
    {"ticker": "CHFJPY=X", "symbol": "CHFJPY", "name": "Swiss Franc / Japanese Yen", "group": "forex"},
    {"ticker": "USDSGD=X", "symbol": "USDSGD", "name": "US Dollar / Singapore Dollar", "group": "forex"},
    {"ticker": "USDHKD=X", "symbol": "USDHKD", "name": "US Dollar / Hong Kong Dollar", "group": "forex"},
    {"ticker": "USDMXN=X", "symbol": "USDMXN", "name": "US Dollar / Mexican Peso", "group": "forex"},
    {"ticker": "USDZAR=X", "symbol": "USDZAR", "name": "US Dollar / South African Rand", "group": "forex"},
    {"ticker": "USDTRY=X", "symbol": "USDTRY", "name": "US Dollar / Turkish Lira", "group": "forex"},
)


def _fetch_yahoo(ticker):
    """
    Fetch current price + 24h change % from Yahoo Finance chart meta.
    Returns (price, change_pct) or (None, None) on empty response.
    """
    response = requests.get(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
        headers=HEADERS,
        timeout=10,
    )
    response.raise_for_status()
    result = response.json().get("chart", {}).get("result", [])
    if not result:
        return None, None
    meta = result[0].get("meta", {})
    price = to_float(meta.get("regularMarketPrice"))
    prev_close = to_float(meta.get("previousClose"))
    if price is None:
        return None, None
    if prev_close:
        change_pct = ((price - prev_close) / prev_close) * 100
    else:
        change_pct = 0
    return price, change_pct


def fetch_metals():
    """
    Fetch gold and silver prices from Yahoo Finance public chart endpoint.
    Returns a list of dicts shaped like the existing markets list.
    """
    errors = []
    metals = []

    for item in METALS:
        try:
            price, change_24h = _fetch_yahoo(item["ticker"])
            if price is None:
                errors.append(f"Yahoo Finance {item['name'].lower()}: empty response")
                continue
            metals.append(
                {
                    "symbol": item["symbol"],
                    "name": item["name"],
                    "price": price,
                    "change_24h": change_24h,
                    "volume": 0,
                    "market_cap": 0,
                    "source": "Yahoo Finance",
                    "chart_url": f"https://www.tradingview.com/chart/?symbol={item['tv']}",
                }
            )
        except Exception as exc:
            errors.append(f"Yahoo Finance {item['name'].lower()}: {exc}")

    if not metals:
        return None, errors or ["all metals sources failed"]
    return metals, errors


def fetch_commodities_forex():
    """
    Fetch commodities + forex quotes from Yahoo Finance public chart endpoint.
    Returns a list of {symbol, name, price, change_pct, group} dicts,
    group is "commodities" or "forex".
    """
    errors = []
    items = []

    for item in COMMODITIES_FOREX:
        try:
            price, change_pct = _fetch_yahoo(item["ticker"])
            if price is None:
                errors.append(f"Yahoo Finance {item['ticker']}: empty response")
                continue
            items.append(
                {
                    "symbol": item["symbol"],
                    "name": item["name"],
                    "price": price,
                    "change_pct": change_pct,
                    "group": item["group"],
                    "source": "Yahoo Finance",
                }
            )
        except Exception as exc:
            errors.append(f"Yahoo Finance {item['ticker']}: {exc}")

    if not items:
        return None, errors or ["all commodities/forex sources failed"]
    return items, errors
