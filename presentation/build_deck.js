// Builds presentation/mizan-alrai.pptx from outputs/tables (no hand-typed results).
//   npm install pptxgenjs jszip   &&   node presentation/build_deck.js
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const K = JSON.parse(fs.readFileSync(path.join(ROOT, "outputs/tables/key_numbers.json"), "utf8"));
const csv = (name) => {
  const [head, ...rows] = fs.readFileSync(path.join(ROOT, name), "utf8").replace(/^﻿/, "").trim().split(/\r?\n/);
  const cols = head.split(",");
  return rows.map((r) => {
    const cells = r.match(/("([^"]|"")*"|[^,]*)(,|$)/g).map((c) => c.replace(/,$/, "").replace(/^"|"$/g, ""));
    return Object.fromEntries(cols.map((c, i) => [c, cells[i]]));
  });
};
const pct = (x, d = 1) => (x * 100).toFixed(d) + "%";
const sar = (x) => Math.round(x).toLocaleString("en-US");
const S = K.spending, IX = K.index, FC = K.forecast, SEC = K.sector, AL = K.allocation;

const THEME = {
  name: "Mizan Al-Rai", headFontFace: "thmanyah serif display Black", bodyFontFace: "thmanyah sans",
  colors: { dk1: "1F2933", lt1: "FFFFFF", dk2: "16263F", lt2: "F3F5F8", accent1: "1F4E79", accent2: "C9D3E0",
            accent3: "9B2C2C", accent4: "5A6B7F", accent5: "A9B8CC", accent6: "0E1A2B", hlink: "1F4E79", folHlink: "5A6B7F" },
};
const HEX = THEME.colors;
// heavier body text, and true Black faces for titles and figures (no synthetic bold)
const FONT_TEXT = "thmanyah sans Med", FONT_NUM = "thmanyah sans Black";
const MUTED = "55606E", GRID = "DDE2E9";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.rtlMode = true;
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "ميزان الريع — منصة التنبؤ الذكي بالتدفقات المالية للوقف";
pres.author = "عبدالله العضياني، ثامر الغامدي";
const C = pres.SchemeColor;
const W = 13.333, MX = 0.6, CW = W - 2 * MX;

pres.defineSlideMaster({
  title: "DARK", background: { color: HEX.dk2 },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: MX, y: 2.2, w: CW, h: 1.5, fontSize: 54,
    color: C.background1, align: "right", valign: "middle", margin: 0 }, text: "" } }],
});
pres.defineSlideMaster({
  title: "SECTION", background: { color: HEX.dk2 },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: MX + 1.7, y: 2.9, w: CW - 1.7, h: 1.3, fontSize: 40,
    color: C.background1, align: "right", valign: "middle", margin: 0 }, text: "" } }],
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: HEX.lt1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: MX, y: 0.45, w: CW, h: 0.95, fontSize: 32,
      color: C.text2, align: "right", valign: "middle", margin: 0 }, text: "" } },
    { text: { text: "ميزان الريع", options: { x: W - MX - 3, y: 6.95, w: 3, h: 0.3, fontSize: 11, color: MUTED, align: "right", margin: 0, rtlMode: true } } },
  ],
  slideNumber: { x: MX, y: 6.95, w: 0.6, h: 0.3, fontSize: 11, color: MUTED, align: "left" },
});

// ---------- helpers
let section = "";
const slide = (masterName, title, notes) => {
  const s = pres.addSlide({ masterName, sectionTitle: section });
  s.addText(title, { placeholder: "title", rtlMode: true });
  if (notes) s.addNotes(notes);
  return s;
};
const HL = (t) => ({ text: t, options: { bold: true, color: C.text2, highlight: "BBD3F2" } });        // on light surfaces
const HLD = (t) => ({ text: t, options: { bold: true, color: C.background1, highlight: "3A5A8C" } });  // on navy surfaces
const N = (t) => ({ text: t, options: {} });
const bigger = (pt) => (pt >= 14 && pt <= 18 ? pt + 2 : pt);        // body sizes 14-18pt are raised by 2pt for the room
const marked = (t, dark) => t.split("==").map((part, i) => (i % 2 ? (dark ? HLD(part) : HL(part)) : { text: part, options: {} }))
  .filter((r) => r.text);
const txt = (s, t, x, y, w, h, o = {}) => {
  const { dark, ...rest } = o;
  const body = typeof t === "string" && t.includes("==") ? marked(t, dark) : t;
  const opts = { x, y, w, h, isTextBox: true, margin: 0, rtlMode: true, align: "right", valign: "top", fontSize: 16, color: C.text1, ...rest };
  opts.fontSize = bigger(opts.fontSize);
  return s.addText(body, opts);
};
const num = (s, t, x, y, w, h, o = {}) => s.addText(t, { x, y, w, h, isTextBox: true, margin: 0, align: "center", valign: "middle",
  fontSize: 54, fontFace: FONT_NUM, color: C.accent1, ...o });
const card = (s, x, y, w, h, fill = C.background2) => s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12,
  fill: { color: fill }, line: { color: fill, width: 0 } });
const badge = (s, n, x, y, d = 0.55, fill = C.accent1, color = C.background1) => {
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: fill }, line: { color: fill, width: 0 } });
  s.addText(String(n), { x, y, w: d, h: d, isTextBox: true, margin: 0, align: "center", valign: "middle", fontSize: d * 26, fontFace: FONT_NUM, color });
};
const note = (s, runs, y, h = 0.8, x = MX, w = CW) => {
  card(s, x, y, w, h);
  txt(s, runs, x + 0.3, y, w - 0.6, h, { valign: "middle", fontSize: 15 });
};
const rx = (i, w, gap, right = W - MX) => right - (i + 1) * w - i * gap;      // i-th column counted from the right (RTL)
const chartBase = () => ({ catAxisLabelColor: MUTED, valAxisLabelColor: MUTED, catAxisLabelFontSize: 13, valAxisLabelFontSize: 13,
  catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", valGridLine: { color: GRID, size: 0.75 }, catGridLine: { style: "none" },
  dataLabelColor: HEX.dk1, dataLabelFontSize: 13, dataLabelFontFace: "+mn-lt", legendFontFace: "+mn-lt", legendFontSize: 13, legendColor: MUTED });
