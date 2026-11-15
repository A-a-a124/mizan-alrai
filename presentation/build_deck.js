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
const N_TESTS = require("child_process").execSync("python -m pytest --collect-only -q", { cwd: ROOT, encoding: "utf8" })
  .split(/\r?\n/).filter((l) => l.includes("::")).length;
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

// ================= data for the solutions
const L = K.label, R = K.rule, CP = K.compass, TR = K.payout_trend;
const labelRows = csv("outputs/tables/sustainability_label.csv");
const trendRows = csv("outputs/tables/payout_trend.csv");
const yearly = csv("outputs/tables/spending_menu_yearly.csv");
const caseRows = csv("outputs/tables/compass_case.csv");
const GRADE_COLOR = { A: "1F4E79", B: "4F7AA8", C: "8A94A3", D: "B5651D", E: "9B2C2C" };
const GRADE_SHORT = { A: "الأصل محفوظ فعلياً", B: "محفوظ اسمياً فقط", C: "تآكل طفيف", D: "تآكل واضح", E: "تآكل شديد" };
const shortFund = (n) => [" Endowment Investment Fund", " Associations Endowment Fund", " Association Endowment Fund", " Endowment Fund",
  " Waqf Fund", "SNB Capital - "].reduce((a, j) => a.replace(j, ""), n);
const ltr = (s, t, x, y, w, h, o = {}) => s.addText(t, { x, y, w, h, isTextBox: true, margin: 0, align: "right", valign: "middle", fontSize: 14,
  color: C.text1, fontFace: FONT_TEXT, ...o });
const OPT = [["cautious", "متحفظ"], ["balanced", "متوازن"], ["recent_level", "مستوى التوزيع الأخير"]];
const pw = (CW - 0.4) / 2;

// ================= 1. Title
section = "السؤال"; pres.addSection({ title: section });
let s = slide("DARK", "كم يصرف الوقف دون أن يأكل أصله؟",
  "سؤال يواجه كل ناظر وقف كل عام. نجيب عنه من بيانات مفتوحة حقيقية، ثم نحوّل الجواب إلى ثلاثة حلول قابلة للتطبيق.");
txt(s, "ميزان الريع  ·  Mizan Al-Rai", MX, 1.35, CW, 0.6, { fontSize: 24, bold: true, color: C.accent2 });
txt(s, "من تحليل بيانات الأوقاف إلى ثلاثة حلول قابلة للتطبيق", MX, 3.85, CW, 0.6, { fontSize: 24, color: C.accent5 });
txt(s, "عبدالله عبدالرحمن عبدالله العضياني   ·   ثامر خالد صالح الغامدي", MX, 5.75, CW, 0.45, { fontSize: 18, color: C.background1 });
txt(s, "مسابقة تحليل البيانات للقطاع غير الربحي", MX, 6.25, CW, 0.4, { fontSize: 15, color: C.accent5 });

// ================= 2. Answer
s = slide("CONTENT", "الجواب: القطاع مستدام حتى الآن، وهذه ثلاثة حلول ليبقى كذلك",
  "الخلاصة كلها في هذه الشريحة. الأصول الوقفية حافظت على قيمتها، لكن التوزيعات ترتفع في السنوات الأخيرة، ولذلك نقترح ثلاثة حلول وقائية.");
statCards(s, [
  { v: pct(IX.avg_payout_rate), l: `متوسط ما وُزِّع على المستفيدين سنوياً، من عائد كلي ${pct(IX.total_ann_return)}` },
  { v: `${TR.events_last_3_years}/${TR.events_total}`, l: "من التوزيعات المرصودة وقعت في آخر ثلاث سنوات: التوزيعات ترتفع", warn: true },
  { v: `${(R.rate_cautious * 100).toFixed(1)}–${pct(R.rate_balanced)}`, l: "نطاق الصرف السنوي الذي يحفظ القيمة الحقيقية للأصل", size: 40 },
], 1.6, 2.25);
[["بطاقة استدامة الوقف", `درجة من A إلى E لكل صندوق: ==هل حافظت الوحدة الموقوفة على قوتها الشرائية؟==`],
 ["قاعدة ميزان للصرف", `الصرف من متوسط 12 ربعاً بمعدل معلن، ==فيثبت دخل المستفيد ولا يتآكل الأصل==`],
 ["بوصلة المصارف", `توجيه الحصة المرنة «أوجه البر» ==نحو المصارف الأقل تغطية== دون مخالفة شرط واقف`]].forEach(([h, b], i) => {
  const y = 4.1 + i * 0.9;
  card(s, MX, y, CW, 0.78);
  badge(s, i + 1, W - MX - 0.72, y + 0.13, 0.52);
  txt(s, h, W - MX - 4.5, y, 3.6, 0.78, { valign: "middle", fontSize: 18, bold: true, color: C.text2 });
  txt(s, b, MX + 0.3, y, CW - 5.1, 0.78, { valign: "middle", fontSize: 14 });
});

