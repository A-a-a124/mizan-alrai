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
figure.sm img { width:60%; margin:0 auto; }
table.compact { font-size:8.1pt; margin:4px 0 6px; }
table.compact td, table.compact th { padding:2px 6px; }
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
  <div class="sub"><b>$name</b>: $tagline العائلي والأهلي — من التحليل إلى ثلاثة حلول قابلة للتطبيق</div>
  <div class="team">إعداد: $team</div>

  <div class="lede"><b>الخلاصة:</b> الأصول الوقفية المدرجة ولّدت عائداً كلياً مقدَّراً <b>$tot_ret سنوياً</b>، ووُزِّع منه على المستفيدين
  نحو <b>$avg_pay سنوياً</b> في المتوسط، فبقيت قيمة الوحدة تنمو $price_ret سنوياً: <b>القطاع حافظ على أصله حتى الآن</b>.
  لكن $ev_recent من $ev_total توزيعاً مرصوداً وقعت في آخر ثلاث سنوات، وحجم التوزيع في سنته بلغ $pay_lo–$pay_hi من قيمة الوحدة.
  لو صار هذا المستوى سنوياً لتآكل الأصل. لذلك نقدّم ثلاثة حلول تُبقي الوقف مستداماً.</div>

  <div class="kpis">
    <div class="kpi"><div class="v"><span class="ltr">$rate_n–$rate_bal</span></div><div class="l">نطاق الصرف السنوي الذي يحفظ القيمة الحقيقية للأصل</div></div>
    <div class="kpi"><div class="v">$aum_a</div><div class="l">من الأصول الوقفية المصنّفة تحمل الدرجة A في بطاقة الاستدامة</div></div>
    <div class="kpi"><div class="v">$p_cut_sm</div><div class="l">احتمال قطع صرف المستفيد أكثر من 5% في سنة مع قاعدة التمهيد ($p_cut_un بدونها)</div></div>
    <div class="kpi"><div class="v warn">$orph</div><div class="l">حصة الأيتام من $n_masarif مصرفاً وقفياً منشوراً، مقابل $mosq للمساجد</div></div>
  </div>

  <h2>سؤال القرار</h2>
  <p>يواجه ناظر الوقف كل عام قراراً واحداً متكرراً: <b>كم أصرف، وعلى أي مصرف؟</b> الصرف الزائد يُرضي المستفيدين اليوم ويُضعف
  الوقف غداً، والصرف الناقص يحبس الخير. حوّلنا هذا القرار إلى أرقام من بيانات حقيقية، ثم إلى أدوات يستطيع الناظر ومدير الصندوق والجهة المنظِّمة اعتمادها.</p>

  <h2>البيانات: حقيقية ومفتوحة، وموثّقة حتى آخر صف</h2>
  <div class="two">
    <div><h3>الهيئة العامة للأوقاف</h3>
      <p class="small">18 مجموعة بيانات من منصة البيانات المفتوحة الوطنية، منها $n_masarif مصرفاً وقفياً في $regions منطقة، والشهادات الوقفية
      (من $c19 في 2019 إلى $c25 في 2025)، والمستفيدون المباشرون (من $b23 إلى $b25).</p></div>
    <div><h3>السوق المالية السعودية (تداول)</h3>
      <p class="small">أسعار وحدات $funds صندوقاً استثمارياً وقفياً مرخصاً (أصول ≈ $aum مليار ريال) من $start إلى $end.
      هذه الصناديق أوقاف: وحداتها موقوفة وعوائدها تُصرف على جهات غير ربحية، فهي بيانات قطاع غير ربحي.</p></div>
  </div>
  <p class="small">كل لقطة خام محمية بفحص سلامة، و<b>$n_rules قاعدة تنظيف</b> موثقة آلياً، منها توحيد التهجئات العربية للمصارف، وإزالة أسعار ما قبل الاستثمار،
  واستيفاء الفجوات الربعية مع تعليمها، و<b>كشف $n_payouts توزيعاً مخفياً</b> يظهر كهبوط في سعر الوحدة بينما صناديق المديرين الآخرين صاعدة.</p>
  <figure class="sm"><img src="../outputs/figures/fig04_waqf_index.png"><figcaption>شكل 1 — المسافة بين الخطين هي ما وُزِّع على المستفيدين (أقصى تراجع <span class="ltr">$mdd</span>).</figcaption></figure>
  <div class="meta">$name · التشغيل الكامل: <span class="ltr">python scripts/run_all.py</span> — يعيد بناء كل رقم وشكل من البيانات الخام · $n_tests اختباراً آلياً ناجحاً · فحص تلقائي على Windows وLinux</div>
