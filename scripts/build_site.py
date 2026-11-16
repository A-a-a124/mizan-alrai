"""Write the public landing page (index.html at the repo root, served by GitHub Pages).

    python scripts/build_site.py
"""

from __future__ import annotations

import csv
import json
import re
import subprocess
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
<meta name="description" content="$tagline: ثلاثة حلول من بيانات مفتوحة حقيقية تُبقي الوقف مستداماً">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="dashboard/style.css?v=6">
</head><body>

<section class="hero" data-scene="hero">
  <svg id="heroScale" viewBox="0 0 420 232" role="img" aria-label="ميزان بين هذا الجيل والأجيال القادمة"></svg>
  <div style="color:#9fb3d6;font-weight:600">$name · <span class="ltr">$name_en</span></div>
  <h1>كم يصرف الوقف دون أن يأكل أصله؟</h1>
  <p class="tag">الوقف وعدٌ لجيلين: من يحتاج اليوم، ومن يأتي بعدنا. حلّلنا البيانات المفتوحة للأوقاف السعودية لنعرف أين يستقيم الميزان.</p>
  <div class="team">إعداد: $team</div>
  <div class="down">انزل لتقرأ القصة ↓</div>
</section>

<div class="wrap">

<section class="scene" id="s-data" data-scene="data">
  <h2 class="reveal"><span class="hl">بدأنا من بيانات حقيقية مفتوحة</span></h2>
  <div class="pair reveal">
    <div><div class="bignum" data-to="$n_raw">$n</div><div class="l">مصرفاً وقفياً مسجّلاً في $regions منطقة<br>الهيئة العامة للأوقاف، منصة البيانات المفتوحة الوطنية</div></div>
    <div><div class="bignum" data-to="$funds">$funds</div><div class="l">صندوقاً وقفياً مرخّصاً بأسعار وحداتها الشهرية<br>السوق المالية السعودية (تداول)</div></div>
  </div>
</section>

<section class="scene" data-scene="index">
  <h2 class="reveal"><span class="hl">الوقف ينمو، وبعض نموّه يُوزَّع</span></h2>
  <p class="lead reveal">مؤشر الصناديق الوقفية ولّد عائداً كلياً مقدَّراً <b>$tot سنوياً</b>، بينما ارتفع سعر الوحدة <b>$price سنوياً</b> فقط. الفرق بين الخطين هو ما وصل للمستفيدين: نحو <b>$avg_pay سنوياً</b>.</p>
  <div class="fig reveal"><svg id="stIndex" viewBox="0 0 560 300" role="img" aria-label="مؤشر صناديق الوقف: العائد الكلي مقابل السعر"></svg></div>
</section>

<section class="scene" data-scene="payouts">
  <h2 class="reveal"><span class="hl">لكن التوزيعات تتسارع</span></h2>
  <p class="lead reveal"><b>$ev_recent من $ev_total</b> توزيعاً رصدناه وقعت في آخر ثلاث سنوات. القطاع حافظ على أصله حتى الآن، والسؤال: ماذا لو صار مستوى التوزيع الأخير عادة سنوية؟</p>
  <div class="fig reveal"><svg id="stPayouts" viewBox="0 0 560 300" role="img" aria-label="عدد التوزيعات المرصودة في كل سنة"></svg>
    <div class="note">عدد التوزيعات المرصودة في كل سنة (مكتشَفة من هبوط سعر الوحدة مقارنة بالصناديق المماثلة).</div></div>
</section>

<section class="scene" data-scene="frontier">
  <h2 class="reveal"><span class="hl">كل نقطة صرف إضافية لها ثمن</span></h2>
  <p class="lead reveal">حاكينا 10,000 مسار للسنوات العشر القادمة من تاريخ الصناديق نفسه. لو صُرف <b>$obs</b> كل سنة لحُفظت القيمة الحقيقية للأصل باحتمال <b>$p_obs</b> فقط. عند <b>$rate_bal</b> يرتفع الاحتمال إلى <b>$p_bal</b>.</p>
  <div class="duo reveal">
    <div class="fig"><svg id="stFrontier" viewBox="0 0 560 300" role="img" aria-label="احتمال حفظ الأصل لكل معدل صرف"></svg></div>
    <div><div class="l">معدل الصرف السنوي</div><div class="bignum" id="stRate" style="font-size:clamp(34px,6vw,60px)">$rate_bal</div>
         <div class="l" style="margin-top:10px">احتمال حفظ الأصل بعد 10 سنوات</div><div class="bignum" id="stProb" style="font-size:clamp(34px,6vw,60px)">$p_bal</div></div>
  </div>
</section>

