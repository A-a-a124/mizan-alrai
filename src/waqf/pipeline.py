"""End-to-end pipeline. Steps are importable so the notebook narrates the same code."""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import allocate, clean, config, forecast, index, ingest, risk, viz

SCENARIOS = {
    "base": ("العائد الكلي المقدَّر (الأساس)", "log_ret_total", 0.0),
    "stress": ("ضغط: العائد الكلي − 1% سنوياً", "log_ret_total", config.STRESS_SHIFT),
    "price_only": ("عائد السعر فقط (متحفظ)", "log_ret", 0.0),
}
CASE_ENDOWMENT = 10_000_000.0


@dataclass
class Results:
    log: clean.CleaningLog = field(default_factory=clean.CleaningLog)
    tables: dict = field(default_factory=dict)
    key: dict = field(default_factory=dict)


def step_ingest(res: Results) -> ingest.RawData:
    raw = ingest.load_all()
    res.tables["data_manifest"] = raw.manifest
    return raw


def step_clean(raw: ingest.RawData, res: Results) -> dict:
    disb = clean.clean_disbursements(raw.gasa, res.log)
    yearly = clean.clean_yearly(raw.gasa, res.log)
    prices = clean.clean_fund_prices(raw.prices, raw.funds, res.log)
    universe = clean.fund_universe_clean(raw.funds)
    rets = index.detect_payouts(index.fund_returns(prices), res.log)
    out = {"disbursements": disb, "fund_prices": prices, "fund_returns": rets, "fund_universe": universe,
           **{f"gasa_{k}": v for k, v in yearly.items()}}
    config.DATA_CLEAN.mkdir(parents=True, exist_ok=True)
    for name, df in out.items():
        df.to_csv(config.DATA_CLEAN / f"{name}.csv", index=False, encoding="utf-8-sig")
    res.tables["cleaning_log"] = res.log.frame()
    return out


def step_sector(c: dict, res: Results) -> dict:
    disb = c["disbursements"]
    nat = (disb.groupby(["masraf", "masraf_ar", "masraf_en", "group"], as_index=False)["waqf_count"].sum()
               .assign(share=lambda d: d["waqf_count"] / d["waqf_count"].sum())
               .sort_values("share", ascending=False))
    regions = allocate.region_profiles(disb)
    certs = c["gasa_certificates"]
    cagr = (certs["registered_waqfs"].iloc[-1] / certs["registered_waqfs"].iloc[0]) ** (1 / (len(certs) - 1)) - 1
    ben = c["gasa_beneficiaries"]
    sh = nat.set_index("masraf")["share"]
    res.tables.update(masarif_national=nat, region_profiles=regions)
    res.key["sector"] = {
        "waqf_designations": int(disb["waqf_count"].sum()), "regions": int(disb["region"].nunique()),
        "masarif": int(disb["masraf"].nunique()), "mosques_share": float(sh["mosques"]),
        "flexible_share": float(sh["general_charity"]), "orphans_share": float(sh["orphans"]),
        "widows_share": float(sh["widows"]),
        "social_share": float(nat.loc[nat["group"] == "social", "share"].sum()),
        "certificates_2019": int(certs["registered_waqfs"].iloc[0]),
        "certificates_2025": int(certs["registered_waqfs"].iloc[-1]), "certificates_cagr": float(cagr),
        "beneficiaries_2023": int(ben["direct_beneficiaries"].iloc[0]),
        "beneficiaries_2025": int(ben["direct_beneficiaries"].iloc[-1]),
        "most_concentrated_region": regions.sort_values("hhi").iloc[-1]["region_ar"],
        "most_concentrated_top_share": float(regions.sort_values("hhi").iloc[-1]["top_share"]),
    }
    return {"national": nat, "regions": regions, "certs": certs}


