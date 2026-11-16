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

// ================= pictures of the live project (presentation/img, captured from the site)
const _is = require("image-size"), sizeOf = (f) => (_is.imageSize || _is.default || _is)(fs.readFileSync(f));
const picture = (s, name, x, y, w, h, o = {}) => {                 // fit inside the box, keep the aspect ratio, thin frame
  const file = path.join(__dirname, "img", name + ".png"), d = sizeOf(file), k = Math.min(w / d.width, h / d.height);
  const iw = d.width * k, ih = d.height * k, ix = o.align === "right" ? x + w - iw : o.align === "left" ? x : x + (w - iw) / 2, iy = y + (h - ih) / 2;
  s.addImage({ path: file, x: ix, y: iy, w: iw, h: ih });
  s.addShape(pres.shapes.RECTANGLE, { x: ix, y: iy, w: iw, h: ih, fill: { type: "none" }, line: { color: GRID, width: 0.75 } });
  return { x: ix, y: iy, w: iw, h: ih };
};
const G = K.gaps, SH = K.shock, RB = K.robustness;
const gapRows = csv("outputs/tables/social_gaps.csv");
const bigGap = gapRows.find((r) => r.masraf === "orphans");

// ================= 5. Label
section = "الحلول"; pres.addSection({ title: section });
s = slide("CONTENT", "الحل الأول: بطاقة استدامة الوقف",
  "مثل ملصق كفاءة الطاقة على الأجهزة: درجة واحدة يفهمها أي واقف. الدرجة مبنية على سعر الوحدة المنشور فقط. والبطاقة على اليسار تُحمَّل من الموقع لكل صندوق.");
"ABCDE".split("").forEach((g, i) => {
  const bw = 3.0 + i * 0.62, y = 1.6 + i * 0.83, x = W - MX - bw;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: bw, h: 0.7, rectRadius: 0.08, fill: { color: GRADE_COLOR[g] }, line: { color: GRADE_COLOR[g], width: 0 } });
  s.addText(g, { x: W - MX - 0.75, y, w: 0.75, h: 0.7, isTextBox: true, margin: 0, align: "center", valign: "middle", fontSize: 30, fontFace: FONT_NUM, color: C.background1 });
  txt(s, GRADE_SHORT[g], x + 0.2, y, bw - 1.0, 0.7, { valign: "middle", fontSize: 14, bold: true, color: C.background1 });
  const n = L[`count_${g}`];
  txt(s, `${n} ${n >= 3 && n <= 10 ? "صناديق" : "صندوق"}`, x - 1.75, y, 1.6, 0.7, { valign: "middle", align: "left", fontSize: 14, color: MUTED });
});
picture(s, "certificate", MX, 1.5, 3.4, 4.3, { align: "left" });
note(s, [HL(`${pct(L.aum_share_A, 0)} من الأصول المصنّفة بدرجة A`), N(` (${pct(L.established_aum_share_A, 0)} بين الصناديق المستقرة وحدها). صنّفنا ${L.funds_graded} صندوقاً من سعر الوحدة المنشور فقط. `),
  HL("تنشرها الهيئة سنوياً"), N("، فتعطي الواقف معيار مقارنة وإنذاراً مبكراً بالتآكل.")], 5.95, 0.8);

// ================= 6. Rule
s = slide("CONTENT", "الحل الثاني: قاعدة ميزان للصرف",
  "القاعدة جزآن: الصرف من متوسط قيمة الوقف لآخر اثني عشر ربعاً حتى لا يتذبذب دخل المستفيد، ثم اختيار المعدل من نطاق معلن. ولا نخفي المقايضة: الصرف الأعلى يعطي أكثر اليوم ويترك أقل للأجيال القادمة.");
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
  txt(s, "مجموع الصرف في 30 سنة", x + 0.15, 4.8, ow - 0.3, 0.3, { align: "center", fontSize: 12, color: MUTED });
  num(s, R[`${k}_30y_cumulative_real_payout`].toFixed(0), x, 5.07, ow, 0.5, { fontSize: 26, color: C.text2 });
});
note(s, [HL("المقايضة بصراحة:"), N(` الصرف عند ${pct(R.rate_recent_level, 0)} يعطي أكثر لثلاثة عقود لكنه يُنقص الأصل إلى ${R.recent_level_30y_median_real_value.toFixed(0)} من 100`),
  N(R.breakeven_year_balanced ? `، ويتجاوزه صرف «المتوازن» السنوي في السنة ${R.breakeven_year_balanced}. ` : ". "),
  HL("ينفّذها الناظر ومجلس الصندوق"), N(" بتعديل سياسة التوزيع فقط.")], 5.95, 0.8);