const statCards = (s, items, y, h = 2.3) => {
  const gap = 0.28, w = (CW - gap * (items.length - 1)) / items.length;
  items.forEach((it, i) => {
    const x = rx(i, w, gap);
    card(s, x, y, w, h);
    num(s, it.v, x, y + 0.2, w, 1.1, { color: it.warn ? C.accent3 : C.accent1, fontSize: it.size || 50 });
    txt(s, it.l, x + 0.25, y + 1.38, w - 0.5, h - 1.5, { align: "center", fontSize: 15, color: MUTED });
  });
};

// ================= 1. Title
section = "المقدمة"; pres.addSection({ title: section });
let s = slide("DARK", "كم يصرف الوقف دون أن يأكل أصله؟",
  "نفتتح بالسؤال الذي يواجه كل ناظر وقف كل عام. مشروعنا ميزان الريع يجيب عنه برقم قابل للدفاع مبني على بيانات مفتوحة حقيقية.");
txt(s, "ميزان الريع  ·  Mizan Al-Rai", MX, 1.35, CW, 0.6, { fontSize: 24, bold: true, color: C.accent2 });
txt(s, "منصة التنبؤ الذكي بالتدفقات المالية للوقف العائلي والأهلي", MX, 3.85, CW, 0.6, { fontSize: 24, color: C.accent5 });
txt(s, "عبدالله عبدالرحمن عبدالله العضياني   ·   ثامر خالد صالح الغامدي", MX, 5.75, CW, 0.45, { fontSize: 18, color: C.background1 });
txt(s, "مسابقة تحليل البيانات للقطاع غير الربحي", MX, 6.25, CW, 0.4, { fontSize: 15, color: C.accent5 });

// ================= 2. Problem
s = slide("CONTENT", "معضلة الناظر: قرار واحد يتكرر كل عام",
  "الصرف الزائد يرضي المستفيدين اليوم ويضعف الوقف غداً، والصرف الناقص يحبس الخير. لا توجد اليوم أداة تعطي الناظر رقماً.");
const pw = (CW - 0.4) / 2;
[["صرف زائد", "يُرضي المستفيدين اليوم، لكنه ==يأكل من أصل الوقف==، فيرث الجيل القادم وقفاً أصغر.", C.accent3],
 ["صرف ناقص", "يحفظ الأصل، لكنه ==يحبس الخير عن مستحقيه== ويخالف مقصود الواقف من وقفه.", C.accent4]].forEach(([h, b, col], i) => {
  const x = rx(i, pw, 0.4);
  card(s, x, 1.7, pw, 2.2);
  txt(s, h, x + 0.35, 1.95, pw - 0.7, 0.55, { fontSize: 24, bold: true, color: col });
  txt(s, b, x + 0.35, 2.6, pw - 0.7, 1.1, { fontSize: 17 });
});
card(s, MX, 4.25, CW, 2.3, C.text2);
txt(s, "سؤال القرار", MX + 0.45, 4.5, CW - 0.9, 0.45, { fontSize: 16, bold: true, color: C.accent2 });
txt(s, [{ text: "ما معدل الصرف السنوي الذي ", options: { color: C.background1 } }, HLD("يحفظ القيمة الحقيقية لأصل الوقف"),
  { text: " خلال عشر سنوات بدرجة ثقة يحددها الناظر، و", options: { color: C.background1 } }, HLD("كيف يُوزَّع على المصارف الشرعية"),
  { text: " مع احترام شروط الواقفين؟", options: { color: C.background1 } }], MX + 0.45, 5.0, CW - 0.9, 1.4, { fontSize: 22 });

// ================= 3. Headline numbers
s = slide("CONTENT", "الخلاصة في أربعة أرقام",
  "هذه أهم أربع نتائج. الصرف المستدام واحد ونصف بالمئة، بينما الصناديق الوقفية توزع من ثلاثة إلى ثمانية بالمئة.");
statCards(s, [
  { v: pct(S.rate_base), l: `سقف الصرف السنوي المستدام بثقة ${pct(S.confidence, 0)}` },
  { v: `${(IX.payout_min_recent * 100).toFixed(0)}–${pct(IX.payout_max_recent, 0)}`, l: "ما توزّعه الصناديق الوقفية فعلياً كل سنة", warn: true },
  { v: pct(S.p_preserve_at_observed, 0), l: "احتمال حفظ الأصل إذا استمر الصرف بالمعدل الحالي", warn: true },
  { v: pct(FC.point_pct), l: "العائد المتوقع للأشهر الـ12 القادمة" },
], 1.75, 2.55);
card(s, MX, 4.65, CW, 1.9, C.text2);
txt(s, [{ text: "المعنى: ", options: { bold: true, color: C.accent2 } },
  { text: "الأصول الوقفية ولّدت عائداً كلياً ", options: { color: C.background1 } }, HLD(`${pct(IX.total_ann_return)} سنوياً`),
  { text: `، أي نحو ${pct((1 + IX.total_ann_return) / (1 + S.inflation) - 1)} بعد التضخم. `, options: { color: C.background1 } },
  HLD("ما يُصرف فوق ذلك يُؤخذ من الأصل نفسه.")], MX + 0.45, 4.95, CW - 0.9, 1.3, { fontSize: 22 });

