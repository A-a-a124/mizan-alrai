"""Stationary block bootstrap and spending-rule simulation (the spending frontier)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config


def stationary_bootstrap(returns: np.ndarray, n_paths: int, n_months: int,
                         block_mean: float = config.BLOCK_MEAN, seed: int = config.SEED) -> np.ndarray:
    """Politis-Romano stationary bootstrap: keeps autocorrelation and fat tails of real history."""
    rng = np.random.default_rng(seed)
    r = np.asarray(returns, dtype=float)
    n = r.size
    idx = np.empty((n_paths, n_months), dtype=np.int64)
    idx[:, 0] = rng.integers(0, n, n_paths)
    new_block = rng.random((n_paths, n_months)) < 1.0 / block_mean
    starts = rng.integers(0, n, (n_paths, n_months))
    for t in range(1, n_months):
        idx[:, t] = np.where(new_block[:, t], starts[:, t], (idx[:, t - 1] + 1) % n)
    return r[idx]


def simulate_spending(paths: np.ndarray, rate: float, inflation: float = config.INFLATION,
                      smoothing_quarters: int = config.SMOOTHING_QUARTERS) -> dict:
    """Pay rate/4 of the trailing 12-quarter average value every quarter.

    paths: monthly log returns (n_paths, n_months). Start value = 100 (real and nominal).
    """
    n_paths, n_months = paths.shape
    value = np.full(n_paths, 100.0)
    history = [np.full(n_paths, 100.0)] * smoothing_quarters
    annual_spend = np.zeros((n_paths, n_months // 12))
    for t in range(n_months):
        value = value * np.exp(paths[:, t])
        if (t + 1) % 3 == 0:
            history = history[1:] + [value.copy()]
            pay = rate / 4 * np.mean(history, axis=0)
            pay = np.minimum(pay, value)
            value = value - pay
            annual_spend[:, t // 12] += pay
    years = n_months / 12
    deflator = (1 + inflation) ** years
    real_final = value / deflator
    real_spend = annual_spend / (1 + inflation) ** np.arange(1, annual_spend.shape[1] + 1)
    yoy = np.diff(annual_spend, axis=1) / np.maximum(annual_spend[:, :-1], 1e-9)
    return {
        "rate": rate,
        "p_preserve_real": float(np.mean(real_final >= 100.0)),
        "median_real_final": float(np.median(real_final)),
        "p10_real_final": float(np.quantile(real_final, 0.10)),
        "p90_real_final": float(np.quantile(real_final, 0.90)),
        "median_real_spend_total": float(np.median(real_spend.sum(axis=1))),
        "median_first_year_spend": float(np.median(annual_spend[:, 0])),
        "spend_cut_prob": float(np.mean((yoy < -0.10).any(axis=1))) if yoy.size else 0.0,
    }


def nominal_yearly(paths: np.ndarray, rate: float,
                   smoothing_quarters: int = config.SMOOTHING_QUARTERS) -> np.ndarray:
    """Nominal endowment value at each year end (n_paths, years+1) under the spending rule."""
    n_paths, n_months = paths.shape
    value = np.full(n_paths, 100.0)
    history = [np.full(n_paths, 100.0)] * smoothing_quarters
    yearly = [value.copy()]
    for t in range(n_months):
        value = value * np.exp(paths[:, t])
        if (t + 1) % 3 == 0:
            history = history[1:] + [value.copy()]
            value = value - np.minimum(rate / 4 * np.mean(history, axis=0), value)
        if (t + 1) % 12 == 0:
            yearly.append(value.copy())
    return np.vstack(yearly).T


def deflate(nominal: np.ndarray, inflation: float) -> np.ndarray:
    return nominal / (1 + inflation) ** np.arange(nominal.shape[1])


def real_value_bands(paths: np.ndarray, rate: float, inflation: float = config.INFLATION) -> np.ndarray:
    """p10 / median / p90 of real endowment value at each year end (years 0..N)."""
    return np.quantile(deflate(nominal_yearly(paths, rate), inflation), [0.10, 0.50, 0.90], axis=0)


def spending_frontier(returns: np.ndarray, rates=config.SPEND_RATES, inflation: float = config.INFLATION,
                      annual_shift: float = 0.0, n_paths: int = config.N_PATHS,
                      years: int = config.SIM_YEARS, seed: int = config.SEED) -> pd.DataFrame:
    shifted = np.asarray(returns) + annual_shift / 12
    paths = stationary_bootstrap(shifted, n_paths, years * 12, seed=seed)
    return pd.DataFrame([simulate_spending(paths, r, inflation) for r in rates])


def sustainable_rate(frontier: pd.DataFrame, confidence: float = config.CONFIDENCE) -> float:
    """Highest spending rate whose P(real principal preserved) meets the confidence level."""
    ok = frontier.loc[frontier["p_preserve_real"] >= confidence, "rate"]
    return float(ok.max()) if len(ok) else 0.0


def horizon_distribution(returns: np.ndarray, months: int = config.HORIZON_MONTHS,
                         n_paths: int = config.N_PATHS, seed: int = config.SEED) -> np.ndarray:
    """Bootstrap distribution of the next-12-month simple return."""
    paths = stationary_bootstrap(returns, n_paths, months, seed=seed)
    return np.expm1(paths.sum(axis=1))
