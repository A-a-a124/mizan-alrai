"""Verify that a fresh run reproduced the committed results.

    python scripts/run_analysis.py && python scripts/check_reproduced.py

Compares every regenerated table, clean data file and the dashboard data against the versions
stored in git (HEAD). Text is compared exactly after normalising line ends; on a mismatch the
differing values are listed.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WATCHED = ("outputs/tables", "data_clean", "dashboard/data.js")
PREFIX = "window.WAQF_DATA = "


def committed(path: str) -> str:
    raw = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=ROOT, capture_output=True, check=True).stdout
    return raw.decode("utf-8").replace("\r\n", "\n")


def walk(prefix: str, a, b, out: list) -> None:
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            walk(f"{prefix}/{k}", a.get(k), b.get(k), out)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            walk(f"{prefix}/{i}", x, y, out)
    elif a != b:
        out.append(f"    {prefix}: committed={a!r} now={b!r}")


def explain(path: str, old: str, new: str) -> list:
    out: list = []
    if path.endswith(".js"):
        walk("", json.loads(old[len(PREFIX):].rstrip().rstrip(";")), json.loads(new[len(PREFIX):].rstrip().rstrip(";")), out)
    elif path.endswith(".json"):
        walk("", json.loads(old), json.loads(new), out)
    else:
        lo, ln = old.splitlines(), new.splitlines()
        out += [f"    line {i + 1}: committed={x!r} now={y!r}" for i, (x, y) in enumerate(zip(lo, ln)) if x != y]
        if len(lo) != len(ln):
            out.append(f"    line count {len(lo)} -> {len(ln)}")
    return out


def main() -> int:
    files = subprocess.run(["git", "ls-files", *WATCHED], cwd=ROOT, capture_output=True, text=True,
                           check=True).stdout.split()
    bad = 0
    for path in files:
        new = (ROOT / path).read_bytes().decode("utf-8").replace("\r\n", "\n")
        old = committed(path)
        if new != old:
            bad += 1
            diffs = explain(path, old, new)
            print(f"DIFFERENT {path} ({len(diffs)} value(s))")
            print("\n".join(diffs[:15]))
    print(f"{len(files) - bad}/{len(files)} files reproduced exactly")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