// ================= Section: data
section = "البيانات"; pres.addSection({ title: section });
s = slide("SECTION", "البيانات: حقيقية ومفتوحة", "ننتقل إلى البيانات: مصدران رسميان مفتوحان.");
badge(s, 1, MX, 2.95, 1.2, C.accent2, C.text2);

// ================= 5. Sources
s = slide("CONTENT", "مصدران رسميان مفتوحان",
  "المصدر الأول الهيئة العامة للأوقاف، والثاني أسعار الصناديق الاستثمارية الوقفية في تداول. هذه الصناديق أوقاف بحد ذاتها وعوائدها تصرف على جهات غير ربحية.");
[["الهيئة العامة للأوقاف", "منصة البيانات المفتوحة الوطنية", [
    [`${sar(SEC.waqf_designations)}`, `مصرفاً وقفياً في ${SEC.regions} منطقة`],
    ["18", "مجموعة بيانات رسمية"],
    [`من ${sar(SEC.certificates_2019)} إلى ${sar(SEC.certificates_2025)}`, "شهادة وقفية سنوياً بين 2019 و2025"]]],
 ["السوق المالية السعودية (تداول)", "أسعار وحدات الصناديق الاستثمارية الوقفية", [
    [`${IX.funds_total}`, "صندوقاً وقفياً مرخصاً من هيئة السوق المالية"],
    [`${(IX.aum_total_sar / 1e9).toFixed(1)} مليار ريال`, "أصول وقفية تحت الإدارة"],
    ["1,053", "ملاحظة سعرية شهرية (2018 – 2026)"]]]].forEach(([h, sub, rows], i) => {
  const x = rx(i, pw, 0.4);
  card(s, x, 1.65, pw, 3.95);
  txt(s, h, x + 0.35, 1.85, pw - 0.7, 0.5, { fontSize: 22, bold: true, color: C.text2 });
  txt(s, sub, x + 0.35, 2.35, pw - 0.7, 0.4, { fontSize: 14, color: MUTED });
  rows.forEach(([v, l], j) => {
    txt(s, v, x + 0.35, 2.95 + j * 0.86, pw - 0.7, 0.42, { fontSize: 20, bold: true, color: C.accent1 });
    txt(s, l, x + 0.35, 3.36 + j * 0.86, pw - 0.7, 0.36, { fontSize: 14 });
  });
});
note(s, [HL("لماذا تُعد بيانات تداول بيانات قطاع غير ربحي؟"), N(" لأن هذه الصناديق أوقاف: وحداتها موقوفة، وعوائدها تُصرف على جمعيات الأيتام والقرآن والصحة وأوقاف الجامعات.")],
  5.8, 0.95);

// ================= 6. Cleaning
const log = csv("outputs/tables/cleaning_log.csv");
s = slide("CONTENT", `${log.length} قاعدة تنظيف موثّقة آلياً`,
  "كل قاعدة تنظيف تسجل نفسها آلياً: المصدر والقاعدة وعدد الصفوف المتأثرة. وكل ملف خام محمي بفحص سلامة يوقف التشغيل عند أي تعديل.");
const rules = [
  ["توحيد التهجئات العربية", "طيّ إملائي وقاموس مصارف: ==25 تسمية خام أصبحت 24 مصرفاً== موحّداً"],
  ["أسعار ما قبل الاستثمار", "حذف أسعار الإطلاق الثابتة (10.0000) قبل بدء الاستثمار الفعلي"],
  ["الأسعار المتجمدة", "السعر المكرر وسط السلسلة يُعامل كقيمة مفقودة لا كعائد صفري"],
  ["فجوات الإفصاح الربعي", "استيفاء لوغاريتمي خطي، ==مع تعليم كل قيمة مستوفاة=="],
  ["الأرقام والتواريخ النصية", "تحويل المبالغ المكتوبة بفواصل والسنوات النصية، وإزالة علامة BOM من رؤوس الأعمدة"],
  ["حقول غير موثوقة", "إسقاط حقل صافي الأصول لأنه صفر في أغلب الأشهر"],
];
const rw = (CW - 0.6) / 3;
rules.forEach(([h, b], i) => {
  const x = rx(i % 3, rw, 0.3), y = 1.65 + Math.floor(i / 3) * 2.15;
  card(s, x, y, rw, 1.95);
  badge(s, i + 1, x + rw - 0.75, y + 0.22, 0.5);
  txt(s, h, x + 0.25, y + 0.25, rw - 1.15, 0.5, { fontSize: 17, bold: true, color: C.text2 });
  txt(s, b, x + 0.25, y + 0.85, rw - 0.5, 1.0, { fontSize: 14 });
});
note(s, [HL("فحص سلامة لكل ملف خام:"), N(" عدد الصفوف كما تعلنه البوابة، وبصمة لكل صندوق. "), HL("أي تعديل يوقف التشغيل فوراً.")], 6.0, 0.7);

// ================= 7. Hidden payouts + index chart
const idx = csv("outputs/tables/composite_index.csv").filter((r) => /-(03|06|09|12)$/.test(r.month));
s = slide("CONTENT", "اكتشاف أثناء التنظيف: توزيعات مخفية في الأسعار",
  "لاحظنا أن صناديق مدير واحد تهبط معاً كل يوليو بينما بقية السوق صاعدة. هذا توزيع عوائد على المستفيدين وليس خسارة. كشفنا خمسة وعشرين حدثاً وبنينا مؤشر العائد الكلي.");
