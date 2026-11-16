"""Sustainability label, spending menu and masarif compass."""

import numpy as np
import pytest

from waqf import allocate, clean, solutions


@pytest.mark.parametrize("growth,expected", [(0.05, "A"), (0.02, "A"), (0.0199, "B"), (0.0, "B"), (-0.0001, "C"),
                                             (-0.02, "C"), (-0.021, "D"), (-0.05, "D"), (-0.051, "E")])
def test_grade_thresholds(growth, expected):
    assert solutions.grade(growth, inflation=0.02) == expected


def test_grade_never_improves_when_growth_falls():
    order = {g: i for i, g in enumerate(solutions.GRADES)}
    ranks = [order[solutions.grade(x)] for x in np.linspace(0.10, -0.10, 201)]
    assert ranks == sorted(ranks)


def test_label_covers_every_eligible_fund_and_uses_observed_prices_only(raw, cleaned):
    universe = clean.fund_universe_clean(raw.funds)
    label = solutions.sustainability_label(cleaned["rets"], universe)
    eligible = cleaned["rets"].loc[cleaned["rets"]["eligible"], "symbol"].nunique()
    assert len(label) == eligible
    assert set(label["grade"]) <= set(solutions.GRADES)
    # the grade must not depend on the estimated payout sizes
    tampered = cleaned["rets"].assign(payout_est=0.0)
    again = solutions.sustainability_label(tampered, universe)
    assert label.set_index("symbol")["grade"].to_dict() == again.set_index("symbol")["grade"].to_dict()
    assert (label["provisional"] == (label["months"] < solutions.ESTABLISHED_MONTHS)).all()


def test_label_summary_counts_add_up(raw, cleaned):
    label = solutions.sustainability_label(cleaned["rets"], clean.fund_universe_clean(raw.funds))
    s = solutions.label_summary(label)
    assert sum(s[f"count_{g}"] for g in solutions.GRADES) == s["funds_graded"]
    assert s["funds_established"] + s["funds_provisional"] == s["funds_graded"]


def test_payout_paths_constant_return_matches_closed_form():
    """Zero volatility, zero inflation, no smoothing: value follows (g * (1 - rate/4))^(quarters)."""
    monthly = np.full((3, 120), np.log(1.04) / 12)
    pay, val = solutions.payout_paths(monthly, rate=0.02, smooth=False, inflation=0.0)
    expected = 100 * (1.04 ** 0.25 * (1 - 0.02 / 4)) ** 40
    assert val[0, -1] == pytest.approx(expected, rel=1e-9)
    assert pay.shape == (3, 10) and (pay > 0).all()


def test_higher_rate_pays_more_now_and_leaves_less():
    rng = np.random.default_rng(3)
    menu, yearly, breakeven = solutions.spending_menu(rng.normal(0.004, 0.02, 84), {"low": 0.015, "high": 0.04},
                                                      n_paths=1500)
    m = menu.set_index(["option", "years"])
    assert m.loc[("high", 10), "cumulative_real_payout"] > m.loc[("low", 10), "cumulative_real_payout"]
    assert m.loc[("high", 30), "median_real_value"] < m.loc[("low", 30), "median_real_value"]
    assert m.loc[("low", 30), "p_preserve_real"] > m.loc[("high", 30), "p_preserve_real"]
    assert set(breakeven) == {"low"}
    assert len(yearly) == 2 * solutions.SIM_HORIZON_YEARS


def test_smoothing_does_not_change_the_rate_only_the_ride():
    rng = np.random.default_rng(4)
    e = solutions.smoothing_effect(rng.normal(0.004, 0.025, 84), rate=0.02, n_paths=1500)
    assert e["smoothed_payout_volatility"] < e["unsmoothed_payout_volatility"]


def test_compass_case_sums_to_masarif_budget(cleaned):
    profile = allocate.profile_from_counts(cleaned["disb"])
    alloc = allocate.allocate(allocate.Plan(10_000_000, 0.015), profile)
    labels = {code: lab for _, (code, lab, _, _) in clean.MASRAF_MAP.items()}
    alloc["label_ar"] = alloc["line"].map(labels)
    case = solutions.compass_case(alloc)
    masarif = alloc.loc[alloc["kind"] != "waterfall", "amount"].sum()
    assert case["total"].sum() == pytest.approx(masarif)
    assert (case["from_flexible_share"] >= 0).all()
    assert case.loc[case["line"] == "orphans", "total"].iloc[0] > case.loc[case["line"] == "orphans", "from_waqif_conditions"].iloc[0]


def test_compass_regions_gain_is_bounded_by_flexible_share(cleaned):
    regions = solutions.compass_regions(allocate.region_profiles(cleaned["disb"]))
    assert (regions["gain_points"] <= regions["flexible_share"] + 1e-12).all()
    assert (regions["social_share_after"] <= 1 + 1e-12).all()
    assert list(regions["gain_points"]) == sorted(regions["gain_points"], reverse=True)


def test_payout_trend_counts_every_event(cleaned):
    trend = solutions.payout_trend(cleaned["rets"])
    assert trend["events"].sum() == cleaned["rets"]["payout_flag"].sum()
    assert trend["observed_share"].between(0, 1).all()