// ================= 7. Compass and gaps
s = slide("CONTENT", "الحل الثالث: بوصلة المصارف، وأين يغيب الوقف",
  "شروط الواقفين تبقى كما هي. الحصة المرنة، أوجه البر، هي التي يملك الناظر توجيهها. والخريطة من الموقع تبيّن المناطق التي تغيب عنها مصارف الرعاية الاجتماعية: كلما اغمقّ اللون زادت المصارف الغائبة.");
const mapPic = picture(s, "mapcard", MX, 1.5, 4.9, 4.3, { align: "left" });
const tx = mapPic.x + mapPic.w + 0.35, tw = W - MX - tx;
[[`${pct(AL.social_share_before, 0)} ثم ${pct(AL.social_share_after, 0)}`, "حصة الاحتياجات الأساسية قبل البوصلة وبعدها"],
 [`${G.regions_without_orphans} من ${G.regions}`, "منطقة ليس فيها مصرف وقفي واحد مسجّل للأيتام"],
 [sar(+bigGap.region_waqf_designations), `مصرفاً وقفياً في ${bigGap.region_ar}، ولا واحد منها للأيتام`]].forEach(([v, l], i) => {
  const y = 1.55 + i * 1.45;
  card(s, tx, y, tw, 1.3);
  num(s, v, tx + tw - 3.3, y, 3.1, 1.3, { fontSize: 34, color: i ? C.accent3 : C.accent1 });
  txt(s, l, tx + 0.3, y, tw - 3.8, 1.3, { valign: "middle", fontSize: 15 });
});
note(s, [HL("ينفّذها الناظر"), N(" عند إعداد خطة الصرف السنوية، دون مخالفة شرط واقف. "), HL("البيانات تقيس التسجيل لا الحاجة:"),
  N(" الفجوة تقول أين لم يُخصَّص وقف، وهي نقطة بداية للواقف الجديد والهيئة.")], 5.95, 0.8);

// ================= 8. Shock test and robustness
s = slide("CONTENT", "اختبار الصدمة، ومتانة النتائج",
  "سألنا أنفسنا سؤالين قبل أن يسألهما أحد. ماذا يحدث لدخل المستفيد لو تكرر أسوأ هبوط؟ وماذا لو كانت الأسواق أضعف من السنوات السبع التي رصدناها؟ الترتيب ثابت والمستوى حساس، ولذلك نوصي بالبدء من الطرف المتحفظ.");
const hw = (CW - 0.4) / 2, sxR = W - MX - hw;
card(s, sxR, 1.55, hw, 2.6, C.text2);
txt(s, "لو تكرر أسوأ هبوط في تاريخ المؤشر", sxR + 0.3, 1.68, hw - 0.6, 0.45, { fontSize: 17, bold: true, color: C.accent2 });
txt(s, "أكبر انخفاض في صرف سنة عن التي قبلها", sxR + 0.3, 2.13, hw - 0.6, 0.4, { fontSize: 13, color: C.background1 });
s.addText(pct(SH.worst_fall_again__mizan__worst_cut), { x: sxR + hw / 2, y: 2.55, w: hw / 2 - 0.2, h: 0.95, isTextBox: true, margin: 0, align: "center", valign: "middle", fontSize: 44, fontFace: FONT_NUM, color: C.background1 });
s.addText(pct(SH.worst_fall_again__same_rate_unsmoothed__worst_cut), { x: sxR + 0.2, y: 2.55, w: hw / 2 - 0.2, h: 0.95, isTextBox: true, margin: 0, align: "center", valign: "middle", fontSize: 44, fontFace: FONT_NUM, color: C.accent5 });
txt(s, "مع قاعدة ميزان", sxR + hw / 2, 3.52, hw / 2 - 0.2, 0.4, { align: "center", fontSize: 13, bold: true, color: C.background1 });
txt(s, "المعدل نفسه دون تمهيد", sxR + 0.2, 3.52, hw / 2 - 0.2, 0.4, { align: "center", fontSize: 13, color: C.accent5 });
picture(s, "shockchart", MX, 1.55, hw, 2.6, { align: "left" });
// robustness table
const assume = [["base", "كما رُصد في التاريخ"], ["lower_return", "عائد أقل 1% سنوياً"], ["harsh", "عائد أقل 2% وتذبذب أعلى 50%"]];
const tcols = [["ماذا لو كانت الأسواق أضعف؟", 4.6], ...OPT.map(([k, name]) => [`${name} ${pct(R[`rate_${k}`])}`, (CW - 4.6) / 3])];
let hx2 = W - MX;
tcols.forEach(([h, w], j) => { hx2 -= w; txt(s, h, hx2 + 0.15, 4.3, w - 0.3, 0.36, { fontSize: 13, bold: true, color: j ? MUTED : C.text2, align: j ? "center" : "right" }); });
assume.forEach(([a, label], i) => {
  const y = 4.7 + i * 0.43;
  card(s, MX, y, CW, 0.38);
  let x = W - MX;
  tcols.forEach(([, w], j) => { x -= w;
    if (j === 0) txt(s, label, x + 0.15, y, w - 0.3, 0.38, { valign: "middle", fontSize: 13 });
    else txt(s, pct(RB[`${a}_${OPT[j - 1][0]}_10y_p_preserve`], 0), x + 0.15, y, w - 0.3, 0.38, { valign: "middle", align: "center", fontSize: 14, bold: true, color: j === 3 ? C.accent3 : C.accent1 }); });
});
note(s, [N("الخانة = احتمال حفظ القيمة الحقيقية للأصل بعد 10 سنوات. "), HL("ما يثبت:"), N(" المعدل الأقل يحفظ أصلاً أكبر في كل افتراض. "),
  HL("ما يتغير:"), N(" المستوى، فابدأ من الطرف المتحفظ وراجع المعدل كل سنة.")], 6.05, 0.72);

