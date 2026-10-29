"""Write the public landing page (index.html at the repo root, served by GitHub Pages).

    python scripts/build_site.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from waqf.config import PROJECT_AR, PROJECT_EN, TAGLINE_AR, TEAM_MEMBERS  # noqa: E402

REPO = "https://github.com/A-a-a124/mizan-alrai"

PAGE = Template("""<!doctype html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>$name · $name_en</title>
<meta name="description" content="$tagline — سقف صرف مستدام وتوزيع شرعي للمصارف من بيانات مفتوحة حقيقية">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;600;700&display=swap" rel="stylesheet">
<style>
:root{--bg:#f6f6f3;--card:#fff;--rule:#e6e5e0;--ink:#0b0b0b;--ink2:#52514e;--navy:#0d366b;--blue:#2a78d6;--orange:#eb6834}
@media (prefers-color-scheme: dark){:root:where(:not([data-theme="light"])){--bg:#121211;--card:#20201f;--rule:#383835;--ink:#f0efec;--ink2:#c3c2b7;--navy:#9ec5f4;--blue:#3987e5;--orange:#d95926}}
:root[data-theme="dark"]{--bg:#121211;--card:#20201f;--rule:#383835;--ink:#f0efec;--ink2:#c3c2b7;--navy:#9ec5f4;--blue:#3987e5;--orange:#d95926}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:"IBM Plex Sans Arabic","Segoe UI",Tahoma,sans-serif;line-height:1.7}
.wrap{max-width:980px;margin:0 auto;padding:36px 16px 48px}
.brand{color:var(--blue);font-weight:600;letter-spacing:.3px}
h1{font-size:clamp(30px,6vw,46px);line-height:1.2;margin:6px 0 4px;color:var(--navy)}
.tag{font-size:18px;color:var(--ink2);margin:0 0 6px}.team{color:var(--ink2);font-size:14px}
.lede{background:var(--card);border:1px solid var(--rule);border-right:4px solid var(--blue);border-radius:10px;padding:14px 16px;margin:20px 0;font-size:16px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin:0 0 22px}
.kpi{background:var(--card);border:1px solid var(--rule);border-radius:12px;padding:14px}
.kpi .v{font-size:30px;font-weight:700;color:var(--navy);line-height:1.2}.kpi .v.w{color:var(--orange)}.kpi .l{font-size:13.5px;color:var(--ink2)}
.links{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px}
a.card{display:block;text-decoration:none;color:inherit;background:var(--card);border:1px solid var(--rule);border-radius:12px;padding:16px;transition:border-color .15s}
a.card:hover,a.card:focus-visible{border-color:var(--blue);outline:none}
a.card b{display:block;color:var(--navy);font-size:17px;margin-bottom:2px}a.card span{color:var(--ink2);font-size:14px}
img.hero{width:100%;border:1px solid var(--rule);border-radius:12px;margin:22px 0 6px;background:#fff}
.cap{font-size:13px;color:var(--ink2)}footer{margin-top:28px;font-size:13px;color:var(--ink2)}
.ltr{direction:ltr;unicode-bidi:embed}
</style></head><body><div class="wrap">
<div class="brand">$name · <span class="ltr">$name_en</span></div>
<h1>كم يصرف الوقف دون أن يأكل أصله؟</h1>
<p class="tag">$tagline: تنبؤ بالعوائد، وسقف صرف مستدام، وتوزيع شرعي للمصارف</p>
<div class="team">إعداد: $team</div>

<div class="lede">الأصول الوقفية المدرجة في السوق السعودية ولّدت عائداً كلياً مقدَّراً <b>$tot سنوياً</b>،
لذلك فإن الصرف الذي يحفظ القيمة الحقيقية للوقف عشر سنوات بثقة $conf هو <b>$rate سنوياً</b>،
بينما توزّع الصناديق الوقفية فعلياً $pay_lo–$pay_hi.</div>

<div class="kpis">
  <div class="kpi"><div class="v">$rate</div><div class="l">سقف الصرف السنوي المستدام</div></div>
  <div class="kpi"><div class="v w">$p_obs</div><div class="l">احتمال حفظ الأصل بمعدل الصناديق الحالي (≈$obs)</div></div>
  <div class="kpi"><div class="v">$fc</div><div class="l">العائد المتوقع للأشهر الـ12 القادمة</div></div>
  <div class="kpi"><div class="v w">$orph</div><div class="l">حصة الأيتام من $n مصرفاً وقفياً</div></div>
</div>

<div class="links">
  <a class="card" href="dashboard/"><b>محاكي القرار التفاعلي ←</b><span>حرّك معدل الصرف وشاهد الأثر على الأصل والمصارف فوراً</span></a>
  <a class="card" href="report/executive_summary.pdf"><b>الملخص التنفيذي (PDF) ←</b><span>4 صفحات: القرار، قصة الأثر، التوصيات</span></a>
  <a class="card" href="https://colab.research.google.com/github/A-a-a124/mizan-alrai/blob/main/analysis.ipynb"><b>دفتر التحليل على Colab ←</b><span>Python كامل بالسرد العربي، يعمل بضغطة Run all</span></a>
  <a class="card" href="$repo"><b>الكود والبيانات ←</b><span>المصدر الكامل، 28 اختباراً، سجل استخدام الذكاء الاصطناعي</span></a>
</div>

<img class="hero" src="outputs/figures/fig08_spending_frontier.png" alt="منحنى حدود الصرف المستدام: احتمال حفظ القيمة الحقيقية لكل معدل صرف">
<div class="cap">حدود الصرف المستدام — 10,000 مسار محاكاة من التاريخ الفعلي لـ$funds صندوقاً وقفياً مرخصاً.</div>

<footer>البيانات: الهيئة العامة للأوقاف (منصة البيانات المفتوحة الوطنية) · السوق المالية السعودية (تداول). تحليل مستقل لأغراض مسابقة تحليل البيانات للقطاع غير الربحي.</footer>
</div></body></html>
""")


def pct(x: float, d: int = 1) -> str:
    return f"{x * 100:.{d}f}%"


def main() -> None:
    k = json.loads((ROOT / "outputs" / "tables" / "key_numbers.json").read_text(encoding="utf-8"))
    s, ix, fc, sec = k["spending"], k["index"], k["forecast"], k["sector"]
    html = PAGE.substitute(
        name=PROJECT_AR, name_en=PROJECT_EN, tagline=TAGLINE_AR, repo=REPO,
        team=" · ".join(TEAM_MEMBERS), tot=pct(ix["total_ann_return"]), conf=pct(s["confidence"], 0),
        rate=pct(s["rate_base"]), pay_lo=pct(ix["payout_min_recent"], 0), pay_hi=pct(ix["payout_max_recent"], 0),
        p_obs=pct(s["p_preserve_at_observed"], 0), obs=pct(s["observed_payout_rate"]), fc=pct(fc["point_pct"]),
        orph=pct(sec["orphans_share"]), n=f"{sec['waqf_designations']:,}", funds=ix["funds_total"])
    (ROOT / "index.html").write_text(html, encoding="utf-8")
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")
    print("index.html written")
    build_x_card(k)


CARD = Template("""<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;600;700&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box}html,body{margin:0;width:1600px;height:900px;overflow:hidden}
body{background:linear-gradient(135deg,#0d366b 0%,#123f7a 55%,#184f95 100%);color:#fff;
  font-family:"IBM Plex Sans Arabic","Segoe UI",Tahoma,sans-serif;padding:70px 90px;position:relative}
.brand{font-size:34px;font-weight:600;color:#9ec5f4}.brand span{direction:ltr;unicode-bidi:embed;opacity:.8}
h1{font-size:76px;line-height:1.2;margin:18px 0 10px;font-weight:700}
.sub{font-size:30px;color:#cde2fb;margin-bottom:46px}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:22px}
.k{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.18);border-radius:22px;padding:26px 26px 22px}
.k .v{font-size:72px;font-weight:700;line-height:1.05}.k .v.w{color:#ffb38f}.k .l{font-size:23px;color:#cde2fb;margin-top:10px;line-height:1.45}
.insight{margin-top:34px;font-size:31px;line-height:1.5;background:rgba(255,179,143,.12);border-right:6px solid #ffb38f;border-radius:14px;padding:18px 26px}
.insight b{color:#ffb38f}
.foot{position:absolute;bottom:52px;right:90px;left:90px;display:flex;justify-content:space-between;font-size:24px;color:#9ec5f4}
.foot .u{direction:ltr;unicode-bidi:embed;color:#fff;font-weight:600}
</style></head><body>
<div class="brand">$name · <span>$name_en</span></div>
<h1>كم يصرف الوقف دون أن يأكل أصله؟</h1>
<div class="sub">تحليل بيانات مفتوحة حقيقية: $n مصرفاً وقفياً و$funds صندوقاً وقفياً · Python</div>
<div class="kpis">
 <div class="k"><div class="v">$rate</div><div class="l">سقف الصرف السنوي المستدام</div></div>
 <div class="k"><div class="v w"><span dir="ltr">$pay_lo_n–$pay_hi</span></div><div class="l">ما توزّعه الصناديق الوقفية فعلياً</div></div>
 <div class="k"><div class="v w">$p_obs</div><div class="l">احتمال حفظ الأصل بالمعدل الحالي</div></div>
 <div class="k"><div class="v">$fc</div><div class="l">العائد المتوقع للأشهر الـ12 القادمة</div></div>
</div>
<div class="insight">الصرف بمعدل الصناديق الحالي يُفقد الوقف <b>$erosion</b> من قيمته الحقيقية خلال 10 سنوات، والأيتام لا يتجاوزون <b>$orph</b> من المصارف.</div>
<div class="foot"><div>$team</div><div class="u">a-a-a124.github.io/mizan-alrai</div></div>
</body></html>""")


def build_x_card(k: dict) -> None:
    """Share image for the competition's X post (outputs/social/x_card.png, 1600x900)."""
    import shutil
    import subprocess
    import tempfile
    import time
    s, ix, fc, sec = k["spending"], k["index"], k["forecast"], k["sector"]
    out = ROOT / "outputs" / "social"
    out.mkdir(parents=True, exist_ok=True)
    html = out / "x_card.html"
    html.write_text(CARD.substitute(
        name=PROJECT_AR, name_en=PROJECT_EN, team=" · ".join(TEAM_MEMBERS), n=f"{sec['waqf_designations']:,}",
        funds=ix["funds_total"], rate=pct(s["rate_base"]), pay_lo=pct(ix["payout_min_recent"], 0),
        pay_hi=pct(ix["payout_max_recent"], 0), p_obs=pct(s["p_preserve_at_observed"], 0),
        pay_lo_n=f"{ix['payout_min_recent'] * 100:.0f}", erosion=pct(1 - s["median_real_final_observed"] / 100, 0),
        orph=pct(sec["orphans_share"]), fc=pct(fc["point_pct"])), encoding="utf-8")
    browser = next((c for c in (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                                shutil.which("msedge"), shutil.which("chrome"), shutil.which("chromium"))
                    if c and Path(c).exists()), None)
    if browser is None:
        print("x_card.html written (no browser found for PNG)")
        return
    png = out / "x_card.png"
    png.unlink(missing_ok=True)
    profile = tempfile.mkdtemp(prefix="mizan-card-")
    subprocess.run([browser, "--headless=new", "--disable-gpu", f"--user-data-dir={profile}", "--no-first-run",
                    "--hide-scrollbars", "--window-size=1600,900", "--virtual-time-budget=10000",
                    f"--screenshot={png}", html.resolve().as_uri()], capture_output=True, timeout=120)
    for _ in range(40):
        if png.exists() and png.stat().st_size:
            break
        time.sleep(0.5)
    shutil.rmtree(profile, ignore_errors=True)
    print("outputs/social/x_card.png written" if png.exists() else "x_card.png NOT produced")


if __name__ == "__main__":
    main()
