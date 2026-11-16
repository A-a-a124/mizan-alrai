"""Solutions layer: turns the analysis into three things a nazir, fund manager or regulator can adopt.

1. Waqf Sustainability Label  - an A-E grade per fund from what is directly observed: did the endowed
   unit keep its purchasing power?
2. Mizan Spending Rule        - a menu of spending rates with the intergenerational trade-off made explicit.
3. Masarif Compass            - where directing the flexible "general charity" share matters most.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import allocate, config, risk

# ---------------------------------------------------------------- 1. label

GRADE_FLOORS = (("B", 0.0), ("C", -0.02), ("D", -0.05))     # nominal unit growth per year; below D is E
GRADES = ("A", "B", "C", "D", "E")
ESTABLISHED_MONTHS = 36                                      # shorter records are graded but marked provisional
GRADE_MEANING_AR = {
    "A": "الأصل محفوظ فعلياً: قيمة الوحدة نمت بمعدل التضخم أو أكثر",
    "B": "محفوظ اسمياً فقط: قيمة الوحدة نمت أقل من التضخم",
    "C": "تآكل طفيف: قيمة الوحدة نقصت حتى 2% سنوياً",
    "D": "تآكل واضح: قيمة الوحدة نقصت بين 2% و5% سنوياً",
    "E": "تآكل شديد: قيمة الوحدة نقصت أكثر من 5% سنوياً",
}


def grade(unit_growth: float, inflation: float = config.INFLATION) -> str:
    """A if the unit kept pace with inflation; then by nominal growth floors."""
    if unit_growth >= inflation:
        return "A"
    for g, floor in GRADE_FLOORS:
        if unit_growth >= floor:
            return g
    return "E"


def sustainability_label(rets: pd.DataFrame, universe: pd.DataFrame, inflation: float = config.INFLATION) -> pd.DataFrame:
    """One row per fund with at least MIN_FUND_MONTHS of history.

    The grade uses only the observed unit price (after distributions), so it does not depend on the
    estimated payout sizes. Payout, volatility and drawdown are reported beside it as context.
    """
    rows = []
    for symbol, g in rets[rets["eligible"]].groupby("symbol"):
        g = g.sort_values("month")
        months = len(g)
        unit_growth = float(np.expm1(g["log_ret"].mean() * 12))
        wealth = np.exp(g["log_ret"].cumsum())
        rows.append({
            "symbol": symbol, "fund_name": g["fund_name"].iloc[0], "manager": g["manager"].iloc[0],
            "fund_type": g["fund_type"].iloc[0], "months": months,
            "provisional": months < ESTABLISHED_MONTHS,
            "unit_growth": unit_growth,
            "real_unit_growth": (1 + unit_growth) / (1 + inflation) - 1,
            "est_payout_rate": float(np.expm1(g["payout_est"].sum()) / (months / 12)),
            "volatility": float(g["log_ret"].std(ddof=1) * np.sqrt(12)),
            "max_drawdown": float((wealth / wealth.cummax() - 1).min()),
            "grade": grade(unit_growth, inflation),
            "grade_if_inflation_low": grade(unit_growth, inflation - 0.005),
            "grade_if_inflation_high": grade(unit_growth, inflation + 0.005),
        })
    out = pd.DataFrame(rows).merge(universe[["symbol", "aum_sar"]], on="symbol", how="left")
    out["grade_meaning_ar"] = out["grade"].map(GRADE_MEANING_AR)
    out["grade_rank"] = out["grade"].map({g: i for i, g in enumerate(GRADES)})
    return out.sort_values(["grade_rank", "provisional", "unit_growth"], ascending=[True, True, False]) \
              .drop(columns="grade_rank").reset_index(drop=True)


def label_summary(label: pd.DataFrame) -> dict:
    est = label[~label["provisional"]]
    counts = label["grade"].value_counts().reindex(GRADES, fill_value=0)
    aum = label.groupby("grade")["aum_sar"].sum().reindex(GRADES, fill_value=0.0)
    return {
        "funds_graded": int(len(label)), "funds_established": int(len(est)),
        "funds_provisional": int(label["provisional"].sum()),
        **{f"count_{g}": int(counts[g]) for g in GRADES},
        **{f"established_{g}": int((est["grade"] == g).sum()) for g in GRADES},
        "aum_graded_sar": float(label["aum_sar"].sum()),
        "aum_share_A": float(aum["A"] / aum.sum()) if aum.sum() else 0.0,
        "aum_share_below_B": float(aum[["C", "D", "E"]].sum() / aum.sum()) if aum.sum() else 0.0,
        # the same share among funds with a full record only: one large young fund can carry the headline
        "established_aum_sar": float(est["aum_sar"].sum()),
        "established_aum_share_A": float(est.loc[est["grade"] == "A", "aum_sar"].sum() / est["aum_sar"].sum())
        if est["aum_sar"].sum() else 0.0,
        "largest_fund_share_of_graded_aum": float(label["aum_sar"].max() / label["aum_sar"].sum()) if label["aum_sar"].sum() else 0.0,
        "largest_fund_is_provisional": bool(label.loc[label["aum_sar"].idxmax(), "provisional"]) if label["aum_sar"].notna().any() else False,
        "grades_changed_by_inflation": int(((label["grade"] != label["grade_if_inflation_low"])
                                            | (label["grade"] != label["grade_if_inflation_high"])).sum()),
        "established_months": ESTABLISHED_MONTHS,
    }


# ---------------------------------------------------------------- 2. spending rule

TRADEOFF_YEARS = (10, 20, 30)
SIM_HORIZON_YEARS = 40          # far beyond 7 years of history: used only to locate the break-even year


def payout_paths(paths: np.ndarray, rate: float, smooth: bool = True, inflation: float = config.INFLATION,
                 smoothing_quarters: int = config.SMOOTHING_QUARTERS) -> tuple[np.ndarray, np.ndarray]:
    """Real annual payouts and real year-end values (start = 100) for every simulated path.

    smooth=True pays rate/4 of the trailing 12-quarter average each quarter (the Mizan rule);
    smooth=False pays rate/4 of the current value (payout follows the market).
    """
    n_paths, n_months = paths.shape
    years = n_months // 12
    value = np.full(n_paths, 100.0)
    history = [value.copy()] * smoothing_quarters
    payout = np.zeros((n_paths, years))
    values = np.zeros((n_paths, years))
    for t in range(years * 12):
        value = value * np.exp(paths[:, t])
        if (t + 1) % 3 == 0:
            history = history[1:] + [value.copy()]
            base = np.mean(history, axis=0) if smooth else value
            pay = np.minimum(rate / 4 * base, value)
            value = value - pay
            payout[:, t // 12] += pay
        if (t + 1) % 12 == 0:
            values[:, t // 12] = value
    deflator = (1 + inflation) ** np.arange(1, years + 1)
    return payout / deflator, values / deflator


def spending_menu(returns: np.ndarray, rates: dict[str, float], inflation: float = config.INFLATION,
                  n_paths: int = config.N_PATHS, seed: int = config.SEED) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Trade-off table (rate x horizon), yearly median payouts, and break-even years against the highest rate."""
    paths = risk.stationary_bootstrap(np.asarray(returns), n_paths, SIM_HORIZON_YEARS * 12, seed=seed)
    table, yearly, medians = [], [], {}
    for name, rate in rates.items():
        pay, val = payout_paths(paths, rate, smooth=True, inflation=inflation)
        medians[name] = np.median(pay, axis=0)
        for y in range(SIM_HORIZON_YEARS):
            yearly.append({"option": name, "rate": rate, "year": y + 1,
                           "median_real_payout": float(medians[name][y]),
                           "median_real_value": float(np.median(val[:, y]))})
        for years in TRADEOFF_YEARS:
            table.append({
                "option": name, "rate": rate, "years": years,
                "median_real_value": float(np.median(val[:, years - 1])),
                "p_preserve_real": float(np.mean(val[:, years - 1] >= 100.0)),
                "cumulative_real_payout": float(np.median(pay[:, :years].sum(axis=1))),
                "annual_real_payout_at_end": float(medians[name][years - 1]),
            })
    high = max(rates, key=rates.get)
    breakeven = {}
    for name in rates:
        if name == high:
            continue
        ahead = np.nonzero(medians[name] >= medians[high])[0]
        breakeven[name] = int(ahead[0] + 1) if len(ahead) else None      # None = not within the simulated horizon
    return pd.DataFrame(table), pd.DataFrame(yearly), breakeven