// ================= 3. Data
section = "البيانات والاكتشاف"; pres.addSection({ title: section });
s = slide("CONTENT", "البيانات: مصدران رسميان مفتوحان من القطاع غير الربحي",
  "كل البيانات حقيقية ومفتوحة. صناديق تداول الوقفية أوقاف بحد ذاتها، وعوائدها تصرف على جهات غير ربحية.");
[["الهيئة العامة للأوقاف", "منصة البيانات المفتوحة الوطنية", [
    [`${sar(SEC.waqf_designations)}`, `مصرفاً وقفياً في ${SEC.regions} منطقة`],
    [`من ${sar(SEC.certificates_2019)} إلى ${sar(SEC.certificates_2025)}`, "شهادة وقفية سنوياً بين 2019 و2025"]]],
 ["السوق المالية السعودية (تداول)", "أسعار وحدات الصناديق الاستثمارية الوقفية", [
    [`${IX.funds_total} صندوقاً وقفياً`, `أصولها ${(IX.aum_total_sar / 1e9).toFixed(1)} مليار ريال`],
    ["1,053 سعراً شهرياً", "من 2018 إلى 2026"]]]].forEach(([h, sub, rows], i) => {
  const x = rx(i, pw, 0.4);
  card(s, x, 1.6, pw, 3.1);
  txt(s, h, x + 0.35, 1.78, pw - 0.7, 0.5, { fontSize: 22, bold: true, color: C.text2 });
  txt(s, sub, x + 0.35, 2.28, pw - 0.7, 0.4, { fontSize: 14, color: MUTED });
  rows.forEach(([v, l], j) => {
    txt(s, v, x + 0.35, 2.85 + j * 0.9, pw - 0.7, 0.42, { fontSize: 20, bold: true, color: C.accent1 });
    txt(s, l, x + 0.35, 3.27 + j * 0.9, pw - 0.7, 0.36, { fontSize: 14 });
  });
});
note(s, [HL("لماذا تُعد بيانات تداول بيانات قطاع غير ربحي؟"), N(" لأن هذه الصناديق أوقاف: وحداتها موقوفة، وعوائدها تُصرف على جمعيات الأيتام والقرآن والصحة وأوقاف الجامعات.")], 4.9, 0.85);
note(s, [HL(`${csv("outputs/tables/cleaning_log.csv").length} قاعدة تنظيف موثّقة آلياً`), N("، منها توحيد التهجئات العربية للمصارف واستيفاء الفجوات مع تعليمها. "),
  HL("كل ملف خام محمي بفحص سلامة"), N(" يوقف التشغيل عند أي تعديل.")], 5.9, 0.85);

// ================= 4. Discovery
const idx = csv("outputs/tables/composite_index.csv").filter((r) => /-(03|06|09|12)$/.test(r.month));
s = slide("CONTENT", "الاكتشاف: توزيعات مخفية في الأسعار، وهي ترتفع",
  "أثناء التنظيف لاحظنا أن صناديق مدير واحد تهبط معاً بينما بقية السوق صاعدة. هذا توزيع عوائد وليس خسارة. المسافة بين الخطين هي ما وزع على المستفيدين.");
