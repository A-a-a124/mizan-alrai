"""Export precomputed model outputs for the offline decision dashboard (dashboard/data.js).

The dashboard never re-implements the model: every probability it shows is looked up
from this grid, produced by the same risk module the report uses.
"""

from __future__ import annotations

import json

import numpy as np

from . import allocate, clean, config, risk, solutions

INFLATION_GRID = (0.0, 0.01, 0.015, 0.02, 0.025, 0.03, 0.04)
SAMPLE_PATHS = 20


def _grid(series: np.ndarray, shift: float) -> dict:
    paths = risk.stationary_bootstrap(np.asarray(series) + shift / 12, config.N_PATHS, config.SIM_YEARS * 12)
    out = {}
    for rate in config.SPEND_RATES:
        nom = risk.nominal_yearly(paths, rate)
        per_infl = {}
        for infl in INFLATION_GRID:
            real = risk.deflate(nom, infl)
            q = np.quantile(real, [0.10, 0.50, 0.90], axis=0)
            per_infl[f"{infl:.3f}"] = {"p": round(float(np.mean(real[:, -1] >= 100)), 4),
                                       "bands": np.round(q, 2).tolist()}
        # a few of the simulated paths themselves (nominal; the page deflates them), for the path animation
        per_infl["paths"] = np.round(nom[:SAMPLE_PATHS], 1).tolist()
        out[f"{rate:.3f}"] = per_infl
    return out


def _matrix(m) -> dict:
    """Region x masraf counts as a dense grid (rows = regions by size, columns = masarif by national size)."""
    regions = (m.groupby(["region", "region_ar"], as_index=False)["waqf_count"].sum()
                .sort_values("waqf_count", ascending=False))
    masarif = (m.groupby(["masraf", "masraf_ar", "group"], as_index=False)["waqf_count"].sum()
                .sort_values("waqf_count", ascending=False))
    wide = m.pivot(index="region", columns="masraf", values="waqf_count").loc[regions["region"], masarif["masraf"]]
    return {"regions": regions.rename(columns={"region": "key", "region_ar": "ar", "waqf_count": "total"}).to_dict("records"),
            "masarif": masarif.rename(columns={"masraf": "key", "masraf_ar": "ar", "waqf_count": "total"}).to_dict("records"),
            "counts": wide.astype(int).values.tolist()}


def _fund_series(series) -> dict:
    out = {}
    for symbol, g in series.groupby("symbol"):
        paid = g["payout_flag"].values
        out[symbol] = {"m": g["month"].tolist(), "p": np.round(g["price_100"], 2).tolist(),
                       "pay": np.nonzero(paid)[0].tolist(), "est": np.round(g.loc[paid, "payout_est"], 4).tolist()}
    return out


def _shocks(shocks) -> dict:
    out = {}
    for (scenario, strategy), g in shocks.groupby(["scenario", "strategy"], sort=False):
        out.setdefault(scenario, {})[strategy] = {"rate": float(g["rate"].iloc[0]),
                                                  "pay": np.round(g["real_payout"], 3).tolist(),
                                                  "val": np.round(g["real_value"], 2).tolist()}
    return out


def _records(frame, decimals: int) -> list:
    return frame.round(decimals).astype(object).replace({np.nan: None}).to_dict(orient="records")


def export(c: dict, ix: dict, fc: dict, sp: dict, al: dict, res) -> None:
    from .pipeline import SAVE_DECIMALS, SCENARIOS, rounded
    grids = {}
    for key, (label, col, shift) in SCENARIOS.items():
        series = ix["total"]["ret"].values if col == "log_ret_total" else ix["price"]["ret"].values
        grids[key] = {"label": label, "grid": _grid(series, shift)}

    disb = c["disbursements"]
    labels = {code: lab for _, (code, lab, _, _) in clean.MASRAF_MAP.items()}
    groups = {code: grp for _, (code, _, _, grp) in clean.MASRAF_MAP.items()}
    profiles = {"national": allocate.profile_from_counts(disb).round(5).to_dict()}
    region_names = {"national": "المملكة (المزيج الوطني)"}
    for region, g in disb.groupby("region"):
        profiles[region] = allocate.profile_from_counts(disb, region).round(5).to_dict()
        region_names[region] = g["region_ar"].iloc[0]
    profiles["family_mixed"] = {"family": 0.60, "general_charity": 0.40}
    region_names["family_mixed"] = "وقف عائلي مشترك (60% ذرية + 40% أوجه البر)"

    idx = res.tables["composite_index"]
    payload = {
        "generated_from": "scripts/run_analysis.py",
        "rates": [round(r, 3) for r in config.SPEND_RATES],
        "inflation": list(INFLATION_GRID),
        "years": config.SIM_YEARS,
        "scenarios": grids,
        "profiles": profiles,
        "profile_names": region_names,
        "masraf_labels": labels,
        "masraf_groups": groups,
        "priorities": allocate.DEFAULT_PRIORITIES,
        "defaults": {"confidence": config.CONFIDENCE, "inflation": config.INFLATION,
                     "upkeep_share": config.UPKEEP_SHARE, "reserve_share": 0.10, "floor": config.MASRAF_FLOOR,
                     "endowment": 10_000_000},
        "key": rounded(res.key),
        "index": {"month": idx["month"].tolist(), "total": np.round(idx["total_index"], 2).tolist(),
                  "price": np.round(idx["price_index"], 2).tolist(), "n_funds": idx["n_funds"].tolist()},
        "solutions": {name: _records(res.tables[name], SAVE_DECIMALS) for name in
                      ("sustainability_label", "payout_trend", "spending_menu", "spending_menu_yearly",
                       "compass_case", "compass_regions")},
        "explore": {"matrix": _matrix(res.tables["region_masraf_matrix"]),
                    "gaps": _records(res.tables["social_gaps"], SAVE_DECIMALS),
                    "managers": _records(res.tables["manager_ranking"], SAVE_DECIMALS),
                    "fund_series": _fund_series(res.tables["fund_series"]),
                    "social": list(solutions.SOCIAL)},
        "shocks": _shocks(res.tables["shock_tests"]),
        "funds": res.tables["fund_summary"].round(SAVE_DECIMALS).astype(object).replace({np.nan: None}).to_dict(orient="records"),
    }
    config.DASHBOARD.mkdir(parents=True, exist_ok=True)
    with open(config.DASHBOARD / "data.js", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(
        "window.WAQF_DATA = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=float) + ";\n")
