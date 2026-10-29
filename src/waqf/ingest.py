"""Load raw snapshots and verify their integrity checks before anything else runs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from . import config


class IntegrityError(RuntimeError):
    """Raised when a raw snapshot no longer matches its recorded checks."""


@dataclass(frozen=True)
class RawData:
    gasa: dict
    funds: pd.DataFrame
    prices: pd.DataFrame
    manifest: pd.DataFrame


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_gasa(path: Path = config.GASA_SNAPSHOT) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    data.pop("_provenance", None)
    for title, table in data.items():
        if "counts" in table:
            got = sum(int(c[2]) for c in table["counts"])
        else:
            got = len(table["rows"])
        if got != table["n_rows"]:
            raise IntegrityError(f"GASA '{title}': {got} rows != portal n_rows {table['n_rows']}")
    return data


def load_fund_prices(path: Path = config.FUND_PRICES,
                     checksums: Path = config.FUND_CHECKSUMS) -> pd.DataFrame:
    prices = pd.read_csv(path, dtype={"symbol": str}, parse_dates=["valuation_date"])
    expected = json.loads(checksums.read_text(encoding="utf-8"))
    got = (prices.assign(p=(prices["unit_price"] * 10_000).round().astype("int64"))
                 .groupby("symbol")["p"].agg(["size", "sum"]))
    for symbol, (n, total) in expected.items():
        if symbol not in got.index or tuple(got.loc[symbol]) != (n, total):
            raise IntegrityError(f"Fund {symbol}: checksum mismatch")
    return prices


def load_fund_universe(path: Path = config.FUND_UNIVERSE) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"symbol": str})


def load_all() -> RawData:
    """Load every raw source; abort loudly on any integrity failure."""
    gasa = load_gasa()
    prices = load_fund_prices()
    funds = load_fund_universe()
    files = [config.GASA_SNAPSHOT, config.FUND_UNIVERSE, config.FUND_PRICES]
    manifest = pd.DataFrame({
        "file": [str(f.relative_to(config.ROOT)).replace("\\", "/") for f in files],
        "sha256": [sha256(f) for f in files],
        "bytes": [f.stat().st_size for f in files],
    })
    return RawData(gasa=gasa, funds=funds, prices=prices, manifest=manifest)