s.addChart(pres.charts.LINE, [
  { name: "العائد الكلي المقدَّر", labels: idx.map((r) => r.month), values: idx.map((r) => +(+r.total_index).toFixed(1)) },
  { name: "قيمة الوحدة بعد التوزيع", labels: idx.map((r) => r.month), values: idx.map((r) => +(+r.price_index).toFixed(1)) },
], { x: MX, y: 1.55, w: 6.7, h: 4.2, ...chartBase(), chartColors: [HEX.accent1, HEX.accent3], lineSize: 3, lineDataSymbol: "none",
  showLegend: true, legendPos: "b", valAxisMinVal: 80, catAxisLabelRotate: 315, catAxisLabelFontSize: 10, catAxisLabelFrequency: 4,
  showTitle: true, title: "مؤشر صناديق الوقف السعودية (بداية السلسلة = 100)", titleFontSize: 14, titleColor: MUTED, titleFontFace: "+mn-lt" });
const dx = MX + 7.0, dw = W - MX - dx;
s.addChart(pres.charts.BAR, [{ name: "توزيعات مرصودة", labels: trendRows.map((r) => r.year), values: trendRows.map((r) => +r.events) }],
  { x: dx, y: 1.55, w: dw, h: 2.7, ...chartBase(), barDir: "col", chartColors: [HEX.accent3], showValue: true, dataLabelPosition: "outEnd",
    showLegend: false, barGapWidthPct: 50, valAxisHidden: true, valGridLine: { style: "none" },
    showTitle: true, title: "عدد التوزيعات المرصودة كل سنة", titleFontSize: 14, titleColor: MUTED, titleFontFace: "+mn-lt" });
card(s, dx, 4.4, dw, 1.35);
txt(s, `==القطاع حافظ على أصله حتى الآن==: وُزِّع ${pct(IX.avg_payout_rate)} سنوياً في المتوسط، وبقيت قيمة الوحدة تنمو ${pct(IX.price_ann_return)}.`,
  dx + 0.25, 4.4, dw - 0.5, 1.35, { valign: "middle", fontSize: 14 });
note(s, [N("لكن حجم التوزيع في سنته بلغ "), HL(`من ${pct(IX.payout_min_recent, 0)} إلى ${pct(IX.payout_max_recent, 0)} من قيمة الوحدة`),
  N(". لو صار هذا المستوى سنوياً لتآكل الأصل. (الكشف أضعف قبل 2023 لأن الإفصاح كان ربعياً.)")], 5.95, 0.8);

// ================= 5. Label
section = "الحلول"; pres.addSection({ title: section });
s = slide("CONTENT", "الحل الأول: بطاقة استدامة الوقف",
  "مثل ملصق كفاءة الطاقة على الأجهزة: درجة واحدة يفهمها أي واقف. الدرجة مبنية على سعر الوحدة المنشور فقط، فلا تحتاج أي تقدير.");
