"""Generate and execute analysis.ipynb (Arabic narrative over the same pipeline code).

    python scripts/build_notebook.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from waqf.config import PROJECT_AR, PROJECT_EN, TAGLINE_AR, TEAM_MEMBERS  # noqa: E402


def md(text: str):
    return nbf.v4.new_markdown_cell(f'<div dir="rtl" style="text-align:right">\n\n{text.strip()}\n\n</div>')


def code(src: str):
    return nbf.v4.new_code_cell(src.strip())


CELLS = [
    md(f"""
# {PROJECT_AR} · {PROJECT_EN}
## {TAGLINE_AR}
### كم يصرف الناظر هذا العام دون أن يأكل الأصل؟ وكيف يوزّعه على المصارف؟

**الفريق:** {" · ".join(TEAM_MEMBERS)}

**سؤال القرار:** ما معدل الصرف السنوي الذي يحفظ القيمة *الحقيقية* (بعد التضخم) لأصل الوقف خلال عشر سنوات
بدرجة ثقة يحددها الناظر، وكيف يُوزَّع هذا المبلغ على المصارف الشرعية مع احترام شروط الواقفين؟

**البيانات (حقيقية ومفتوحة من القطاع غير الربحي فقط):**
1. الهيئة العامة للأوقاف — 18 مجموعة بيانات على منصة البيانات المفتوحة الوطنية (15,305 مصرفاً وقفياً في 13 منطقة، الشهادات الوقفية، المستفيدون…).
2. السوق المالية السعودية (تداول) — أسعار وحدات **26 صندوقاً استثمارياً وقفياً** مرخصاً من هيئة السوق المالية (2018–2026). هذه الصناديق أوقاف بحد ذاتها: وحداتها موقوفة وعوائدها تُصرف على جهات غير ربحية (جمعيات، أوقاف جامعات، رعاية أيتام…)، فهي بيانات قطاع غير ربحي.

**التشغيل:** `python scripts/run_analysis.py` يعيد بناء كل المخرجات من البيانات الخام في ثوانٍ. هذا الدفتر يستدعي **الدوال نفسها** خطوة بخطوة ويشرحها.
"""),
    md("""
**تشغيل على Google Colab:** الخلية التالية تنسخ المستودع وتثبت المتطلبات تلقائياً عند التشغيل على Colab،
ثم يمكن تنفيذ الدفتر كاملاً من القائمة: *Runtime ← Run all*. على الجهاز المحلي لا تفعل شيئاً.
"""),
    code("""
import os, sys, subprocess
if "google.colab" in sys.modules:                      # Colab: fetch code + raw data, install deps
    if not os.path.exists("/content/mizan-alrai"):
        subprocess.run(["git", "clone", "--depth", "1", "https://github.com/A-a-a124/mizan-alrai.git",
                        "/content/mizan-alrai"], check=True)
    os.chdir("/content/mizan-alrai")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "statsmodels", "arabic-reshaper", "python-bidi"],
                   check=True)
print("working directory:", os.getcwd())
"""),
    code("""
import sys, json
from pathlib import Path
ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "src"))
import pandas as pd, numpy as np
from IPython.display import Image, display
from waqf import pipeline, config, clean, forecast
pd.set_option("display.max_colwidth", 120); pd.set_option("display.width", 160)
res = pipeline.Results()
def show(name): display(Image(filename=str(config.FIGURES / name), width=820))
"""),
    md("""
## 1. البيانات الخام والتحقق من سلامتها
بوابة البيانات المفتوحة وموقع تداول يحجبان الطلبات الآلية (جدار حماية WAF)، لذلك جُمعت البيانات عبر واجهات المعاينة
الرسمية داخل المتصفح وحُفظت كلقطات ثابتة في `data_raw/` مع **فحوص سلامة**: عدد صفوف كل جدول كما تعلنه البوابة،
و(عدد الملاحظات + مجموع الأسعار) لكل صندوق. أي تعديل في الملفات يوقف التشغيل فوراً (مختبر في `tests/`).
"""),
    code("""
raw = pipeline.step_ingest(res)
display(res.tables["data_manifest"])
print("GASA tables:", len(raw.gasa), "| funds:", raw.prices.symbol.nunique(), "| price observations:", len(raw.prices))
"""),
    md("""
