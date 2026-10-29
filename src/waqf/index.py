"""Monthly returns, hidden-distribution detection and the Saudi Waqf Growth Index."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .clean import CleaningLog

PAYOUT_FUND_DROP = -0.02      # fund's own monthly log return at or below -2 %
PAYOUT_RESIDUAL = -0.03       # and at least 3 pts below peers run by other managers
MIN_PEERS = 2                 # peers must be observed (not interpolated) prices


def fund_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Long table of monthly log returns on the cleaned regular grid."""
    p = prices.sort_values(["symbol", "month"]).copy()
    p["log_ret"] = p.groupby("symbol")["unit_price"].transform(lambda s: np.log(s).diff())
    return p.dropna(subset=["log_ret"])


def detect_payouts(rets: pd.DataFrame, log: CleaningLog | None = None) -> pd.DataFrame:
    """Flag months where a fund drops while other managers' funds do not.

    Waqf funds pay part of their return to the beneficiary masraf; the unit price
    falls on the payout date. Tadawul publishes no payout amounts, so the size is
    estimated as the gap to the median return of peer funds run by other managers.
    """
    r = rets.copy()
    r["peer_median"] = np.nan
    for (month, manager), idx in r.groupby(["month", "manager"]).groups.items():
        peers = r[(r["month"] == month) & (r["manager"] != manager) & r["accumulating"]
                  & (r["flag"] == "observed")]
        if len(peers) >= MIN_PEERS:
            r.loc[idx, "peer_median"] = peers["log_ret"].median()
    r["residual"] = r["log_ret"] - r["peer_median"]
    r["payout_flag"] = (r["log_ret"] <= PAYOUT_FUND_DROP) & (r["residual"] <= PAYOUT_RESIDUAL)
    r["payout_est"] = np.where(r["payout_flag"], -r["residual"], 0.0)
    r["log_ret_total"] = r["log_ret"] + r["payout_est"]
    if log is not None:
        ev = r[r["payout_flag"]]
        log.add("Tadawul prices", "Detect hidden distribution payouts (price drop vs other managers' peers)",
                len(ev), ", ".join(f"{s} {m}" for s, m in zip(ev["symbol"], ev["month"].astype(str))))
    return r


def composite_index(rets: pd.DataFrame, column: str = "log_ret") -> pd.DataFrame:
    """Equal-weight, chain-linked index of eligible accumulating funds (base 100)."""
    use = rets[rets["eligible"] & rets["accumulating"]]
    by_m = use.groupby("month").agg(ret=(column, "mean"), n_funds=("symbol", "nunique"))
    by_m["index"] = 100 * np.exp(by_m["ret"].cumsum())
    return by_m


def summary_stats(monthly_log_returns: pd.Series) -> dict:
    r = monthly_log_returns.dropna()
    wealth = np.exp(r.cumsum())
    drawdown = wealth / wealth.cummax() - 1
    return {
        "months": int(r.size),
        "ann_return": float(np.exp(r.mean() * 12) - 1),
        "ann_vol": float(r.std(ddof=1) * np.sqrt(12)),
        "max_drawdown": float(drawdown.min()),
        "worst_12m": float(np.exp(r.rolling(12).sum().min()) - 1),
        "best_12m": float(np.exp(r.rolling(12).sum().max()) - 1),
    }


def payout_rates(rets: pd.DataFrame) -> pd.DataFrame:
    """Estimated annual payout per fund and year (sum of detected payout log-drops)."""
    ev = rets[rets["payout_flag"]].assign(year=lambda d: d["month"].dt.year)
    return (ev.groupby(["symbol", "fund_name", "year"], as_index=False)["payout_est"].sum()
              .assign(payout_pct=lambda d: np.expm1(d["payout_est"])))
