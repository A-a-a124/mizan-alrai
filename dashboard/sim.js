// The simulator: every probability is looked up in the precomputed grid (data.js), never recomputed here.
topbar('sim', '../');

for (const [k, v] of Object.entries(D.scenarios)) $('scen').add(new Option(v.label, k));
D.inflation.forEach(i => $('infl').add(new Option(pct(i, 1), i, false, Math.abs(i - D.defaults.inflation) < 1e-9)));
for (const [k, v] of Object.entries(D.profile_names)) $('prof').add(new Option(v, k));
$('rate').max = D.rates.length - 1;
$('rate').value = D.rates.findIndex(r => Math.abs(r - D.key.spending.rate_base) < 1e-9);

function state() {
  return { V: Math.max(0, +$('endow').value || 0), rate: D.rates[+$('rate').value], scen: $('scen').value,
           infl: +$('infl').value, conf: +$('conf').value, prof: $('prof').value, resv: Math.max(0, +$('resv').value || 0) };
}
const cell = (s, rate) => D.scenarios[s.scen].grid[rk(rate)][ik(s.infl)];
function sustainable(s) { let best = 0; for (const r of D.rates) if (cell(s, r).p >= s.conf) best = Math.max(best, r); return best; }

function drawFrontier(s, sus) {
  const target = { ps: D.rates.map(r => cell(s, r).p), rate: s.rate, sus, conf: s.conf };
  animate('front', target, c => {
    const svg = $('front'); svg.innerHTML = '';
    const pad = { l: 44, r: 12, t: 12, b: 30 };
    const a = axes(svg, 0, D.rates[D.rates.length - 1], 0, 1, [0, .02, .04, .06, .08], [0, .25, .5, .75, 1], v => pct(v, 0), v => pct(v, 0), pad);
    const at = r => { const i = Math.min(D.rates.length - 2, Math.floor(r / .005)), f = (r - D.rates[i]) / .005; return c.ps[i] + (c.ps[i + 1] - c.ps[i]) * f; };
    el('line', { x1: pad.l, x2: 560 - pad.r, y1: a.sy(c.conf), y2: a.sy(c.conf), stroke: css('--text-muted'), 'stroke-dasharray': '5 4' }, svg);
    el('path', { d: path(D.rates.map((r, i) => [a.sx(r), a.sy(c.ps[i])])) + `L${a.sx(.08)} ${a.sy(0)} L${a.sx(0)} ${a.sy(0)}Z`, fill: css('--band-1') }, svg);
    el('path', { d: path(D.rates.map((r, i) => [a.sx(r), a.sy(c.ps[i])])), fill: 'none', stroke: css('--series-1'), 'stroke-width': 2.4 }, svg);
    D.rates.forEach((r, i) => el('circle', { cx: a.sx(r), cy: a.sy(c.ps[i]), r: 3, fill: css('--series-1') }, svg));
    el('circle', { cx: a.sx(c.sus), cy: a.sy(at(c.sus)), r: 7, fill: css('--series-3'), stroke: css('--card'), 'stroke-width': 2 }, svg);
    el('circle', { cx: a.sx(c.rate), cy: a.sy(at(c.rate)), r: 9, fill: css('--series-2'), stroke: css('--card'), 'stroke-width': 2 }, svg);
    hover(svg, $('tipF'), D.rates, a.sx, i => `صرف <b>${pct(D.rates[i])}</b> ← حفظ الأصل <b>${pct(target.ps[i], 0)}</b>`);
  });
}

