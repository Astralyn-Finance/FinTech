import numpy as np
import pandas as pd

from .base import BaseOptimizerAgent, OptimizationResult, search_penalty_for_target
from .admm_sparse import project_box_simplex


class ProximalGradientOptimizerAgent(BaseOptimizerAgent):
    """Same regularized objective as the ADMM agent, solved instead by
    accelerated proximal gradient descent (FISTA):

        minimize    0.5 w^T Sigma w  -  kappa * mu^T w  +  lambda * ||w||_1
        subject to  sum(w) = 1,  min_weight <= w <= max_weight

    Included as an independent second solver for the same problem class:
    useful for cross-checking the ADMM agent's answer, and cheaper per-iteration
    for larger asset universes since it never solves a linear system — just a
    gradient step plus a projection each round.

    Same cardinality caveat as the ADMM agent: the right L1 strength for a
    target holdings count depends on the actual data, so when
    `target_num_holdings` is set this agent bisection-searches for it.
    """
    name = "Proximal-Gradient"

    def _solve(self, mu, cov, constraints, lam, max_iter, tol):
        n = len(mu)
        Sigma = cov.values
        kappa = 1.0 / max(constraints.risk_aversion, 1e-6)
        L = np.linalg.eigvalsh(Sigma).max()
        step = 1.0 / L
        lo = np.full(n, constraints.min_weight)
        hi = np.full(n, constraints.max_weight)

        w = np.ones(n) / n
        y = w.copy()
        t = 1.0
        it = 0
        for it in range(max_iter):
            grad = Sigma @ y - kappa * mu.values
            v = y - step * grad
            shrunk = np.sign(v) * np.maximum(np.abs(v) - step * lam, 0.0)
            w_new = project_box_simplex(shrunk, lo, hi)
            t_new = 0.5 * (1 + np.sqrt(1 + 4 * t ** 2))
            y = w_new + ((t - 1) / t_new) * (w_new - w)
            if np.linalg.norm(w_new - w) < tol:
                w = w_new
                break
            w, t = w_new, t_new
        return w, it + 1

    def optimize(self, mu: pd.Series, cov: pd.DataFrame, constraints,
                 risk_free_rate: float = 0.06,
                 max_iter: int = 1000, tol: float = 1e-7) -> OptimizationResult:
        base_lam = constraints.l1_penalty if constraints.l1_penalty > 0 else 1e-4
        target = getattr(constraints, "target_num_holdings", None)

        if target:
            _, (w, it), _held = search_penalty_for_target(
                lambda lam: self._solve(mu, cov, constraints, lam, max_iter, tol),
                target, base_lam,
            )
        else:
            w, it = self._solve(mu, cov, constraints, base_lam, max_iter, tol)

        weights = {tk: round(max(0.0, val), 6) for tk, val in zip(mu.index, w)}
        exp_ret, exp_vol, sharpe = self._sharpe(mu, weights, cov, risk_free_rate)
        return OptimizationResult(
            algorithm=self.name,
            weights=weights,
            expected_return=exp_ret,
            expected_volatility=exp_vol,
            sharpe_ratio=sharpe,
            diagnostics={"iterations": it},
        )