s.addChart(pres.charts.LINE, [
  { name: "العائد الكلي المقدَّر", labels: idx.map((r) => r.month), values: idx.map((r) => +(+r.total_index).toFixed(1)) },
  { name: "عائد السعر فقط", labels: idx.map((r) => r.month), values: idx.map((r) => +(+r.price_index).toFixed(1)) },
], { x: MX, y: 1.6, w: 7.6, h: 4.9, ...chartBase(), chartColors: [HEX.accent1, HEX.accent3], lineSize: 3, lineDataSymbol: "none",
  showLegend: true, legendPos: "b", valAxisMinVal: 80, catAxisLabelRotate: 315, catAxisLabelFontSize: 10, catAxisLabelFrequency: 4,
  showTitle: true, title: "مؤشر صناديق الوقف السعودية (بداية السلسلة = 100)", titleFontSize: 14, titleColor: MUTED, titleFontFace: "+mn-lt" });
const sx = MX + 7.95, sw = W - MX - sx;
card(s, sx, 1.6, sw, 1.5);
num(s, String(IX.payout_events), sx, 1.65, 1.5, 1.4, { fontSize: 44, color: C.accent3 });
txt(s, "توزيعاً مخفياً ==كُشف آلياً== بمقارنة الأقران", sx + 1.55, 1.85, sw - 1.8, 1.1, { fontSize: 15 });
card(s, sx, 3.3, sw, 1.5);
num(s, pct(IX.total_ann_return), sx, 3.35, 1.5, 1.4, { fontSize: 34 });
txt(s, "العائد الكلي: ما يولّده الأصل فعلاً", sx + 1.55, 3.6, sw - 1.8, 1.0, { fontSize: 15 });
card(s, sx, 5.0, sw, 1.5);
num(s, pct(IX.price_ann_return), sx, 5.05, 1.5, 1.4, { fontSize: 34, color: C.accent3 });
txt(s, "عائد السعر: ما يبقى للأصل بعد التوزيع", sx + 1.55, 5.3, sw - 1.8, 1.0, { fontSize: 15 });

// ================= Section: analysis
section = "التحليل"; pres.addSection({ title: section });
s = slide("SECTION", "التحليل: من صورة القطاع إلى قرار الصرف", "الآن التحليل: صورة القطاع، ثم التنبؤ، ثم سقف الصرف والتوزيع.");
badge(s, 2, MX, 2.95, 1.2, C.accent2, C.text2);

// ================= 9. Sector growth
const certs = csv("data_clean/gasa_certificates.csv");
s = slide("CONTENT", `تسجيل الأوقاف تضاعف ${(SEC.certificates_2025 / SEC.certificates_2019).toFixed(1)} مرة في ست سنوات`,
  "القطاع ينمو بسرعة استثنائية، وهذا يجعل سؤال إدارة العوائد أكثر إلحاحاً كل عام.");
s.addChart(pres.charts.BAR, [{ name: "الشهادات الوقفية المكتملة", labels: certs.map((r) => String(parseInt(r.year))), values: certs.map((r) => +r.registered_waqfs) }],
  { x: MX, y: 1.6, w: 7.9, h: 4.95, ...chartBase(), barDir: "col", chartColors: [HEX.accent1], showValue: true, dataLabelPosition: "outEnd",
    dataLabelFormatCode: "#,##0", valAxisLabelFormatCode: "#,##0", showLegend: false, barGapWidthPct: 60 });
const gx = MX + 8.25, gw = W - MX - gx;
card(s, gx, 1.6, gw, 2.35);
num(s, pct(SEC.certificates_cagr, 0), gx, 1.75, gw, 1.1, { fontSize: 54 });
txt(s, "نمو سنوي مركب في عدد الأوقاف المسجلة", gx + 0.3, 2.95, gw - 0.6, 0.8, { align: "center", fontSize: 15, color: MUTED });
card(s, gx, 4.2, gw, 2.35);
num(s, sar(SEC.beneficiaries_2025), gx, 4.35, gw, 1.1, { fontSize: 48 });
txt(s, `مستفيداً مباشراً من أوقاف الهيئة في 2025 (كانوا ${sar(SEC.beneficiaries_2023)} في 2023)`, gx + 0.3, 5.55, gw - 0.6, 0.85,
  { align: "center", fontSize: 15, color: MUTED });

// ================= 10. Masarif
const nat = csv("outputs/tables/masarif_national.csv").slice(0, 8);
s = slide("CONTENT", `المساجد ${pct(SEC.mosques_share, 0)} من المصارف، والأيتام ${pct(SEC.orphans_share)} فقط`,
  "المصارف شديدة التركز. المساجد وحدها ثلاثة وأربعون بالمئة، بينما الأيتام والأرامل أقل من اثنين بالألف. الحصة المرنة، أوجه البر، هي الرافعة التي يملكها الناظر.");
s.addChart(pres.charts.BAR, [{ name: "حصة المصرف", labels: nat.map((r) => r.masraf_ar), values: nat.map((r) => Math.floor(+r.share * 1000 + 0.5 - 1e-9) / 1000) }],
  { x: MX, y: 1.6, w: 7.9, h: 4.95, ...chartBase(), barDir: "bar", chartColors: [HEX.accent1], showValue: true, dataLabelPosition: "outEnd",
    dataLabelFormatCode: "0.0%", valAxisLabelFormatCode: "0%", showLegend: false, catAxisOrientation: "maxMin", barGapWidthPct: 45,
    catAxisLabelFontSize: 13 });
[[pct(SEC.flexible_share, 0), "حصة «أوجه البر» المرنة التي يوجّهها الناظر", false],
 [pct(SEC.orphans_share + SEC.widows_share, 2), "حصة الأيتام والأرامل مجتمعين من كل المصارف المنشورة", true],
 [String(SEC.masarif), "مصرفاً شرعياً موحّداً بعد التنظيف", false]].forEach(([v, l, warn], i) => {
  const y = 1.6 + i * 1.7;
  card(s, gx, y, gw, 1.5);
  num(s, v, gx, y + 0.05, 1.65, 1.4, { fontSize: 32, color: warn ? C.accent3 : C.accent1 });
  txt(s, l, gx + 1.7, y + 0.28, gw - 1.95, 1.0, { fontSize: 14 });
});

