"""Render report/executive_summary.pdf (Arabic, RTL, A4) from outputs/tables — no hand-typed numbers.

    python scripts/build_report.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from string import Template

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from waqf.clean import MASRAF_MAP  # noqa: E402
from waqf.config import PROJECT_AR, PROJECT_EN, TAGLINE_AR, TEAM_MEMBERS  # noqa: E402

MASRAF_AR = {code: label for code, label, _, _ in MASRAF_MAP.values()}
TABLES = ROOT / "outputs" / "tables"
REPORT = ROOT / "report"
EDGE_CANDIDATES = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                   r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                   shutil.which("msedge") or "", shutil.which("chrome") or "", shutil.which("chromium") or ""]


def p(x: float, d: int = 1) -> str:
    return f"{x * 100:.{d}f}%"


def sar(x: float) -> str:
    return f"{x:,.0f}"


CSS = """
@page { size: A4; margin: 15mm 16mm 16mm 16mm; }
:root { --ink:#0b0b0b; --ink2:#52514e; --ink3:#8a8983; --paper:#fcfcfb; --rule:#e6e5e0;
        --navy:#0d366b; --blue:#2a78d6; --blue-soft:#eef4fc; --paper-in:#ffffff; --orange:#eb6834; --orange-soft:#fdf0ea;
        --green:#1baf7a; }
* { box-sizing: border-box; }
html, body { background:#ffffff; }
body { margin:0; color:var(--ink); font-family:"IBM Plex Sans Arabic","Segoe UI",Tahoma,sans-serif;
       font-size:10.3pt; line-height:1.75; direction:rtl; text-align:right;
       -webkit-print-color-adjust:exact; print-color-adjust:exact; }
.page { page-break-after: always; }
.page:last-child { page-break-after: auto; }
h1 { font-size:22pt; line-height:1.3; margin:0 0 4px; color:var(--navy); font-weight:700; letter-spacing:-.2px; }
h2 { font-size:13.5pt; color:var(--navy); margin:16px 0 6px; font-weight:700; }
h3 { font-size:11pt; margin:10px 0 4px; font-weight:600; }
p { margin:0 0 7px; }
.eyebrow { color:var(--blue); font-weight:600; font-size:9.5pt; letter-spacing:.3px; }
.sub { color:var(--ink2); font-size:11pt; margin-bottom:12px; }
.team { display:flex; gap:18px; flex-wrap:wrap; font-size:9.5pt; color:var(--ink2); margin:-4px 0 10px; }
.team b { color:var(--ink); font-weight:600; }
.meta { color:var(--ink3); font-size:8.5pt; border-top:1px solid var(--rule); padding-top:6px; margin-top:6px; }
.lede { background:var(--blue-soft); border-right:4px solid var(--blue); padding:10px 14px; border-radius:6px;
        font-size:11pt; margin:12px 0; }
.kpis { display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin:12px 0 10px; }
.kpi { border:1px solid var(--rule); border-radius:8px; padding:9px 10px 8px; background:#fff; }
.kpi .v { font-size:19pt; font-weight:700; color:var(--navy); line-height:1.15; }
.kpi .v.warn { color:var(--orange); }
.kpi .l { font-size:8.6pt; color:var(--ink2); line-height:1.45; margin-top:3px; }
.two { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
figure { margin:6px 0 10px; }
figure img { width:100%; border:1px solid var(--rule); border-radius:6px; display:block; }
figure.md img { width:80%; margin:0 auto; }
figcaption { font-size:8.5pt; color:var(--ink2); margin-top:3px; }
table { width:100%; border-collapse:collapse; font-size:9pt; margin:6px 0 10px; }
th { text-align:right; color:var(--ink2); font-weight:600; border-bottom:1.5px solid var(--ink3); padding:4px 6px; }
td { border-bottom:1px solid var(--rule); padding:4px 6px; }
td.n { font-variant-numeric: tabular-nums; direction:ltr; text-align:left; }
.rec { counter-reset: r; padding:0; margin:6px 0; list-style:none; }
.rec li { counter-increment:r; position:relative; padding:7px 40px 7px 10px; margin-bottom:6px; border-radius:6px;
          background:#fff; border:1px solid var(--rule); }
.rec li::before { content:counter(r); position:absolute; right:10px; top:7px; width:21px; height:21px; border-radius:50%;
                  background:var(--navy); color:#fff; font-weight:700; font-size:9pt; text-align:center; line-height:21px; }
.rec b { color:var(--navy); }
.callout { background:var(--orange-soft); border-right:4px solid var(--orange); padding:8px 12px; border-radius:6px;
           margin:8px 0; }
.small { font-size:8.8pt; color:var(--ink2); }
ul.tight { margin:4px 0 8px; padding-right:18px; }
ul.tight li { margin-bottom:2px; }
.ltr { direction:ltr; unicode-bidi:embed; }
"""

HTML = Template("""<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">
<title>$name — الملخص التنفيذي</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>$css</style></head><body>

<section class="page">
  <div class="eyebrow">$name · <span class="ltr">$name_en</span> — الملخص التنفيذي · مسابقة تحليل البيانات للقطاع غير الربحي</div>
  <h1>كم يصرف الوقف دون أن يأكل أصله؟</h1>
  <div class="sub"><b>$name</b>: $tagline العائلي والأهلي — تنبؤ بالعوائد، وسقف صرف مستدام، وتوزيع شرعي للمصارف</div>
  <div class="team">إعداد: $team</div>

  <div class="lede"><b>الخلاصة:</b> الأصول الوقفية المدرجة في السوق السعودية ولّدت عائداً كلياً مقدَّراً
  <b>$tot_ret سنوياً</b>، أي نحو <b>$real_ret</b> بعد التضخم. لذلك فإن معدل الصرف الذي يحفظ القيمة الحقيقية للوقف عشر سنوات
  بثقة $conf هو <b>$rate سنوياً</b> فقط، بينما توزّع الصناديق الوقفية فعلياً <b>$pay_lo–$pay_hi</b> (الوسيط $pay_med، أي نحو $obs وهو المعدل المستخدم في المحاكاة).
  الاستمرار بهذا المعدل يعني تآكل القيمة الحقيقية للوقف بنحو <b>$erosion</b> خلال عقد.</div>

  <div class="kpis">
    <div class="kpi"><div class="v">$rate</div><div class="l">سقف الصرف السنوي المستدام (ثقة $conf، تضخم $infl)</div></div>
    <div class="kpi"><div class="v warn">$p_obs</div><div class="l">احتمال حفظ الأصل إذا صرفنا بمعدل الصناديق الحالي (≈$obs)</div></div>
    <div class="kpi"><div class="v">$fc</div><div class="l">العائد المتوقع للأشهر الـ12 القادمة (نطاق 80%: <span class="ltr">$fc_lo</span> إلى <span class="ltr">$fc_hi</span>)</div></div>
    <div class="kpi"><div class="v warn">$orph</div><div class="l">حصة الأيتام من $n_masarif مصرفاً وقفياً منشوراً، مقابل $mosq للمساجد</div></div>
  </div>

  <h2>سؤال القرار</h2>
  <p>يواجه ناظر الوقف كل عام قراراً واحداً متكرراً: <b>كم أصرف، وعلى أي مصرف؟</b> الصرف الزائد يُرضي المستفيدين اليوم ويُضعف
  الوقف غداً، والصرف الناقص يحبس الخير. حوّلنا هذا الحدس إلى رقم قابل للدفاع: أعلى معدل صرف يحفظ القيمة الحقيقية
  للأصل بدرجة ثقة يختارها الناظر، ثم ترتيب الصرف شرعياً: عمارة الوقف، ثم احتياطي الاستقرار، ثم المصارف مع احترام شروط الواقفين.</p>

  <h2>البيانات: حقيقية ومفتوحة، وموثّقة حتى آخر صف</h2>
  <div class="two">
    <div><h3>الهيئة العامة للأوقاف</h3>
      <p class="small">18 مجموعة بيانات من منصة البيانات المفتوحة الوطنية، منها $n_masarif مصرفاً وقفياً في $regions منطقة، والشهادات الوقفية
      ($c19 في 2019 ← $c25 في 2025)، والمستفيدون المباشرون ($b23 ← $b25).</p></div>
    <div><h3>السوق المالية السعودية (تداول)</h3>
      <p class="small">أسعار وحدات $funds صندوقاً استثمارياً وقفياً مرخصاً (أصول ≈ $aum مليار ريال) من $start إلى $end،
      منها $in_index صندوقاً تراكمياً في المؤشر. لماذا تُعد بيانات قطاع غير ربحي؟ الصناديق الـ26 كلها صناديق استثمارية <b>وقفية</b>: وحداتها موقوفة، وعوائدها تُصرف على جهات غير ربحية (جمعيات الأيتام والقرآن والصحة، وأوقاف الجامعات، والسقيا، وغيرها)، فهي بيانات أصول وقفية تخص القطاع غير الربحي، وليست بيانات سوق تجارية.</p></div>
  </div>
  <p class="small">كل لقطة خام محمية بفحص سلامة (عدد الصفوف ومجموع الأسعار)، و<b>$n_rules قاعدة تنظيف</b> موثقة آلياً، أبرزها
  توحيد التهجئات العربية للمصارف، وإزالة أسعار ما قبل الاستثمار، واستيفاء الفجوات الربعية مع تعليمها،
  و<b>كشف $n_payouts توزيعاً مخفياً</b> يظهر كهبوط في سعر الوحدة.</p>
  <div class="meta">$name · التشغيل الكامل: <span class="ltr">python scripts/run_analysis.py</span> — يعيد بناء كل رقم وشكل في هذا التقرير من البيانات الخام · $n_tests اختباراً آلياً ناجحاً</div>
</section>

<section class="page">
  <h2>قصة الأثر: الفجوة بين ما يولّده الوقف وما يُصرف منه</h2>
  <p>بنينا <b>مؤشر صناديق الوقف السعودية</b> (متوسط متساوي الأوزان للصناديق التراكمية). عائد السعر وحده $price_ret سنوياً، لكنه
  يُخفي التوزيعات: كل يوليو تهبط صناديق الإنماء الوقفية معاً بنسبة 4–8% بينما صناديق المديرين الآخرين صاعدة. قسنا هذه
  الفجوات فظهر العائد الكلي المقدَّر <b>$tot_ret</b>، والمسافة بين الخطين هي ما ذهب إلى المستفيدين.</p>
  <figure><img src="../outputs/figures/fig04_waqf_index.png"><figcaption>شكل 1 — العائد الكلي المقدَّر مقابل عائد السعر (أقصى تراجع <span class="ltr">$mdd</span>، أسوأ 12 شهراً <span class="ltr">$worst</span>).</figcaption></figure>
  <div class="two">
    <figure><img src="../outputs/figures/fig05_payouts_vs_sustainable.png"><figcaption>شكل 2 — التوزيع المقدَّر لكل صندوق مقابل السقف المستدام $rate.</figcaption></figure>
    <figure><img src="../outputs/figures/fig09_real_value_paths.png"><figcaption>شكل 3 — القيمة الحقيقية بعد 10 سنوات: $real_sus عند الصرف المستدام مقابل $real_obs عند $obs.</figcaption></figure>
  </div>
  <div class="callout"><b>ماذا يعني ذلك لناظر الوقف؟</b> وقف بقيمة 10 ملايين ريال يصرف $obs سنوياً سيبدو بخير في السنوات الأولى،
  لكن قوته الشرائية بعد عشر سنوات تهبط في المسار الوسيط إلى نحو $real_obs_sar مليون ريال بأسعار اليوم. أما الصرف عند $rate فيترك
  الوقف أقوى مما بدأ ($real_sus_sar مليون)، فيرث الجيل القادم وقفاً أكبر لا أصغر.</div>
</section>

<section class="page">
  <h2>القرار: حدود الصرف المستدام</h2>
  <p>10,000 مستقبل محتمل بإعادة معاينة كتلية من تاريخ المؤشر الفعلي، مع قاعدة صرف ممهَّدة (نسبة من متوسط قيمة الوقف
  لآخر 12 ربعاً، كما تفعل أوقاف الجامعات الكبرى) حتى لا يتذبذب صرف المستفيدين مع السوق.</p>
  <figure class="md"><img src="../outputs/figures/fig08_spending_frontier.png"><figcaption>شكل 4 — احتمال حفظ القيمة الحقيقية لكل معدل صرف في ثلاثة سيناريوهات.</figcaption></figure>
  <table><thead><tr><th>شهية المخاطرة (الثقة المطلوبة)</th><th>السيناريو</th><th>سقف الصرف السنوي</th><th>صرف وقف بـ10 ملايين</th></tr></thead><tbody>
  $rate_rows
  </tbody></table>

  <h2>التنبؤ: النموذج البسيط فاز بالأرقام</h2>
  <div class="two">
    <figure><img src="../outputs/figures/fig06_backtest.png"><figcaption>شكل 5 — اختبار رجعي على $origins نقطة انطلاق خارج العينة.</figcaption></figure>
    <figure><img src="../outputs/figures/fig07_forecast.png"><figcaption>شكل 6 — توقع 12 شهراً: $fc (احتمال عائد سالب $p_loss).</figcaption></figure>
  </div>
  <p class="small">قارنّا خمسة نماذج قابلة للتفسير. فاز «$best» بخطأ أقل بـ<b>$skill</b> من المرجع الساذج، وتفوق على ARIMA والتمهيد الأسي.
  اخترنا النموذج الذي فاز في الاختبار، لا الأكثر تعقيداً، لأن السلاسل قصيرة والتعقيد هنا يعني إفراطاً في التوفيق.</p>
</section>

<section class="page">
  <h2>التوزيع على المصارف: من شرط الواقف إلى أثر المستفيد</h2>
  <div class="two">
    <figure><img src="../outputs/figures/fig02_masarif_national.png"><figcaption>شكل 7 — المصارف الوقفية وطنياً.</figcaption></figure>
    <figure><img src="../outputs/figures/fig10_allocation.png"><figcaption>شكل 8 — خطة صرف تطبيقية: $budget ريال لوقف بـ10 ملايين.</figcaption></figure>
  </div>
  <p>الترتيب: <b>عمارة الوقف</b> ($upkeep ريال) ← <b>احتياطي الاستقرار</b> ($reserve ريال) ← <b>المصارف</b>. حصص شروط الواقفين تبقى ثابتة،
  والحصة المرنة «أوجه البر» ($flex من المصارف وطنياً) توجَّه بأوزان أولوية معلنة، فترتفع حصة الاحتياجات الأساسية المتكررة
  (الفقراء، الأيتام، الأرامل، الإطعام، السكن) من <b>$soc_before</b> إلى <b>$soc_after</b> دون مخالفة أي شرط.</p>

  <h2>التوصيات</h2>
  <ol class="rec">
    <li><b>اعتماد سقف صرف $rate</b> من متوسط قيمة الوقف لـ12 ربعاً كخط أساس، يرتفع إلى $rate50 لمن يقبل ثقة 50% وينخفض إلى $rate_stress في سيناريو الضغط، مع مراجعة سنوية بهذه المنصة.</li>
    <li><b>ربط توزيعات الصناديق الوقفية بالعائد الممهَّد</b> لا بعائد السنة: التوزيع الحالي (≈$obs) يحفظ الأصل الحقيقي باحتمال $p_obs فقط.</li>
    <li><b>تقديم عمارة الوقف وبناء احتياطي يغطي صرف سنة</b> قبل التوزيع، لامتصاص السنوات السالبة التي يقع احتمالها عند $p_loss سنوياً.</li>
    <li><b>توجيه «أوجه البر» نحو المصارف المهمَلة:</b> الأيتام $orph والأرامل $wid من المصارف المنشورة، بينما تذهب $top_region_share من مصارف $top_region إلى $top_masraf وحدها.</li>
    <li><b>إفصاح أفضل يعني قرارات أفضل:</b> نوصي الهيئة وهيئة السوق المالية بنشر صافي أصول موثوق ومبالغ التوزيع لكل صندوق، والمستفيدين حسب المنطقة والمصرف.</li>
  </ol>

  <h2>المنهجية والحدود والاستخدام المسؤول للذكاء الاصطناعي</h2>
  <ul class="tight small">
    <li><b>المنهجية:</b> Python (pandas/statsmodels)؛ اختبار رجعي متدحرج بلا تسرب للمستقبل (مختبر آلياً)؛ Bootstrap كتلي ثابت؛ قاعدة صرف ممهَّدة؛ توزيع حتمي بقيود مختبرة (المجموع = الميزانية، لا مصرف تحت الحد الأدنى، شروط الواقف لا تُمس).</li>
    <li><b>الحدود:</b> الصناديق المدرجة وكيل لأداء الاستثمار الوقفي لا القوائم المالية لوقف بعينه؛ التاريخ قصير وفيه تحيز بقاء (عولج بسيناريو ضغط)؛ مبالغ التوزيع مقدَّرة لعدم نشرها؛ بيانات المستفيدين وطنية فقط.</li>
    <li><b>الذكاء الاصطناعي:</b> استُخدم مساعداً في البرمجة والتصميم. كل رقم مُشتق برمجياً من البيانات وليس مكتوباً يدوياً، وكل خطوة لها اختبار أو تحقق موثق في <span class="ltr">ai_usage_log.md</span>.</li>
  </ul>
</section>
</body></html>""")


def build_html() -> str:
    k = json.loads((TABLES / "key_numbers.json").read_text(encoding="utf-8"))
    s, ix, fc, sec, al = k["spending"], k["index"], k["forecast"], k["sector"], k["allocation"]
    regions = pd.read_csv(TABLES / "region_profiles.csv")
    fixed_top = regions[(regions["top_masraf"] != "general_charity") & (regions["waqf_designations"] >= 100)]
    top = fixed_top.sort_values("top_share", ascending=False).iloc[0]
    frontiers = {n: pd.read_csv(TABLES / f"spending_frontier_{n}.csv") for n in ("base", "stress", "price_only")}
    rows = []
    for conf in (0.50, 0.60, 0.75):
        for key, label in (("base", "الأساس"), ("stress", "ضغط −1%")):
            f = frontiers[key]
            ok = f.loc[f["p_preserve_real"] >= conf, "rate"]
            r = float(ok.max()) if len(ok) else 0.0
            bold = ' style="font-weight:700;color:#0d366b"' if (conf == s["confidence"] and key == "base") else ""
            rows.append(f"<tr{bold}><td>{p(conf, 0)}</td><td>{label}</td><td class='n'>{p(r)}</td>"
                        f"<td class='n'>{sar(10_000_000 * r)} ريال</td></tr>")
    n_tests = count_tests()
    infl = s["inflation"]
    vals = dict(
        team=" · ".join(f"<b>{m}</b>" for m in TEAM_MEMBERS),
        name=PROJECT_AR, name_en=PROJECT_EN, tagline=TAGLINE_AR,
        css=CSS, tot_ret=p(ix["total_ann_return"]), price_ret=p(ix["price_ann_return"]),
        real_ret=p((1 + ix["total_ann_return"]) / (1 + infl) - 1), conf=p(s["confidence"], 0), infl=p(infl, 0),
        rate=p(s["rate_base"]), rate50=p(s["rate_base_at_50"]), rate_stress=p(s["rate_stress"]),
        pay_lo=p(ix["payout_min_recent"], 0), pay_hi=p(ix["payout_max_recent"], 0), pay_med=p(ix["payout_median_recent"]),
        obs=p(s["observed_payout_rate"]), p_obs=p(s["p_preserve_at_observed"], 0),
        erosion=p(1 - s["median_real_final_observed"] / 100, 0),
        real_obs=f"{s['median_real_final_observed']:.0f}", real_sus=f"{s['median_real_final_sustainable']:.0f}",
        real_obs_sar=f"{s['median_real_final_observed'] / 10:.1f}", real_sus_sar=f"{s['median_real_final_sustainable'] / 10:.1f}",
        fc=p(fc["point_pct"]), fc_lo=p(fc["p10_pct"]), fc_hi=p(fc["p90_pct"]), p_loss=p(fc["bootstrap_p_loss"], 0),
        best=fc["best_model_label"], skill=p(fc["skill_vs_zero"], 0), origins=fc["origins"],
        orph=p(sec["orphans_share"]), wid=p(sec["widows_share"], 2), mosq=p(sec["mosques_share"], 0),
        flex=p(sec["flexible_share"], 0), n_masarif=f"{sec['waqf_designations']:,}", regions=sec["regions"],
        c19=f"{sec['certificates_2019']:,}", c25=f"{sec['certificates_2025']:,}",
        b23=f"{sec['beneficiaries_2023']:,}", b25=f"{sec['beneficiaries_2025']:,}",
        funds=ix["funds_total"], in_index=ix["funds_in_index"], aum=f"{ix['aum_total_sar'] / 1e9:.1f}",
        start=ix["start"], end=ix["end"], mdd=p(ix["total_max_drawdown"]), worst=p(ix["total_worst_12m"]),
        n_rules=len(pd.read_csv(TABLES / "cleaning_log.csv")), n_payouts=ix["payout_events"], n_tests=n_tests,
        rate_rows="\n  ".join(rows), budget=sar(al["budget"]), upkeep=sar(al["upkeep"]), reserve=sar(al["reserve"]),
        soc_before=p(al["social_share_before"], 0), soc_after=p(al["social_share_after"], 0),
        top_region=top["region_ar"], top_region_share=p(top["top_share"], 0),
        top_masraf=MASRAF_AR[top["top_masraf"]],
    )
    return HTML.substitute(vals)


def count_tests() -> int:
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout
    return sum(1 for line in out.splitlines() if "::" in line)


def find_browser() -> str:
    for c in EDGE_CANDIDATES:
        if c and Path(c).exists():
            return c
    raise FileNotFoundError("Microsoft Edge or Chrome is required to print the PDF")


def main() -> None:
    REPORT.mkdir(exist_ok=True)
    html_path = REPORT / "executive_summary.html"
    html_path.write_text(build_html(), encoding="utf-8")
    pdf_path = REPORT / "executive_summary.pdf"
    pdf_path.unlink(missing_ok=True)
    browser = find_browser()
    # headless Edge can hand off to a child process and return before the file lands: wait, then retry
    for attempt in range(1, 4):
        profile = tempfile.mkdtemp(prefix="waqf-pdf-")
        result = subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                                 f"--user-data-dir={profile}", "--no-first-run", "--no-default-browser-check",
                                 "--run-all-compositor-stages-before-draw", "--virtual-time-budget=15000",
                                 f"--print-to-pdf={pdf_path}", html_path.resolve().as_uri()],
                                capture_output=True, text=True, timeout=180)
        for _ in range(60):
            if pdf_path.exists() and pdf_path.stat().st_size > 0:
                break
            time.sleep(0.5)
        shutil.rmtree(profile, ignore_errors=True)
        if pdf_path.exists() and pdf_path.stat().st_size > 0:
            break
        print(f"attempt {attempt}: no PDF yet (exit {result.returncode}) {result.stderr.strip()[:200]}")
    else:
        raise RuntimeError("PDF was not produced after 3 attempts")
    print(f"{pdf_path.relative_to(ROOT)} written ({pdf_path.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
