"""
Portfolio Strategy Orchestrator

Pipeline : CANDIDATES -> COORDINATOR -> BLACK-LITTERMAN -> SHORTLIST -> FINAL MVO

"""

import pandas as pd

from risk_profiling import RiskProfilingAgent, UserProfile
from optimizers.mvo_qp import MVOOptimizerAgent
from optimizers.black_litterman import BlackLittermanOptimizerAgent
from optimizers.admm_sparse import ADMMOptimizerAgent
from optimizers.proximal_gradient import ProximalGradientOptimizerAgent
from coordinator import ViewCoordinatorAgent
from stock_selector import select_top_n


class PortfolioStrategyOrchestrator:
    def __init__(self):
        self.risk_agent = RiskProfilingAgent()
        self.candidate_optimizers = {
            "mvo": MVOOptimizerAgent(),
            "admm": ADMMOptimizerAgent(),
            "proximal_gradient": ProximalGradientOptimizerAgent(),
        }
        self.coordinator = ViewCoordinatorAgent()
        self.black_litterman = BlackLittermanOptimizerAgent()
        self.final_optimizer = MVOOptimizerAgent()

    def run(self, profile: UserProfile, mu: pd.Series, cov: pd.DataFrame,
            sentiment_views: dict = None, sentiment_confidences: dict = None,
            market_caps: pd.Series = None, sector_map: dict = None,
            risk_free_rate: float = 0.06) -> dict:

        constraints = self.risk_agent.build_constraints(profile)

        # Step 1: candidates
        candidates = {
            key: agent.optimize(mu, cov, constraints, risk_free_rate)
            for key, agent in self.candidate_optimizers.items()
        }

        # Step 2: candidates -> optimizer-derived views
        optimizer_views, optimizer_confidences = self.coordinator.build_views(
            candidates, mu, cov, constraints.risk_aversion,
        )

        # Step 3: merge with sentiment views. 
        sentiment_views = sentiment_views or {}
        sentiment_confidences = sentiment_confidences or {
            t: constraints.bl_confidence for t in sentiment_views
        }
        all_views = {**optimizer_views, **sentiment_views}
        all_confidences = {**optimizer_confidences, **sentiment_confidences}

        # Step 4: Black-Litterman posterior
        posterior_mu, posterior_cov, bl_diagnostics = self.black_litterman.compute_posterior(
            mu, cov, constraints, market_caps=market_caps,
            views=all_views, view_confidences=all_confidences,
        )

        # Step 5: shortlist if the user said how many stocks they want
        if constraints.target_num_holdings:
            shortlist = select_top_n(posterior_mu, posterior_cov, constraints.target_num_holdings)
        else:
            shortlist = list(mu.index)

        sub_mu = posterior_mu.loc[shortlist]
        sub_cov = posterior_cov.loc[shortlist, shortlist]

        # Step 6: final constrained MVO on the (shortlisted) posterior
        final = self.final_optimizer.optimize(sub_mu, sub_cov, constraints,
                                                risk_free_rate, sector_map=sector_map)

        return {
            "constraints": constraints,
            "candidates": candidates,
            "views": {
                "assets": all_views,
                "confidences": all_confidences,
                "n_from_optimizers": len(optimizer_views),
                "n_from_sentiment": len(sentiment_views),
            },
            "posterior": {"mu": posterior_mu, "cov": posterior_cov, **bl_diagnostics},
            "shortlist": shortlist if constraints.target_num_holdings else None,
            "recommended": final,
            "explanation": self._explain(profile, final, all_views,
                                          shortlist if constraints.target_num_holdings else None),
        }

    @staticmethod
    def _explain(profile: UserProfile, chosen, views: dict, shortlist) -> str:
        base = (
            f"Based on a {profile.risk_tolerance.value} risk tolerance, "
            f"{profile.objective.value.replace('_', ' ')} objective and a "
            f"{profile.time_horizon.value}-term horizon: expected annual return "
            f"{chosen.expected_return:.1%}, volatility {chosen.expected_volatility:.1%}, "
            f"Sharpe {chosen.sharpe_ratio:.2f}."
        )
        if shortlist:
            base += f" Shortlisted to {len(shortlist)} stocks as requested."
        if views:
            base += f" {len(views)} view(s) informed the posterior return estimate."
        return base
