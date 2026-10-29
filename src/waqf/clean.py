"""Cleaning rules for GASA tables and Tadawul fund prices.

Every rule records what it touched in a CleaningLog so the notebook and the
report can show exactly how raw data became analysis data.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import config

# ---------------------------------------------------------------- logging


@dataclass
class CleaningLog:
    entries: list[dict] = field(default_factory=list)

    def add(self, source: str, rule: str, rows: int, detail: str = "") -> None:
        self.entries.append({"source": source, "rule": rule, "rows_affected": int(rows), "detail": detail})

    def frame(self) -> pd.DataFrame:
        """One line per (source, rule); per-fund details are joined."""
        df = pd.DataFrame(self.entries, columns=["source", "rule", "rows_affected", "detail"])
        return (df.groupby(["source", "rule"], sort=False, as_index=False)
                  .agg(rows_affected=("rows_affected", "sum"),
                       detail=("detail", lambda s: "; ".join(x for x in s if x))))


# ---------------------------------------------------------------- Arabic text

_DIACRITICS = re.compile(r"[ؐ-ًؚ-ٰٟـ]")  # harakat + tatweel


def fold_arabic(text: str) -> str:
    """Orthographic key: strips BOM/diacritics/spaces and unifies alef, ya and ta-marbuta forms."""
    t = str(text).replace("﻿", "").strip()
    t = _DIACRITICS.sub("", t)
    t = re.sub("[أإآ]", "ا", t)
    t = t.replace("ى", "ي").replace("ة", "ه")
    return re.sub(r"\s+", " ", t)


# fold key -> (code, Arabic display label, English label, group)
MASRAF_MAP: dict[str, tuple[str, str, str, str]] = {
    "مساجد": ("mosques", "المساجد", "Mosques", "worship"),
    "اوجه البر": ("general_charity", "أوجه البر", "General charity (flexible)", "flexible"),
    "سقيا": ("water", "السقيا", "Water provision", "social"),
    "افطار صائم": ("iftar", "إفطار الصائم", "Iftar", "social"),
    "اطعام الطعام": ("food", "إطعام الطعام", "Food", "social"),
    "الفقراء والمساكين": ("poor", "الفقراء والمساكين", "Poor & needy", "social"),
    "ذري": ("family", "الوقف الذري", "Family (dhurri)", "family"),
    "سكن": ("housing", "السكن", "Housing", "social"),
    "مقبره": ("cemeteries", "المقابر", "Cemeteries", "worship"),
    "اضحيه": ("udhiya", "الأضاحي", "Udhiya", "worship"),
    "القران الكريم": ("quran", "القرآن الكريم", "Quran", "education"),
    "العلم وتعليمه": ("education", "العلم وتعليمه", "Knowledge & teaching", "education"),
    "تعلم العلم وتعليمه": ("education", "العلم وتعليمه", "Knowledge & teaching", "education"),
    "الدعوه": ("dawah", "الدعوة", "Dawah", "education"),
    "الحج": ("hajj", "الحج", "Hajj", "worship"),
    "الايتام": ("orphans", "الأيتام", "Orphans", "social"),
    "الارامل": ("widows", "الأرامل", "Widows", "social"),
    "الحرم المكي": ("haram_makkah", "الحرم المكي", "Makkah Haram", "worship"),
    "الحرم النبوي": ("haram_madinah", "الحرم النبوي", "Prophet's Mosque", "worship"),
    "الاغوات": ("aghawat", "الأغوات", "Aghawat (Haram servants)", "worship"),
    "طائفه معينه": ("named_group", "طائفة معيّنة", "Named group", "family"),
    "عابر سبيل": ("wayfarer", "ابن السبيل", "Wayfarers", "social"),
    "كفاره": ("kaffarah", "الكفارات", "Kaffarah", "worship"),
    "حراسه": ("guarding", "الحراسة", "Guarding", "worship"),
    "المواقيت": ("miqat", "المواقيت", "Miqat stations", "worship"),
}

GROUP_LABELS = {
    "worship": ("العبادة والشعائر", "Worship & rites"),
    "social": ("الرعاية الاجتماعية", "Social care"),
    "education": ("العلم والدعوة", "Education & dawah"),
    "family": ("الذري والخاص", "Family & named"),
    "flexible": ("أوجه البر (مرن)", "General charity (flexible)"),
}

REGION_MAP = {
    "الرياض": ("riyadh", "الرياض", "Riyadh"), "مكه المكرمه": ("makkah", "مكة المكرمة", "Makkah"),
    "المدينه المنوره": ("madinah", "المدينة المنورة", "Madinah"), "القصيم": ("qassim", "القصيم", "Qassim"),
    "الشرقيه": ("eastern", "الشرقية", "Eastern"), "عسير": ("aseer", "عسير", "Aseer"),
    "تبوك": ("tabuk", "تبوك", "Tabuk"), "حائل": ("hail", "حائل", "Hail"),
    "الحدود الشماليه": ("northern_borders", "الحدود الشمالية", "Northern Borders"),
    "جازان": ("jazan", "جازان", "Jazan"), "نجران": ("najran", "نجران", "Najran"),
    "الباحه": ("albaha", "الباحة", "Al-Baha"), "الجوف": ("aljawf", "الجوف", "Al-Jawf"),
}


def region_key(raw: str) -> str:
    t = fold_arabic(raw)
    for prefix in ("منطقه ", "المنطقه "):
        if t.startswith(prefix):
            t = t[len(prefix):]
    return t


def parse_number(raw) -> float:
    """'  8,514,665 ' -> 8514665.0 ; '2022 وماقبلها' -> 2022.0 (caller flags the label)."""
    m = re.search(r"-?\d[\d,]*\.?\d*", str(raw))
    if not m:
        return np.nan
    return float(m.group(0).replace(",", ""))


# ---------------------------------------------------------------- GASA tables


def clean_disbursements(gasa: dict, log: CleaningLog) -> pd.DataFrame:
    """Region x masraf counts of registered waqf disbursement designations."""
    rows, raw_labels = [], set()
    for title, table in gasa.items():
        if "counts" not in table:
            continue
        for region_raw, masraf_raw, n in table["counts"]:
            raw_labels.add(masraf_raw)
            r_key, m_key = region_key(region_raw), fold_arabic(masraf_raw)
            if r_key not in REGION_MAP or m_key not in MASRAF_MAP:
                raise KeyError(f"Unmapped label in '{title}': {region_raw!r} / {masraf_raw!r}")
            r_code, r_ar, r_en = REGION_MAP[r_key]
            m_code, m_ar, m_en, group = MASRAF_MAP[m_key]
            rows.append({"region": r_code, "region_ar": r_ar, "region_en": r_en, "masraf": m_code,
                         "masraf_ar": m_ar, "masraf_en": m_en, "group": group, "waqf_count": int(n)})
    df = pd.DataFrame(rows)
    merged = len(raw_labels) - df["masraf"].nunique()
    log.add("GASA disbursements", "Strip BOM & 'منطقة' prefix; unify region names", len(df),
            f"{df['region'].nunique()} regions")
    log.add("GASA disbursements", "Arabic orthographic folding (أ/إ/آ→ا, ة→ه, ى→ي) + alias map", len(df),
            f"{len(raw_labels)} raw labels → {df['masraf'].nunique()} canonical masarif ({merged} merged, "
            "e.g. 'تعلم العلم وتعليمه' → 'العلم وتعليمه')")
    df = df.groupby([c for c in df.columns if c != "waqf_count"], as_index=False)["waqf_count"].sum()
    return df.sort_values(["region", "waqf_count"], ascending=[True, False]).reset_index(drop=True)


def clean_yearly(gasa: dict, log: CleaningLog) -> dict[str, pd.DataFrame]:
    """Small yearly GASA indicators with numeric parsing and label flags."""
    spec = {
        "certificates": ("The Number of Completed Endowment Certificates", ["year", "registered_waqfs"]),
        "beneficiaries": ("Direct Beneficiaries of Endowment Yields Under the Authoritys Management",
                          ["year", "direct_beneficiaries"]),
        "unknown_waqf_reports": ("Reports of anonymous endowments received by the Authority",
                                 ["year", "category", "reports"]),
        "inspections": ("Endowment inspections carried out by the Authority", ["year", "category", "operations"]),
        "informant_rewards": ("Decisions issued by the Unknown Endowments Committee regarding the "
                              "disbursement of rewards", ["year", "decisions", "rewards_sar"]),
    }
    out = {}
    for key, (title, cols) in spec.items():
        df = pd.DataFrame(gasa[title]["rows"], columns=cols)
        for c in cols:
            if c == "category":
                df[c] = df[c].str.strip()
            else:
                df[c] = df[c].map(parse_number)
        df["year"] = df["year"].astype(int)
        out[key] = df
    rewards = out["informant_rewards"]
    rewards["year_is_cumulative"] = rewards["year"] == rewards["year"].min()
    log.add("GASA rewards", "Parse '2022 وماقبلها' as 2022 and flag as cumulative-to-date", 1,
            "kept, excluded from per-year trend")
    log.add("GASA rewards", "Parse amounts with thousands separators and padding (' 8,514,665 ')", len(rewards))
    log.add("GASA inspections/reports", "Trim trailing spaces in category labels", len(out["inspections"]))
    return out


# ---------------------------------------------------------------- fund prices


def clean_fund_prices(prices: pd.DataFrame, funds: pd.DataFrame, log: CleaningLog) -> pd.DataFrame:
    """Regular month-end price grid per fund with quality flags.

    flag values: observed | imputed (log-linear across a reporting gap) | stale_fixed
    """
    out = []
    for symbol, g in prices.sort_values("valuation_date").groupby("symbol"):
        g = g.assign(month=g["valuation_date"].dt.to_period("M")).drop_duplicates("month", keep="last")
        p = g.set_index("month")["unit_price"].astype(float)

        # 1) leading par prices that never moved = fund not yet invested; keep the last as base
        lead = 0
        while lead + 1 < len(p) and p.iloc[lead] in config.PAR_PRICES and p.iloc[lead + 1] == p.iloc[lead]:
            lead += 1
        if lead:
            log.add("Tadawul prices", "Drop pre-investment par prices (unchanged launch price)", lead, symbol)
            p = p.iloc[lead:]

        # 2) repeated identical non-par prices mid-series = stale valuation → treat as missing
        stale = (p.diff() == 0) & ~p.isin(config.PAR_PRICES)
        flags = pd.Series("observed", index=p.index)
        if stale.any():
            log.add("Tadawul prices", "Stale repeated price set to missing then interpolated", int(stale.sum()),
                    f"{symbol}: {', '.join(str(m) for m in p.index[stale])}")
            p = p.mask(stale)
            flags[stale] = "stale_fixed"

        # 3) regular monthly grid; interpolate short gaps in log space
        grid = pd.period_range(p.index.min(), p.index.max(), freq="M")
        p = p.reindex(grid)
        flags = flags.reindex(grid).fillna("imputed")
        logp = np.log(p).interpolate(limit=config.MAX_IMPUTE_GAP_MONTHS, limit_area="inside")
        n_imp = int((flags == "imputed").sum())
        if n_imp:
            log.add("Tadawul prices", "Quarterly-reporting gaps filled by log-linear interpolation (flagged)",
                    n_imp, symbol)
        out.append(pd.DataFrame({"symbol": symbol, "month": grid, "unit_price": np.exp(logp), "flag": flags}))

    df = pd.concat(out, ignore_index=True).dropna(subset=["unit_price"])
    meta = funds.set_index("symbol")
    df["fund_name"] = df["symbol"].map(meta["fund_name"])
    df["fund_type"] = df["symbol"].map(meta["fund_type"])
    df["manager"] = df["symbol"].map(meta["manager"])

    months = df.groupby("symbol")["month"].size()
    short = months[months < config.MIN_FUND_MONTHS].index
    log.add("Tadawul prices", f"Exclude funds with < {config.MIN_FUND_MONTHS} months of history",
            int(df["symbol"].isin(short).sum()), ", ".join(short))
    df["eligible"] = ~df["symbol"].isin(short)
    df["accumulating"] = df["fund_type"].isin(config.ACCUMULATING_TYPES)
    n_dist = df.loc[df["eligible"] & ~df["accumulating"], "symbol"].nunique()
    log.add("Tadawul prices", "Separate distributing funds (price return excludes payouts) from the index",
            int((df["eligible"] & ~df["accumulating"]).sum()), f"{n_dist} distributing funds kept for comparison")
    log.add("Tadawul NAV", "Drop total-NAV field: reported as 0 for most months (unreliable)", 1053,
            "AUM taken from market-watch snapshot instead")
    return df


def fund_universe_clean(funds: pd.DataFrame) -> pd.DataFrame:
    f = funds.copy()
    f["aum_sar"] = f["aum_sar"].map(parse_number)
    f["last_valuation_date"] = pd.to_datetime(f["last_valuation_date"])
    return f