</section>

<section class="page">
  <h2>الحل الأول: بطاقة استدامة الوقف</h2>
  <p>تصنيف من A إلى E لكل صندوق وقفي، يجيب عن سؤال واحد يفهمه أي واقف: <b>هل حافظت قيمة الوحدة الموقوفة على قوتها الشرائية؟</b>
  الدرجة مبنية على سعر الوحدة المرصود مباشرة (بعد التوزيعات)، فلا تعتمد على أي تقدير. صنّفنا $lab_n صندوقاً، منها $lab_prov بسجل أقل من $lab_months شهراً وُسمت «مبدئي».</p>
  <table class="compact"><thead><tr><th>الدرجة</th><th>المعنى</th><th>عدد الصناديق</th><th>منها مبدئي</th></tr></thead><tbody>
  $grade_rows
  </tbody></table>
  <table class="compact"><thead><tr><th>الصندوق</th><th>المدير</th><th>أشهر</th><th>نمو الوحدة سنوياً</th><th>أسوأ هبوط</th><th>الدرجة</th></tr></thead><tbody>
  $fund_rows
  </tbody></table>
  <p class="small"><b>من ينفّذها؟</b> الهيئة العامة للأوقاف أو هيئة السوق المالية تنشرها سنوياً من بيانات منشورة أصلاً، ومدير الصندوق يضعها في نشرة الصندوق.
  <b>ماذا تضيف؟</b> معياراً واحداً شفافاً يقارن به الواقف بين الصناديق، وإنذاراً مبكراً لأي صندوق يبدأ أصله بالتآكل.
  <b>حدودها:</b> الصناديق الجديدة انطلقت في سوق هابط فدرجتها مبدئية، وتغيير افتراض التضخم نصف نقطة يغيّر درجة $lab_sens صندوق فقط.</p>
</section>

<section class="page">
  <h2>الحل الثاني: قاعدة ميزان للصرف</h2>
  <p>قاعدة من جزأين. <b>أولاً: الصرف من متوسط قيمة الوقف لآخر 12 ربعاً</b> لا من قيمته اليوم، فلا يتذبذب دخل المستفيد مع السوق:
  عند المعدل نفسه ينخفض احتمال قطع الصرف أكثر من 5% في سنة واحدة من <b>$p_cut_un</b> إلى <b>$p_cut_sm</b>.
  <b>ثانياً: اختيار المعدل من نطاق معلن</b> حسب شهية المخاطرة، مع رؤية المقايضة كاملة:</p>
  <table><thead><tr><th>الخيار</th><th>معدل الصرف</th><th>قيمة الأصل الحقيقية بعد 30 سنة</th><th>احتمال حفظ الأصل</th><th>مجموع الصرف الحقيقي في 30 سنة</th><th>الصرف السنوي في السنة 30</th></tr></thead><tbody>
  $menu_rows
  </tbody></table>
  <p class="small">الأرقام لأصل قيمته 100 اليوم، بأسعار اليوم، من $paths مسار محاكاة بإعادة معاينة كتلية لتاريخ المؤشر الفعلي وتضخم $infl.</p>
  <div class="callout"><b>المقايضة بصراحة:</b> الصرف عند $rate_recent يعطي المستفيدين أكثر في العقود الأولى ($cum_recent مقابل $cum_bal خلال 30 سنة)،
  لكنه يُنقص الأصل إلى $val_recent ويهبط بالصرف السنوي عاماً بعد عام. الصرف عند $rate_bal يُبقي الأصل ويزيد الصرف السنوي،
  ويتجاوز صرفه السنوي صرف الخيار الأعلى $breakeven_txt. القرار إذن عدالة بين الأجيال، وقاعدة ميزان تجعله قراراً معلناً لا نتيجة غير مقصودة.</div>
  <div class="two">
    <figure><img src="../outputs/figures/fig08_spending_frontier.png"><figcaption>شكل 2 — احتمال حفظ القيمة الحقيقية لكل معدل صرف.</figcaption></figure>
    <figure><img src="../outputs/figures/fig07_forecast.png"><figcaption>شكل 3 — توقع 12 شهراً: $fc (احتمال عائد سالب $p_loss)، بنموذج اجتاز اختباراً رجعياً على $origins نقطة.</figcaption></figure>
  </div>
  <p class="small"><b>من ينفّذها؟</b> ناظر الوقف ومجلس إدارة الصندوق، بتعديل سياسة التوزيع فقط. <b>ماذا تضيف؟</b> دخلاً أثبت للمستفيد وأصلاً لا يتآكل.
  <b>حدودها:</b> التاريخ $hist شهراً فقط، فالمحاكاة لثلاثين سنة تقدير لا تنبؤ، وفي سيناريو الضغط ينخفض المعدل المتحفظ إلى $rate_stress.</p>