def step_index(c: dict, res: Results) -> dict:
    rets = c["fund_returns"]
    price = index.composite_index(rets, "log_ret")
    total = index.composite_index(rets, "log_ret_total")
    stats = {"price": index.summary_stats(price["ret"]), "total": index.summary_stats(total["ret"])}
    payouts = index.payout_rates(rets)
    per_fund = []
    for sym, g in rets.groupby("symbol"):
        st = index.summary_stats(g["log_ret"])
        per_fund.append({"symbol": sym, "fund_name": g["fund_name"].iloc[0], "manager": g["manager"].iloc[0],
                         "fund_type": g["fund_type"].iloc[0], "in_index": bool(g["eligible"].iloc[0]
                                                                              and g["accumulating"].iloc[0]),
                         "months": st["months"], "price_ann_return": st["ann_return"], "ann_vol": st["ann_vol"],
                         "total_ann_return_est": index.summary_stats(g["log_ret_total"])["ann_return"],
                         "payout_events": int(g["payout_flag"].sum())})
    fund_summary = pd.DataFrame(per_fund).merge(
        c["fund_universe"][["symbol", "aum_sar"]], on="symbol", how="left").sort_values("aum_sar", ascending=False)
    idx_tbl = pd.DataFrame({"month": price.index.astype(str), "n_funds": price["n_funds"],
                            "price_index": price["index"].values, "total_index": total["index"].values,
                            "price_ret": price["ret"].values, "total_ret": total["ret"].values})
    res.tables.update(composite_index=idx_tbl, fund_summary=fund_summary, payouts=payouts)
    recent = payouts.sort_values("year").groupby("symbol").tail(1)
    res.key["index"] = {**{f"{k}_{m}": v for k, s in stats.items() for m, v in s.items()},
                        "funds_total": int(c["fund_universe"].shape[0]),
                        "funds_in_index": int(fund_summary["in_index"].sum()),
                        "aum_total_sar": float(c["fund_universe"]["aum_sar"].sum()),
                        "start": str(price.index[0]), "end": str(price.index[-1]),
                        "payout_events": int(rets["payout_flag"].sum()),
                        "payout_median_recent": float(recent["payout_pct"].median()),
                        "payout_min_recent": float(recent["payout_pct"].min()),
                        "payout_max_recent": float(recent["payout_pct"].max())}
    return {"price": price, "total": total, "stats": stats, "payouts": payouts}


def step_forecast(ix: dict, res: Results) -> dict:
    series = ix["total"]["ret"]
    bt = forecast.backtest(series)
    scores = forecast.score(bt)
    best = scores.index[0]
    fc = forecast.final_forecast(series, bt, best)
    dist = risk.horizon_distribution(series.values)
    fc["bootstrap_p_loss"] = float(np.mean(dist < 0))
    fc["bootstrap_median_pct"] = float(np.median(dist))
    res.tables.update(backtest_detail=bt, backtest_scores=scores.reset_index())
    res.key["forecast"] = {**fc, "best_model_label": forecast.MODEL_LABELS_AR[best],
                           "skill_vs_zero": float(scores.loc[best, "skill_vs_zero"]),
                           "mae": float(scores.loc[best, "mae"]), "origins": int(scores.loc[best, "origins"])}
    return {"backtest": bt, "scores": scores, "forecast": fc, "dist": dist}


def step_spending(ix: dict, res: Results) -> dict:
    frontiers, rates = {}, {}
    for key, (_, col, shift) in SCENARIOS.items():
        series = ix["total"]["ret"].values if col == "log_ret_total" else ix["price"]["ret"].values
        f = risk.spending_frontier(series, annual_shift=shift)
        frontiers[key] = f
        rates[key] = risk.sustainable_rate(f)
        res.tables[f"spending_frontier_{key}"] = f
    base = ix["total"]["ret"].values
    paths = risk.stationary_bootstrap(base, config.N_PATHS, config.SIM_YEARS * 12)
    observed = round(res.key["index"]["payout_median_recent"] * 200) / 200
    bands = {"sustainable": risk.real_value_bands(paths, rates["base"]),
             "observed": risk.real_value_bands(paths, observed)}
    fb = frontiers["base"].set_index("rate")
    res.key["spending"] = {
        "confidence": config.CONFIDENCE, "inflation": config.INFLATION, "years": config.SIM_YEARS,
        "paths": config.N_PATHS, **{f"rate_{k}": v for k, v in rates.items()},
        "rate_base_at_50": risk.sustainable_rate(frontiers["base"], 0.50),
        "rate_base_at_75": risk.sustainable_rate(frontiers["base"], 0.75),
        "observed_payout_rate": observed,
        "p_preserve_at_observed": float(fb.loc[np.isclose(fb.index, observed), "p_preserve_real"].iloc[0]),
        "median_real_final_sustainable": float(bands["sustainable"][1][-1]),
        "median_real_final_observed": float(bands["observed"][1][-1]),
    }
    return {"frontiers": frontiers, "rates": rates, "bands": bands, "observed": observed}