## 2. تنظيف البيانات وتوثيقه
كل قاعدة تنظيف تُسجَّل آلياً في سجل التنظيف (المصدر، القاعدة، عدد الصفوف المتأثرة). أبرز المشكلات الحقيقية التي عولجت:
- **تهجئات متعددة للمصرف نفسه** (`تعلم العلم وتعليمه` / `العلم وتعليمه`، `اضحيه`، `الدعوه`) ← طيّ إملائي عربي + قاموس مصارف موحّد.
- **علامة BOM** في رؤوس الأعمدة، ومسافات زائدة، وأرقام بفواصل آلاف (`' 8,514,665 '`)، وسنة نصية (`2022 وماقبلها`).
- **أسعار إطلاق ثابتة** قبل بدء الاستثمار (10.0000 لعدة أرباع) ← حُذفت.
- **أسعار مكررة متجمدة** وسط السلسلة ← عوملت كقيم مفقودة.
- **فجوات إفصاح ربعي** ← استيفاء لوغاريتمي خطي مُعلَّم (`imputed`).
- **حقل صافي الأصول = 0** في أغلب الأشهر ← أُسقط لعدم موثوقيته.
- **توزيعات مخفية:** سعر الوحدة يهبط عند توزيع العوائد على المستفيدين (كل يوليو في صناديق الإنماء) ← كشفناها آلياً (القسم 4).
"""),
    code("""
c = pipeline.step_clean(raw, res)
display(res.tables["cleaning_log"])
"""),
    code("""
# مثال قبل/بعد: من 25 تسمية خام إلى 24 مصرفاً موحّداً
raw_labels = sorted({m for t in raw.gasa.values() if "counts" in t for _, m, _ in t["counts"]})
mapping = pd.DataFrame({"raw_label": raw_labels})
mapping["canonical"] = mapping.raw_label.map(lambda s: clean.MASRAF_MAP[clean.fold_arabic(s)][1])
display(mapping[mapping.raw_label != mapping.canonical])
print(c["fund_prices"].flag.value_counts().to_dict())
"""),
    md("""
## 3. صورة القطاع: أين تذهب الأوقاف اليوم؟
"""),
    code("""
sec = pipeline.step_sector(c, res)
k = res.key["sector"]
show("fig01_sector_growth.png"); show("fig02_masarif_national.png"); show("fig03_region_heatmap.png")
print(f"المساجد {k['mosques_share']:.1%} | أوجه البر (مرن) {k['flexible_share']:.1%} | الأيتام {k['orphans_share']:.2%} | الأرامل {k['widows_share']:.2%}")
display(sec["regions"][["region_ar","waqf_designations","flexible_share","social_share","hhi","top_masraf","top_share"]].round(3))
"""),
    md("""
**قراءة:** نمو تسجيل الأوقاف استثنائي (≈70% سنوياً)، لكن المصارف شديدة التركّز: المساجد وحدها 43%، بينما الأيتام والأرامل
أقل من 0.2% مجتمعين. الحصة المرنة (**أوجه البر 25%**) هي الرافعة الوحيدة التي يملك الناظر توجيهها دون مخالفة شرط واقف.
"""),
    md("""
## 4. أداء الأصول الوقفية: مؤشر صناديق الوقف السعودية
بنينا مؤشراً متساوي الأوزان من **الصناديق التراكمية** المؤهلة (≥ 12 شهراً). اكتشاف مهم أثناء التنظيف: هبوط متزامن في
صناديق مدير واحد بينما صناديق المديرين الآخرين صاعدة = **توزيع عوائد** وليس خسارة. قدّرنا حجمه بالفجوة عن متوسط الأقران،
فحصلنا على مؤشرين: *عائد السعر* (ما يبقى للأصل) و*العائد الكلي المقدَّر* (ما يولّده الأصل فعلاً).
"""),
    code("""
ix = pipeline.step_index(c, res)
show("fig04_waqf_index.png"); show("fig05_payouts_vs_sustainable.png")
display(pd.DataFrame(ix["stats"]).T.round(4))
display(res.tables["fund_summary"].round(4).head(26))
"""),
    md("""
## 5. التنبؤ بعائد الأشهر الـ12 القادمة (مع اختبار رجعي)
خمسة نماذج قابلة للتفسير تُقارَن باختبار رجعي متدحرج (كل نقطة انطلاق ترى ماضيها فقط — مختبر آلياً ضد تسرب المستقبل).
المعيار: متوسط الخطأ المطلق لعائد 12 شهراً. اخترنا البسيط لأنه **فاز بالأرقام** لا لأنه أسهل.
"""),
    code("""
fc = pipeline.step_forecast(ix, res)
display(fc["scores"].round(4))
show("fig06_backtest.png"); show("fig07_forecast.png")
f = res.key["forecast"]
print(f"التوقع: {f['point_pct']:.2%}  نطاق 80%: [{f['p10_pct']:.2%}, {f['p90_pct']:.2%}]  احتمال عائد سالب: {f['bootstrap_p_loss']:.0%}")
"""),
    md("""
## 6. القرار: معدل الصرف المستدام (محاكاة مونت كارلو)
10,000 مستقبل محتمل بإعادة معاينة كتلية ثابتة (تحافظ على ذيول التوزيع والارتباط الذاتي الفعلي)، وقاعدة صرف ممهَّدة
(نسبة من متوسط قيمة الوقف لآخر 12 ربعاً، كما تفعل أوقاف الجامعات الكبرى) وتضخم 2%. ثلاثة سيناريوهات: الأساس،
والضغط (−1% سنوياً لتحيز البقاء)، وعائد السعر فقط.
"""),
    code("""