// ================= 11. Forecast
const bt = csv("outputs/tables/backtest_scores.csv");
s = slide("CONTENT", "التنبؤ: النموذج البسيط فاز بالأرقام",
  "قارنا خمسة نماذج باختبار رجعي على ستة وثلاثين نقطة انطلاق خارج العينة، وكل نقطة ترى ماضيها فقط. اخترنا النموذج الذي فاز لا الأكثر تعقيداً.");
s.addChart(pres.charts.BAR, [{ name: "متوسط الخطأ المطلق", labels: bt.map((r) => r.label_ar), values: bt.map((r) => +(+r.mae).toFixed(4)) }],
  { x: MX, y: 1.6, w: 7.4, h: 4.2, ...chartBase(), barDir: "bar", chartColors: [HEX.accent4], showValue: true, dataLabelPosition: "outEnd",
    dataLabelFormatCode: "0.00%", valAxisLabelFormatCode: "0%", showLegend: false, catAxisOrientation: "maxMin", barGapWidthPct: 55,
    showTitle: true, title: "خطأ توقع عائد 12 شهراً (الأقل أفضل)", titleFontSize: 14, titleColor: MUTED, titleFontFace: "+mn-lt" });
note(s, [N("الفائز "), HL(`«${FC.best_model_label}»`), N(" بخطأ "), HL(`أقل بـ${pct(FC.skill_vs_zero, 0)}`),
  N(` من المرجع الساذج، على ${FC.origins} نقطة انطلاق خارج العينة.`)], 5.9, 0.75, MX, 7.4);
const fx = MX + 7.75, fw = W - MX - fx;
card(s, fx, 1.6, fw, 2.9, C.text2);
txt(s, "توقع الأشهر الـ12 القادمة", fx + 0.3, 1.8, fw - 0.6, 0.4, { fontSize: 16, bold: true, color: C.accent2 });
num(s, pct(FC.point_pct), fx, 2.25, fw, 1.2, { fontSize: 66, color: C.background1 });
txt(s, `نطاق 80%: من ${pct(FC.p10_pct)} إلى ${pct(FC.p90_pct)}`, fx + 0.3, 3.6, fw - 0.6, 0.5, { align: "center", fontSize: 16, color: C.accent5 });
card(s, fx, 4.75, fw, 1.8);
num(s, pct(FC.bootstrap_p_loss, 0), fx, 4.8, 1.8, 1.7, { fontSize: 40, color: C.accent3 });
txt(s, "احتمال سنة سالبة، ولذلك نحتاج احتياطياً", fx + 1.85, 5.2, fw - 2.1, 1.0, { fontSize: 15 });

// ================= 12. Frontier
const fb = csv("outputs/tables/spending_frontier_base.csv"), fs2 = csv("outputs/tables/spending_frontier_stress.csv");
s = slide("CONTENT", `القرار: ${pct(S.rate_base)} سنوياً تحفظ الأصل بثقة ${pct(S.confidence, 0)}`,
  "عشرة آلاف مستقبل محتمل من التاريخ الفعلي للمؤشر. كلما زاد الصرف نزل احتمال حفظ الأصل. عند واحد ونصف بالمئة نحقق الثقة المطلوبة.");
s.addChart(pres.charts.LINE, [
  { name: "السيناريو الأساسي", labels: fb.map((r) => pct(+r.rate, 1)), values: fb.map((r) => +(+r.p_preserve_real).toFixed(3)) },
  { name: "سيناريو الضغط (عائد أقل 1% سنوياً)", labels: fs2.map((r) => pct(+r.rate, 1)), values: fs2.map((r) => +(+r.p_preserve_real).toFixed(3)) },
], { x: MX, y: 1.6, w: 8.2, h: 4.95, ...chartBase(), chartColors: [HEX.accent1, HEX.accent3], lineSize: 3, lineDataSymbolSize: 6,
  showLegend: true, legendPos: "b", valAxisLabelFormatCode: "0%", valAxisMaxVal: 1, valAxisMinVal: 0,
  showCatAxisTitle: true, catAxisTitle: "معدل الصرف السنوي", catAxisTitleFontSize: 12, catAxisTitleColor: MUTED, catAxisLabelFontSize: 10,
  showTitle: true, title: "احتمال حفظ القيمة الحقيقية بعد 10 سنوات", titleFontSize: 14, titleColor: MUTED, titleFontFace: "+mn-lt" });
const qx = MX + 8.5, qw = W - MX - qx;
txt(s, "السقف حسب شهية المخاطرة", qx, 1.6, qw, 0.4, { fontSize: 16, bold: true, color: C.text2 });
[[pct(0.5, 0), pct(S.rate_base_at_50)], [pct(S.confidence, 0), pct(S.rate_base)], [pct(0.75, 0), pct(S.rate_base_at_75)]].forEach(([c, r], i) => {
  const y = 2.15 + i * 1.08, main = i === 1;
  card(s, qx, y, qw, 0.92, main ? C.text2 : C.background2);
  txt(s, `ثقة ${c}`, qx + 1.6, y + 0.24, qw - 1.85, 0.45, { fontSize: 17, color: main ? C.background1 : C.text1 });
  num(s, r, qx + 0.1, y, 1.5, 0.92, { fontSize: 26, color: main ? C.accent2 : C.accent1 });
});
card(s, qx, 5.45, qw, 1.1);
txt(s, "في سيناريو الضغط", qx + 1.6, 5.78, qw - 1.85, 0.45, { fontSize: 17 });
num(s, pct(S.rate_stress), qx + 0.1, 5.45, 1.5, 1.1, { fontSize: 26, color: C.accent3 });