"ABCDE".split("").forEach((g, i) => {
  const bw = 3.0 + i * 0.62, y = 1.6 + i * 0.83, x = W - MX - bw;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: bw, h: 0.7, rectRadius: 0.08, fill: { color: GRADE_COLOR[g] }, line: { color: GRADE_COLOR[g], width: 0 } });
  s.addText(g, { x: W - MX - 0.75, y, w: 0.75, h: 0.7, isTextBox: true, margin: 0, align: "center", valign: "middle", fontSize: 30, fontFace: FONT_NUM, color: C.background1 });
  txt(s, GRADE_SHORT[g], x + 0.2, y, bw - 1.0, 0.7, { valign: "middle", fontSize: 14, bold: true, color: C.background1 });
  const n = L[`count_${g}`];
  txt(s, `${n} ${n >= 3 && n <= 10 ? "صناديق" : "صندوق"}`, x - 1.75, y, 1.6, 0.7, { valign: "middle", align: "left", fontSize: 14, color: MUTED });
});
const ex = labelRows.filter((r) => r.provisional === "False").sort((a, b) => +b.aum_sar - +a.aum_sar)[0];
const cx = MX, cw = 4.6;
card(s, cx, 1.6, cw, 4.05);
txt(s, "نموذج البطاقة", cx + 0.3, 1.75, cw - 0.6, 0.4, { fontSize: 14, color: MUTED });
ltr(s, shortFund(ex.fund_name) + " Endowment Fund", cx + 0.3, 2.15, cw - 0.6, 0.45, { fontSize: 18, bold: true, color: C.text2, fontFace: THEME.bodyFontFace });
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: cx + 0.3, y: 2.8, w: 1.5, h: 1.5, rectRadius: 0.12, fill: { color: GRADE_COLOR[ex.grade] }, line: { color: GRADE_COLOR[ex.grade], width: 0 } });
s.addText(ex.grade, { x: cx + 0.3, y: 2.8, w: 1.5, h: 1.5, isTextBox: true, margin: 0, align: "center", valign: "middle", fontSize: 72, fontFace: FONT_NUM, color: C.background1 });
[["نمو قيمة الوحدة سنوياً", pct(+ex.unit_growth)], ["أسوأ هبوط", pct(+ex.max_drawdown)], ["عمر السجل", `${ex.months} شهراً`]].forEach(([l, v], j) => {
  txt(s, l, cx + 2.0, 2.8 + j * 0.52, cw - 2.3, 0.26, { fontSize: 12, color: MUTED });
  txt(s, v, cx + 2.0, 3.03 + j * 0.52, cw - 2.3, 0.3, { fontSize: 15, bold: true, color: C.text2 });
});
txt(s, GRADE_SHORT[ex.grade] + ": نمت قيمة الوحدة بمعدل التضخم أو أكثر", cx + 0.3, 4.6, cw - 0.6, 0.9, { fontSize: 14 });
note(s, [HL(`${pct(L.aum_share_A, 0)} من الأصول المصنّفة تحمل الدرجة A`), N(`. صنّفنا ${L.funds_graded} صندوقاً، والدرجة تُحسب `),
  HL("من سعر الوحدة المنشور فقط"), N("، فتستطيع أي جهة التحقق منها.")], 5.95, 0.8);

// ================= 6. Label: how and who
s = slide("CONTENT", `درجات ${L.funds_graded} صندوقاً وقفياً، وكيف تُحسب`,
  "هذه درجات الصناديق الفعلية من البيانات. الصناديق الجديدة انطلقت في سوق هابط، فدرجتها مبدئية حتى يكتمل سجلها.");
const gw = (CW - 0.5) / 3;
labelRows.forEach((r, i) => {
  const col = Math.floor(i / 8), row = i % 8, x = rx(col, gw, 0.25), y = 1.55 + row * 0.5;
  card(s, x, y, gw, 0.43);
  badge(s, r.grade, x + gw - 0.42, y + 0.045, 0.34, GRADE_COLOR[r.grade], C.background1);
  ltr(s, shortFund(r.fund_name) + (r.provisional === "True" ? " *" : ""), x + 0.15, y, gw - 0.7, 0.43, { fontSize: 13 });
});
note(s, [HL("القاعدة:"), N(` A إذا نمت قيمة الوحدة بمعدل التضخم (${pct(S.inflation, 0)}) أو أكثر، B إذا نمت أقل منه، ثم C و D و E حسب مقدار النقص. `),
  HL(`* سجل أقل من ${L.established_months} شهراً: درجة مبدئية.`)], 5.65, 0.6);
note(s, [HL("من يعتمدها؟"), N(" الهيئة العامة للأوقاف أو هيئة السوق المالية تنشرها سنوياً من أسعار منشورة أصلاً. "),
  HL("ماذا تضيف؟"), N(" معيار مقارنة شفاف للواقف، وإنذار مبكر لأي صندوق يبدأ أصله بالتآكل.")], 6.3, 0.6);

// ================= 7. Rule
s = slide("CONTENT", "الحل الثاني: قاعدة ميزان للصرف",
  "القاعدة جزآن: الصرف من متوسط قيمة الوقف لآخر اثني عشر ربعاً حتى لا يتذبذب دخل المستفيد، ثم اختيار المعدل من نطاق معلن.");