let fanAxis = null;
function drawFan(s, sus) {
  const target = { A: cell(s, s.rate).bands, B: cell(s, sus).bands };
  animate('fan', target, c => {
    const svg = $('fan'); svg.innerHTML = '';
    const { A, B } = c, yrs = A[0].map((_, i) => i);
    const lo = Math.min(...A[0], ...B[0]), hi = Math.max(...A[2], ...B[2]);
    const y0 = Math.floor(lo / 10) * 10, y1 = Math.ceil(hi / 10) * 10, step = (y1 - y0) > 60 ? 20 : 10, yt = [];
    for (let v = y0; v <= y1; v += step) yt.push(v);
    const pad = { l: 40, r: 30, t: 12, b: 30 };
    const a = axes(svg, 0, 10, y0, y1, [0, 2, 4, 6, 8, 10], yt, v => v + ' سنة', v => v, pad);
    fanAxis = { a, y0, y1 };
    el('line', { x1: pad.l, x2: 560 - pad.r, y1: a.sy(100), y2: a.sy(100), stroke: css('--text-muted'), 'stroke-dasharray': '5 4' }, svg);
    const band = (Q, fill) => el('path', { d: path(yrs.map(i => [a.sx(i), a.sy(Q[2][i])]).concat(yrs.slice().reverse().map(i => [a.sx(i), a.sy(Q[0][i])]))) + 'Z', fill }, svg);
    band(B, css('--band-1')); band(A, css('--band-2'));
    el('g', { id: 'fanPaths' }, svg);
    el('path', { d: path(yrs.map(i => [a.sx(i), a.sy(B[1][i])])), fill: 'none', stroke: css('--series-1'), 'stroke-width': 2 }, svg);
    el('path', { d: path(yrs.map(i => [a.sx(i), a.sy(A[1][i])])), fill: 'none', stroke: css('--series-2'), 'stroke-width': 2.4 }, svg);
    el('text', { x: a.sx(10) + 4, y: a.sy(A[1][10]) + 4, 'text-anchor': 'start' }, svg).textContent = A[1][10].toFixed(0);
    el('text', { x: a.sx(10) + 4, y: a.sy(B[1][10]) + 4, 'text-anchor': 'start' }, svg).textContent = B[1][10].toFixed(0);
    const T = target;
    hover(svg, $('tipV'), yrs, a.sx, i => `السنة ${i}<br>المختار ${pct(s.rate)}: <b>${T.A[1][i].toFixed(0)}</b> (${T.A[0][i].toFixed(0)}–${T.A[2][i].toFixed(0)})<br>المستدام ${pct(sus)}: <b>${T.B[1][i].toFixed(0)}</b>`);
  });
  $('pathsNote').textContent = '';
}

// draw a handful of the simulated paths themselves, one after another
let pathsTimer = 0;
function playPaths() {
  const s = state(), nominal = D.scenarios[s.scen].grid[rk(s.rate)].paths, g = $('fanPaths');
  if (!g || !fanAxis) return;
  clearInterval(pathsTimer); g.innerHTML = '';
  const real = nominal.map(p => p.map((v, t) => v / Math.pow(1 + s.infl, t)));
  let i = 0, kept = 0;
  const one = () => {
    if (i >= real.length) { clearInterval(pathsTimer); return; }
    const p = real[i], ok = p[p.length - 1] >= 100, { a, y0, y1 } = fanAxis;
    const line = el('path', { d: path(p.map((v, t) => [a.sx(t), a.sy(Math.max(y0, Math.min(y1, v)))])), fill: 'none',
                              stroke: ok ? css('--series-3') : css('--series-2'), 'stroke-width': 1.1, opacity: .75 }, g);
    const len = line.getTotalLength();
    if (!still()) { line.style.strokeDasharray = len; line.style.strokeDashoffset = len; line.getBoundingClientRect();
      line.style.transition = 'stroke-dashoffset .5s ease'; line.style.strokeDashoffset = 0; }
    kept += ok; i += 1;
    $('pathsNote').textContent = `${i} مساراً من ${D.key.spending.paths.toLocaleString('en-US')}: ${kept} حفظت القيمة الحقيقية و${i - kept} لم تحفظها (العيّنة للتوضيح، والاحتمال أعلاه من كل المسارات).`;
  };
  if (still()) { while (i < real.length) one(); } else { one(); pathsTimer = setInterval(one, 170); }
}
$('playPaths').onclick = playPaths;

function drawIndex() {
  const svg = $('idx'); svg.innerHTML = '';
  const I = D.index, n = I.month.length, xs = I.month.map((_, i) => i);
  const lo = Math.floor(Math.min(...I.price) / 10) * 10, hi = Math.ceil(Math.max(...I.total) / 10) * 10, yt = [];
  for (let v = lo; v <= hi; v += 10) yt.push(v);
  const ticks = xs.filter(i => I.month[i].endsWith('-01'));
  const pad = { l: 40, r: 12, t: 12, b: 30 };
  const a = axes(svg, 0, n - 1, lo, hi, ticks, yt, i => I.month[i].slice(0, 4), v => v, pad);
  el('path', { d: path(xs.map(i => [a.sx(i), a.sy(I.price[i])])), fill: 'none', stroke: css('--series-2'), 'stroke-width': 2 }, svg);
  el('path', { d: path(xs.map(i => [a.sx(i), a.sy(I.total[i])])), fill: 'none', stroke: css('--series-1'), 'stroke-width': 2 }, svg);
  hover(svg, $('tipI'), xs, a.sx, i => `<span class="ltr">${I.month[i]}</span> · ${I.n_funds[i]} صندوق<br>العائد الكلي: <b>${I.total[i].toFixed(1)}</b><br>السعر فقط: <b>${I.price[i].toFixed(1)}</b>`);
  $('funds').innerHTML = '<tr><th>الصندوق</th><th>أشهر</th><th>عائد السعر/سنة</th><th>الأصول (مليون)</th></tr>' +
    D.funds.map(f => `<tr><td>${f.fund_name}${f.in_index ? ' <span class="pill">في المؤشر</span>' : ''}</td><td class="n">${f.months}</td><td class="n">${pct(f.price_ann_return)}</td><td class="n">${f.aum_sar ? (f.aum_sar / 1e6).toFixed(1) : '—'}</td></tr>`).join('');
}

