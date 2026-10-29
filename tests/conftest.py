import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from waqf import clean, index, ingest  # noqa: E402


@pytest.fixture(scope="session")
def raw():
    return ingest.load_all()


@pytest.fixture(scope="session")
def cleaned(raw):
    log = clean.CleaningLog()
    prices = clean.clean_fund_prices(raw.prices, raw.funds, log)
    rets = index.detect_payouts(index.fund_returns(prices), log)
    return {"log": log, "prices": prices, "rets": rets,
            "disb": clean.clean_disbursements(raw.gasa, log)}
