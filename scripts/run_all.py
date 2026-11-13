"""Fully automated rebuild: analysis -> tests -> notebook -> report -> site, stopping at the first failure.

    python scripts/run_all.py            # everything
    python scripts/run_all.py --quick    # analysis + tests only (no browser needed)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STEPS = [
    ("analysis", [sys.executable, "scripts/run_analysis.py"], True),
    ("tests", [sys.executable, "-m", "pytest", "-q"], True),
    ("notebook", [sys.executable, "scripts/build_notebook.py"], False),
    ("report", [sys.executable, "scripts/build_report.py"], False),
    ("site", [sys.executable, "scripts/build_site.py"], False),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--quick", action="store_true", help="analysis + tests only")
    args = ap.parse_args()
    results = []
    for name, cmd, in_quick in STEPS:
        if args.quick and not in_quick:
            continue
        t0 = time.time()
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        ok = proc.returncode == 0
        results.append((name, ok, time.time() - t0))
        print(f"[{'ok' if ok else 'FAIL'}] {name:<9} {time.time() - t0:5.1f}s")
        if not ok:
            print((proc.stdout + proc.stderr)[-3000:])
            break
    passed = all(ok for _, ok, _ in results)
    print("ALL STEPS PASSED" if passed else "STOPPED AT FIRST FAILURE")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