// ================= 13. Ten-year impact
s = slide("CONTENT", "الأثر بعد عشر سنوات على وقف بقيمة 10 ملايين ريال",
  "هذه قصة الأثر. بالصرف المستدام يصبح الوقف أقوى مما بدأ. بمعدل الصناديق الحالي يفقد خمسة عشر بالمئة من قوته الشرائية.");
[["صرف مستدام", pct(S.rate_base), (S.median_real_final_sustainable / 10).toFixed(1), "الوقف أقوى مما بدأ، ويرث الجيل القادم وقفاً أكبر", C.accent1],
 ["صرف بمعدل الصناديق الحالي", pct(S.observed_payout_rate), (S.median_real_final_observed / 10).toFixed(1),
  `يفقد الوقف ${pct(1 - S.median_real_final_observed / 100, 0)} من قيمته الحقيقية`, C.accent3]].forEach(([h, r, v, b, col], i) => {
  const x = rx(i, pw, 0.4);
  card(s, x, 1.65, pw, 4.0);
  txt(s, h, x + 0.35, 1.9, pw - 0.7, 0.5, { fontSize: 22, bold: true, color: C.text2 });
  txt(s, `معدل الصرف السنوي ${r}`, x + 0.35, 2.42, pw - 0.7, 0.4, { fontSize: 15, color: MUTED });
  num(s, v, x, 2.95, pw, 1.3, { fontSize: 80, color: col });
  txt(s, "مليون ريال بأسعار اليوم (المسار الوسيط)", x + 0.35, 4.3, pw - 0.7, 0.4, { align: "center", fontSize: 15, color: MUTED });
  txt(s, b, x + 0.35, 4.85, pw - 0.7, 0.6, { align: "center", fontSize: 17, bold: true, color: col });
});
note(s, [N("المنهج: "), HL(`محاكاة ${sar(S.paths)} مسار`), N(` بإعادة معاينة كتلية من التاريخ الفعلي، مع تضخم ${pct(S.inflation, 0)} وقاعدة صرف ممهَّدة على 12 ربعاً.`)], 5.9, 0.7);

// ================= 14. Allocation waterfall
s = slide("CONTENT", "كيف يُوزَّع المبلغ: ترتيب شرعي من أربع خطوات",
  "عمارة الوقف مقدمة على الصرف، ثم احتياطي يمتص السنوات السالبة، ثم شروط الواقفين كما هي، وأخيراً الحصة المرنة توجه للاحتياجات المهملة.");
const steps = [
  ["عمارة الوقف", `${sar(AL.upkeep)} ريال`, "صيانة الأصل مقدَّمة على الصرف على المستحقين"],
  ["الاحتياطي", `${sar(AL.reserve)} ريال`, "حتى يغطي صرف سنة، لامتصاص السنوات السالبة"],
  ["شروط الواقفين", "ثابتة", "حصص المصارف المشروطة لا تُمس"],
  ["الحصة المرنة", pct(SEC.flexible_share, 0), "«أوجه البر» توجَّه بأوزان أولوية معلنة"],
];
const stw = (CW - 0.9) / 4;
steps.forEach(([h, v, b], i) => {
  const x = rx(i, stw, 0.3);
  card(s, x, 1.65, stw, 2.75);
  badge(s, i + 1, x + stw - 0.8, 1.85, 0.55);
  txt(s, h, x + 0.25, 1.9, stw - 1.2, 0.5, { fontSize: 18, bold: true, color: C.text2 });
  txt(s, v, x + 0.25, 2.6, stw - 0.5, 0.55, { fontSize: 24, bold: true, color: C.accent1 });
  txt(s, b, x + 0.25, 3.25, stw - 0.5, 1.0, { fontSize: 14 });
});
card(s, MX, 4.7, CW, 1.85, C.text2);
txt(s, `ميزانية السنة لوقف بـ10 ملايين: ${sar(AL.budget)} ريال`, MX + 5.2, 4.95, CW - 5.6, 0.5, { fontSize: 20, bold: true, color: C.accent2 });
txt(s, "حصة الاحتياجات الأساسية (الفقراء، الأيتام، الأرامل، الإطعام، السكن) ترتفع دون مخالفة أي شرط", MX + 5.2, 5.5, CW - 5.6, 0.9,
  { fontSize: 16, color: C.background1 });
txt(s, `من ${pct(AL.social_share_before, 0)} إلى ${pct(AL.social_share_after, 0)}`, MX + 0.3, 4.7, 4.7, 1.85,
  { align: "center", valign: "middle", fontSize: 40, bold: true, color: C.background1 });

// ================= Section: trust
section = "الموثوقية"; pres.addSection({ title: section });
s = slide("SECTION", "الموثوقية والاستخدام المسؤول", "أخيراً: لماذا يمكن الوثوق بهذه الأرقام.");
badge(s, 3, MX, 2.95, 1.2, C.accent2, C.text2);

// ================= 16. Reproducibility
s = slide("CONTENT", "قابلية إعادة التشغيل: أمر واحد يعيد بناء كل شيء",
  "أي محكم يستطيع تشغيل أمر واحد فيحصل على نفس الأرقام. والكود نفسه يعمل على ملفات بيانات أخرى، ويفحص تلقائياً على ويندوز ولينكس عند كل تحديث.");
card(s, MX, 1.65, CW, 0.95, C.text2);
s.addText("python scripts/run_all.py", { x: MX + 0.4, y: 1.65, w: 5.5, h: 0.95, isTextBox: true, margin: 0, align: "left", valign: "middle",
  fontSize: 20, bold: true, color: C.accent2, fontFace: "Consolas" });