def smoothing_effect(returns: np.ndarray, rate: float, years: int = 10, inflation: float = config.INFLATION,
                     n_paths: int = config.N_PATHS, seed: int = config.SEED) -> dict:
    """Does paying from the 12-quarter average steady the beneficiary's income at the same rate?"""
    paths = risk.stationary_bootstrap(np.asarray(returns), n_paths, years * 12, seed=seed)
    out = {"rate": rate, "years": years}
    for key, smooth in (("smoothed", True), ("unsmoothed", False)):
        pay, _ = payout_paths(paths, rate, smooth=smooth, inflation=inflation)
        change = np.diff(pay, axis=1) / pay[:, :-1]
        out[f"{key}_payout_volatility"] = float(np.median(change.std(axis=1, ddof=1)))
        out[f"{key}_worst_annual_cut"] = float(np.median(change.min(axis=1)))
        out[f"{key}_p_cut_over_5pct"] = float(np.mean((change < -0.05).any(axis=1)))
    return out


def payout_trend(rets: pd.DataFrame) -> pd.DataFrame:
    """Detected distribution events per calendar year, beside how many funds were observable that year."""
    r = rets.assign(year=rets["month"].dt.year)
    by_year = r.groupby("year").agg(funds_observed=("symbol", "nunique"), events=("payout_flag", "sum"),
                                    observed_months=("flag", lambda s: int((s == "observed").sum())),
                                    months=("flag", "size"))
    by_year["events"] = by_year["events"].astype(int)
    by_year["observed_share"] = by_year["observed_months"] / by_year["months"]
    return by_year.drop(columns=["observed_months", "months"]).reset_index()


