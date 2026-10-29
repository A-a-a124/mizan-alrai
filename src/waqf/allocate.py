"""Turn a sustainable spending rate into a masarif allocation.

Waterfall (classical waqf practice — عمارة الوقف مقدَّمة على الصرف على المستحقين):
  1. upkeep of the endowed asset
  2. stability reserve (until it holds one year of planned distribution)
  3. masarif: waqif-conditioned shares are fixed; the flexible share ("أوجه البر")
     is spread over priority masarif by transparent weights, each above a floor.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import config

FLEXIBLE = "general_charity"

# default priorities for the flexible share: recurring human needs first
DEFAULT_PRIORITIES = {
    "poor": 3.0, "orphans": 3.0, "widows": 2.5, "food": 2.0, "housing": 2.0,
    "education": 2.0, "quran": 1.5, "water": 1.5, "mosques": 1.0,
}


@dataclass(frozen=True)
class Plan:
    endowment_value: float
    spend_rate: float
    reserve_balance: float = 0.0
    upkeep_share: float = config.UPKEEP_SHARE
    reserve_share: float = 0.10
    floor: float = config.MASRAF_FLOOR


def profile_from_counts(disb: pd.DataFrame, region: str | None = None) -> pd.Series:
    """Waqif-condition mix (share of waqf designations per masraf), national or for one region."""
    d = disb if region is None else disb[disb["region"] == region]
    s = d.groupby("masraf")["waqf_count"].sum()
    return (s / s.sum()).sort_values(ascending=False)


def split_flexible(amount: float, priorities: dict[str, float], floor_amount: float) -> pd.Series:
    """Proportional to priority weights with a floor; sums exactly to amount."""
    w = pd.Series(priorities, dtype=float)
    w = w[w > 0]
    if amount <= 0 or w.empty:
        return pd.Series(0.0, index=w.index)
    base = min(floor_amount, amount / len(w))
    rest = amount - base * len(w)
    return base + rest * w / w.sum()


def allocate(plan: Plan, profile: pd.Series, priorities: dict[str, float] | None = None) -> pd.DataFrame:
    priorities = DEFAULT_PRIORITIES if priorities is None else priorities
    budget = plan.endowment_value * plan.spend_rate
    upkeep = budget * plan.upkeep_share
    reserve_target = budget * config.RESERVE_TARGET_YEARS
    reserve = min(budget * plan.reserve_share, max(0.0, reserve_target - plan.reserve_balance))
    masarif_total = budget - upkeep - reserve

    profile = profile / profile.sum()
    fixed = profile.drop(FLEXIBLE, errors="ignore") * masarif_total
    flexible_amount = float(profile.get(FLEXIBLE, 0.0) * masarif_total)
    flex = split_flexible(flexible_amount, priorities, plan.floor * masarif_total)

    lines = [{"line": "upkeep", "kind": "waterfall", "amount": upkeep},
             {"line": "reserve", "kind": "waterfall", "amount": reserve}]
    lines += [{"line": m, "kind": "waqif_condition", "amount": a} for m, a in fixed.items() if a > 0]
    lines += [{"line": m, "kind": "flexible", "amount": a} for m, a in flex.items() if a > 0]
    out = pd.DataFrame(lines)
    out = out.groupby(["line", "kind"], as_index=False, sort=False)["amount"].sum()
    out["share_of_budget"] = out["amount"] / budget if budget else 0.0
    return out


def region_profiles(disb: pd.DataFrame) -> pd.DataFrame:
    """Per region: waqf designations, flexible share and concentration (HHI)."""
    rows = []
    for region, g in disb.groupby("region"):
        share = g.set_index("masraf")["waqf_count"] / g["waqf_count"].sum()
        top = share.idxmax()
        rows.append({
            "region": region,
            "region_ar": g["region_ar"].iloc[0],
            "region_en": g["region_en"].iloc[0],
            "waqf_designations": int(g["waqf_count"].sum()),
            "masarif_count": int(g["masraf"].nunique()),
            "flexible_share": float(share.get(FLEXIBLE, 0.0)),
            "social_share": float(g.loc[g["group"] == "social", "waqf_count"].sum() / g["waqf_count"].sum()),
            "hhi": float((share ** 2).sum()),
            "top_masraf": top,
            "top_share": float(share.max()),
        })
    return pd.DataFrame(rows).sort_values("waqf_designations", ascending=False).reset_index(drop=True)