</section>

<section class="page">
  <h2>الحل الثالث: بوصلة المصارف</h2>
  <p>شروط الواقفين تبقى كما هي. الحصة المرنة «أوجه البر» ($flex من المصارف وطنياً) هي التي يملك الناظر توجيهها، فتُوزَّع بأوزان أولوية معلنة نحو الاحتياجات الأقل تغطية.
  مثال وقف بقيمة 10 ملايين ريال وميزانية $budget ريال بعد عمارة الوقف والاحتياطي:</p>
  <div class="two">
    <table><thead><tr><th>المصرف</th><th>من شروط الواقفين</th><th>بعد التوجيه</th></tr></thead><tbody>
    $compass_rows
    </tbody></table>
    <figure><img src="../outputs/figures/fig02_masarif_national.png"><figcaption>شكل 4 — المصارف الوقفية وطنياً: المساجد $mosq والأيتام $orph.</figcaption></figure>
  </div>
  <p class="small"><b>من ينفّذها؟</b> ناظر الوقف عند إعداد خطة الصرف السنوية. <b>ماذا تضيف؟</b> ترتفع حصة الاحتياجات الأساسية من <b>$soc_before</b> إلى <b>$soc_after</b> دون مخالفة أي شرط،
  وأكبر أثر في $compass_region. <b>حدودها:</b> الأوزان افتراضات معلنة قابلة للتعديل، لأن بيانات الاحتياج حسب المنطقة غير منشورة.</p>

  <h2>خلاصة الحلول</h2>
  <table><thead><tr><th>الحل</th><th>من ينفّذه</th><th>بماذا</th><th>ماذا يضيف</th></tr></thead><tbody>
    <tr><td><b>بطاقة استدامة الوقف</b></td><td>الهيئة العامة للأوقاف، هيئة السوق المالية</td><td>أسعار الوحدات المنشورة</td><td>معيار مقارنة شفاف لـ$lab_n صندوقاً وإنذار مبكر بالتآكل</td></tr>
    <tr><td><b>قاعدة ميزان للصرف</b></td><td>النظّار ومجالس الصناديق</td><td>تعديل سياسة التوزيع</td><td>احتمال قطع الصرف من $p_cut_un إلى $p_cut_sm، وأصل محفوظ</td></tr>
    <tr><td><b>بوصلة المصارف</b></td><td>النظّار</td><td>خطة الصرف السنوية</td><td>حصة الاحتياجات الأساسية من $soc_before إلى $soc_after</td></tr>
  </tbody></table>

  <h2>المنهجية والحدود والاستخدام المسؤول للذكاء الاصطناعي</h2>
  <ul class="tight small">
    <li><b>المنهجية:</b> Python (pandas/statsmodels)؛ اختبار رجعي متدحرج بلا تسرب للمستقبل؛ Bootstrap كتلي ثابت؛ قواعد حتمية مختبرة آلياً، والمخرجات متطابقة عند إعادة التشغيل.</li>
    <li><b>الحدود:</b> الصناديق المدرجة وكيل لأداء الاستثمار الوقفي لا القوائم المالية لوقف بعينه؛ مبالغ التوزيع مقدَّرة لعدم نشرها، والكشف أضعف في السنوات التي كان الإفصاح فيها ربعياً؛ بيانات المستفيدين وطنية فقط.</li>
    <li><b>الذكاء الاصطناعي:</b> استُخدم مساعداً في البرمجة والتصميم. كل رقم مُشتق برمجياً من البيانات، وكل خطوة لها تحقق موثق في <span class="ltr">ai_usage_log.md</span>، ومنها تصحيح قراءة سابقة خاطئة لمعدل التوزيع.</li>
  </ul>
