import cvxpy as cp
import pandas as pd

from .base import BaseOptimizerAgent, OptimizationResult
from data.nifty50 import sector_map


class MVOOptimizerAgent(BaseOptimizerAgent):
    """Classic Markowitz mean-variance optimization, solved as a convex QP.

    Maximize:    mu^T w  -  (risk_aversion / 2) * w^T Sigma w
    Subject to:  sum(w) = 1,  
                 min_weight <= w <= max_weight,
                 sqrt(w^T Sigma w) <= max_volatility (if set)
    """
    name = "MVO-QP"

    def optimize(self, mu: pd.Series, cov: pd.DataFrame, constraints,
                 risk_free_rate: float = 0.06, sector_map = None,) -> OptimizationResult:
        
        n = len(mu)
        w = cp.Variable(n) #portfolio weights

        #portfolio risk and expected return
        risk = cp.quad_form(w, cov.values)
        ret = mu.values @ w

        # maximize expected return while penalizing portfolio variance
        objective = cp.Maximize(ret - 0.5 * constraints.risk_aversion * risk)

        cons = [
            cp.sum(w) == 1,
            w >= constraints.min_weight,
            w <= constraints.max_weight,
        ]

        # Maximum portfolio volatility constraint
        if constraints.max_volatility:
            cons.append(risk <= constraints.max_volatility ** 2)

        # Optional sector constraints
        if sector_map:
            sector_max = getattr(
                constraints,
                "sector_max_weight",
                None
            )

            if sector_max is not None:
                sectors = {}

                for ticker, sector in sector_map.items():
                    if ticker in mu.index:
                        sectors.setdefault(sector, []).append(
                            list(mu.index).index(ticker)
                        )

                for sector, indices in sectors.items():
                    cons.append(
                        cp.sum(w[indices]) <= sector_max
                    )

        # Solve QP
        prob = cp.Problem(objective, cons)
        prob.solve()

        # Check solver result before accessing w.value
        if w.value is None:
            raise RuntimeError(
                f"MVO optimization failed. Solver status: {prob.status}"
            )

        weights = {t: round(max(0.0, float(v)), 6) for t, v in zip(mu.index, w.value)}

        exp_ret, exp_vol, sharpe = self._sharpe(mu, weights, cov, risk_free_rate)

        return OptimizationResult(
            algorithm=self.name,
            weights=weights,
            expected_return=exp_ret,
            expected_volatility=exp_vol,
            sharpe_ratio=sharpe,
            diagnostics={"solver_status": prob.status},
        )