<section class="scene" data-scene="solutions">
  <h2 class="reveal"><span class="hl">ثلاثة حلول تُبقي الميزان مستقيماً</span></h2>
  <p class="lead reveal">كل حل مبني على رقم من البيانات، وله جهة تستطيع تنفيذه ببيانات منشورة أصلاً.</p>
  <div class="cards3 reveal">
    <a class="card" href="dashboard/#label"><span class="n">1</span><h3>بطاقة استدامة الوقف</h3><p>درجة من A إلى E لكل صندوق: هل حافظت الوحدة على قوتها الشرائية؟ <b>$aum_a</b> من الأصول المصنّفة بدرجة A، و$below_b صندوقاً دون B.</p></a>
    <a class="card" href="dashboard/#rule"><span class="n">2</span><h3>قاعدة ميزان للصرف</h3><p>الصرف من متوسط 12 ربعاً بمعدل بين <span class="ltr">$rate_n–$rate_bal</span>. احتمال انخفاض الصرف أكثر من 5% في سنة ما ينزل من <b>$cut_raw</b> إلى <b>$cut_smooth</b>.</p></a>
    <a class="card" href="dashboard/#compass"><span class="n">3</span><h3>بوصلة المصارف</h3><p>توجيه حصة «أوجه البر» المرنة نحو الرعاية الاجتماعية يرفع حصتها من <b>$soc_before</b> إلى <b>$soc_after</b> دون المساس بشرط الواقف.</p></a>
  </div>
</section>

<section class="scene" data-scene="gaps">
  <h2 class="reveal"><span class="hl">وأين يغيب الوقف؟</span></h2>
  <p class="lead reveal"><b>$no_orphans من $regions</b> منطقة ليس فيها مصرف وقفي واحد مسجّل للأيتام. في <b>$gap_region</b> وحدها <b>$gap_count</b> مصرفاً وقفياً، ولا واحد منها للأيتام.</p>
  <div class="duo reveal">
    <div class="fig"><svg id="stMap" class="map" role="img" aria-label="المناطق التي ليس فيها مصرف وقفي للأيتام"></svg>
      <div class="note"><span style="color:var(--critical)">■</span> منطقة بلا مصرف وقفي مسجّل للأيتام</div></div>
    <div><a class="btn" href="dashboard/explore.html">افتح الخريطة التفاعلية وفجوات كل منطقة</a></div>
  </div>
</section>

<section class="scene" id="s-shock" data-scene="shock">
  <h2 class="reveal"><span class="hl">وماذا لو ساءت الأحوال؟</span></h2>
  <p class="lead reveal">أعدنا أسوأ هبوط في تاريخ المؤشر على وقف يصرف $rate_bal سنوياً. هذا أكبر انخفاض في مبلغ الصرف من سنة إلى التي تليها:</p>
  <div class="pair reveal">
    <div><div class="bignum ltr" data-to="$shock_mizan" style="color:var(--series-3)">-$shock_mizan%</div><div class="l">بقاعدة ميزان (الصرف من متوسط 12 ربعاً)</div></div>
    <div><div class="bignum ltr" data-to="$shock_raw" style="color:var(--series-2)">-$shock_raw%</div><div class="l">بالمعدل نفسه دون تمهيد</div></div>
  </div>
  <div class="reveal"><a class="btn" href="dashboard/#shock">جرّب اختبار الصدمة على وقفك</a></div>
</section>

<section class="scene" data-scene="end" style="border-bottom:0">
  <h2 class="reveal"><span class="hl">جرّب بنفسك</span></h2>
  <div class="lede reveal">الأصول الوقفية المدرجة في السوق السعودية ولّدت عائداً كلياً مقدَّراً <b>$tot سنوياً</b>،
ووُزِّع منه نحو <b>$avg_pay سنوياً</b> في المتوسط، فحافظ القطاع على أصله حتى الآن. لكن التوزيعات ترتفع:
$ev_recent من $ev_total توزيعاً مرصوداً وقعت في آخر ثلاث سنوات. لذلك نقدّم ثلاثة حلول تُبقي الوقف مستداماً:
<b>بطاقة استدامة الوقف</b>، و<b>قاعدة ميزان للصرف</b> (نطاق <span class="ltr">$rate_n–$rate_bal</span> سنوياً)، و<b>بوصلة المصارف</b>.</div>
  <div class="links reveal">
    <a class="card" href="dashboard/"><b>المحاكي والحلول الثلاثة ←</b><span>حرّك معدل الصرف وشاهد الميزان يميل، وارسم مسارات المحاكاة، واختبر الصدمات</span></a>
    <a class="card" href="dashboard/explore.html"><b>استكشف البيانات ←</b><span>خريطة المناطق، فجوات المصارف، مديرو الصناديق، وصفحة وبطاقة لكل صندوق</span></a>
    <a class="card" href="dashboard/plan.html"><b>وقفك في دقيقة ←</b><span>ثلاثة أسئلة ثم خطة صرف من صفحة واحدة جاهزة للطباعة</span></a>
    <a class="card" href="report/executive_summary.pdf"><b>الملخص التنفيذي (PDF) ←</b><span>4 صفحات: القرار، قصة الأثر، التوصيات</span></a>
    <a class="card" href="https://colab.research.google.com/github/A-a-a124/mizan-alrai/blob/main/analysis.ipynb"><b>دفتر التحليل على Colab ←</b><span>Python كامل بالسرد العربي، يعمل بضغطة Run all</span></a>
    <a class="card" href="$repo"><b>الكود والبيانات ←</b><span>المصدر الكامل، $tests اختباراً آلياً، سجل استخدام الذكاء الاصطناعي</span></a>
  </div>
  <footer class="reveal">البيانات: الهيئة العامة للأوقاف (منصة البيانات المفتوحة الوطنية) · السوق المالية السعودية (تداول) · حدود المناطق: geoBoundaries، © مساهمو OpenStreetMap. تحليل مستقل لأغراض مسابقة تحليل البيانات للقطاع غير الربحي. الصناديق المدرجة وكيل لأداء الاستثمار الوقفي، ومبالغ التوزيع مقدَّرة.</footer>