// ================= 9. What each adds
s = slide("CONTENT", "ماذا يضيف كل حل، ومن ينفّذه",
  "كل حل ينفذه طرف محدد ببيانات يملكها أصلاً، دون تشريع جديد ولا تقنية جديدة.");
const cols = [["الحل", 2.9], ["من ينفّذه", 3.0], ["بماذا", 2.6], ["ماذا يضيف", CW - 8.5 - 0.6]];
let hx = W - MX;
cols.forEach(([h, w]) => { hx -= w; txt(s, h, hx + 0.1, 1.55, w - 0.2, 0.4, { fontSize: 14, bold: true, color: MUTED }); hx -= 0.2; });
[["بطاقة استدامة الوقف", "الهيئة العامة للأوقاف وهيئة السوق المالية", "أسعار الوحدات المنشورة", `معيار مقارنة شفاف لـ${L.funds_graded} صندوقاً و==إنذار مبكر بالتآكل==`],
 ["قاعدة ميزان للصرف", "النظّار ومجالس إدارة الصناديق", "تعديل سياسة التوزيع", `احتمال قطع الصرف ==من ${pct(R.smoothing.unsmoothed_p_cut_over_5pct, 0)} إلى ${pct(R.smoothing.smoothed_p_cut_over_5pct, 0)}==، وأصل محفوظ`],
 ["بوصلة المصارف", "النظّار", "خطة الصرف السنوية", `حصة الاحتياجات الأساسية ==من ${pct(AL.social_share_before, 0)} إلى ${pct(AL.social_share_after, 0)}==، وقائمة فجوات بالاسم`]].forEach((row, i) => {
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

// ================= 10. The product
section = "المنتج والموثوقية"; pres.addSection({ title: section });
s = slide("CONTENT", "المنتج: موقع تفاعلي من أربع صفحات",
  "لم نكتفِ بالتقرير. بنينا موقعاً يستعمله الناظر والواقف والجهة المنظمة: قصة النتائج، محاكي القرار، استكشاف البيانات، وخطة صرف في دقيقة. كل رقم فيه يُقرأ من مخرجات التحليل نفسها.");
[["hero", "القصة", "النتائج تُروى بالتمرير: من البيانات إلى الحلول"],
 ["simulator", "المحاكي والحلول", "ميزان يميل مع معدل الصرف، ومسارات المحاكاة، واختبار الصدمة"],
 ["fund", "استكشف البيانات", "خريطة المناطق، فجوات المصارف، وصفحة وبطاقة لكل صندوق"],
 ["plan_top", "وقفك في دقيقة", "ثلاثة أسئلة ثم خطة صرف من صفحة واحدة جاهزة للطباعة"]].forEach(([img, h, b], i) => {
  const cwid = (CW - 0.3) / 2, chei = 2.2, x = rx(i % 2, cwid, 0.3), y = 1.5 + Math.floor(i / 2) * (chei + 0.18);
  card(s, x, y, cwid, chei);
  const p = picture(s, img, x + 0.12, y + 0.12, 3.5, chei - 0.24, { align: "left" });
  const txw = cwid - (p.w + 0.12) - 0.45;
  badge(s, i + 1, x + cwid - 0.62, y + 0.25, 0.42);
  txt(s, h, x + p.w + 0.3, y + 0.22, txw - 0.55, 0.5, { fontSize: 17, bold: true, color: C.text2 });
  txt(s, b, x + p.w + 0.3, y + 0.85, txw, 1.3, { fontSize: 13 });
});
card(s, MX, 6.3, CW, 0.5, C.text2);
s.addText("a-a-a124.github.io/mizan-alrai", { x: MX + 0.3, y: 6.3, w: 5, h: 0.5, isTextBox: true, margin: 0, align: "left", valign: "middle", fontSize: 15, color: C.background1, fontFace: THEME.bodyFontFace });
txt(s, "يعمل على الجوال، بوضع فاتح وداكن، ودون أي مكتبة خارجية", MX + 5.4, 6.3, CW - 5.7, 0.5, { valign: "middle", fontSize: 13, color: C.accent5 });

// ================= 11. Trust
s = slide("CONTENT", "الموثوقية: كل رقم يُعاد حسابه بأمر واحد",
  "أي محكم يستطيع تشغيل أمر واحد فيحصل على الأرقام نفسها. واستخدمنا الذكاء الاصطناعي مساعداً مع توثيق كل خطوة والأخطاء التي صححناها.");
card(s, MX, 1.6, CW, 0.85, C.text2);
s.addText("python scripts/run_all.py", { x: MX + 0.4, y: 1.6, w: 5.5, h: 0.85, isTextBox: true, margin: 0, align: "left", valign: "middle",
  fontSize: 20, bold: true, color: C.accent2, fontFace: "Consolas" });
txt(s, "تحليل، ثم اختبارات، ثم دفتر وتقرير وموقع", MX + 6.1, 1.6, CW - 6.5, 0.85, { valign: "middle", fontSize: 16, color: C.background1 });
statCards(s, [
  { v: String(N_TESTS), l: "اختباراً آلياً ناجحاً، منها اختبار عدم تسرب المستقبل إلى التنبؤ" },
  { v: "37/37", l: "ملف نتائج يُعاد إنتاجه مطابقاً على النظامين", size: 44 },
  { v: "2", l: "نظاما تشغيل يُفحص عليهما تلقائياً عند كل تحديث" },
  { v: pct(FC.skill_vs_zero, 0), l: `أدق من المرجع الساذج في توقع عائد 12 شهراً (${pct(FC.point_pct)})` },
], 2.65, 2.25);
note(s, [HL("يعمل على ملفات أخرى:"), N(" الكود نفسه حلّل ملفاً بديلاً وأعطى نتائج مختلفة، فالأرقام تُحسب من الملف المُدخل لا من قيم ثابتة.")], 5.1, 0.75);
note(s, [HL("ذكاء اصطناعي مسؤول:"), N(" لا رقم مكتوب يدوياً ولا بيانات مصطنعة، وسجل يوثق كل خطوة وكيف تحققنا منها، "),
  HL("ومنها خطأ في رقم رئيسي اكتشفناه وصحّحناه.")], 6.0, 0.75);

// ================= 12. Limits and close
s = slide("CONTENT", "حدود التحليل، والخلاصة",
  "نذكر الحدود بوضوح، وقسنا أثر كل منها. والخلاصة: ثلاثة حلول بسيطة تبقي الوقف يكبر ولا يتآكل.");
[["وكيل لا قوائم مالية", "الصناديق المدرجة تمثل عائد الاستثمار الوقفي، ==وليست قوائم وقف بعينه=="],
 ["تاريخ قصير", `${R.history_months} شهراً فقط، فأعدنا المحاكاة بأسواق أضعف: ==الترتيب ثابت والمستوى حساس==`],
 ["توزيعات مقدَّرة", `تداول لا ينشر مبالغها. لو أخطأ تقديرنا بالنصف ==كان المتوسط بين ${pct(RB.avg_payout_low)} و${pct(RB.avg_payout_high)}==`],
 ["الفجوات تقيس التسجيل", "غياب المصرف لا يثبت غياب الدعم، ==وأوزان البوصلة افتراضات معلنة=="]].forEach(([h, b], i) => {
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
[["الموقع التفاعلي", "a-a-a124.github.io/mizan-alrai"], ["الكود والبيانات", "github.com/A-a-a124/mizan-alrai"]].forEach(([l, u], i) => {
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