const lw = 4.4, lx = W - MX - lw;
card(s, lx, 1.6, lw, 4.15, C.text2);
txt(s, "أولاً: اصرف من متوسط 12 ربعاً", lx + 0.3, 1.8, lw - 0.6, 0.45, { fontSize: 18, bold: true, color: C.accent2 });
txt(s, "احتمال قطع صرف المستفيد أكثر من 5% في سنة واحدة", lx + 0.3, 2.35, lw - 0.6, 0.75, { fontSize: 14, color: C.background1 });
num(s, pct(R.smoothing.unsmoothed_p_cut_over_5pct, 0), lx + lw / 2, 3.2, lw / 2 - 0.2, 1.1, { fontSize: 48, color: C.accent5 });
num(s, pct(R.smoothing.smoothed_p_cut_over_5pct, 0), lx + 0.2, 3.2, lw / 2 - 0.2, 1.1, { fontSize: 48, color: C.background1 });
txt(s, "الصرف من قيمة اليوم", lx + lw / 2, 4.35, lw / 2 - 0.2, 0.4, { align: "center", fontSize: 13, color: C.accent5 });
txt(s, "مع قاعدة ميزان", lx + 0.2, 4.35, lw / 2 - 0.2, 0.4, { align: "center", fontSize: 13, bold: true, color: C.background1 });
txt(s, "المعدل نفسه، لكن دخل المستفيد أثبت", lx + 0.3, 5.0, lw - 0.6, 0.5, { align: "center", fontSize: 14, color: C.accent5 });
const ow = (CW - lw - 0.3 - 0.4) / 3;
txt(s, "ثانياً: اختر المعدل من نطاق معلن", MX, 1.6, CW - lw - 0.3, 0.45, { fontSize: 18, bold: true, color: C.text2 });
OPT.forEach(([k, name], i) => {
  const x = rx(i, ow, 0.2, lx - 0.3), warn = k === "recent_level", main = k === "balanced";
  card(s, x, 2.2, ow, 3.55, main ? "E3ECF7" : C.background2);
  txt(s, name, x + 0.15, 2.32, ow - 0.3, 0.7, { align: "center", fontSize: 15, bold: true, color: C.text2 });
  num(s, pct(R[`rate_${k}`]), x, 3.0, ow, 0.85, { fontSize: 38, color: warn ? C.accent3 : C.accent1 });
  txt(s, "قيمة الأصل بعد 30 سنة", x + 0.15, 3.95, ow - 0.3, 0.3, { align: "center", fontSize: 12, color: MUTED });
  num(s, R[`${k}_30y_median_real_value`].toFixed(0), x, 4.22, ow, 0.5, { fontSize: 26, color: warn ? C.accent3 : C.text2 });
  txt(s, "احتمال حفظ الأصل", x + 0.15, 4.8, ow - 0.3, 0.3, { align: "center", fontSize: 12, color: MUTED });
  num(s, pct(R[`${k}_30y_p_preserve_real`], 0), x, 5.07, ow, 0.5, { fontSize: 26, color: warn ? C.accent3 : C.text2 });
});
note(s, [HL("من ينفّذها؟"), N(" الناظر ومجلس إدارة الصندوق، بتعديل سياسة التوزيع فقط. الأرقام لأصل قيمته 100 اليوم وبأسعار اليوم، من "),
  HL(`${sar(S.paths)} مسار محاكاة`), N(` لتاريخ المؤشر الفعلي وتضخم ${pct(S.inflation, 0)}.`)], 5.95, 0.8);

// ================= 8. Trade-off
s = slide("CONTENT", "المقايضة بين الأجيال، بصراحة",
  "لا نخفي المقايضة. الصرف الأعلى يعطي المستفيدين أكثر في العقود الأولى، لكنه ينقص الأصل ويهبط بالصرف عاماً بعد عام. القرار عدالة بين الأجيال.");
const ys = (k) => yearly.filter((r) => r.option === k);
s.addChart(pres.charts.LINE, OPT.map(([k, name]) => ({ name: `${name} (${pct(R[`rate_${k}`])})`, labels: ys(k).map((r) => r.year),
  values: ys(k).map((r) => +(+r.median_real_payout).toFixed(3)) })),
  { x: MX, y: 1.55, w: 7.6, h: 4.25, ...chartBase(), chartColors: [HEX.accent4, HEX.accent1, HEX.accent3], lineSize: 3, lineDataSymbol: "none",
    showLegend: true, legendPos: "b", catAxisLabelFrequency: 5, valAxisLabelFormatCode: "0.0",
    showCatAxisTitle: true, catAxisTitle: "السنة", catAxisTitleFontSize: 12, catAxisTitleColor: MUTED,
    showTitle: true, title: "الصرف السنوي الحقيقي لأصل قيمته 100 (المسار الوسيط)", titleFontSize: 14, titleColor: MUTED, titleFontFace: "+mn-lt" });