</section>

<section class="page">
  <h2>أين يغيب الوقف؟ فجوات المصارف بالاسم</h2>
  <p>قاطعنا المناطق الـ$regions مع المصارف الوقفية المسجّلة. <b>$no_orph من $regions</b> منطقة ليس فيها مصرف وقفي واحد مسجّل للأيتام،
  و<b>$no_wid</b> بلا مصرف للأرامل، و<b>$no_house</b> بلا مصرف للسكن. هذه فجوات المناطق الكبرى (500 مصرف مسجّل فأكثر):</p>
  <table class="compact"><thead><tr><th>المنطقة</th><th>المصارف الوقفية المسجّلة</th><th>مصارف الرعاية الاجتماعية الغائبة تماماً</th></tr></thead><tbody>
  $gap_rows
  </tbody></table>
  <p class="small"><b>ماذا تضيف؟</b> تحوّل بوصلة المصارف من نسبة عامة إلى قائمة يبدأ منها الواقف الجديد والهيئة.
  <b>حدودها:</b> البيانات تقيس ما سُجّل وقفاً باسم المصرف، لا الحاجة ولا الدعم الفعلي: قد يُخدم الأيتام من حصة «أوجه البر» أو من جهات غير وقفية.
  والمناطق القليلة التسجيل استُبعدت من الجدول.</p>

  <h2>اختبار الصدمة: ماذا يحدث لدخل المستفيد لو ساءت الأحوال؟</h2>
  <p class="small">أعدنا أسوأ هبوط في تاريخ المؤشر (<span class="ltr">$fall</span> خلال شهرين، <span class="ltr">$fall_from</span>) وصدمات أخرى على وقف يصرف $rate_bal. الخانة = أكبر انخفاض في صرف سنة عن التي قبلها (بأسعار اليوم).</p>
  <table class="compact"><thead><tr><th>الصدمة</th><th>قاعدة ميزان (متوسط 12 ربعاً)</th><th>المعدل نفسه دون تمهيد</th><th>مستوى التوزيع الأخير دون تمهيد</th></tr></thead><tbody>
  $shock_rows
  </tbody></table>

  <h2>متانة النتائج: ما الذي يثبت وما الذي يتغير؟</h2>
  <p class="small">التاريخ المتاح $hist شهراً فقط، فأعدنا المحاكاة بأسواق أضعف مما رصدناه. الخانة = احتمال حفظ القيمة الحقيقية للأصل بعد 10 سنوات.</p>
  <table class="compact"><thead><tr><th>الافتراض</th><th>متحفظ $rate_n%</th><th>متوازن $rate_bal</th><th>مستوى التوزيع الأخير $rate_recent</th></tr></thead><tbody>
  $robust_rows
  </tbody></table>
  <ul class="tight small">
    <li><b>ما يثبت:</b> في كل افتراض وكل أفق، المعدل الأقل يترك أصلاً أكبر واحتمال حفظ أعلى. ترتيب الخيارات لا يتغير.</li>
    <li><b>ما يتغير:</b> المستوى. لو نقص العائد 1% سنوياً نزل احتمال حفظ الأصل عند $rate_bal من $p_base إلى $p_lower. لذلك نوصي بالبدء من الطرف المتحفظ ومراجعة المعدل سنوياً.</li>
    <li><b>التوزيعات مقدَّرة:</b> لو أخطأ تقدير حجمها بالنصف زيادة أو نقصاً كان متوسط التوزيع بين $pay_rng_lo و$pay_rng_hi سنوياً بدل $avg_pay. بطاقة الاستدامة لا تتأثر لأنها من سعر الوحدة المرصود.</li>
    <li><b>بطاقة الاستدامة:</b> أكبر صندوق ($big_share من الأصول المصنّفة) درجته مبدئية. بين الصناديق المستقرة وحدها $aum_a_est من الأصول بدرجة A.</li>
  </ul>

  <h2>سؤالان متوقعان</h2>
  <ul class="tight small">
    <li><b>كيف تحاكون 30 سنة من 7 سنوات؟</b> لا نتنبأ بثلاثين سنة. نعيد تركيب أشهر التاريخ الفعلي في $paths مسار لنقارن قواعد الصرف تحت الظروف نفسها. القرار مبني على أفق 10 سنوات، وأرقام 30 و40 سنة توضّح اتجاه المقايضة فقط، وجدول المتانة أعلاه يبيّن حدودها.</li>
    <li><b>الصناديق المدرجة ليست الأوقاف العائلية والأهلية؟</b> صحيح. لا بيانات مالية مفتوحة لتلك الأوقاف (في سجل الهيئة $family_n مصرفاً ذرياً فقط من $n_masarif). الصناديق الوقفية المدرجة هي الأصول الوقفية الوحيدة ذات سعر شهري منشور، فهي وكيل لعائد الاستثمار الوقفي. وأي وقف يملك بياناته يعيد الحساب عليها بأمر واحد.</li>
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
    lab, rule, comp, trend = k["label"], k["rule"], k["compass"], k["payout_trend"]
    label = pd.read_csv(TABLES / "sustainability_label.csv", dtype={"symbol": str})
    chip = {"A": "#1F4E79", "B": "#4F7AA8", "C": "#8A8983", "D": "#B5651D", "E": "#9B2C2C"}
    meaning = label.drop_duplicates("grade").set_index("grade")["grade_meaning_ar"].to_dict()
    grade_rows = "\n  ".join(
        f"<tr><td><b style='color:{chip[g]}'>{g}</b></td><td>{meaning.get(g, '')}</td>"
        f"<td class='n'>{lab[f'count_{g}']}</td><td class='n'>{lab[f'count_{g}'] - lab[f'established_{g}']}</td></tr>"
        for g in "ABCDE" if lab[f"count_{g}"])
    fund_rows = "\n  ".join(
        f"<tr><td class='ltr' style='text-align:right'>{short(r.fund_name)}{' <span style=\"color:#8a8983\">(مبدئي)</span>' if r.provisional else ''}</td>"
        f"<td class='ltr' style='text-align:right'>{r.manager.replace(' Investment Co', '').replace(' Capital', '').replace(' Investment', '')}</td>"
        f"<td class='n'>{r.months}</td><td class='n'>{p(r.unit_growth)}</td><td class='n'>{p(r.max_drawdown)}</td>"
        f"<td><b style='color:{chip[r.grade]}'>{r.grade}</b></td></tr>" for r in label.itertuples())
    names = {"cautious": "متحفظ", "balanced": "متوازن", "recent_level": "مستوى التوزيع الأخير"}
    menu_rows = "\n  ".join(
        f"<tr{' style=\"font-weight:700;color:#0d366b\"' if o == 'balanced' else ''}><td>{names[o]}</td><td class='n'>{p(rule[f'rate_{o}'])}</td>"
        f"<td class='n'>{rule[f'{o}_30y_median_real_value']:.0f}</td><td class='n'>{p(rule[f'{o}_30y_p_preserve_real'], 0)}</td>"
        f"<td class='n'>{rule[f'{o}_30y_cumulative_real_payout']:.0f}</td><td class='n'>{rule[f'{o}_30y_annual_real_payout_at_end']:.2f}</td></tr>"
        for o in names)
    case = pd.read_csv(TABLES / "compass_case.csv")
    compass_rows = "\n    ".join(
        f"<tr><td>{r.label_ar}</td><td class='n'>{sar(r.from_waqif_conditions)}</td><td class='n'><b>{sar(r.total)}</b></td></tr>"
        for r in case[case["social"]].sort_values("total", ascending=False).itertuples())
    be = rule["breakeven_year_balanced"]
    breakeven_txt = f"في السنة {be} تقريباً" if be else f"بعد أكثر من {rule['sim_horizon_years']} سنة"
    infl = s["inflation"]
    rb, gp, sh = k["robustness"], k["gaps"], k["shock"]
    gaps = pd.read_csv(TABLES / "social_gaps.csv")
    big = gaps[gaps["region_waqf_designations"] >= 500]
    gap_rows = "\n  ".join(
        f"<tr><td><b>{region}</b></td><td class='n'>{int(g['region_waqf_designations'].iloc[0]):,}</td><td>{'، '.join(g['masraf_ar'])}</td></tr>"
        for region, g in big.groupby("region_ar", sort=False))
    shock_names = {"worst_fall_again": "يتكرر أسوأ هبوط تاريخي", "worst_fall_twice": "يتكرر الهبوط مرتين في عشر سنوات",
                   "inflation_4pct_5y": "تضخم 4% لخمس سنوات", "flat_3y": "ثلاث سنوات بلا عائد"}
    shock_rows = "\n  ".join(
        f"<tr><td>{label}</td>" + "".join(
            f"<td class='n'>{'<b>' if st == 'mizan' else ''}{p(sh[f'{sc}__{st}__worst_cut'])}{'</b>' if st == 'mizan' else ''}</td>"
            for st in ("mizan", "same_rate_unsmoothed", "recent_level_unsmoothed")) + "</tr>"
        for sc, label in shock_names.items())
    assume = {"base": "كما رُصد في التاريخ", "lower_return": "عائد أقل 1% سنوياً", "harsh": "عائد أقل 2% وتذبذب أعلى 50%"}
    robust_rows = "\n  ".join(
        f"<tr><td>{label}</td>" + "".join(f"<td class='n'>{p(rb[f'{a}_{o}_10y_p_preserve'], 0)}</td>"
                                         for o in ("cautious", "balanced", "recent_level")) + "</tr>"
        for a, label in assume.items())
    vals = dict(
        gap_rows=gap_rows, shock_rows=shock_rows, robust_rows=robust_rows,
        no_orph=gp["regions_without_orphans"], no_wid=gp["regions_without_widows"], no_house=gp["regions_without_housing"],
        fall=p(sh["worst_fall"]), fall_from=sh["worst_fall_from"],
        p_base=p(rb["base_balanced_10y_p_preserve"], 0), p_lower=p(rb["lower_return_balanced_10y_p_preserve"], 0),
        pay_rng_lo=p(rb["avg_payout_low"]), pay_rng_hi=p(rb["avg_payout_high"]),
        aum_a_est=p(lab["established_aum_share_A"], 0), big_share=p(lab["largest_fund_share_of_graded_aum"], 0),
        family_n=f"{sec['family_designations']:,}",
        team=" · ".join(f"<b>{m}</b>" for m in TEAM_MEMBERS),
        avg_pay=p(ix["avg_payout_rate"]), ev_recent=trend["events_last_3_years"], ev_total=trend["events_total"],
        rate_bal=p(rule["rate_balanced"]), rate_n=f"{rule['rate_cautious'] * 100:.1f}", rate_recent=p(rule["rate_recent_level"], 0),
        aum_a=p(lab["aum_share_A"], 0), lab_n=lab["funds_graded"], lab_prov=lab["funds_provisional"],
        lab_months=lab["established_months"], lab_sens=lab["grades_changed_by_inflation"],
        p_cut_un=p(rule["smoothing"]["unsmoothed_p_cut_over_5pct"], 0), p_cut_sm=p(rule["smoothing"]["smoothed_p_cut_over_5pct"], 0),
        grade_rows=grade_rows, fund_rows=fund_rows, menu_rows=menu_rows, compass_rows=compass_rows,
        cum_recent=f"{rule['recent_level_30y_cumulative_real_payout']:.0f}", cum_bal=f"{rule['balanced_30y_cumulative_real_payout']:.0f}",
        val_recent=f"{rule['recent_level_30y_median_real_value']:.0f}", breakeven_txt=breakeven_txt,
        paths=f"{s['paths']:,}", hist=rule["history_months"], compass_region=comp["top_region_ar"],
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


def short(name: str) -> str:
    for junk in (" Endowment Investment Fund", " Associations Endowment Fund", " Association Endowment Fund",
                 " Endowment Fund", " Waqf Fund", "SNB Capital - "):
        name = name.replace(junk, "")
    return name


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
