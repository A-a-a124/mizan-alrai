"""Export precomputed model outputs for the offline decision dashboard (dashboard/data.js).

The dashboard never re-implements the model: every probability it shows is looked up
from this grid, produced by the same risk module the report uses.
"""

from __future__ import annotations

import json

import numpy as np

from . import allocate, clean, config, risk

INFLATION_GRID = (0.0, 0.01, 0.015, 0.02, 0.025, 0.03, 0.04)


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
        out[f"{rate:.3f}"] = per_infl
    return out


def export(c: dict, ix: dict, fc: dict, sp: dict, al: dict, res) -> None:
    from .pipeline import SCENARIOS
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
        "key": res.key,
        "index": {"month": idx["month"].tolist(), "total": np.round(idx["total_index"], 2).tolist(),
                  "price": np.round(idx["price_index"], 2).tolist(), "n_funds": idx["n_funds"].tolist()},
        "funds": res.tables["fund_summary"].replace({np.nan: None}).to_dict(orient="records"),
    }
    config.DASHBOARD.mkdir(parents=True, exist_ok=True)
    (config.DASHBOARD / "data.js").write_text(
        "window.WAQF_DATA = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":"), default=float) + ";\n",
        encoding="utf-8")
