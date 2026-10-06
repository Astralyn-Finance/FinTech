import pandas as pd
from pypfopt import EfficientFrontier
from pypfopt.black_litterman import BlackLittermanModel, market_implied_prior_returns

from .base import BaseOptimizerAgent, OptimizationResult


class BlackLittermanOptimizerAgent(BaseOptimizerAgent):
    """Black-Litterman: blends a market-implied equilibrium prior with "views"
    from any source -- sentiment scores, or (new) other optimizer agents'
    implied convictions via the Coordinator. Whatever the source, this agent
    doesn't care; it just blends views with confidences into a posterior.

    Two entry points:
    - `compute_posterior()` returns the posterior mu/cov directly, for a
      pipeline stage (e.g. a final MVO) to optimize on. This is what the
      orchestrator's candidates -> coordinator -> BL -> final-MVO flow uses.

    - `optimize()` calls compute_posterior() and then makes its own final
      weight decision on the posterior -- for using Black-Litterman as a
      standalone agent (kept for backward compatibility / direct comparison).
    """
    name = "Black-Litterman"

    def compute_posterior(self, mu: pd.Series, cov: pd.DataFrame, constraints,
                           market_caps: pd.Series = None,
                           views: dict = None, view_confidences: dict = None):
        """Returns (posterior_mu, posterior_cov, diagnostics)."""
        if market_caps is not None:
            pi = market_implied_prior_returns(market_caps, constraints.risk_aversion, cov)
        else:
            '''
            No market-cap data yet -> fall back to the input mu itself as the
            prior, NOT a flat zero. Falling back to mu means "absent market-cap
            equilibrium, use our best existing estimate" -- assets with no view
            keep their own mu; assets with a view get pulled toward it, weighted
            by confidence.
            '''
            pi = mu

        viewdict = views or {}
        if viewdict:
            view_confidences = view_confidences or {}
            confidences = [view_confidences.get(t, constraints.bl_confidence) for t in viewdict]
            bl = BlackLittermanModel(cov, pi=pi, absolute_views=viewdict,
                                      omega="idzorek", view_confidences=confidences)
            posterior_mu = bl.bl_returns()
            posterior_cov = bl.bl_cov()
        else:
            # PyPortfolioOpt's BlackLittermanModel requires at least one view,
            # so with none to blend in, use the prior directly.
            posterior_mu = pi
            posterior_cov = cov

        diagnostics = {"n_views": len(viewdict), "used_market_prior": market_caps is not None}
        return posterior_mu, posterior_cov, diagnostics

    def optimize(self, mu: pd.Series, cov: pd.DataFrame, constraints,
                 risk_free_rate: float = 0.06,
                 market_caps: pd.Series = None,
                 sentiment_views: dict = None,
                 view_confidences: dict = None) -> OptimizationResult:

        posterior_mu, posterior_cov, diagnostics = self.compute_posterior(
            mu, cov, constraints, market_caps=market_caps,
            views=sentiment_views, view_confidences=view_confidences,
        )

        ef = EfficientFrontier(posterior_mu, posterior_cov,
                                weight_bounds=(constraints.min_weight, constraints.max_weight))
        ef.max_quadratic_utility(risk_aversion=constraints.risk_aversion)
        clean = ef.clean_weights()
        weights = {t: round(max(0.0, w), 6) for t, w in clean.items()}

        exp_ret, exp_vol, sharpe = self._sharpe(mu, weights, cov, risk_free_rate)
        return OptimizationResult(
            algorithm=self.name,
            weights=weights,
            expected_return=exp_ret,
            expected_volatility=exp_vol,
            sharpe_ratio=sharpe,
            diagnostics=diagnostics,
        )
