"""
End-to-end demo: CANDIDATES -> COORDINATOR -> BLACK-LITTERMAN -> SHORTLIST -> FINAL MVO

"""

import numpy as np
import pandas as pd

from risk_profiling import UserProfile, RiskTolerance, InvestmentObjective, TimeHorizon
from orchestrator import PortfolioStrategyOrchestrator

try:
    from data.data_fetcher import load_nifty50_data
    mu, cov, market_caps, sectors, source = load_nifty50_data(years=1)

    if len(mu) == 0:
        raise RuntimeError("no usable data returned")
    print(f"Loaded real Nifty 50 data for {len(mu)} tickers (source: {source}).\n")

except Exception as e:
    print(f"Could not load live Nifty 50 data ({type(e).__name__}: {e}).")
    print("Using a synthetic stand-in universe instead so the pipeline can still be demonstrated.\n")
    
    np.random.seed(42)
    tickers = ["HDFCBANK.NS", "ICICIBANK.NS", "RELIANCE.NS", "BHARTIARTL.NS", "LT.NS",
               "SBIN.NS", "INFY.NS", "AXISBANK.NS", "BAJFINANCE.NS", "TCS.NS"]
    n = len(tickers)
    mu = pd.Series(np.random.uniform(0.08, 0.22, n), index=tickers)
    raw = np.random.randn(n, n) * 0.02
    cov = pd.DataFrame(raw @ raw.T + np.eye(n) * 0.01, index=tickers, columns=tickers)
    market_caps, sectors = None, None

sentiment_ticker = mu.index[6] if len(mu) > 6 else mu.index[0]
sentiment_views = {sentiment_ticker: 0.20}  # stand-in for a FinBERT-derived signal

orchestrator = PortfolioStrategyOrchestrator()

for n_stocks in [None, 5]:
    profile = UserProfile(
        risk_tolerance=RiskTolerance.MODERATE,
        objective=InvestmentObjective.BALANCED_GROWTH,
        time_horizon=TimeHorizon.LONG,
        max_single_position=0.25,
        target_num_holdings=n_stocks,
    )
    out = orchestrator.run(profile, mu, cov, sentiment_views=sentiment_views,
                            market_caps=market_caps, sector_map=sectors)

    label = f"TOP {n_stocks} STOCKS" if n_stocks else "FULL UNIVERSE"
    print(f"=== {label} ===")
    print("Candidates:")
    for r in out["candidates"].values():
        print(f"  {r.algorithm:18s} return={r.expected_return:7.2%}  vol={r.expected_volatility:7.2%}")
    print(f"Views feeding Black-Litterman: {out['views']['n_from_optimizers']} from optimizer "
          f"disagreement, {out['views']['n_from_sentiment']} from sentiment")
    if out["shortlist"]:
        print("Shortlist:", ", ".join(out["shortlist"]))
    print("Final recommendation:")
    for t, w in sorted(out["recommended"].weights.items(), key=lambda kv: -kv[1]):
        if w > 0.005:
            print(f"  {t:15s} {w:6.1%}")
    print(out["explanation"])
    print()