# ---------------------------------------------------------------- 3. compass

SOCIAL = ("poor", "orphans", "widows", "food", "housing")


def compass_case(alloc: pd.DataFrame) -> pd.DataFrame:
    """Riyals per masraf from the waqif's conditions and from the directed flexible share."""
    a = alloc[alloc["kind"] != "waterfall"]
    t = a.pivot_table(index=["line", "label_ar"], columns="kind", values="amount", aggfunc="sum", fill_value=0.0)
    for col in ("waqif_condition", "flexible"):
        if col not in t:
            t[col] = 0.0
    t = t.rename(columns={"waqif_condition": "from_waqif_conditions", "flexible": "from_flexible_share"})
    t["total"] = t["from_waqif_conditions"] + t["from_flexible_share"]
    t["multiple"] = np.where(t["from_waqif_conditions"] > 0, t["total"] / t["from_waqif_conditions"].replace(0, np.nan), np.nan)
    t = t.reset_index()
    t["social"] = t["line"].isin(SOCIAL)
    return t[["line", "label_ar", "social", "from_waqif_conditions", "from_flexible_share", "total", "multiple"]] \
        .sort_values("total", ascending=False).reset_index(drop=True)


def compass_regions(regions: pd.DataFrame, priorities: dict[str, float] | None = None) -> pd.DataFrame:
    """Per region: social-care share today and after directing the flexible share by the priority weights."""
    priorities = allocate.DEFAULT_PRIORITIES if priorities is None else priorities
    social_weight = sum(v for k, v in priorities.items() if k in SOCIAL) / sum(priorities.values())
    r = regions[["region", "region_ar", "region_en", "waqf_designations", "flexible_share", "social_share"]].copy()
    r["social_share_after"] = r["social_share"] + r["flexible_share"] * social_weight
    r["gain_points"] = r["social_share_after"] - r["social_share"]
    return r.sort_values("gain_points", ascending=False).reset_index(drop=True)