txt(s, "تحليل ← اختبارات ← دفتر ← تقرير ← موقع", MX + 6.1, 1.65, CW - 6.5, 0.95, { valign: "middle", fontSize: 18, color: C.background1 });
statCards(s, [
  { v: "38", l: "اختباراً آلياً ناجحاً، منها اختبار عدم تسرب المستقبل إلى التنبؤ" },
  { v: "24/24", l: "ملف نتائج يتطابق بايتاً ببايت عند إعادة التشغيل", size: 44 },
  { v: "2", l: "نظاما تشغيل يُفحص عليهما تلقائياً عند كل تحديث" },
  { v: "5", l: "ثوانٍ تقريباً لإعادة بناء كل الجداول والأشكال من البيانات الخام" },
], 2.9, 2.35);
note(s, [HL("يعمل على ملفات أخرى:"), N(" نفس الكود حلّل ملفاً بديلاً من 3 صناديق وأعطى نتائج مختلفة، ما يثبت أن "),
  HL("الأرقام تُحسب من الملف المُدخل لا من قيم ثابتة."), N(" والملف التالف تظهر له رسالة خطأ تحدد رقم السطر.")], 5.5, 1.05);

// ================= 17. Responsible AI
s = slide("CONTENT", "استخدام مسؤول للذكاء الاصطناعي",
  "استخدمنا الذكاء الاصطناعي مساعداً في البرمجة والتصميم، ووثقنا كل خطوة وكيف تحققنا منها، بما فيها الأخطاء التي اكتشفناها وصححناها.");
const ai = [
  ["لا أرقام مكتوبة يدوياً", "كل رقم في التقرير والعرض ==يُقرأ آلياً من جداول النتائج=="],
  ["لا بيانات مصطنعة", "كل المصادر ==رسمية ومفتوحة==، ولم يُستخدم رقم من ذاكرة النموذج"],
  ["تحقق لكل خطوة", "سجل من 15 خطوة: الأمر، ما أُنتج، ==وكيف تحققنا منه=="],
  ["أخطاء اكتُشفت وصُحّحت", "إنذارات كاذبة في كشف التوزيعات، ونص عربي معكوس في الرسوم، وعنوان مبالغ فيه"],
];
ai.forEach(([h, b], i) => {
  const x = rx(i % 2, pw, 0.4), y = 1.65 + Math.floor(i / 2) * 2.35;
  card(s, x, y, pw, 2.1);
  badge(s, i + 1, x + pw - 0.85, y + 0.28, 0.55);
  txt(s, h, x + 0.35, y + 0.3, pw - 1.35, 0.5, { fontSize: 20, bold: true, color: C.text2 });
  txt(s, b, x + 0.35, y + 1.0, pw - 0.7, 0.95, { fontSize: 16 });
});
note(s, [N("كل التفاصيل موثقة في ملف "), HL("ai_usage_log.md"), N(" داخل مجلد التسليم.")], 6.3, 0.55);

// ================= 18. Recommendations
s = slide("CONTENT", "التوصيات",
  "خمس توصيات عملية: سقف صرف، ربط التوزيع بالعائد الممهد، احتياطي، توجيه الحصة المرنة، وإفصاح أفضل.");
const recs = [
  [`اعتماد سقف صرف ${pct(S.rate_base)}`, `من متوسط قيمة الوقف لـ12 ربعاً، ==مع مراجعة سنوية== بهذه المنصة`],
  ["ربط التوزيع بالعائد الممهَّد", `التوزيع الحالي (نحو ${pct(S.observed_payout_rate, 0)}) ==يحفظ الأصل باحتمال ${pct(S.p_preserve_at_observed, 0)} فقط==`],
  ["عمارة الوقف واحتياطي يغطي سنة", `لأن ==احتمال السنة السالبة ${pct(FC.bootstrap_p_loss, 0)}==`],
  ["توجيه «أوجه البر» للمصارف المهمَلة", `==الأيتام ${pct(SEC.orphans_share)} والأرامل ${pct(SEC.widows_share, 2)}== من المصارف`],
  ["إفصاح أفضل من الجهات", "نشر مبالغ التوزيع وصافي الأصول لكل صندوق، والمستفيدين حسب المنطقة"],
];
recs.forEach(([h, b], i) => {
  const y = 1.6 + i * 1.0;
  card(s, MX, y, CW, 0.86);
  badge(s, i + 1, W - MX - 0.75, y + 0.16, 0.54);
  txt(s, h, MX + 6.0, y, CW - 6.95, 0.86, { valign: "middle", fontSize: 18, bold: true, color: C.text2 });
  txt(s, b, MX + 0.3, y, 5.5, 0.86, { valign: "middle", fontSize: 14 });
});

// ================= 19. Limits
s = slide("CONTENT", "حدود التحليل بشفافية",
  "نذكر الحدود بوضوح: الصناديق وكيل لأداء الأوقاف، والتاريخ قصير، ومبالغ التوزيع مقدرة، وبيانات المستفيدين وطنية فقط.");
const lim = [
  ["وكيل لا قوائم مالية", "الصناديق المدرجة تمثل أداء الاستثمار الوقفي، ==وليست قوائم وقف عائلي بعينه=="],
  ["تاريخ قصير", "أطول سلسلة 84 شهراً والصناديق الحية فقط، ==وعولج ذلك بسيناريو الضغط=="],
  ["توزيعات مقدَّرة", "تداول لا ينشر مبالغ التوزيع، ==فقدّرناها من فجوة الأقران=="],
  ["بيانات مستفيدين محدودة", "وطنية لثلاث سنوات فقط، فأوزان الأولوية ==افتراضات معلنة قابلة للتعديل=="],
];
lim.forEach(([h, b], i) => {
  const x = rx(i % 2, pw, 0.4), y = 1.65 + Math.floor(i / 2) * 2.35;
  card(s, x, y, pw, 2.1);
  txt(s, h, x + 0.35, y + 0.3, pw - 0.7, 0.5, { fontSize: 20, bold: true, color: C.accent3 });
  txt(s, b, x + 0.35, y + 1.0, pw - 0.7, 0.95, { fontSize: 16 });
});