</section>

</div>
<script src="dashboard/data.js?v=6"></script>
<script src="dashboard/map.js?v=6"></script>
<script src="dashboard/common.js?v=6"></script>
<script src="dashboard/story.js?v=6"></script>
</body></html>
""")


def pct(x: float, d: int = 1) -> str:
    return f"{x * 100:.{d}f}%"


def count_tests() -> int:
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"], cwd=ROOT, capture_output=True, text=True).stdout
    found = re.search(r"(\d+) tests? collected", out)
    return int(found.group(1)) if found else 0


def main() -> None:
    k = json.loads((ROOT / "outputs" / "tables" / "key_numbers.json").read_text(encoding="utf-8"))
    s, ix, fc, sec = k["spending"], k["index"], k["forecast"], k["sector"]
    rule, lab, shock, alloc = k["rule"], k["label"], k["shock"], k["allocation"]
    with open(ROOT / "outputs" / "tables" / "social_gaps.csv", encoding="utf-8-sig", newline="") as fh:
        gap = next(r for r in csv.DictReader(fh) if r["masraf"] == "orphans")      # largest region with no orphans masraf
    html = PAGE.substitute(
        name=PROJECT_AR, name_en=PROJECT_EN, tagline=TAGLINE_AR, repo=REPO, team=" · ".join(TEAM_MEMBERS),
        tot=pct(ix["total_ann_return"]), price=pct(ix["price_ann_return"]), avg_pay=pct(ix["avg_payout_rate"]),
        ev_recent=k["payout_trend"]["events_last_3_years"], ev_total=k["payout_trend"]["events_total"],
        obs=pct(s["observed_payout_rate"]), p_obs=pct(s["p_preserve_at_observed"], 0),
        rate_n=f"{rule['rate_cautious'] * 100:.1f}", rate_bal=pct(rule["rate_balanced"]),
        p_bal=pct(rule["balanced_10y_p_preserve_real"], 0), aum_a=pct(lab["aum_share_A"], 0),
        below_b=lab["count_C"] + lab["count_D"] + lab["count_E"],
        cut_raw=pct(rule["smoothing"]["unsmoothed_p_cut_over_5pct"], 0),
        cut_smooth=pct(rule["smoothing"]["smoothed_p_cut_over_5pct"], 0),
        soc_before=pct(alloc["social_share_before"], 0), soc_after=pct(alloc["social_share_after"], 0),
        no_orphans=k["gaps"]["regions_without_orphans"], regions=sec["regions"],
        gap_region=gap["region_ar"], gap_count=f"{int(gap['region_waqf_designations']):,}",
        shock_mizan=f"{-shock['worst_fall_again__mizan__worst_cut'] * 100:.1f}",
        shock_raw=f"{-shock['worst_fall_again__same_rate_unsmoothed__worst_cut'] * 100:.1f}",
        n=f"{sec['waqf_designations']:,}", n_raw=sec["waqf_designations"], funds=ix["funds_total"], tests=count_tests())
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
<div class="sub">ثلاثة حلول من بيانات مفتوحة حقيقية: $n مصرفاً وقفياً و$funds صندوقاً وقفياً · Python</div>
<div class="kpis">
 <div class="k"><div class="v"><span dir="ltr">$rate_n–$rate_bal</span></div><div class="l">نطاق الصرف الذي يحفظ الأصل (قاعدة ميزان)</div></div>
 <div class="k"><div class="v">$aum_a</div><div class="l">من الأصول المصنّفة بدرجة A في بطاقة استدامة الوقف</div></div>
 <div class="k"><div class="v w">$orph</div><div class="l">حصة الأيتام من المصارف (بوصلة المصارف ترفعها)</div></div>
 <div class="k"><div class="v">$fc</div><div class="l">العائد المتوقع للأشهر الـ12 القادمة</div></div>
</div>
<div class="insight">القطاع حافظ على أصله حتى الآن، لكن <b>$ev_recent من $ev_total</b> توزيعاً مرصوداً وقعت في آخر ثلاث سنوات. ثلاثة حلول تُبقيه مستداماً.</div>
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
        pay_hi=pct(ix["payout_max_recent"], 0), rate_n=f"{k['rule']['rate_cautious'] * 100:.1f}",
        rate_bal=pct(k["rule"]["rate_balanced"]), aum_a=pct(k["label"]["aum_share_A"], 0),
        ev_recent=k["payout_trend"]["events_last_3_years"], ev_total=k["payout_trend"]["events_total"],
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