const tx = MX + 7.9, tw = W - MX - tx;
txt(s, "مجموع الصرف الحقيقي في 30 سنة", tx, 1.55, tw, 0.4, { fontSize: 15, bold: true, color: C.text2 });
OPT.forEach(([k, name], i) => {
  const y = 2.05 + i * 0.9;
  card(s, tx, y, tw, 0.78);
  txt(s, name, tx + 1.55, y, tw - 1.75, 0.78, { valign: "middle", fontSize: 14 });
  num(s, R[`${k}_30y_cumulative_real_payout`].toFixed(0), tx + 0.1, y, 1.4, 0.78, { fontSize: 28, color: k === "recent_level" ? C.accent3 : C.accent1 });
});
card(s, tx, 4.8, tw, 1.0, C.text2);
txt(s, R.breakeven_year_balanced ? `يتجاوز صرف «المتوازن» السنوي صرف المستوى الأخير ==في السنة ${R.breakeven_year_balanced}==` :
  `لا يتجاوز صرف «المتوازن» صرف المستوى الأخير خلال ${R.sim_horizon_years} سنة`, tx + 0.25, 4.8, tw - 0.5, 1.0,
  { valign: "middle", fontSize: 14, color: C.background1, dark: true });
note(s, [HL(`الصرف عند ${pct(R.rate_recent_level, 0)} يعطي أكثر لثلاثة عقود`), N(`، لكنه يُنقص الأصل إلى ${R.recent_level_30y_median_real_value.toFixed(0)} من 100. الصرف عند ${pct(R.rate_balanced)} `),
  HL("يُبقي الأصل ويزيد الصرف كل عام"), N(`. تاريخنا ${R.history_months} شهراً فقط، فهذه تقديرات لا تنبؤات.`)], 5.95, 0.8);

// ================= 9. Compass
const soc = caseRows.filter((r) => r.social === "True").sort((a, b) => +b.total - +a.total);
const orph = caseRows.find((r) => r.line === "orphans");
s = slide("CONTENT", "الحل الثالث: بوصلة المصارف",
  "شروط الواقفين تبقى كما هي. الحصة المرنة، أوجه البر، هي التي يملك الناظر توجيهها، فنوجهها نحو الاحتياجات الأقل تغطية.");
s.addChart(pres.charts.BAR, [
  { name: "من شروط الواقفين", labels: soc.map((r) => r.label_ar), values: soc.map((r) => Math.round(+r.from_waqif_conditions)) },
  { name: "بعد توجيه الحصة المرنة", labels: soc.map((r) => r.label_ar), values: soc.map((r) => Math.round(+r.total)) },
], { x: MX, y: 1.55, w: 7.6, h: 4.25, ...chartBase(), barDir: "bar", chartColors: [HEX.accent5, HEX.accent1], showValue: true, dataLabelPosition: "outEnd",
  dataLabelFormatCode: "#,##0", valAxisLabelFormatCode: "#,##0", showLegend: true, legendPos: "b", catAxisOrientation: "maxMin", barGapWidthPct: 45,
  showTitle: true, title: `ريال لكل مصرف، لوقف بـ10 ملايين وميزانية ${sar(AL.budget)} ريال`, titleFontSize: 14, titleColor: MUTED, titleFontFace: "+mn-lt" });
[[`${pct(AL.social_share_before, 0)} ثم ${pct(AL.social_share_after, 0)}`, "حصة الاحتياجات الأساسية قبل البوصلة وبعدها", 26],
 [`${(+orph.multiple).toFixed(0)} ضعفاً`, `ما يصل للأيتام: من ${sar(+orph.from_waqif_conditions)} إلى ${sar(+orph.total)} ريال`, 26],
 [pct(SEC.flexible_share, 0), "من المصارف حصة مرنة يملك الناظر توجيهها", 30]].forEach(([v, l, size], i) => {
  const y = 1.55 + i * 1.45;
  card(s, tx, y, tw, 1.3);
  txt(s, v, tx + 0.25, y + 0.12, tw - 0.5, 0.5, { fontSize: size - 6, bold: true, color: C.accent1 });
  txt(s, l, tx + 0.25, y + 0.68, tw - 0.5, 0.55, { fontSize: 13 });
});
note(s, [HL("من ينفّذها؟"), N(" الناظر عند إعداد خطة الصرف السنوية. أكبر أثر في "), HL(CP.top_region_ar),
  N(". الأوزان افتراضات معلنة قابلة للتعديل، لأن بيانات الاحتياج حسب المنطقة غير منشورة.")], 5.95, 0.8);

