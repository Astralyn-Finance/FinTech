import numpy as np
import pandas as pd

from .base import BaseOptimizerAgent, OptimizationResult, search_penalty_for_target


def project_box_simplex(v: np.ndarray, lo: np.ndarray, hi: np.ndarray,
                         tol: float = 1e-8, max_iter: int = 100) -> np.ndarray:
    """Euclidean projection of v onto {x : sum(x)=1, lo<=x<=hi}, via bisection
    on the shift parameter (standard water-filling approach)."""
    shift_lo, shift_hi = -10.0, 10.0
    shift = 0.0
    for _ in range(max_iter):
        shift = 0.5 * (shift_lo + shift_hi)
        x = np.clip(v - shift, lo, hi)
        s = x.sum()
        if abs(s - 1.0) < tol:
            break
        if s > 1.0:
            shift_lo = shift
        else:
            shift_hi = shift
    return np.clip(v - shift, lo, hi)


class ADMMOptimizerAgent(BaseOptimizerAgent):
    """Regularized mean-variance portfolio, solved by ADMM:

        minimize    0.5 w^T Sigma w  -  kappa * mu^T w  +  lambda * ||w||_1
        subject to  sum(w) = 1,  min_weight <= w <= max_weight

    where kappa = 1 / risk_aversion and lambda = l1_penalty (both come from the
    risk-profiling agent). The L1 term pushes small positions to exactly zero,
    giving a concentrated, lower-turnover portfolio — useful when the user set
    `target_num_holdings` to a focused number rather than "as diversified as
    possible" (which is what plain MVO tends to produce).

    Implementation note: this folds the L1 shrinkage and the box/simplex
    projection into a single z-update rather than a textbook 3-block ADMM split.
    That's a fast, good approximation at portfolio scale (tens to low hundreds
    of assets) - reach for a stricter split only if you need provable optimality
    at much larger scale.

    Cardinality note: too little L1 penalty barely changes anything; too much
    collapses the whole portfolio into equal-weight (every asset gets shrunk to
    zero, and the simplex projection redistributes mass symmetrically). The
    useful range sits between those two failure modes and depends on the actual
    return/risk data, not just the risk profile - so when `target_num_holdings`
    is set, this agent runs a small bisection search over the penalty strength
    (using the real mu/cov) rather than trusting a single precomputed value.
    """
    name = "ADMM-Sparse"

    def _solve(self, mu, cov, constraints, lam, rho, max_iter, tol):
        n = len(mu)
        Sigma = cov.values
        kappa = 1.0 / max(constraints.risk_aversion, 1e-6)
        A = Sigma + rho * np.eye(n)
        lo = np.full(n, constraints.min_weight)
        hi = np.full(n, constraints.max_weight)

        w = np.ones(n) / n
        z = w.copy()
        u = np.zeros(n)
        primal_res = np.inf
        it = 0
        for it in range(max_iter):
            rhs = kappa * mu.values + rho * (z - u)
            w = np.linalg.solve(A, rhs)
            v = w + u
            shrunk = np.sign(v) * np.maximum(np.abs(v) - lam / rho, 0.0)
            z_new = project_box_simplex(shrunk, lo, hi)
            u = u + w - z_new
            primal_res = np.linalg.norm(w - z_new)
            z = z_new
            if primal_res < tol:
                break
        return z, it + 1, primal_res

    def optimize(self, mu: pd.Series, cov: pd.DataFrame, constraints,
                 risk_free_rate: float = 0.06,
                 rho: float = 0.1, max_iter: int = 300, tol: float = 1e-7) -> OptimizationResult:
        base_lam = constraints.l1_penalty if constraints.l1_penalty > 0 else 1e-4
        target = getattr(constraints, "target_num_holdings", None)

        if target:
            _, (z, it, primal_res), _held = search_penalty_for_target(
                lambda lam: self._solve(mu, cov, constraints, lam, rho, max_iter, tol),
                target, base_lam,
            )
        else:
            z, it, primal_res = self._solve(mu, cov, constraints, base_lam, rho, max_iter, tol)

        weights = {t: round(max(0.0, val), 6) for t, val in zip(mu.index, z)}
        exp_ret, exp_vol, sharpe = self._sharpe(mu, weights, cov, risk_free_rate)
        return OptimizationResult(
            algorithm=self.name,
            weights=weights,
            expected_return=exp_ret,
            expected_volatility=exp_vol,
            sharpe_ratio=sharpe,
            diagnostics={"iterations": it, "primal_residual": float(primal_res)},
        )
