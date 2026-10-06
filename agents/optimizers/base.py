from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict
import numpy as np
import pandas as pd


@dataclass
class OptimizationResult:
    algorithm: str
    weights: Dict[str, float]
    expected_return: float
    expected_volatility: float
    sharpe_ratio: float
    diagnostics: dict = field(default_factory=dict)


class BaseOptimizerAgent(ABC):
    """Every optimizer agent is a deterministic, independently testable service -
    never an LLM call. The orchestrator (and eventually a LangGraph agent) invokes
    these as tools; none of them reason in natural language."""

    name: str = "base"

    @abstractmethod
    def optimize(self, mu: pd.Series, cov: pd.DataFrame, constraints,
                 risk_free_rate: float = 0.06) -> "OptimizationResult":
        """
        mu: annualized expected return per asset (index = ticker).
        cov: annualized covariance matrix.
        risk_free_rate: default ~6% (approx. Indian 10Y G-Sec).
        """
        raise NotImplementedError

    @staticmethod
    def _sharpe(mu: pd.Series, weights: Dict[str, float], cov: pd.DataFrame, rf: float):
        w = np.array([weights[t] for t in mu.index])
        ret = float(w @ mu.values)
        vol = float(np.sqrt(w @ cov.values @ w))
        sharpe = (ret - rf) / vol if vol > 1e-9 else 0.0
        return ret, vol, sharpe


def search_penalty_for_target(solve_fn, target_holdings: int, base_lam: float,
                               n_candidates: int = 25, upper_mult: float = 6.0):
    """Grid-search an L1 penalty strength for a holdings count close to
    target_holdings. `solve_fn(lam)` must return a tuple whose first element
    is the weights array.
    """
    lam_grid = [0.0] + list(np.geomspace(max(base_lam * 0.02, 1e-6), base_lam * upper_mult, n_candidates))
    best = None
    for lam in lam_grid:
        result = solve_fn(lam)
        held = int(np.sum(np.asarray(result[0]) > 0.005))
        diff = abs(held - target_holdings)
        if best is None or diff < best[0] or (diff == best[0] and lam < best[1]):
            best = (diff, lam, result, held)
    _, lam, result, held = best
    return lam, result, held
