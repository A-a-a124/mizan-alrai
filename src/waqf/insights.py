"""Deeper cuts of the same data: masarif gaps by region, fund managers, and shock tests of the spending rule."""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config, solutions

# ---------------------------------------------------------------- 1. masarif gaps (region x masraf)


def region_matrix(disb: pd.DataFrame) -> pd.DataFrame:
    """Every region x masraf pair, including the absent ones (count 0), with shares inside the region."""
    regions = disb[["region", "region_ar", "region_en"]].drop_duplicates()
    masarif = disb[["masraf", "masraf_ar", "masraf_en", "group"]].drop_duplicates()
    grid = regions.merge(masarif, how="cross")
    grid = grid.merge(disb[["region", "masraf", "waqf_count"]], on=["region", "masraf"], how="left")
    grid["waqf_count"] = grid["waqf_count"].fillna(0).astype(int)
    grid["share_in_region"] = grid["waqf_count"] / grid.groupby("region")["waqf_count"].transform("sum")
    national = grid.groupby("masraf")["waqf_count"].transform("sum") / grid["waqf_count"].sum()
    grid["national_share"] = national
    grid["absent"] = grid["waqf_count"] == 0
    return grid.sort_values(["region", "masraf"]).reset_index(drop=True)


def social_gaps(matrix: pd.DataFrame) -> pd.DataFrame:
    """Named gaps: social-care masarif with no registered waqf at all in a region."""
    gaps = matrix[matrix["absent"] & matrix["masraf"].isin(solutions.SOCIAL)]
    size = matrix.groupby("region")["waqf_count"].sum().rename("region_waqf_designations")
    out = gaps.merge(size, on="region")[["region", "region_ar", "masraf", "masraf_ar", "region_waqf_designations"]]
    return out.sort_values(["region_waqf_designations", "masraf"], ascending=[False, True]).reset_index(drop=True)


def gaps_summary(matrix: pd.DataFrame, gaps: pd.DataFrame) -> dict:
    n_regions = matrix["region"].nunique()
    absent_by_masraf = gaps.groupby("masraf")["region"].nunique()
    out = {"regions": int(n_regions), "social_gaps": int(len(gaps)),
           "pairs_total": int(len(matrix)), "pairs_absent": int(matrix["absent"].sum())}
    for m in solutions.SOCIAL:
        out[f"regions_without_{m}"] = int(absent_by_masraf.get(m, 0))
    return out


# ---------------------------------------------------------------- 2. fund managers


def manager_ranking(label: pd.DataFrame, rets: pd.DataFrame) -> pd.DataFrame:
    """One row per manager: how its graded funds kept their unit value, and how regularly they paid out."""
    order = {g: i for i, g in enumerate(solutions.GRADES)}
    r = rets[rets["eligible"]].assign(year=rets["month"].dt.year)
    per_fund = pd.DataFrame({"years": r.groupby("symbol")["year"].nunique(),
                             "payout_years": r[r["payout_flag"]].groupby("symbol")["year"].nunique()}).fillna(0)
    lab = label.merge(per_fund, left_on="symbol", right_index=True, how="left")
    rows = []
    for manager, g in lab.groupby("manager"):
        w = g["aum_sar"].fillna(0.0)
        rows.append({
            "manager": manager, "funds": int(len(g)), "aum_sar": float(w.sum()),
            "funds_A": int((g["grade"] == "A").sum()),
            "funds_below_B": int(g["grade"].isin(["C", "D", "E"]).sum()),
            "avg_grade_score": float(g["grade"].map(order).mean()),          # 0 = all A ... 4 = all E
            "unit_growth_avg": float(g["unit_growth"].mean()),
            "unit_growth_aum_weighted": float(np.average(g["unit_growth"], weights=w) if w.sum() > 0
                                              else g["unit_growth"].mean()),
            "worst_drawdown": float(g["max_drawdown"].min()),
            "payout_regularity": float(g["payout_years"].sum() / g["years"].sum()),   # share of fund-years with a payout
            "provisional_funds": int(g["provisional"].sum()),
        })
    out = pd.DataFrame(rows).sort_values(["avg_grade_score", "unit_growth_avg"], ascending=[True, False])
    out.insert(0, "rank", range(1, len(out) + 1))
    return out.reset_index(drop=True)


def fund_series(rets: pd.DataFrame) -> pd.DataFrame:
    """Monthly unit price of every eligible fund, rebased to 100 at its first month, with payout marks."""
    r = rets[rets["eligible"]].sort_values(["symbol", "month"]).copy()
    first = r.groupby("symbol")["unit_price"].transform("first")
    r["price_100"] = r["unit_price"] / first * 100
    peak = r.groupby("symbol")["price_100"].cummax()
    r["drawdown"] = r["price_100"] / peak - 1
    r["month"] = r["month"].dt.strftime("%Y-%m")
    return r[["symbol", "month", "price_100", "drawdown", "payout_flag", "payout_est", "flag"]].reset_index(drop=True)


