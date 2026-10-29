"""Publication-quality static figures (Arabic, RTL-aware) for the notebook and report.

Palette: validated reference palette (dataviz skill) — categorical order blue, orange,
aqua; sequential single-hue blue; text in ink tokens, never series colours.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from .config import PROJECT_AR, PROJECT_EN  # noqa: E402

BY = f"تحليل «{PROJECT_AR}»"

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
INK_3 = "#8a8983"
GRID = "#e6e5e0"
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"
CRITICAL = "#d03b3b"
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

_PREFERRED_FONTS = ("Segoe UI", "Noto Sans Arabic", "Noto Naskh Arabic", "DejaVu Sans")
_INSTALLED = {f.name for f in matplotlib.font_manager.fontManager.ttflist}
_FONTS = [f for f in _PREFERRED_FONTS if f in _INSTALLED] or ["DejaVu Sans"]   # only existing fonts: no warnings

plt.rcParams.update({
    "font.family": _FONTS, "font.size": 10.5, "axes.edgecolor": GRID, "axes.labelcolor": INK_2,
    "xtick.color": INK_2, "ytick.color": INK_2, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.8, "axes.axisbelow": True, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "lines.linewidth": 2.0, "legend.frameon": False, "ytick.major.size": 0, "xtick.major.size": 0,
})


def ar(text: str) -> str:
    """Arabic label hook (shaping, when needed, happens once in Text.set_text below)."""
    return str(text)


def _enable_rtl_fallback() -> None:
    """Matplotlib >= 3.11 lays out Arabic natively. Older versions (e.g. Google Colab) draw it
    reversed and unjoined, so shape every Arabic string once with arabic_reshaper + python-bidi."""
    major, minor = (int(x) for x in matplotlib.__version__.split(".")[:2])
    if (major, minor) >= (3, 11):
        return
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
    except ImportError:
        import warnings
        warnings.warn("pip install arabic-reshaper python-bidi to render Arabic on matplotlib < 3.11")
        return
    from matplotlib.text import Text
    original = Text.set_text

    def set_text(self, s):
        s = "" if s is None else str(s)
        shaped = any("ﭐ" <= ch <= "﻿" for ch in s)       # already in presentation forms
        if not shaped and any("ء" <= ch <= "ي" for ch in s):
            s = get_display(arabic_reshaper.reshape(s))
        original(self, s)

    Text.set_text = set_text


_enable_rtl_fallback()


def pct(x: float, digits: int = 1) -> str:
    return f"{x * 100:.{digits}f}%"


def _frame(fig, title: str, subtitle: str = "", source: str = "") -> None:
    fig.text(0.985, 0.975, ar(title), ha="right", va="top", fontsize=14, weight="bold", color=INK)
    if subtitle:
        fig.text(0.985, 0.915, ar(subtitle), ha="right", va="top", fontsize=10, color=INK_2)
    if source:
        fig.text(0.985, 0.015, ar("المصدر: " + source), ha="right", va="bottom", fontsize=8, color=INK_3)
    fig.text(0.015, 0.015, f"{PROJECT_AR} · {PROJECT_EN}", ha="left", va="bottom", fontsize=8, color=INK_3,
             weight="bold")


def _save(fig, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def _rounded_hbars(ax, y, widths, colors, height=0.62):
    bars = ax.barh(y, widths, height=height, color=colors, edgecolor=SURFACE, linewidth=2)
    ax.tick_params(axis="y", length=0)
    return bars


def short_fund(name: str) -> str:
    for junk in (" Endowment Investment Fund", " Associations Endowment Fund", " Association Endowment Fund",
                 " Endowment Fund", " Waqf Fund", "SNB Capital - "):
        name = name.replace(junk, "")
    return name


# ------------------------------------------------------------------ sector


def fig_sector_growth(certs: pd.DataFrame, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8, 4.4))
    fig.subplots_adjust(top=0.80, bottom=0.12, left=0.07, right=0.97)
    ax.bar(certs["year"].astype(str), certs["registered_waqfs"], color=S1, width=0.6, edgecolor=SURFACE, lw=2)
    for x, v in zip(certs["year"].astype(str), certs["registered_waqfs"]):
        ax.text(x, v + 150, f"{int(v):,}", ha="center", va="bottom", fontsize=9, color=INK_2)
    ax.grid(axis="x", visible=False)
    ax.set_ylim(0, certs["registered_waqfs"].max() * 1.15)
    growth = (certs["registered_waqfs"].iloc[-1] / certs["registered_waqfs"].iloc[0]) ** (1 / (len(certs) - 1)) - 1
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:,.0f}")
    multiple = certs["registered_waqfs"].iloc[-1] / certs["registered_waqfs"].iloc[0]
    _frame(fig, f"الأوقاف المسجلة سنوياً تضاعفت {multiple:.0f} مرة خلال {len(certs) - 1} سنوات",
           f"عدد الشهادات الوقفية المكتملة — نمو سنوي مركب {pct(growth, 0)} (2019–2025)",
           "الهيئة العامة للأوقاف، منصة البيانات المفتوحة")
    return _save(fig, path)


def fig_masarif_national(nat: pd.DataFrame, path: Path, top: int = 14) -> Path:
    d = nat.sort_values("share", ascending=False)
    head = d.head(top).copy()
    other = d.iloc[top:]["share"].sum()
    if other > 0:
        head = pd.concat([head, pd.DataFrame([{"masraf_ar": "أخرى", "share": other, "group": "other",
                                              "waqf_count": d.iloc[top:]["waqf_count"].sum()}])])
    head = head.iloc[::-1]
    colors = [S2 if g == "social" else (S3 if g == "flexible" else (INK_3 if g == "other" else S1))
              for g in head["group"]]
    fig, ax = plt.subplots(figsize=(8, 6.2))
    fig.subplots_adjust(top=0.86, bottom=0.08, left=0.06, right=0.78)
    y = np.arange(len(head))
    _rounded_hbars(ax, y, head["share"], colors)
    ax.set_yticks(y, [ar(t) for t in head["masraf_ar"]])
    ax.yaxis.tick_right()
    ax.invert_xaxis()
    ax.grid(axis="y", visible=False)
    ax.xaxis.set_major_formatter(lambda v, _: pct(v, 0))
    for yi, s, n in zip(y, head["share"], head["waqf_count"]):
        ax.text(s + 0.004, yi, f"{pct(s)}  ({int(n):,})", va="center", ha="right", fontsize=8.5, color=INK_2)
    ax.set_xlim(head["share"].max() * 1.25, 0)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in (S1, S2, S3)]
    ax.legend(handles, [ar("عبادة وتعليم وذري"), ar("رعاية اجتماعية"), ar("أوجه البر (مرن)")],
              loc="lower left", fontsize=9)
    sh = d.set_index("masraf")["share"]
    _frame(fig, f"المساجد تستحوذ على {pct(sh['mosques'], 0)} من المصارف، والأيتام {pct(sh['orphans'])} فقط",
           f"توزيع {int(d['waqf_count'].sum()):,} مصرفاً وقفياً منشوراً حسب نوع المصرف (13 منطقة)",
           "الهيئة العامة للأوقاف — المصارف الوقفية حسب المنطقة")
    return _save(fig, path)


def fig_region_heatmap(disb: pd.DataFrame, group_labels: dict, path: Path) -> Path:
    t = disb.pivot_table(index="region_ar", columns="group", values="waqf_count", aggfunc="sum", fill_value=0)
    totals = t.sum(axis=1)
    share = t.div(totals, axis=0).loc[totals.sort_values(ascending=False).index]
    order = ["worship", "social", "education", "family", "flexible"]
    share = share[[c for c in order if c in share.columns]]
    fig, ax = plt.subplots(figsize=(8.2, 6.4))
    fig.subplots_adjust(top=0.84, bottom=0.06, left=0.04, right=0.80)
    cmap = LinearSegmentedColormap.from_list("seq", SEQ)
    ax.imshow(share.values, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    ax.grid(False)
    for i in range(share.shape[0]):
        for j in range(share.shape[1]):
            v = share.values[i, j]
            ax.text(j, i, pct(v, 0), ha="center", va="center", fontsize=8.5,
                    color="white" if v > 0.45 else INK)
    ax.set_xticks(range(share.shape[1]), [ar(group_labels[c][0]) for c in share.columns], fontsize=9)
    ax.xaxis.tick_top()
    labels = [ar(f"{r}  ({int(totals[r]):,})") for r in share.index]
    ax.set_yticks(range(share.shape[0]), labels)
    ax.yaxis.tick_right()
    ax.invert_xaxis()
    ax.tick_params(length=0)
    _frame(fig, "خريطة تركّز المصارف: مناطق بلا رعاية اجتماعية تقريباً",
           "حصة كل مجموعة مصارف داخل المنطقة (بين قوسين: عدد المصارف)", "الهيئة العامة للأوقاف")
    return _save(fig, path)


# ------------------------------------------------------------------ funds


def fig_index(price_idx: pd.DataFrame, total_idx: pd.DataFrame, stats: dict, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    fig.subplots_adjust(top=0.80, bottom=0.12, left=0.07, right=0.88)
    x = price_idx.index.to_timestamp()
    ax.plot(x, total_idx["index"], color=S1, label=ar("العائد الكلي المقدَّر (مع التوزيعات)"))
    ax.plot(x, price_idx["index"], color=S2, label=ar("عائد السعر فقط (بعد التوزيعات)"))
    ax.fill_between(x, price_idx["index"], total_idx["index"], color=S1, alpha=0.08, lw=0)
    for s, c, k in ((total_idx, S1, "total"), (price_idx, S2, "price")):
        ax.text(x[-1], s["index"].iloc[-1], f"  {s['index'].iloc[-1]:.0f}\n  {pct(stats[k]['ann_return'])}/سنة"
                .replace("/سنة", ""), color=INK_2, fontsize=9, va="center")
    ax.axhline(100, color=INK_3, lw=0.8, ls="--")
    ax.legend(loc="upper left", fontsize=9)
    ax.set_ylabel(ar("المؤشر (100 = ديسمبر 2019)"))
    _frame(fig, "مؤشر صناديق الوقف السعودية: الفجوة بين الخطين هي ما وُزِّع على المستفيدين",
           f"متوسط متساوي الأوزان لـ12 صندوقاً وقفياً تراكمياً — عائد كلي {pct(stats['total']['ann_return'])} "
           f"مقابل {pct(stats['price']['ann_return'])} سنوياً",
           f"تداول — أسعار وحدات الصناديق الوقفية؛ {BY}")
    return _save(fig, path)


def fig_payouts_vs_sustainable(payout: pd.DataFrame, sustainable: float, path: Path) -> Path:
    latest = payout.sort_values("year").groupby("fund_name").tail(1).sort_values("payout_pct")
    fig, ax = plt.subplots(figsize=(8.4, 5.6))
    fig.subplots_adjust(top=0.84, bottom=0.10, left=0.06, right=0.70)
    y = np.arange(len(latest))
    _rounded_hbars(ax, y, latest["payout_pct"], [S2] * len(latest))
    ax.axvline(sustainable, color=S1, lw=2)
    ax.text(sustainable, len(latest) - 0.3, ar(f" المعدل المستدام {pct(sustainable)} "), color=INK,
            fontsize=9, ha="left", va="bottom")
    ax.set_yticks(y, [f"{short_fund(n)}  ({yr})" for n, yr in zip(latest["fund_name"], latest["year"])], fontsize=8.5)
    ax.yaxis.tick_right()
    ax.invert_xaxis()
    ax.xaxis.set_major_formatter(lambda v, _: pct(v, 0))
    ax.grid(axis="y", visible=False)
    for yi, v in zip(y, latest["payout_pct"]):
        ax.text(v + 0.002, yi, pct(v), va="center", ha="right", fontsize=8.5, color=INK_2)
    ax.set_xlim(latest["payout_pct"].max() * 1.25, 0)
    lo_p, hi_p = latest["payout_pct"].min(), latest["payout_pct"].max()
    _frame(fig, f"الصناديق توزّع {pct(lo_p, 0)}–{pct(hi_p, 0)} سنوياً مقابل {pct(sustainable)} مستدام",
           "التوزيع المقدَّر لآخر سنة رُصد فيها توزيع، مقابل معدل الصرف الذي يحفظ الأصل الحقيقي بثقة 60%",
           "تداول؛ كشف التوزيعات من هبوط السعر مقارنة بصناديق المديرين الآخرين")
    return _save(fig, path)


def fig_backtest(scores: pd.DataFrame, path: Path) -> Path:
    s = scores.sort_values("mae", ascending=False)
    best = scores.index[0]
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.subplots_adjust(top=0.78, bottom=0.12, left=0.06, right=0.70)
    y = np.arange(len(s))
    _rounded_hbars(ax, y, s["mae"], [S1 if m == best else "#b7d3f6" for m in s.index])
    ax.set_yticks(y, [ar(t) for t in s["label_ar"]])
    ax.yaxis.tick_right()
    ax.invert_xaxis()
    ax.grid(axis="y", visible=False)
    ax.xaxis.set_major_formatter(lambda v, _: pct(v, 1))
    for yi, (m, row) in zip(y, s.iterrows()):
        note = "" if m == "zero_return" else ar(f"  (أفضل من الساذج بـ{pct(row['skill_vs_zero'], 0)})")
        ax.text(row["mae"] + 0.0008, yi, pct(row["mae"], 2) + note, va="center", ha="right", fontsize=8.5,
                color=INK_2)
    ax.set_xlim(s["mae"].max() * 1.9, 0)
    _frame(fig, "اختبار رجعي: النموذج البسيط يتفوق على المعقد",
           f"متوسط الخطأ المطلق لتوقع عائد 12 شهراً عبر {int(s['origins'].iloc[0])} نقطة انطلاق خارج العينة",
           BY)
    return _save(fig, path)


def fig_forecast_fan(total_idx: pd.DataFrame, fc: dict, dist: np.ndarray, path: Path) -> Path:
    hist = total_idx["index"].iloc[-36:]
    x = hist.index.to_timestamp()
    last = hist.iloc[-1]
    future = pd.period_range(total_idx.index[-1], periods=13, freq="M").to_timestamp()
    t = np.arange(0, 13) / 12
    point = last * np.exp(fc["point_log"] * t)
    lo = last * (1 + fc["p10_pct"]) ** t
    hi = last * (1 + fc["p90_pct"]) ** t
    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    fig.subplots_adjust(top=0.80, bottom=0.12, left=0.07, right=0.90)
    ax.plot(x, hist, color=S1)
    ax.fill_between(future, lo, hi, color=S1, alpha=0.15, lw=0, label=ar("نطاق 80% (من أخطاء الاختبار الرجعي)"))
    ax.plot(future, point, color=S1, ls="--", label=ar("التوقع"))
    ax.text(future[-1], point[-1], f"  {pct(fc['point_pct'])}", color=INK, fontsize=10, va="center")
    ax.text(future[-1], hi[-1], f"  {pct(fc['p90_pct'])}", color=INK_2, fontsize=8.5, va="center")
    ax.text(future[-1], lo[-1], f"  {pct(fc['p10_pct'])}", color=INK_2, fontsize=8.5, va="center")
    ax.legend(loc="upper left", fontsize=9)
    p_loss = float(np.mean(dist < 0))
    _frame(fig, f"توقع الأشهر الـ12 القادمة: {pct(fc['point_pct'])} مع احتمال خسارة {pct(p_loss, 0)}",
           "العائد الكلي لمؤشر صناديق الوقف — آخر 36 شهراً + التوقع", BY)
    return _save(fig, path)


# ------------------------------------------------------------------ decision


def fig_frontier(frontiers: dict[str, pd.DataFrame], labels: dict[str, str], confidence: float,
                 rates: dict[str, float], path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8.6, 4.9))
    fig.subplots_adjust(top=0.80, bottom=0.12, left=0.08, right=0.97)
    for (k, f), c in zip(frontiers.items(), (S1, S2, S3)):
        ax.plot(f["rate"], f["p_preserve_real"], color=c, marker="o", ms=4, label=ar(labels[k]))
        r = rates[k]
        yv = float(f.loc[np.isclose(f["rate"], r), "p_preserve_real"].iloc[0])
        ax.plot([r], [yv], marker="o", ms=10, color=c, mec=SURFACE, mew=2, zorder=5)
    ax.axhline(confidence, color=INK_3, ls="--", lw=1)
    ax.text(0.079, confidence + 0.015, ar(f"مستوى الثقة المطلوب {pct(confidence, 0)}"), ha="right",
            fontsize=9, color=INK_2)
    ax.xaxis.set_major_formatter(lambda v, _: pct(v, 0))
    ax.yaxis.set_major_formatter(lambda v, _: pct(v, 0))
    ax.set_xlabel(ar("معدل الصرف السنوي من قيمة الوقف"))
    ax.set_ylabel(ar("احتمال حفظ القيمة الحقيقية بعد 10 سنوات"))
    ax.set_ylim(0, 1)
    ax.legend(loc="upper right", fontsize=9)
    _frame(fig, f"حدود الصرف المستدام: {pct(rates['base'])} سنوياً تحفظ الأصل بثقة {pct(confidence, 0)}",
           "10,000 مسار محاكاة (Bootstrap كتلي) — تضخم 2% — قاعدة صرف ممهَّدة على 12 ربعاً", BY)
    return _save(fig, path)


def fig_real_paths(paths: dict[str, np.ndarray], labels: dict[str, str], path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    fig.subplots_adjust(top=0.80, bottom=0.12, left=0.07, right=0.88)
    years = np.arange(0, 11)
    for (k, q), c in zip(paths.items(), (S1, S2)):
        ax.fill_between(years, q[0], q[2], color=c, alpha=0.12, lw=0)
        ax.plot(years, q[1], color=c, label=ar(labels[k]))
        ax.text(10.1, q[1][-1], f"{q[1][-1]:.0f}", color=INK, fontsize=10, va="center")
    ax.axhline(100, color=INK_3, ls="--", lw=1)
    ax.set_xlabel(ar("السنوات"))
    ax.set_ylabel(ar("القيمة الحقيقية للوقف (100 = اليوم)"))
    ax.legend(loc="lower left", fontsize=9)
    loss = 1 - list(paths.values())[-1][1][-1] / 100
    _frame(fig, f"الصرف بمعدلات الصناديق الحالية يُفقد الوقف {pct(loss, 0)} من قيمته الحقيقية في 10 سنوات",
           "الوسيط ونطاق 10–90% للقيمة الحقيقية (بعد التضخم)", BY)
    return _save(fig, path)


def fig_allocation(alloc: pd.DataFrame, labels: dict[str, str], groups: dict[str, str], budget: float,
                   endowment: float, path: Path) -> Path:
    a = alloc.groupby("line", as_index=False)["amount"].sum().sort_values("amount", ascending=True)
    kind = alloc.drop_duplicates("line").set_index("line")["kind"]
    big = a[a["amount"] >= budget * 0.02]
    small = a[a["amount"] < budget * 0.02]["amount"].sum()
    if small > 0:
        big = pd.concat([pd.DataFrame([{"line": "_other", "amount": small}]), big])
    colors = []
    for line in big["line"]:
        k = kind.get(line, "other")
        colors.append(INK_3 if k == "waterfall" else (S2 if groups.get(line) == "social" else S1))
    fig, ax = plt.subplots(figsize=(8.2, 5.4))
    fig.subplots_adjust(top=0.84, bottom=0.10, left=0.06, right=0.76)
    y = np.arange(len(big))
    _rounded_hbars(ax, y, big["amount"], colors)
    ax.set_yticks(y, [ar(labels.get(line, "مصارف أخرى (<2% لكل منها)")) for line in big["line"]])
    ax.yaxis.tick_right()
    ax.invert_xaxis()
    ax.grid(axis="y", visible=False)
    ax.xaxis.set_major_formatter(lambda v, _: f"{v / 1000:,.0f}k")
    for yi, v in zip(y, big["amount"]):
        ax.text(v + budget * 0.005, yi, f"{v:,.0f}", va="center", ha="right", fontsize=8.5, color=INK_2)
    ax.set_xlim(big["amount"].max() * 1.3, 0)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in (INK_3, S2, S1)]
    ax.legend(handles, ["عمارة واحتياطي", "رعاية اجتماعية", "مصارف أخرى"], loc="lower left", fontsize=9)
    _frame(fig, f"خطة الصرف لوقف بقيمة {endowment / 1e6:,.0f} ملايين ريال: {budget:,.0f} ريال هذا العام",
           "عمارة الوقف والاحتياطي أولاً، ثم شروط الواقفين، ثم الحصة المرنة لأولويات الاحتياج",
           f"{BY} — مزيج المصارف الوطني من بيانات الهيئة العامة للأوقاف")
    return _save(fig, path)
