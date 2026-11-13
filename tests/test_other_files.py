"""The pipeline must run on files other than the bundled snapshot, and fail clearly on bad ones."""

import json
import subprocess
import sys

import pandas as pd
import pytest

from waqf import config, ingest, pipeline

EXAMPLE = config.ROOT / "examples" / "three_funds_prices.csv"


@pytest.fixture()
def restore_output_dirs():
    saved = (config.DATA_CLEAN, config.FIGURES, config.TABLES, config.DASHBOARD)
    yield
    config.DATA_CLEAN, config.FIGURES, config.TABLES, config.DASHBOARD = saved


def test_runs_on_another_price_file_without_touching_published_outputs(tmp_path, restore_output_dirs):
    published = (config.ROOT / "outputs" / "tables" / "key_numbers.json").read_bytes()
    res = pipeline.run(figures=False, prices=EXAMPLE, out_dir=tmp_path)
    key = json.loads((tmp_path / "outputs" / "tables" / "key_numbers.json").read_text(encoding="utf-8"))
    assert key["index"]["funds_total"] == 3
    assert 0 <= key["spending"]["rate_base"] <= 0.08
    assert key["forecast"]["origins"] > 0
    assert (tmp_path / "dashboard" / "data.js").exists()
    assert (tmp_path / "data_clean" / "fund_prices.csv").exists()
    assert res.key["index"]["funds_total"] == 3
    assert (config.ROOT / "outputs" / "tables" / "key_numbers.json").read_bytes() == published


def test_different_data_gives_different_results(tmp_path, restore_output_dirs):
    other = pipeline.run(figures=False, prices=EXAMPLE, out_dir=tmp_path).key
    bundled = json.loads((config.ROOT / "outputs" / "tables" / "key_numbers.json").read_text(encoding="utf-8"))
    assert other["index"]["total_ann_return"] != bundled["index"]["total_ann_return"]


def test_cli_end_to_end_on_another_file(tmp_path):
    out = tmp_path / "run"
    proc = subprocess.run([sys.executable, "scripts/run_analysis.py", "--prices", str(EXAMPLE),
                           "--out", str(out), "--no-figures"], cwd=config.ROOT, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert "sustainable spend rate" in proc.stdout
    assert (out / "outputs" / "tables" / "spending_frontier_base.csv").exists()


def test_cli_refuses_custom_prices_without_out_dir():
    proc = subprocess.run([sys.executable, "scripts/run_analysis.py", "--prices", str(EXAMPLE)],
                          cwd=config.ROOT, capture_output=True, text=True)
    assert proc.returncode == 2 and "--out" in proc.stderr


def test_missing_column_is_reported(tmp_path):
    bad = tmp_path / "bad.csv"
    pd.DataFrame({"symbol": ["A"], "date": ["2024-01-31"], "unit_price": [10]}).to_csv(bad, index=False)
    with pytest.raises(ingest.SchemaError, match="valuation_date"):
        ingest.read_prices(bad)


@pytest.mark.parametrize("price", ["abc", "-5", "0"])
def test_invalid_price_is_reported(tmp_path, price):
    bad = tmp_path / "bad.csv"
    bad.write_text(f"symbol,valuation_date,unit_price\nA,2024-01-31,10\nA,2024-02-29,{price}\n", encoding="utf-8")
    with pytest.raises(ingest.SchemaError, match="line 3"):
        ingest.read_prices(bad)


def test_too_short_history_gives_clear_error(tmp_path, restore_output_dirs):
    short = tmp_path / "short.csv"
    full = pd.read_csv(EXAMPLE, dtype={"symbol": str})
    full[full["valuation_date"] >= "2025-01-01"].to_csv(short, index=False)
    with pytest.raises(ValueError, match="at least 48"):
        pipeline.run(figures=False, prices=short, out_dir=tmp_path / "o")


def test_cli_reports_bad_file_without_traceback(tmp_path):
    proc = subprocess.run([sys.executable, "scripts/run_analysis.py", "--prices", str(tmp_path / "nope.csv"),
                           "--out", str(tmp_path / "o")], cwd=config.ROOT, capture_output=True, text=True)
    assert proc.returncode == 1 and proc.stderr.startswith("error:") and "Traceback" not in proc.stderr