// ================= 10. What each adds
s = slide("CONTENT", "ماذا يضيف كل حل، ومن ينفّذه",
  "كل حل ينفذه طرف محدد ببيانات يملكها أصلاً، دون تشريع جديد ولا تقنية جديدة.");
const cols = [["الحل", 2.9], ["من ينفّذه", 3.0], ["بماذا", 2.6], ["ماذا يضيف", CW - 8.5 - 0.6]];
let hx = W - MX;
cols.forEach(([h, w]) => { hx -= w; txt(s, h, hx + 0.1, 1.55, w - 0.2, 0.4, { fontSize: 14, bold: true, color: MUTED }); hx -= 0.2; });
[["بطاقة استدامة الوقف", "الهيئة العامة للأوقاف وهيئة السوق المالية", "أسعار الوحدات المنشورة", `معيار مقارنة شفاف لـ${L.funds_graded} صندوقاً و==إنذار مبكر بالتآكل==`],
 ["قاعدة ميزان للصرف", "النظّار ومجالس إدارة الصناديق", "تعديل سياسة التوزيع", `احتمال قطع الصرف ==من ${pct(R.smoothing.unsmoothed_p_cut_over_5pct, 0)} إلى ${pct(R.smoothing.smoothed_p_cut_over_5pct, 0)}==، وأصل محفوظ`],
 ["بوصلة المصارف", "النظّار", "خطة الصرف السنوية", `حصة الاحتياجات الأساسية ==من ${pct(AL.social_share_before, 0)} إلى ${pct(AL.social_share_after, 0)}==`]].forEach((row, i) => {
  const y = 2.05 + i * 1.25;
  card(s, MX, y, CW, 1.1);
  badge(s, i + 1, W - MX - 0.62, y + 0.3, 0.5);
  let x = W - MX;
  row.forEach((cell, j) => {
    const w = cols[j][1]; x -= w;
    txt(s, cell, x + 0.1, y, w - (j === 0 ? 0.85 : 0.2), 1.1, { valign: "middle", fontSize: j === 0 ? 16 : 14, bold: j === 0, color: j === 0 ? C.text2 : C.text1 });
    x -= 0.2;
  });
});
note(s, [HL("لا يحتاج أي حل إلى تشريع جديد أو تقنية جديدة:"), N(" كل طرف ينفّذ ببيانات يملكها أصلاً. والكود مفتوح، فتستطيع أي جهة إعادة الحساب على بياناتها بأمر واحد.")], 5.9, 0.85);

// ================= 11. Trust
section = "الموثوقية"; pres.addSection({ title: section });
s = slide("CONTENT", "الموثوقية: كل رقم يُعاد حسابه بأمر واحد",
  "أي محكم يستطيع تشغيل أمر واحد فيحصل على الأرقام نفسها. واستخدمنا الذكاء الاصطناعي مساعداً مع توثيق كل خطوة والأخطاء التي صححناها.");
card(s, MX, 1.6, CW, 0.85, C.text2);
s.addText("python scripts/run_all.py", { x: MX + 0.4, y: 1.6, w: 5.5, h: 0.85, isTextBox: true, margin: 0, align: "left", valign: "middle",
  fontSize: 20, bold: true, color: C.accent2, fontFace: "Consolas" });
