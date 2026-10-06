"""
Strategy Combiner Agent:

Combines multiple optimizer agents' portfolios into ONE blended portfolio,
instead of the orchestrator just picking a single "winner" strategy.

"""

import cvxpy as cp
import numpy as np
import pandas as pd

from optimizers.base import BaseOptimizerAgent, OptimizationResult


class StrategyCombinerAgent:
    name = "Combined (Strategy-Blend)"

    def combine(self, results: dict, mu: pd.Series, cov: pd.DataFrame, constraints,
                risk_free_rate: float = 0.06) -> OptimizationResult:
        keys = list(results.keys())
        if len(keys) == 1:
            return results[keys[0]]

        # Each strategy's weight vector, aligned to mu's asset order (m strategies x n assets)
        W = np.array([[results[k].weights.get(t, 0.0) for t in mu.index] for k in keys])

        strat_mu = W @ mu.values                # expected return of each strategy
        strat_cov = W @ cov.values @ W.T         # how the strategies co-move
        strat_cov = strat_cov + np.eye(len(keys)) * 1e-8  # ridge: guards against
        # near-identical strategies making this matrix singular

        alloc = self._allocate_across_strategies(
            strat_mu, strat_cov, constraints.risk_aversion, constraints.max_volatility
        )

        combined_w = alloc @ W
        combined_w = np.clip(combined_w, 0.0, None)
        total = combined_w.sum()
        combined_w = combined_w / total if total > 0 else combined_w

        weights = {t: round(float(v), 6) for t, v in zip(mu.index, combined_w)}
        exp_ret, exp_vol, sharpe = BaseOptimizerAgent._sharpe(mu, weights, cov, risk_free_rate)

        return OptimizationResult(
            algorithm=self.name,
            weights=weights,
            expected_return=exp_ret,
            expected_volatility=exp_vol,
            sharpe_ratio=sharpe,
            diagnostics={
                "strategy_allocation": {k: round(float(a), 4) for k, a in zip(keys, alloc)},
            },
        )

    @staticmethod
    def _allocate_across_strategies(strat_mu, strat_cov, risk_aversion, max_volatility):
        """Small mean-variance QP over the strategies themselves:
        maximize  strat_mu^T a  -  0.5 * risk_aversion * a^T strat_cov a
        s.t.      sum(a) = 1,  a >= 0,  (optional) sqrt(a^T strat_cov a) <= max_volatility
        """
        m = len(strat_mu)
        a = cp.Variable(m)
        risk = cp.quad_form(a, strat_cov)
        objective = cp.Maximize(strat_mu @ a - 0.5 * risk_aversion * risk)
        cons = [cp.sum(a) == 1, a >= 0]
        if max_volatility:
            cons.append(risk <= max_volatility ** 2)

        prob = cp.Problem(objective, cons)
        prob.solve()

        if a.value is None:  # infeasible (e.g. vol cap unreachable) -> fall back to equal-weight
            return np.ones(m) / m
        vals = np.clip(a.value, 0, None)
        return vals / vals.sum() if vals.sum() > 0 else np.ones(m) / m
