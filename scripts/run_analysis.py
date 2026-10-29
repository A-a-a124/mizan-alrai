"""Rebuild every output from the raw snapshots with one command.

    python scripts/run_analysis.py

Writes data_clean/, outputs/tables/, outputs/figures/ and dashboard/data.js.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from waqf import pipeline  # noqa: E402


def main() -> None:
    t0 = time.time()
    res = pipeline.run()
    k = res.key
    print(f"Done in {time.time() - t0:.1f}s")
    print(f"  cleaning rules applied : {len(res.tables['cleaning_log'])}")
    print(f"  waqf index             : {k['index']['total_ann_return']:.2%}/yr total, "
          f"{k['index']['price_ann_return']:.2%}/yr price-only")
    print(f"  12-month forecast      : {k['forecast']['point_pct']:.2%} "
          f"[{k['forecast']['p10_pct']:.2%}, {k['forecast']['p90_pct']:.2%}] ({k['forecast']['model']})")
    print(f"  sustainable spend rate : {k['spending']['rate_base']:.1%} at {k['spending']['confidence']:.0%} "
          f"confidence (stress {k['spending']['rate_stress']:.1%})")
    print(f"  observed fund payouts  : {k['spending']['observed_payout_rate']:.1%} -> P(preserve) "
          f"{k['spending']['p_preserve_at_observed']:.0%}")


if __name__ == "__main__":
    main()
