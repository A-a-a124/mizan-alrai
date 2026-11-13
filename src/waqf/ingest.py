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


def load_gasa(path: Path | None = None) -> dict:
    path = Path(path) if path is not None else config.GASA_SNAPSHOT
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


PRICE_COLUMNS = ("symbol", "valuation_date", "unit_price")
UNIVERSE_COLUMNS = ("symbol", "fund_name", "manager", "fund_type", "aum_sar")


class SchemaError(ValueError):
    """Raised when an input file does not have the documented columns or value types."""


def read_prices(path: Path) -> pd.DataFrame:
    """Read and validate a fund price file: symbol, valuation_date (ISO), unit_price (> 0)."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Price file not found: {path}")
    prices = pd.read_csv(path, dtype={"symbol": str})
    missing = [c for c in PRICE_COLUMNS if c not in prices.columns]
    if missing:
        raise SchemaError(f"{path.name}: missing column(s) {missing}; required {list(PRICE_COLUMNS)}")
    prices = prices[list(PRICE_COLUMNS)].copy()
    prices["valuation_date"] = pd.to_datetime(prices["valuation_date"], errors="coerce")
    prices["unit_price"] = pd.to_numeric(prices["unit_price"], errors="coerce")
    bad = (prices["valuation_date"].isna() | prices["unit_price"].isna() | (prices["unit_price"] <= 0)
           | prices["symbol"].isna())
    if bad.any():
        raise SchemaError(f"{path.name}: {int(bad.sum())} row(s) with an invalid date, symbol or "
                          f"non-positive price (first at line {int(bad.idxmax()) + 2})")
    if prices.empty:
        raise SchemaError(f"{path.name}: no rows")
    return prices


def default_universe(prices: pd.DataFrame) -> pd.DataFrame:
    """Minimal fund table when only prices are supplied: every fund is treated as accumulating."""
    symbols = sorted(prices["symbol"].unique())
    last = prices.sort_values("valuation_date").groupby("symbol").tail(1).set_index("symbol")
    return pd.DataFrame({"symbol": symbols, "fund_name": symbols, "manager": symbols,
                         "shariah": "", "fund_type": "Growth",
                         "last_unit_price": [last.loc[s, "unit_price"] for s in symbols],
                         "last_valuation_date": [last.loc[s, "valuation_date"].date().isoformat() for s in symbols],
                         "aum_sar": ""})


def load_fund_prices(path: Path | None = None, checksums: Path | None = None) -> pd.DataFrame:
    """Bundled snapshot: validated against its checksums. Any other file: schema-validated only."""
    path = Path(path) if path is not None else config.FUND_PRICES
    prices = read_prices(path)
    if checksums is None:
        if path.resolve() != config.FUND_PRICES.resolve():
            return prices
        checksums = config.FUND_CHECKSUMS
    expected = json.loads(Path(checksums).read_text(encoding="utf-8"))
    got = (prices.assign(p=(prices["unit_price"] * 10_000).round().astype("int64"))
                 .groupby("symbol")["p"].agg(["size", "sum"]))
    for symbol, (n, total) in expected.items():
        if symbol not in got.index or tuple(got.loc[symbol]) != (n, total):
            raise IntegrityError(f"Fund {symbol}: checksum mismatch")
    return prices


def load_fund_universe(path: Path | None = None) -> pd.DataFrame:
    path = Path(path) if path is not None else config.FUND_UNIVERSE
    funds = pd.read_csv(path, dtype={"symbol": str})
    missing = [c for c in UNIVERSE_COLUMNS if c not in funds.columns]
    if missing:
        raise SchemaError(f"{path.name}: missing column(s) {missing}; required {list(UNIVERSE_COLUMNS)}")
    return funds


def _display_path(f: Path) -> str:
    try:
        return f.resolve().relative_to(config.ROOT).as_posix()
    except ValueError:
        return f.name


def load_all(gasa: Path | None = None, prices: Path | None = None, universe: Path | None = None) -> RawData:
    """Load every raw source; abort loudly on any integrity or schema failure.

    With no arguments the bundled snapshots are used. Passing ``prices`` runs the same analysis on
    another fund price file; its ``universe`` is optional (a minimal one is derived from the prices).
    """
    gasa_path = Path(gasa) if gasa is not None else config.GASA_SNAPSHOT
    prices_path = Path(prices) if prices is not None else config.FUND_PRICES
    gasa = load_gasa(gasa_path)
    prices = load_fund_prices(prices_path)
    custom_prices = prices_path.resolve() != config.FUND_PRICES.resolve()
    if universe is not None:
        universe_path = Path(universe)
        funds = load_fund_universe(universe_path)
    elif custom_prices:
        universe_path = None
        funds = default_universe(prices)
    else:
        universe_path = config.FUND_UNIVERSE
        funds = load_fund_universe(universe_path)
    unknown = sorted(set(prices["symbol"]) - set(funds["symbol"]))
    if unknown:
        raise SchemaError(f"Price file has symbol(s) missing from the fund table: {unknown[:5]}")
    files = [f for f in (gasa_path, universe_path, prices_path) if f is not None]
    manifest = pd.DataFrame({
        "file": [_display_path(f) for f in files],
        "sha256": [sha256(f) for f in files],
        "bytes": [f.stat().st_size for f in files],
    })
    return RawData(gasa=gasa, funds=funds, prices=prices, manifest=manifest)
