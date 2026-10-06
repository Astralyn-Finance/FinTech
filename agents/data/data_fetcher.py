"""
Nifty 50 Data Loader

"""

from datetime import date, timedelta

from .nifty50 import yahoo_tickers, sector_map
from .estimation import estimate_mu_cov  
from . import source_router


def load_nifty50_data(years: int = 3):
    """
    Fetch historical prices (NSE Bhavcopy first, yfinance fallback).
    Returns (mu, cov, market_caps, sector_map, price_source).
    """
    tickers = yahoo_tickers()
    end = date.today()
    start = end - timedelta(days=365 * years)

    prices = source_router.get_historical_ohlcv(tickers, start, end)
    mu, cov = estimate_mu_cov(prices)

    fundamentals = source_router.get_fundamentals(list(prices.columns))
    market_caps = {t: p.market_cap for t, p in fundamentals.items() if p.market_cap}
    import pandas as pd
    market_caps = pd.Series(market_caps) if market_caps else None

    sectors = sector_map()
    return mu, cov, market_caps, sectors, prices.attrs.get("source", "unknown")


if __name__ == "__main__":
    mu, cov, caps, sectors, source = load_nifty50_data()
    print(f"Price data source: {source}")
    print("Top 10 by estimated annual return:")
    print(mu.sort_values(ascending=False).head(10))
    print(f"\nMarket caps fetched for {0 if caps is None else len(caps)} / {len(mu)} tickers")
