"""
View Coordinator Agent:

Converts each candidate optimizer's suggested portfolio into a Black-Litterman
"view" via reverse-optimization -- the same trick Black-Litterman itself uses
to build its market-implied prior from cap weights:

    implied_return = risk_aversion * Sigma @ w

If a candidate optimizer wants to overweight a stock relative to the plain
input mu, that overweighting implies it has an above-mu expected return in
that optimizer's eyes and vice versa for underweighting.

"""

import numpy as np
import pandas as pd


class ViewCoordinatorAgent:
    def build_views(self, candidate_results: dict, mu: pd.Series, cov: pd.DataFrame,
                     risk_aversion: float, min_deviation_z: float = 0.25):
        """Returns (views, confidences) -- both dicts keyed by ticker, ready to
        pass into BlackLittermanOptimizerAgent. Only includes tickers where the
        candidates' (z-scored) signal meaningfully differs from neutral
        (min_deviation_z, in standard-deviations), keeping the view set small
        rather than opinionated about everything.
        """
        tickers = list(mu.index)
        implied_matrix = np.array([
            risk_aversion * (cov.values @ np.array([r.weights.get(t, 0.0) for t in tickers]))
            for r in candidate_results.values()
        ])  # shape: (n_candidates, n_assets) -- raw magnitude not trusted, see docstring

        mean_implied = implied_matrix.mean(axis=0)
        std_implied = implied_matrix.std(axis=0)

        spread = mean_implied.std()
        spread = spread if spread > 1e-12 else 1.0
        z = (mean_implied - mean_implied.mean()) / spread

        mu_spread = mu.values.std()
        mu_spread = mu_spread if mu_spread > 1e-12 else 0.01

        views, confidences = {}, {}
        for i, t in enumerate(tickers):
            if abs(z[i]) < min_deviation_z:
                continue
            views[t] = float(mu.values[i] + z[i] * mu_spread)
            # Agreement -> confidence: candidates tightly clustered (low std
            # relative to the typical cross-asset spread) -> high confidence.
            agreement = 1.0 / (1.0 + std_implied[i] / (spread + 1e-8))
            confidences[t] = float(np.clip(agreement, 0.05, 0.95))

        return views, confidences
