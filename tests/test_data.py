"""Integrity checks and cleaning rules."""

import json

import numpy as np
import pandas as pd
import pytest

from waqf import clean, config, ingest


def test_raw_snapshots_pass_integrity(raw):
    assert len(raw.gasa) == 18
    assert raw.prices["symbol"].nunique() == 26
    assert len(raw.prices) == 1053


def test_tampered_price_is_detected(tmp_path):
    bad = pd.read_csv(config.FUND_PRICES, dtype={"symbol": str})
    bad.loc[0, "unit_price"] += 0.0001
    path = tmp_path / "prices.csv"
    bad.to_csv(path, index=False)
    with pytest.raises(ingest.IntegrityError):
        ingest.load_fund_prices(path)


def test_tampered_gasa_count_is_detected(tmp_path):
    data = json.loads(config.GASA_SNAPSHOT.read_text(encoding="utf-8"))
    key = next(k for k, v in data.items() if "counts" in v)
    data[key]["counts"][0][2] += 1
    path = tmp_path / "gasa.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ingest.IntegrityError):
        ingest.load_gasa(path)


@pytest.mark.parametrize("a,b", [("أوجه البر", "اوجه البر"), ("الأضحية", "الاضحيه"), ("﻿مساجد ", "مساجد"),
                                 ("إفطار صائم", "افطار صائم")])
def test_fold_arabic_unifies_spellings(a, b):
    assert clean.fold_arabic(a) == clean.fold_arabic(b)


def test_fold_arabic_is_idempotent():
    s = "منطقة المدينة المنورة"
    assert clean.fold_arabic(clean.fold_arabic(s)) == clean.fold_arabic(s)


def test_every_raw_label_is_mapped_and_nothing_lost(raw, cleaned):
    total_raw = sum(c[2] for t in raw.gasa.values() if "counts" in t for c in t["counts"])
    assert cleaned["disb"]["waqf_count"].sum() == total_raw == 15305
    assert cleaned["disb"]["region"].nunique() == 13
    assert "education" in set(cleaned["disb"]["masraf"])        # 'تعلم العلم وتعليمه' merged


@pytest.mark.parametrize("raw_value,expected", [(" 8,514,665 ", 8514665.0), ("2022 وماقبلها", 2022.0), ("x", np.nan)])
def test_parse_number(raw_value, expected):
    got = clean.parse_number(raw_value)
    assert (np.isnan(got) and np.isnan(expected)) or got == expected


def test_price_grid_is_regular_and_positive(cleaned):
    p = cleaned["prices"]
    assert (p["unit_price"] > 0).all()
    for _, g in p.groupby("symbol"):
        ordinals = g["month"].map(lambda m: m.ordinal).sort_values()
        assert (ordinals.diff().dropna() == 1).all()


def test_pre_investment_par_prices_removed(cleaned):
    wareef = cleaned["prices"].query("symbol == '045007'").sort_values("month")
    assert str(wareef["month"].iloc[0]) == "2020-06"     # 2018-10 .. 2020-03 were unchanged 10.0000


def test_short_histories_excluded(cleaned):
    eligible = cleaned["prices"].groupby("symbol")["eligible"].first()
    assert not eligible["011171"]                          # 1 month
    assert eligible["014012"]