# ---------------------------------------------------------------- 3. shock tests


def worst_window(returns: np.ndarray) -> tuple[int, int]:
    """Start and end (exclusive) of the deepest peak-to-trough fall in a monthly log-return series."""
    level = np.concatenate([[0.0], np.cumsum(returns)])
    peak_at = np.maximum.accumulate(level)
    trough = int(np.argmin(level - peak_at))
    peak = int(np.argmax(level[:trough + 1]))
    return peak, trough


SHOCK_YEARS = 10
STRATEGIES = {"mizan": ("rate_balanced", True), "same_rate_unsmoothed": ("rate_balanced", False),
              "recent_level_unsmoothed": ("rate_recent_level", False)}


def shock_scenarios(returns: np.ndarray, months: pd.Series | None = None) -> dict[str, dict]:
    """Deterministic return and inflation paths. Outside the shock, every month earns the historical mean."""
    r = np.asarray(returns, dtype=float)
    n = SHOCK_YEARS * 12
    mean = float(r.mean())
    start, end = worst_window(r)
    crash = r[start:end]
    replay = np.full(n, mean)
    replay[12:12 + len(crash)] = crash                       # the fall arrives at the start of year 2
    double = np.full(n, mean)
    double[12:12 + len(crash)] = crash
    double[60:60 + len(crash)] = crash                       # and again at the start of year 6
    base_infl = np.full(SHOCK_YEARS, config.INFLATION)
    hot = base_infl.copy()
    hot[:5] = 0.04
    window = None if months is None else (str(months.iloc[start]), str(months.iloc[end - 1]))
    return {
        "calm": {"returns": np.full(n, mean), "inflation": base_infl},
        "worst_fall_again": {"returns": replay, "inflation": base_infl,
                             "fall": float(np.expm1(crash.sum())), "fall_months": int(len(crash)), "window": window},
        "worst_fall_twice": {"returns": double, "inflation": base_infl},
        "inflation_4pct_5y": {"returns": np.full(n, mean), "inflation": hot},
        "flat_3y": {"returns": np.concatenate([np.zeros(36), np.full(n - 36, mean)]), "inflation": base_infl},
    }


def shock_table(returns: np.ndarray, rates: dict[str, float], months: pd.Series | None = None) -> tuple[pd.DataFrame, dict]:
    """Real payout and real value per year for each scenario x strategy (start value = 100)."""
    rows, summary = [], {}
    scenarios = shock_scenarios(returns, months)
    for name, sc in scenarios.items():
        deflator = np.cumprod(1 + sc["inflation"])
        for strategy, (rate_key, smooth) in STRATEGIES.items():
            pay, val = solutions.payout_paths(sc["returns"][None, :], rates[rate_key], smooth=smooth, inflation=0.0)
            pay, val = pay[0] / deflator, val[0] / deflator
            change = np.diff(pay) / pay[:-1]
            for y in range(SHOCK_YEARS):
                rows.append({"scenario": name, "strategy": strategy, "rate": rates[rate_key], "year": y + 1,
                             "real_payout": float(pay[y]), "real_value": float(val[y])})
            summary[f"{name}__{strategy}__worst_cut"] = float(change.min())
            summary[f"{name}__{strategy}__value_10y"] = float(val[-1])
            summary[f"{name}__{strategy}__payout_total"] = float(pay.sum())
    fall = scenarios["worst_fall_again"]
    summary.update(worst_fall=fall["fall"], worst_fall_months=fall["fall_months"],
                   worst_fall_from=fall["window"][0] if fall["window"] else None,
                   worst_fall_to=fall["window"][1] if fall["window"] else None)
    return pd.DataFrame(rows), summary


# ---------------------------------------------------------------- 4. impact in riyals


def legacy(menu: pd.DataFrame, sustainable_rate: float, years: int = 30) -> dict:
    """What each option hands to the next generation: the value left, and the yearly payout that value
    can sustain at the sustainable rate. Per 100 riyals of endowment today, in today's prices."""
    m = menu[menu["years"] == years].set_index("option")
    out = {"years": years, "sustainable_rate": sustainable_rate}
    for option in m.index:
        left = float(m.loc[option, "median_real_value"])
        out[f"{option}_value_left"] = left
        out[f"{option}_sustainable_payout_after"] = left * sustainable_rate
    out["balanced_vs_recent_extra_payout_after"] = (out["balanced_sustainable_payout_after"]
                                                    - out["recent_level_sustainable_payout_after"])
    return out
