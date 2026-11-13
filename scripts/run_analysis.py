"""Run the whole analysis with one command.

    python scripts/run_analysis.py                      # bundled data -> reproduces the published results
    python scripts/run_analysis.py --prices my.csv --out runs/my_waqf     # same analysis on another file

Writes data_clean/, outputs/tables/, outputs/figures/ and dashboard/data.js (under --out when given).

Input formats
  --prices    CSV with columns: symbol, valuation_date (YYYY-MM-DD), unit_price (> 0). Any frequency;
              the last valuation of each month is used. Needs >= 48 months of index history.
  --universe  optional CSV: symbol, fund_name, manager, fund_type, aum_sar. Without it every fund in
              --prices is treated as an accumulating ("Growth") fund.
  --gasa      optional JSON in the same layout as data_raw/gasa/gasa_open_data_snapshot.json.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from waqf import pipeline  # noqa: E402
from waqf.ingest import IntegrityError, SchemaError  # noqa: E402


def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Mizan Al-Rai: waqf yield forecast, sustainable spending, allocation.")
    ap.add_argument("--prices", type=Path, help="fund price CSV to analyse instead of the bundled Tadawul snapshot")
    ap.add_argument("--universe", type=Path, help="fund description CSV matching --prices (optional)")
    ap.add_argument("--gasa", type=Path, help="GASA open-data snapshot JSON (optional)")
    ap.add_argument("--out", type=Path, help="directory for all outputs (default: the project folder)")
    ap.add_argument("--no-figures", action="store_true", help="skip PNG figures (faster)")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.prices is not None and args.out is None:
        print("error: --prices needs --out, so the published results in this folder are not overwritten",
              file=sys.stderr)
        return 2
    t0 = time.time()
    try:
        res = pipeline.run(figures=not args.no_figures, gasa=args.gasa, prices=args.prices,
                           universe=args.universe, out_dir=args.out)
    except (SchemaError, IntegrityError, FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    k = res.key
    print(f"Done in {time.time() - t0:.1f}s")
    print(f"  cleaning rules applied : {len(res.tables['cleaning_log'])}")
    print(f"  waqf index             : {k['index']['total_ann_return']:.2%}/yr total, "
          f"{k['index']['price_ann_return']:.2%}/yr price-only "
          f"({k['index']['funds_in_index']} funds, {k['index']['start']} to {k['index']['end']})")
    print(f"  12-month forecast      : {k['forecast']['point_pct']:.2%} "
          f"[{k['forecast']['p10_pct']:.2%}, {k['forecast']['p90_pct']:.2%}] ({k['forecast']['model']})")
    print(f"  sustainable spend rate : {k['spending']['rate_base']:.1%} at {k['spending']['confidence']:.0%} "
          f"confidence (stress {k['spending']['rate_stress']:.1%})")
    label = "observed fund payouts " if k["spending"]["observed_payout_is_detected"] else "reference payout rate "
    print(f"  {label} : {k['spending']['observed_payout_rate']:.1%} -> P(preserve) "
          f"{k['spending']['p_preserve_at_observed']:.0%}")
    if args.out is not None:
        print(f"  outputs written to     : {args.out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