def step_allocate(c: dict, sp: dict, res: Results) -> dict:
    profile = allocate.profile_from_counts(c["disbursements"])
    plan = allocate.Plan(endowment_value=CASE_ENDOWMENT, spend_rate=sp["rates"]["base"])
    alloc = allocate.allocate(plan, profile)
    labels = {code: lab for _, (code, lab, _, _) in clean.MASRAF_MAP.items()}
    labels.update(upkeep="عمارة الوقف وصيانته", reserve="احتياطي استقرار الصرف")
    alloc["label_ar"] = alloc["line"].map(labels)
    res.tables["allocation_case"] = alloc
    budget = CASE_ENDOWMENT * sp["rates"]["base"]
    social = alloc[alloc["line"].isin(["poor", "orphans", "widows", "food", "housing"])]["amount"].sum()
    social_fixed = profile.reindex(["poor", "orphans", "widows", "food", "housing"]).fillna(0).sum()
    masarif_total = budget - alloc.loc[alloc["kind"] == "waterfall", "amount"].sum()
    res.key["allocation"] = {"endowment": CASE_ENDOWMENT, "budget": budget,
                             "upkeep": float(alloc.loc[alloc["line"] == "upkeep", "amount"].sum()),
                             "reserve": float(alloc.loc[alloc["line"] == "reserve", "amount"].sum()),
                             "social_share_after": float(social / masarif_total),
                             "social_share_before": float(social_fixed)}
    return {"allocation": alloc, "labels": labels, "profile": profile, "budget": budget}


def step_figures(c: dict, sec: dict, ix: dict, fc: dict, sp: dict, al: dict) -> list:
    F = config.FIGURES
    labels = {k: v[0] for k, v in SCENARIOS.items()}
    obs = sp["observed"]
    return [
        viz.fig_sector_growth(sec["certs"], F / "fig01_sector_growth.png"),
        viz.fig_masarif_national(sec["national"], F / "fig02_masarif_national.png"),
        viz.fig_region_heatmap(c["disbursements"], clean.GROUP_LABELS, F / "fig03_region_heatmap.png"),
        viz.fig_index(ix["price"], ix["total"], ix["stats"], F / "fig04_waqf_index.png"),
        viz.fig_payouts_vs_sustainable(ix["payouts"], sp["rates"]["base"], F / "fig05_payouts_vs_sustainable.png"),
        viz.fig_backtest(fc["scores"], F / "fig06_backtest.png"),
        viz.fig_forecast_fan(ix["total"], fc["forecast"], fc["dist"], F / "fig07_forecast.png"),
        viz.fig_frontier(sp["frontiers"], labels, config.CONFIDENCE, sp["rates"], F / "fig08_spending_frontier.png"),
        viz.fig_real_paths(sp["bands"], {"sustainable": f"صرف مستدام {viz.pct(sp['rates']['base'])}",
                                         "observed": f"صرف بمعدل الصناديق الحالي {viz.pct(obs)}"},
                           F / "fig09_real_value_paths.png"),
        viz.fig_allocation(al["allocation"], al["labels"], {c: g for _, (c, _, _, g) in clean.MASRAF_MAP.items()},
                           al["budget"], CASE_ENDOWMENT, F / "fig10_allocation.png"),
    ]


def write_outputs(res: Results) -> None:
    config.TABLES.mkdir(parents=True, exist_ok=True)
    for name, df in res.tables.items():
        df.to_csv(config.TABLES / f"{name}.csv", index=False, encoding="utf-8-sig")
    (config.TABLES / "key_numbers.json").write_text(
        json.dumps(res.key, ensure_ascii=False, indent=2, default=float), encoding="utf-8")


def run(figures: bool = True) -> Results:
    res = Results()
    raw = step_ingest(res)
    c = step_clean(raw, res)
    sec = step_sector(c, res)
    ix = step_index(c, res)
    fc = step_forecast(ix, res)
    sp = step_spending(ix, res)
    al = step_allocate(c, sp, res)
    write_outputs(res)
    if figures:
        step_figures(c, sec, ix, fc, sp, al)
    from . import export_dashboard
    export_dashboard.export(c, ix, fc, sp, al, res)
    return res