function renderScale(s, sus, med) {
  const gap = s.rate - sus, tilt = Math.max(-1, Math.min(1, gap / 0.03)) * 13;
  animate('scale', { ang: tilt }, c => drawScale($('scale'), c.ang,
    { name: 'هذا الجيل', value: sar(s.V * s.rate) + ' ريال/سنة' },
    { name: 'الأجيال القادمة', value: (s.V * med / 100 / 1e6).toFixed(2) + ' مليون بعد 10 سنوات' }), 700);
  const say = Math.abs(gap) < 1e-9 ? ['الميزان متوازن', `صرف ${pct(s.rate)} هو أعلى معدل يحفظ الأصل بالثقة التي طلبتها.`]
    : gap > 0 ? ['الكفّة تميل إلى هذا الجيل', `صرف ${pct(s.rate)} يزيد ${((gap) * 100).toFixed(1)} نقطة على المعدل المستدام (${pct(sus)}): ما يُصرف اليوم يُؤخذ من نصيب من يأتي بعدنا.`]
    : ['الكفّة تميل إلى الأجيال القادمة', `صرف ${pct(s.rate)} أقل من المعدل المستدام (${pct(sus)}): الأصل ينمو، ويمكن صرف ${sar(s.V * (sus - s.rate))} ريال إضافية سنوياً دون المساس به.`];
  $('scaleSay').innerHTML = `${say[0]}<small>${say[1]}</small>`;
}

function render() {
  const s = state(), sus = sustainable(s), c = cell(s, s.rate), med = c.bands[1][10];
  $('rateVal').textContent = pct(s.rate);
  countUp($('kP'), c.p, v => pct(v, 0));
  $('kP').style.color = c.p >= s.conf ? css('--navy') : css('--series-2');
  $('kPs').textContent = c.p >= s.conf ? '✔ يحقق الثقة المطلوبة (' + pct(s.conf, 0) + ')' : '✖ أقل من الثقة المطلوبة (' + pct(s.conf, 0) + ')';
  countUp($('kR'), sus, v => pct(v));
  $('kRs').textContent = sus === 0 ? 'لا يوجد معدل صرف يحقق هذه الثقة: خفّض الثقة أو راجع السيناريو' : 'أي ' + sar(s.V * sus) + ' ريال سنوياً';
  countUp($('kB'), s.V * s.rate, sar);
  $('kBs').textContent = 'ريال، أي ' + pct(s.rate) + ' من متوسط قيمة الوقف';
  countUp($('kV'), s.V * med / 100 / 1e6, v => v.toFixed(2) + ' م');
  $('kVs').textContent = 'مليون ريال بأسعار اليوم (' + (med >= 100 ? '+' : '') + (med - 100).toFixed(0) + '% من القيمة الحالية)';
  renderScale(s, sus, med); drawFrontier(s, sus); drawFan(s, sus);
  $('alloc').innerHTML = allocRows(s.V, s.rate, D.profiles[s.prof], s.resv);
}

// ---- shock test: precomputed in src/waqf/insights.py (deterministic paths, start value 100)
const SHOCKS = { worst_fall_again: 'يتكرر أسوأ هبوط في تاريخ المؤشر', worst_fall_twice: 'يتكرر الهبوط مرتين في عشر سنوات',
                 inflation_4pct_5y: 'تضخم 4% لخمس سنوات', flat_3y: 'ثلاث سنوات بلا عائد', calm: 'لا صدمة (للمقارنة)' };
const STRAT = { mizan: ['قاعدة ميزان', '--series-3'], same_rate_unsmoothed: ['المعدل نفسه دون تمهيد', '--series-1'],
                recent_level_unsmoothed: ['مستوى التوزيع الأخير دون تمهيد', '--series-2'] };
