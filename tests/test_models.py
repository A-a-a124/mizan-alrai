"""Index, forecast, risk and allocation behaviour."""

import numpy as np
import pandas as pd
import pytest

from waqf import allocate, config, forecast, index, risk


def test_payout_detection_finds_alinma_july_pattern(cleaned):
    ev = cleaned["rets"].query("payout_flag")
    july_2025 = set(ev.loc[ev["month"].astype(str) == "2025-07", "symbol"])
    assert {"045007", "045008", "045009", "045010", "045011"} <= july_2025


def test_total_return_index_never_below_price_index(cleaned):
    price = index.composite_index(cleaned["rets"], "log_ret")["index"]
    total = index.composite_index(cleaned["rets"], "log_ret_total")["index"]
    assert (total >= price - 1e-9).all()


def test_backtest_has_no_look_ahead():
    """A forecast made at origin t must not change when data after t changes."""
    rng = np.random.default_rng(0)
    r = pd.Series(rng.normal(0.004, 0.02, 72), index=pd.period_range("2020-01", periods=72, freq="M"))
    bt1 = forecast.backtest(r)
    r2 = r.copy()
    r2.iloc[-6:] += 0.5                                     # shock only the last 6 months
    bt2 = forecast.backtest(r2)
    early = bt1["origin"] <= r.index[-19]                   # origins whose training ends before the shock
    pd.testing.assert_series_equal(bt1.loc[early, "forecast"].reset_index(drop=True),
                                   bt2.loc[early, "forecast"].reset_index(drop=True))


def test_scores_rank_by_mae():
    rng = np.random.default_rng(1)
    r = pd.Series(rng.normal(0.005, 0.02, 80), index=pd.period_range("2019-01", periods=80, freq="M"))
    s = forecast.score(forecast.backtest(r))
    assert list(s["mae"]) == sorted(s["mae"])
    assert s.loc["zero_return", "skill_vs_zero"] == 0


def test_bootstrap_is_reproducible_and_resamples_history():
    r = np.linspace(-0.05, 0.05, 50)
    a = risk.stationary_bootstrap(r, 200, 24)
    b = risk.stationary_bootstrap(r, 200, 24)
    np.testing.assert_array_equal(a, b)
    assert set(np.round(a.ravel(), 12)) <= set(np.round(r, 12))


def test_frontier_probability_falls_as_spending_rises():
    rng = np.random.default_rng(2)
    f = risk.spending_frontier(rng.normal(0.004, 0.02, 90), n_paths=2000)
    assert (np.diff(f["p_preserve_real"]) <= 1e-12).all()


def test_zero_volatility_sanity():
    """With a constant 3% real return and no spending, real value must grow ~ (1.03)^10."""
    monthly = np.full(60, np.log(1.03 * 1.02) / 12)
    f = risk.spending_frontier(monthly, rates=(0.0,), n_paths=50, inflation=0.02)
    assert f.loc[0, "median_real_final"] == pytest.approx(100 * 1.03 ** 10, rel=1e-6)


def test_sustainable_rate_respects_confidence():
    f = pd.DataFrame({"rate": [0.0, 0.01, 0.02], "p_preserve_real": [0.9, 0.65, 0.4]})
    assert risk.sustainable_rate(f, 0.6) == 0.01
    assert risk.sustainable_rate(f, 0.95) == 0.0


@pytest.mark.parametrize("rate", [0.0, 0.015, 0.05])
def test_allocation_invariants(cleaned, rate):
    profile = allocate.profile_from_counts(cleaned["disb"])
    plan = allocate.Plan(endowment_value=10_000_000, spend_rate=rate)
    a = allocate.allocate(plan, profile)
    budget = 10_000_000 * rate
    assert a["amount"].sum() == pytest.approx(budget)
    assert (a["amount"] >= 0).all()
    if budget:
        assert a.loc[a["line"] == "upkeep", "amount"].iloc[0] == pytest.approx(budget * config.UPKEEP_SHARE)
        masarif = budget - a.loc[a["kind"] == "waterfall", "amount"].sum()
        flex = a[a["kind"] == "flexible"]["amount"]
        assert (flex >= config.MASRAF_FLOOR * masarif - 1e-9).all()


def test_reserve_stops_when_target_met(cleaned):
    profile = allocate.profile_from_counts(cleaned["disb"])
    full = allocate.Plan(endowment_value=1_000_000, spend_rate=0.02, reserve_balance=1e9)
    a = allocate.allocate(full, profile)
    assert a.loc[a["line"] == "reserve", "amount"].iloc[0] == 0


def test_waqif_conditions_are_never_redistributed(cleaned):
    profile = allocate.profile_from_counts(cleaned["disb"])
    a = allocate.allocate(allocate.Plan(10_000_000, 0.02), profile)
    masarif = a.loc[a["kind"] != "waterfall", "amount"].sum()
    fixed = a[a["kind"] == "waqif_condition"].set_index("line")["amount"] / masarif
    expected = profile.drop(allocate.FLEXIBLE)
    pd.testing.assert_series_equal(fixed.sort_index(), expected.reindex(fixed.index).sort_index(),
                                   check_names=False, atol=1e-12)
