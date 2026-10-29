"""12-month return forecasts with a rolling-origin backtest (no look-ahead)."""

from __future__ import annotations

import warnings
from typing import Callable

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from . import config

Model = Callable[[np.ndarray, int], float]   # (train monthly log returns, horizon) -> horizon log return


def zero_return(train: np.ndarray, h: int) -> float:
    """Naive benchmark: next year looks like cash under the mattress."""
    return 0.0


def historical_mean(train: np.ndarray, h: int) -> float:
    return float(train.mean() * h)


def trailing_36m_mean(train: np.ndarray, h: int) -> float:
    return float(train[-36:].mean() * h)


def damped_ets(train: np.ndarray, h: int) -> float:
    level = np.cumsum(train)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = ExponentialSmoothing(level, trend="add", damped_trend=True,
                                   initialization_method="estimated").fit()
    path = fit.forecast(h)
    return float(path[-1] - level[-1])


def arima_ar1(train: np.ndarray, h: int) -> float:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = ARIMA(train, order=(1, 0, 0), trend="c").fit()
    return float(np.sum(fit.forecast(h)))


MODELS: dict[str, Model] = {
    "zero_return": zero_return,
    "historical_mean": historical_mean,
    "trailing_36m_mean": trailing_36m_mean,
    "damped_ets": damped_ets,
    "arima_ar1": arima_ar1,
}

MODEL_LABELS_AR = {
    "zero_return": "عائد صفري (مرجع ساذج)",
    "historical_mean": "المتوسط التاريخي",
    "trailing_36m_mean": "متوسط آخر 36 شهراً",
    "damped_ets": "تمهيد أسي بترند مخمَّد",
    "arima_ar1": "ARIMA(1,0,0)",
}


def backtest(returns: pd.Series, h: int = config.HORIZON_MONTHS,
             min_train: int = config.MIN_TRAIN_MONTHS) -> pd.DataFrame:
    """Expanding-window forecasts; each origin only sees data up to itself."""
    r = returns.dropna().to_numpy()
    idx = returns.dropna().index
    rows = []
    for t in range(min_train, len(r) - h + 1):
        train, actual = r[:t], float(r[t:t + h].sum())
        for name, model in MODELS.items():
            try:
                pred = model(train, h)
            except Exception:          # a failed fit drops the candidate for this origin only
                continue
            rows.append({"origin": idx[t - 1], "model": name, "forecast": pred, "actual": actual})
    bt = pd.DataFrame(rows)
    bt["error"] = bt["forecast"] - bt["actual"]
    return bt


def score(bt: pd.DataFrame) -> pd.DataFrame:
    s = bt.groupby("model").agg(mae=("error", lambda e: e.abs().mean()),
                                rmse=("error", lambda e: np.sqrt((e ** 2).mean())),
                                bias=("error", "mean"),
                                origins=("error", "size"))
    s["skill_vs_zero"] = 1 - s["mae"] / s.loc["zero_return", "mae"]
    s["label_ar"] = s.index.map(MODEL_LABELS_AR)
    return s.sort_values("mae")


def final_forecast(returns: pd.Series, bt: pd.DataFrame, model: str,
                   h: int = config.HORIZON_MONTHS) -> dict:
    """Point forecast on all data + interval from that model's own backtest errors."""
    r = returns.dropna().to_numpy()
    point = MODELS[model](r, h)
    err = bt.loc[bt["model"] == model, "error"].to_numpy()
    lo, hi = np.quantile(point - err, [0.10, 0.90])
    return {
        "model": model,
        "horizon_months": h,
        "point_log": point,
        "point_pct": float(np.expm1(point)),
        "p10_pct": float(np.expm1(lo)),
        "p90_pct": float(np.expm1(hi)),
        "train_end": str(returns.dropna().index[-1]),
    }