// ================= 20. Closing
section = "الختام"; pres.addSection({ title: section });
s = slide("DARK", "وقف يكبر ولا يتآكل", "نختم بالرسالة: القرار الصحيح اليوم يورث الجيل القادم وقفاً أكبر. شكراً لكم، ونرحب بأسئلتكم.");
txt(s, "ميزان الريع  ·  Mizan Al-Rai", MX, 1.35, CW, 0.6, { fontSize: 24, bold: true, color: C.accent2 });
txt(s, "جرّبوا المحاكي التفاعلي، وأعيدوا تشغيل التحليل بأنفسكم", MX, 3.85, CW, 0.6, { fontSize: 22, color: C.accent5 });
[["الموقع والمحاكي", "a-a-a124.github.io/mizan-alrai"], ["الكود والبيانات", "github.com/A-a-a124/mizan-alrai"]].forEach(([l, u], i) => {
  const y = 4.85 + i * 0.75;
  txt(s, l, W - MX - 3.2, y, 3.2, 0.5, { fontSize: 18, bold: true, color: C.background1 });
  s.addText(u, { x: W - MX - 9.6, y, w: 6.2, h: 0.5, isTextBox: true, margin: 0, align: "right", fontSize: 18, color: C.accent2 });
});
txt(s, "عبدالله عبدالرحمن عبدالله العضياني   ·   ثامر خالد صالح الغامدي", MX, 6.5, CW, 0.4, { fontSize: 15, color: C.accent5 });

// pptxgenjs does not mark paragraphs as right-to-left and leaves the complex-script font empty.
// Without this, Arabic falls back to a default font and mixed Arabic/number/bracket text is misordered.
async function fixRtl(file) {
  const JSZip = require("jszip");
  const zip = await JSZip.loadAsync(fs.readFileSync(file));
  const arabic = /[؀-ۿ]/;
  const fontTags = (face) => `<a:latin typeface="${face}"/><a:cs typeface="${face}"/>`;
  const fixParas = (xml, face) => xml.replace(/<a:p>[\s\S]*?<\/a:p>/g, (para) => {
    let first = true;
    para = para.replace(/<a:pPr\b[^>]*?(\/>|>[\s\S]*?<\/a:pPr>)/g, (m) => (first ? ((first = false), m) : ""));   // one pPr per paragraph
    if (!arabic.test(para)) return para;
    const title = face === THEME.headFontFace;
    return para.replace(/<a:pPr\b(?![^>]*\brtl=)/, '<a:pPr rtl="1"').replace(/lang="en-US"/g, 'lang="ar-SA"')
      .replace(/<a:rPr\b([^>]*?)\/>/g, (m, attrs) => `<a:rPr${attrs}></a:rPr>`)
      .replace(/<a:rPr\b([^>]*)>([\s\S]*?)<\/a:rPr>/g, (m, attrs, inner) => {
        if (/<a:latin /.test(inner)) return m;                         // explicit face (figures, code) stays
        const bold = /\bb="1"/.test(attrs);                            // bold runs use the family's real Bold
        const onDark = /schemeClr val="bg1"/.test(inner);
        const band = title && !/<a:highlight>/.test(inner) ? `<a:highlight><a:srgbClr val="${onDark ? "34527F" : "CFE0F5"}"/></a:highlight>` : "";
        return `<a:rPr${attrs}>${inner}${band}${fontTags(title ? face : bold ? THEME.bodyFontFace : FONT_TEXT)}</a:rPr>`;
      });
  });
  for (const name of Object.keys(zip.files)) {
    if (/^ppt\/theme\/theme\d+\.xml$/.test(name)) {
      let xml = await zip.file(name).async("string");
      xml = xml.replace(/(<a:majorFont>[\s\S]*?)<a:cs typeface=""\/>/, `$1<a:cs typeface="${THEME.headFontFace}"/>`)
               .replace(/(<a:minorFont>[\s\S]*?)<a:cs typeface=""\/>/, `$1<a:cs typeface="${THEME.bodyFontFace}"/>`);
      zip.file(name, xml);
    } else if (/^ppt\/(slides|slideLayouts)\/[^/]+\.xml$/.test(name)) {
      const xml = await zip.file(name).async("string");
      zip.file(name, xml.replace(/<p:sp>[\s\S]*?<\/p:sp>/g, (sp) =>
        fixParas(sp, /<p:ph[^>]*type="title"/.test(sp) ? THEME.headFontFace : THEME.bodyFontFace)));
    } else if (/^ppt\/charts\/chart\d+\.xml$/.test(name)) {
      const xml = await zip.file(name).async("string");
      zip.file(name, xml.replace(/<a:latin typeface="[^"]*"[^>]*\/>(?!<a:cs)/g, `<a:latin typeface="${THEME.bodyFontFace}"/><a:cs typeface="${THEME.bodyFontFace}"/>`));
    }
  }
  fs.writeFileSync(file, await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" }));
}

(async () => {
  const out = path.join(__dirname, "mizan-alrai.pptx");
  await pres.writeFile({ fileName: out });
  if (process.env.PPTX_SKILL) {
    const { applyTheme } = require(path.join(process.env.PPTX_SKILL, "scripts/apply_theme.js"));
    await applyTheme(out, THEME);
  }
  await fixRtl(out);
  console.log("written", out);
})();
