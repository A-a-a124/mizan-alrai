"""Masarif gaps, fund managers, per-fund series, shock tests, and the files the dashboard pages need."""

import json
import re

import numpy as np
import pytest

from waqf import clean, config, insights, solutions


@pytest.fixture(scope="module")
def label(raw, cleaned):
    return solutions.sustainability_label(cleaned["rets"], clean.fund_universe_clean(raw.funds))


def test_region_matrix_is_complete_and_keeps_every_count(cleaned):
    disb = cleaned["disb"]
    m = insights.region_matrix(disb)
    assert len(m) == disb["region"].nunique() * disb["masraf"].nunique()
    assert m["waqf_count"].sum() == disb["waqf_count"].sum()
    assert np.allclose(m.groupby("region")["share_in_region"].sum(), 1.0)
    assert (m["absent"] == (m["waqf_count"] == 0)).all()


def test_social_gaps_are_exactly_the_absent_social_pairs(cleaned):
    m = insights.region_matrix(cleaned["disb"])
    gaps = insights.social_gaps(m)
    expected = m[m["absent"] & m["masraf"].isin(solutions.SOCIAL)]
    assert len(gaps) == len(expected)
    present = set(zip(cleaned["disb"]["region"], cleaned["disb"]["masraf"]))
    assert not (set(zip(gaps["region"], gaps["masraf"])) & present)
    summary = insights.gaps_summary(m, gaps)
    assert summary["social_gaps"] == sum(summary[f"regions_without_{s}"] for s in solutions.SOCIAL)


def test_manager_ranking_accounts_for_every_graded_fund(label, cleaned):
    ranking = insights.manager_ranking(label, cleaned["rets"])
    assert ranking["funds"].sum() == len(label)
    assert ranking["manager"].is_unique
    assert list(ranking["rank"]) == list(range(1, len(ranking) + 1))
    assert ranking["avg_grade_score"].is_monotonic_increasing
    assert ranking["payout_regularity"].between(0, 1).all()
    assert np.isclose(ranking["aum_sar"].sum(), label["aum_sar"].sum())


def test_fund_series_starts_at_100_and_marks_the_detected_payouts(cleaned):
    series = insights.fund_series(cleaned["rets"])
    first = series.groupby("symbol")["price_100"].first()
    assert np.allclose(first, 100.0)
    assert (series["drawdown"] <= 1e-12).all()
    eligible = cleaned["rets"][cleaned["rets"]["eligible"]]
    assert series["payout_flag"].sum() == eligible["payout_flag"].sum()


def test_worst_window_finds_the_deepest_fall():
    r = np.array([0.02, 0.01, -0.05, -0.04, 0.03, -0.01, 0.02])
    start, end = insights.worst_window(r)
    assert (start, end) == (2, 4)
    assert np.isclose(r[start:end].sum(), -0.09)


def test_shock_scenarios_differ_only_inside_the_shock():
    rng = np.random.default_rng(1)
    r = rng.normal(0.004, 0.02, 84)
    sc = insights.shock_scenarios(r)
    calm, again = sc["calm"]["returns"], sc["worst_fall_again"]["returns"]
    n = sc["worst_fall_again"]["fall_months"]
    assert len(calm) == insights.SHOCK_YEARS * 12 and np.allclose(calm, r.mean())
    assert np.allclose(again[:12], calm[:12]) and np.allclose(again[12 + n:], calm[12 + n:])
    assert sc["worst_fall_again"]["fall"] < 0


def test_smoothing_softens_the_payout_cut_after_a_fall():
    rng = np.random.default_rng(7)
    r = rng.normal(0.004, 0.025, 84)
    table, summary = insights.shock_table(r, {"rate_balanced": 0.02, "rate_recent_level": 0.04})
    assert set(table["scenario"]) == set(insights.shock_scenarios(r))
    assert summary["worst_fall_again__mizan__worst_cut"] > summary["worst_fall_again__same_rate_unsmoothed__worst_cut"]
    # paying twice the rate leaves less behind in every scenario
    for scenario in table["scenario"].unique():
        assert summary[f"{scenario}__recent_level_unsmoothed__value_10y"] < summary[f"{scenario}__same_rate_unsmoothed__value_10y"]
    assert (table["real_payout"] > 0).all() and (table["real_value"] > 0).all()


def test_legacy_is_the_value_left_times_the_sustainable_rate():
    import pandas as pd
    menu = pd.DataFrame({"option": ["balanced", "recent_level"], "years": [30, 30], "median_real_value": [110.0, 60.0]})
    out = insights.legacy(menu, 0.02)
    assert np.isclose(out["balanced_sustainable_payout_after"], 2.2)
    assert np.isclose(out["balanced_vs_recent_extra_payout_after"], 1.0)


# ---- the pages


def _js_object(path):
    text = path.read_text(encoding="utf-8")
    return json.loads(text[text.index("{"):text.rindex("}") + 1])


def test_map_has_a_shape_for_every_region_in_the_data(cleaned):
    shapes = _js_object(config.ROOT / "dashboard" / "map.js")
    assert set(shapes["regions"]) == set(cleaned["disb"]["region"])
    for shape in shapes["regions"].values():
        assert shape["d"].startswith("M") and 0 <= shape["cx"] <= shapes["width"] and 0 <= shape["cy"] <= shapes["height"]
    assert "OpenStreetMap" in shapes["source"]


def test_dashboard_data_carries_the_explorer_and_the_shocks():
    data = _js_object(config.ROOT / "dashboard" / "data.js")
    matrix = data["explore"]["matrix"]
    assert len(matrix["counts"]) == len(matrix["regions"]) and len(matrix["counts"][0]) == len(matrix["masarif"])
    assert sum(map(sum, matrix["counts"])) == data["key"]["sector"]["waqf_designations"]
    graded = {f["symbol"] for f in data["solutions"]["sustainability_label"]}
    assert graded == set(data["explore"]["fund_series"])
    assert set(data["shocks"]) == {"calm", "worst_fall_again", "worst_fall_twice", "inflation_4pct_5y", "flat_3y"}
    one = data["scenarios"]["base"]["grid"]["0.020"]
    assert len(one["paths"]) == 20 and all(len(p) == data["years"] + 1 and p[0] == 100.0 for p in one["paths"])


@pytest.mark.parametrize("page,scripts", [("dashboard/index.html", ["common.js", "sim.js", "solutions.js"]),
                                          ("dashboard/explore.html", ["map.js", "common.js", "explore.js"]),
                                          ("dashboard/plan.html", ["common.js", "plan.js"]),
                                          ("index.html", ["dashboard/common.js", "dashboard/story.js"])])
def test_every_page_loads_files_that_exist(page, scripts):
    path = config.ROOT / page
    html = path.read_text(encoding="utf-8")
    for src in re.findall(r'(?:src|href)="([^"#?:]+\.(?:js|css))', html):
        assert (path.parent / src).exists(), src
    for name in scripts:
        assert name in html