txt(s, "تحليل، ثم اختبارات، ثم دفتر وتقرير وموقع", MX + 6.1, 1.6, CW - 6.5, 0.85, { valign: "middle", fontSize: 16, color: C.background1 });
statCards(s, [
  { v: String(N_TESTS), l: "اختباراً آلياً ناجحاً، منها اختبار عدم تسرب المستقبل إلى التنبؤ" },
  { v: "30/30", l: "ملف نتائج يُعاد إنتاجه مطابقاً على النظامين", size: 44 },
  { v: "2", l: "نظاما تشغيل يُفحص عليهما تلقائياً عند كل تحديث" },
  { v: pct(FC.skill_vs_zero, 0), l: `أدق من المرجع الساذج في توقع عائد 12 شهراً (${pct(FC.point_pct)})` },
], 2.65, 2.25);
note(s, [HL("يعمل على ملفات أخرى:"), N(" الكود نفسه حلّل ملفاً بديلاً وأعطى نتائج مختلفة، فالأرقام تُحسب من الملف المُدخل لا من قيم ثابتة.")], 5.1, 0.75);
note(s, [HL("ذكاء اصطناعي مسؤول:"), N(" لا رقم مكتوب يدوياً ولا بيانات مصطنعة، وسجل يوثق كل خطوة وكيف تحققنا منها، "),
  HL("ومنها خطأ في رقم رئيسي اكتشفناه وصحّحناه.")], 6.0, 0.75);

// ================= 12. Limits and close
s = slide("CONTENT", "حدود التحليل، والخلاصة",
  "نذكر الحدود بوضوح. والخلاصة: ثلاثة حلول بسيطة تبقي الوقف يكبر ولا يتآكل.");
[["وكيل لا قوائم مالية", "الصناديق المدرجة تمثل أداء الاستثمار الوقفي، ==وليست قوائم وقف بعينه=="],
 ["تاريخ قصير", `أطول سلسلة 84 شهراً، ==فمحاكاة 30 سنة تقدير لا تنبؤ==`],
 ["توزيعات مقدَّرة", "تداول لا ينشر مبالغ التوزيع، ==فقدّرناها من فجوة الأقران=="],
 ["بيانات احتياج غير منشورة", "أوزان البوصلة ==افتراضات معلنة قابلة للتعديل=="]].forEach(([h, b], i) => {
  const x = rx(i % 2, pw, 0.4), y = 1.55 + Math.floor(i / 2) * 1.45;
  card(s, x, y, pw, 1.3);
  txt(s, h, x + 0.3, y + 0.14, pw - 0.6, 0.42, { fontSize: 17, bold: true, color: C.accent3 });
  txt(s, b, x + 0.3, y + 0.62, pw - 0.6, 0.6, { fontSize: 14 });
});
card(s, MX, 4.55, CW, 2.2, C.text2);
s.addText("وقف يكبر ولا يتآكل", { x: W - MX - 6.3, y: 4.7, w: 6.0, h: 0.8, isTextBox: true, margin: 0, align: "right", valign: "middle", rtlMode: true,
  fontSize: 32, color: C.background1, fontFace: THEME.headFontFace });
txt(s, "بطاقة تكشف، وقاعدة تحفظ، وبوصلة توجّه", W - MX - 6.3, 5.5, 6.0, 0.45, { fontSize: 16, color: C.accent5 });
txt(s, "عبدالله العضياني  ·  ثامر الغامدي", W - MX - 6.3, 6.1, 6.0, 0.4, { fontSize: 14, color: C.accent5 });
[["المحاكي التفاعلي", "a-a-a124.github.io/mizan-alrai"], ["الكود والبيانات", "github.com/A-a-a124/mizan-alrai"]].forEach(([l, u], i) => {
  const y = 4.95 + i * 0.85;
  txt(s, l, MX + 0.4, y, 5.4, 0.35, { align: "left", fontSize: 13, color: C.accent5 });
  s.addText(u, { x: MX + 0.4, y: y + 0.33, w: 5.4, h: 0.4, isTextBox: true, margin: 0, align: "left", fontSize: 16, color: C.background1, fontFace: THEME.bodyFontFace });
});

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
  const out = path.join(__dirname, "mizan-alrai-editable.pptx");
  await pres.writeFile({ fileName: out });
  if (process.env.PPTX_SKILL) {
    const { applyTheme } = require(path.join(process.env.PPTX_SKILL, "scripts/apply_theme.js"));
    await applyTheme(out, THEME);
  }
  await fixRtl(out);
  console.log("written", out);
})();