let shock = 'worst_fall_again';
function drawShock() {
  const V = Math.max(0, +$('endow').value || 0), sc = D.shocks[shock], K = D.key.shock, yrs = sc.mizan.pay.map((_, i) => i + 1);
  $('shockChips').innerHTML = Object.entries(SHOCKS).map(([k, n]) => `<button class="chip" data-k="${k}" aria-pressed="${k === shock}">${n}</button>`).join('');
  $('shockChips').querySelectorAll('.chip').forEach(b => b.onclick = () => { shock = b.dataset.k; drawShock(); });
  const target = {}; for (const k in STRAT) target[k] = sc[k].pay.map(v => v / sc[k].pay[0] * 100);   // year 1 = 100
  animate('shock', target, c => {
    const svg = $('shockChart'); svg.innerHTML = '';
    const pad = { l: 36, r: 14, t: 12, b: 30 };
    const a = axes(svg, 1, 10, 60, 110, [1, 2, 4, 6, 8, 10], [60, 70, 80, 90, 100, 110], v => 'السنة ' + v, v => v, pad);
    el('line', { x1: pad.l, x2: 560 - pad.r, y1: a.sy(100), y2: a.sy(100), stroke: css('--text-muted'), 'stroke-dasharray': '5 4' }, svg);
    for (const k in STRAT) {
      el('path', { d: path(c[k].map((v, i) => [a.sx(yrs[i]), a.sy(v)])), fill: 'none', stroke: css(STRAT[k][1]), 'stroke-width': k === 'mizan' ? 3.2 : 2 }, svg);
      c[k].forEach((v, i) => el('circle', { cx: a.sx(yrs[i]), cy: a.sy(v), r: k === 'mizan' ? 3.4 : 2.4, fill: css(STRAT[k][1]) }, svg));
    }
    hover(svg, $('tipS'), yrs, a.sx, i => `السنة ${yrs[i]}: الصرف السنوي<br>` + Object.keys(STRAT).map(k => `${STRAT[k][0]}: <b>${sar(V * sc[k].pay[i] / 100)}</b> ريال`).join('<br>'));
  });
  $('shockLeg').innerHTML = Object.keys(STRAT).map(k => `<span><i style="background:var(${STRAT[k][1]})"></i>${STRAT[k][0]} (${pct(sc[k].rate)})</span>`).join('');
  $('shockCards').innerHTML = Object.keys(STRAT).map(k => {
    const cut = K[`${shock}__${k}__worst_cut`], val = K[`${shock}__${k}__value_10y`];
    return `<div style="border-inline-start-color:var(${STRAT[k][1]})"><div class="l">${STRAT[k][0]}</div>
      <div class="v" style="color:var(${STRAT[k][1]})">${cut < -0.0005 ? '<span class="ltr">' + pct(cut) + '</span>' : 'لا انخفاض'}</div><div class="l">أكبر انخفاض في صرف سنة عن التي قبلها</div>
      <div class="l" style="margin-top:4px">قيمة الوقف بعد 10 سنوات: <b>${sar(V * val / 100)}</b> ريال</div></div>`; }).join('');
  $('shockNote').innerHTML = `أسوأ هبوط في تاريخ مؤشر الصناديق الوقفية: <b class="ltr">${pct(K.worst_fall)}</b> خلال ${K.worst_fall_months === 2 ? 'شهرين' : K.worst_fall_months + ' أشهر'} ` +
    `(<span class="ltr">${K.worst_fall_from}</span> إلى <span class="ltr">${K.worst_fall_to}</span>). خارج الصدمة يُفترض العائد الشهري المتوسط. ` +
    `التاريخ المتاح ${D.key.rule.history_months} شهراً فقط، فالاختبار يوضّح سلوك القاعدة ولا يتنبأ بالأزمات.`;
}

['endow', 'rate', 'scen', 'infl', 'conf', 'prof', 'resv'].forEach(id => $(id).addEventListener('input', render));
$('endow').addEventListener('input', drawShock);
document.addEventListener('mz-redraw', () => { drawIndex(); render(); drawShock(); });
drawIndex(); render(); drawShock();
{ const k = D.key;
$('foot').innerHTML = `<b>ميزان الريع</b> · المصادر: الهيئة العامة للأوقاف (منصة البيانات المفتوحة الوطنية، ${k.sector.waqf_designations.toLocaleString('en-US')} مصرفاً وقفياً) · السوق المالية السعودية، تداول (${k.index.funds_total} صندوقاً وقفياً). ` +
  `العائد الكلي المقدَّر ${pct(k.index.total_ann_return)} سنوياً · توقع 12 شهراً ${pct(k.forecast.point_pct)} · ${k.spending.paths.toLocaleString('en-US')} مسار لكل حالة. ` +
  `الحدود: الصناديق المدرجة وكيل لأداء الاستثمار الوقفي، ومبالغ التوزيع مقدَّرة.`;
}