sp = pipeline.step_spending(ix, res)
show("fig08_spending_frontier.png"); show("fig09_real_value_paths.png")
s = res.key["spending"]
display(pd.DataFrame({"الثقة المطلوبة": ["50%","60% (الافتراضي)","75%"],
                      "المعدل المستدام": [s["rate_base_at_50"], s["rate_base"], s["rate_base_at_75"]]}))
display(res.tables["spending_frontier_base"].round(3))
print(f"الصرف بمعدل الصناديق الحالي {s['observed_payout_rate']:.1%} يحفظ الأصل الحقيقي باحتمال {s['p_preserve_at_observed']:.0%} فقط")
"""),
    md("""
## 7. التوزيع على المصارف: حالة تطبيقية (وقف بقيمة 10 ملايين ريال)
الترتيب الشرعي: **عمارة الوقف أولاً** (10%) ← **احتياطي استقرار** حتى يبلغ صرف سنة ← **المصارف**: شروط الواقفين ثابتة
(المزيج الوطني من بيانات الهيئة افتراضياً)، والحصة المرنة (أوجه البر) تتوزع بأوزان أولوية شفافة مع حد أدنى لكل مصرف.
"""),
    code("""
al = pipeline.step_allocate(c, sp, res)
show("fig10_allocation.png")
display(al["allocation"][["label_ar","kind","amount","share_of_budget"]].round(3))
a = res.key["allocation"]
print(f"حصة الاحتياجات الأساسية المتكررة: {a['social_share_before']:.1%} من شروط الواقفين ← {a['social_share_after']:.1%} بعد توجيه الحصة المرنة")
"""),
    code("""
# حساسية: نفس الميزانية بمزيج وقف عائلي مشترك (60% ذرية + 40% أوجه البر)
from waqf import allocate
mixed = pd.Series({"family": 0.6, "general_charity": 0.4})
display(allocate.allocate(allocate.Plan(10_000_000, s["rate_base"]), mixed).round(1))
"""),
    md("""
## 8. التحقق من قابلية إعادة التشغيل
نكتب المخرجات ونرسم الأشكال ثم نتأكد أن الأرقام المحفوظة تطابق ما حسبه الدفتر الآن.
"""),
    code("""
pipeline.write_outputs(res)
pipeline.step_figures(c, sec, ix, fc, sp, al)
saved = json.loads((config.TABLES / "key_numbers.json").read_text(encoding="utf-8"))
assert saved["spending"]["rate_base"] == res.key["spending"]["rate_base"]
assert abs(saved["forecast"]["point_pct"] - res.key["forecast"]["point_pct"]) < 1e-12
print("✔ key_numbers.json يطابق الحساب الحالي")
"""),
    md("""
## 9. التوصيات
1. **اعتماد سقف صرف 1.5% سنوياً** من متوسط قيمة الوقف (12 ربعاً) كخط أساس لحفظ الأصل الحقيقي بثقة 60%، ومراجعته سنوياً بهذا النموذج.
2. **مراجعة سياسات توزيع الصناديق الوقفية:** معدلات 3–8% الحالية تعني تآكل القيمة الحقيقية؛ يُقترح ربط التوزيع بالعائد الممهَّد لا بالعائد السنوي.
3. **تخصيص عمارة الوقف واحتياطي استقرار** قبل الصرف، لامتصاص السنوات السالبة (احتمالها ≈ 24% في أي سنة).
4. **توجيه حصة "أوجه البر" (25% من المصارف)** نحو الاحتياجات المتكررة المهمَلة (الأيتام، الأرامل، الفقراء، السكن).
5. **مطالبة الجهات بنشر بيانات أدق:** صافي الأصول الفعلي ومبالغ التوزيع لكل صندوق، والمستفيدين حسب المنطقة والمصرف.

## 10. حدود التحليل (بشفافية)
- الصناديق المدرجة **وكيل** لأداء الاستثمار الوقفي، لا القوائم المالية لوقف عائلي بعينه.
- التاريخ قصير (أطوله ≈ 7 سنوات) والصناديق الحية فقط (تحيز البقاء) ← عالجناه بسيناريو ضغط.
- حجم التوزيعات **مقدَّر** من فجوة الأقران، لأن تداول لا ينشر مبالغها.
- بيانات المستفيدين وطنية لثلاث سنوات فقط، فالتوزيع يعتمد على شروط الواقفين وأوزان أولوية معلنة لا على احتياج مقاس.
"""),
]


def main() -> None:
    nb = nbf.v4.new_notebook()
    nb.cells = CELLS
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    nb.metadata["language_info"] = {"name": "python"}
    NotebookClient(nb, timeout=600, kernel_name="python3", resources={"metadata": {"path": str(ROOT)}}).execute()
    nbf.write(nb, ROOT / "analysis.ipynb")
    print("analysis.ipynb written and executed")


if __name__ == "__main__":
    main()
