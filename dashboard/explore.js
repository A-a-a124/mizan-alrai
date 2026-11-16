// Data explorer: map of regions, masarif gaps, fund managers and one page per fund (tables from src/waqf/insights.py).
topbar('explore', '../');
const X = D.explore, MAP = window.WAQF_MAP, LAB = D.solutions.sustainability_label;
const REG = Object.fromEntries(D.solutions.compass_regions.map(r => [r.region, r]));
const MX = X.matrix, SOC = new Set(X.social);
const rowOf = key => MX.counts[MX.regions.findIndex(r => r.key === key)];
const missing = key => MX.masarif.filter((m, j) => SOC.has(m.key) && rowOf(key)[j] === 0);
const nMasarif = n => n.toLocaleString('en-US') + (n >= 3 && n <= 10 ? ' مصارف وقفية مسجّلة' : ' مصرفاً وقفياً مسجّلاً');

// ---------------------------------------------------------------- map
const METRICS = {
  count: { n: 'عدد المصارف الوقفية', v: r => Math.log10(r.waqf_designations), f: r => r.waqf_designations.toLocaleString('en-US'), hi: '--series-1', lo: 'قليل', up: 'كثير' },
  social: { n: 'حصة الرعاية الاجتماعية', v: r => r.social_share, f: r => pct(r.social_share, 0), hi: '--series-3', lo: 'منخفضة', up: 'مرتفعة' },
  flexible: { n: 'حصة «أوجه البر» المرنة', v: r => r.flexible_share, f: r => pct(r.flexible_share, 0), hi: '--series-1', lo: 'منخفضة', up: 'مرتفعة' },
  gaps: { n: 'مصارف اجتماعية غائبة', v: r => missing(r.region).length, f: r => missing(r.region).length + ' من 5', hi: '--critical', lo: 'لا فجوات', up: '5 غائبة' },
};
let metric = 'gaps', picked = 'aseer';
function drawMap() {
  const m = METRICS[metric], svg = $('map'), vals = Object.values(REG).map(m.v), lo = Math.min(...vals), hi = Math.max(...vals);
  svg.setAttribute('viewBox', `0 0 ${MAP.width} ${MAP.height}`); svg.innerHTML = '';
  const low = css('--surface-1'), high = css(m.hi), shade = r => mix(low, high, .12 + .88 * ((m.v(r) - lo) / ((hi - lo) || 1)));
  $('mapChips').innerHTML = Object.entries(METRICS).map(([k, x]) => `<button class="chip" data-k="${k}" aria-pressed="${k === metric}">${x.n}</button>`).join('');
  $('mapChips').querySelectorAll('.chip').forEach(b => b.onclick = () => { metric = b.dataset.k; drawMap(); });
  for (const [key, shape] of Object.entries(MAP.regions)) {
    const r = REG[key], p = el('path', { d: shape.d, fill: shade(r), tabindex: 0, role: 'button', 'aria-label': `${r.region_ar}: ${m.f(r)}`, class: key === picked ? 'on' : '' }, svg);
    const pick = () => { picked = key; drawMap(); drawRegion(); };
    p.onclick = pick; p.onkeydown = keyAct(pick);
    p.onmousemove = ev => { $('tipM').innerHTML = `<b>${r.region_ar}</b><br>${m.n}: <b>${m.f(r)}</b>`; placeTip($('tipM'), ev, svg.parentElement); };
    p.onmouseleave = () => { $('tipM').style.display = 'none'; };
  }
  const on = svg.querySelector('path.on'); if (on) svg.appendChild(on);                     // outline on top
  for (const [key, shape] of Object.entries(MAP.regions)) el('text', { x: shape.cx, y: shape.cy + 3, 'text-anchor': 'middle' }, svg).textContent = REG[key].region_ar;
  $('ramp').innerHTML = `<span>${m.lo}</span><i style="background:linear-gradient(to left, ${mix(low, high, .12)}, ${high})"></i><span>${m.up}</span>`;
}
function drawRegion() {
  const r = REG[picked], row = rowOf(picked), gone = missing(picked);
  const rank = MX.regions.findIndex(x => x.key === picked) + 1;
  const top = MX.masarif.map((m, j) => ({ ar: m.ar, n: row[j], soc: SOC.has(m.key) })).filter(x => x.n > 0).sort((a, b) => b.n - a.n).slice(0, 6);
  $('regionCard').innerHTML = `<h2 style="font-size:22px;color:var(--navy)">${r.region_ar}</h2>
    <div class="sub">${nMasarif(r.waqf_designations)} · الترتيب ${rank} من ${MX.regions.length} مناطق</div>
    ${top.map(x => `<div class="alloc-row"><span>${x.ar}</span><div class="track"><div class="bar" style="width:${(x.n / top[0].n * 100).toFixed(1)}%;background:var(${x.soc ? '--series-3' : '--series-1'})"></div></div><span class="amt">${x.n.toLocaleString('en-US')}</span></div>`).join('')}
    <div class="three" style="grid-template-columns:1fr 1fr">
      <div><div class="l">الرعاية الاجتماعية اليوم</div><div class="v">${pct(r.social_share, 0)}</div></div>
      <div style="border-inline-start-color:var(--series-3)"><div class="l">بعد بوصلة المصارف</div><div class="v" style="color:var(--series-3)">${pct(r.social_share_after, 0)}</div></div></div>
    <div class="adds" style="border-inline-start-color:var(${gone.length ? '--critical' : '--series-3'})">${gone.length
      ? `<b>لا يوجد مصرف وقفي مسجّل في المنطقة لـ:</b> ${gone.map(g => g.ar).join('، ')}.`
      : '<b>مصارف الرعاية الاجتماعية الخمسة كلها ممثّلة في هذه المنطقة.</b>'}</div>
    <div style="margin-top:10px"><a class="btn" href="plan.html?region=${picked}">ابنِ خطة لوقف في ${r.region_ar}</a></div>`;
}

// ---------------------------------------------------------------- gaps
let socialOnly = true;
function drawHeat() {
  const cols = MX.masarif.map((m, j) => ({ ...m, j })).filter(m => !socialOnly || SOC.has(m.key));
  const low = css('--surface-1'), high = css('--series-1');
  $('heat').innerHTML = `<thead><tr><th></th>${cols.map(c => `<th${SOC.has(c.key) ? ' style="color:var(--series-3);font-weight:700"' : ''}>${c.ar}</th>`).join('')}</tr></thead><tbody>` +
    MX.regions.map((r, i) => `<tr><th>${r.ar} <span style="color:var(--text-muted)">${r.total.toLocaleString('en-US')}</span></th>` + cols.map(c => {
      const n = MX.counts[i][c.j], share = n / r.total, tip = `${r.ar} · ${c.ar}: ${n.toLocaleString('en-US')} (${pct(share)})`;
      if (n === 0) return SOC.has(c.key) ? `<td class="gap" title="${tip}">✕</td>` : `<td class="none" title="${tip}"></td>`;
      return `<td title="${tip}" style="background:${mix(low, high, .15 + .85 * Math.sqrt(share))};color:${share > .12 ? '#fff' : 'var(--text-primary)'}">${n >= 100 ? n : ''}</td>`;
    }).join('') + '</tr>').join('') + '</tbody>';
  $('heat').classList.toggle('flat', socialOnly); $('heatToggle').setAttribute('aria-pressed', !socialOnly);
  const big = MX.regions.filter(r => r.total >= 500 && missing(r.key).length), small = MX.regions.filter(r => r.total < 500 && missing(r.key).length);
  const g = D.key.gaps;
  $('gapList').innerHTML = big.map(r => `<div><b>${r.ar}</b> (${nMasarif(r.total)}): لا مصرف مسجّلاً لـ ${missing(r.key).map(m => m.ar).join('، ')}.</div>`).join('') +
    (small.length ? `<div style="border-inline-start-color:var(--text-muted)"><b>مناطق قليلة التسجيل</b> (${small.map(r => r.ar).join('، ')}): أقل من 50 مصرفاً مسجّلاً في كل منها، فغياب المصرف فيها قد يعكس قلة التسجيل لا غياب الحاجة.</div>` : '');
  $('gapLead').innerHTML = `<b>${g.regions_without_orphans} من ${g.regions}</b> منطقة ليس فيها مصرف وقفي مسجّل للأيتام، و<b>${g.regions_without_widows}</b> بلا مصرف للأرامل، و<b>${g.regions_without_housing}</b> بلا مصرف للسكن.`;
}
$('heatToggle').onclick = () => { socialOnly = !socialOnly; drawHeat(); };

// ---------------------------------------------------------------- managers and funds
let manager = null, fund = null;
function drawManagers() {
  const max = Math.max(...X.managers.map(m => Math.abs(m.unit_growth_avg)));
  $('managers').innerHTML = '<tr><th>#</th><th>مدير الصناديق</th><th>درجات صناديقه</th><th>نمو قيمة الوحدة سنوياً (متوسط)</th><th>انتظام التوزيع</th><th>الأصول (مليون)</th></tr>' +
    X.managers.map(m => { const fs = LAB.filter(f => f.manager === m.manager).sort((a, b) => a.grade.localeCompare(b.grade));
      return `<tr class="pick" data-m="${m.manager}" tabindex="0" style="${manager === m.manager ? 'outline:2px solid var(--series-1)' : ''}"><td class="n">${m.rank}</td><td class="ltr" style="text-align:right">${m.manager}</td>
        <td><div class="dots">${fs.map(f => `<span class="g g${f.grade}" style="width:20px;height:20px;font-size:11px${f.provisional ? ';opacity:.55' : ''}" title="${f.fund_name}">${f.grade}</span>`).join('')}</div></td>
        <td><div class="barcell"><i style="width:${(Math.abs(m.unit_growth_avg) / max * 90).toFixed(0)}px;background:var(${m.unit_growth_avg >= 0 ? '--series-3' : '--series-2'})"></i><span class="ltr">${pct(m.unit_growth_avg)}</span></div></td>
        <td class="n">${pct(m.payout_regularity, 0)}</td><td class="n">${(m.aum_sar / 1e6).toFixed(0)}</td></tr>`; }).join('');
  $('managers').querySelectorAll('tr.pick').forEach(tr => { const f = () => { manager = manager === tr.dataset.m ? null : tr.dataset.m; drawManagers(); drawFunds(); };
    tr.onclick = f; tr.onkeydown = keyAct(f); });
}
function drawFunds() {
  const rows = LAB.filter(f => !manager || f.manager === manager).sort((a, b) => a.grade.localeCompare(b.grade) || (b.aum_sar || 0) - (a.aum_sar || 0));
  $('fundsSub').textContent = (manager ? `صناديق ${manager}: ` : '') + nFunds(rows.length) + ' · اضغط صندوقاً لتفتح صفحته';
  $('fundGrid').innerHTML = rows.map(f => `<div class="fund${f.provisional ? ' prov' : ''}" role="button" tabindex="0" data-s="${f.symbol}" style="${fund === f.symbol ? 'border-color:var(--series-1);border-width:2px' : ''}">
    <span class="g g${f.grade}">${f.grade}</span><div><div class="nm">${f.fund_name}</div><div class="mt">${f.months} شهراً</div></div></div>`).join('');
  $('fundGrid').querySelectorAll('.fund').forEach(c => { const f = () => { fund = c.dataset.s; drawFunds(); drawFund(); $('fundPanel').scrollIntoView({ block: 'nearest' }); };
    c.onclick = f; c.onkeydown = keyAct(f); });
}
function drawFund() {
  const f = LAB.find(x => x.symbol === fund), s = X.fund_series[fund], panel = $('fundPanel');
  if (!f || !s) { panel.classList.remove('open'); return; }
  panel.classList.remove('open'); void panel.offsetWidth; panel.classList.add('open');
  $('fundName').textContent = f.fund_name;
  $('fundMeta').innerHTML = `<span class="g g${f.grade}">${f.grade}</span> ${GRADE_TXT[f.grade]}${f.provisional ? ' <span class="pill">درجة مبدئية: سجل أقل من 36 شهراً</span>' : ''}`;
  // the fund against the average of all waqf funds, both = 100 at the fund's first month
  const I = D.index, at = I.month.indexOf(s.m[0]), peers = s.m.map(m => { const j = I.month.indexOf(m); return at >= 0 && j >= 0 ? I.price[j] / I.price[at] * 100 : null; });
  const svg = $('fundChart'); svg.innerHTML = '';
  const all = s.p.concat(peers.filter(v => v != null)), lo = Math.floor(Math.min(...all) / 10) * 10, hi = Math.ceil(Math.max(...all) / 10) * 10, yt = [];
  for (let v = lo; v <= hi; v += (hi - lo) > 60 ? 20 : 10) yt.push(v);
  const xs = s.m.map((_, i) => i), ticks = xs.filter(i => s.m[i].endsWith('-01')), pad = { l: 40, r: 14, t: 14, b: 30 };
  const a = axes(svg, 0, Math.max(1, xs.length - 1), lo, hi, ticks, yt, i => s.m[i].slice(0, 4), v => v, pad);
  el('line', { x1: pad.l, x2: 560 - pad.r, y1: a.sy(100), y2: a.sy(100), stroke: css('--text-muted'), 'stroke-dasharray': '5 4' }, svg);
  const pp = xs.filter(i => peers[i] != null).map(i => [a.sx(i), a.sy(peers[i])]);
  if (pp.length > 1) el('path', { d: path(pp), fill: 'none', stroke: css('--text-muted'), 'stroke-width': 1.6 }, svg);
  const line = el('path', { d: path(xs.map(i => [a.sx(i), a.sy(s.p[i])])), fill: 'none', stroke: css('--series-1'), 'stroke-width': 2.4 }, svg);
  if (!still()) { const len = line.getTotalLength(); line.style.strokeDasharray = len; line.style.strokeDashoffset = len; line.getBoundingClientRect();
    line.style.transition = 'stroke-dashoffset 1s ease'; line.style.strokeDashoffset = 0; }
  s.pay.forEach((i, n) => { el('line', { x1: a.sx(i), x2: a.sx(i), y1: a.sy(s.p[i]), y2: pad.t + 8, stroke: css('--series-2'), 'stroke-dasharray': '2 3' }, svg);
    el('circle', { cx: a.sx(i), cy: a.sy(s.p[i]), r: 5, fill: css('--series-2'), stroke: css('--card'), 'stroke-width': 1.5 }, svg);
    el('text', { x: a.sx(i), y: pad.t + 4, 'text-anchor': 'middle' }, svg).textContent = pct(s.est[n]); });
  hover(svg, $('tipFund'), xs, a.sx, i => `<span class="ltr">${s.m[i]}</span><br>الصندوق: <b>${s.p[i].toFixed(1)}</b>` + (peers[i] != null ? `<br>متوسط الصناديق الوقفية: <b>${peers[i].toFixed(1)}</b>` : '') +
    (s.pay.includes(i) ? `<br>توزيع مقدَّر: <b>${pct(s.est[s.pay.indexOf(i)])}</b> من قيمة الوحدة` : ''));
  $('fundStats').innerHTML = [['نمو قيمة الوحدة سنوياً', pct(f.unit_growth)], ['بعد خصم تضخم 2%', pct(f.real_unit_growth)],
    ['التوزيع المقدَّر سنوياً', f.est_payout_rate == null ? '—' : pct(f.est_payout_rate)], ['توزيعات مرصودة', s.pay.length],
    ['أكبر تراجع من القمة', pct(f.max_drawdown)], ['التذبذب السنوي', pct(f.volatility)], ['طول السجل', f.months + ' شهراً'],
    ['الأصول', f.aum_sar ? (f.aum_sar / 1e6).toFixed(1) + ' مليون ريال' : 'غير منشورة'], ['مدير الصندوق', f.manager]]
    .map(([l, v]) => `<tr><td>${l}</td><td class="n">${v}</td></tr>`).join('');
  const svgText = certificate(f, s.m[s.m.length - 1]);
  $('certImg').src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgText);
  $('certBtn').onclick = () => savePng(svgText, `mizan-label-${f.symbol}.png`);
}

// ---------------------------------------------------------------- printable sustainability certificate
const GRADE_TXT = { A: 'الأصل محفوظ فعلياً: قيمة الوحدة نمت بمعدل التضخم أو أكثر', B: 'محفوظ اسمياً فقط: قيمة الوحدة نمت أقل من التضخم',
  C: 'تآكل طفيف: قيمة الوحدة نقصت حتى 2% سنوياً', D: 'تآكل واضح: قيمة الوحدة نقصت بين 2% و5% سنوياً', E: 'تآكل شديد: قيمة الوحدة نقصت أكثر من 5% سنوياً' };   // = solutions.GRADE_MEANING_AR
const GCOL = { A: '#0a8a3a', B: '#5cab2e', C: '#c99a00', D: '#e46c1f', E: '#c62828' };
function certificate(f, lastMonth) {
  const esc = t => String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;'), ar = 'direction="rtl" font-family="Segoe UI, Tahoma, Arial, sans-serif"';
  const rows = 'ABCDE'.split('').map((g, i) => { const y = 330 + i * 78, w = 250 + i * 62, x = 740 - w;
    return `<path d="M740 ${y} H${x + 30} L${x} ${y + 31} L${x + 30} ${y + 62} H740 Z" fill="${GCOL[g]}"/><text x="700" y="${y + 43}" font-size="38" font-weight="700" fill="#fff" text-anchor="middle" font-family="Segoe UI, Arial">${g}</text>` +
      (g === f.grade ? `<path d="M60 ${y - 6} H190 L226 ${y + 31} L190 ${y + 68} H60 Z" fill="#17263f"/><text x="128" y="${y + 52}" font-size="60" font-weight="700" fill="#fff" text-anchor="middle" font-family="Segoe UI, Arial">${g}</text>` : ''); }).join('');
  const cell = (x, y, label, value) => `<rect x="${x}" y="${y}" width="330" height="92" rx="12" fill="#f3f5f9"/><text x="${x + 310}" y="${y + 34}" font-size="19" fill="#475467" ${ar}>${label}</text><text x="${x + 310}" y="${y + 74}" font-size="30" font-weight="700" fill="#17263f" ${ar}>${value}</text>`;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 1040" width="800" height="1040"><rect width="800" height="1040" fill="#fff"/>
    <rect width="800" height="150" fill="#17263f"/><text x="740" y="70" font-size="44" font-weight="700" fill="#fff" ${ar}>بطاقة استدامة الوقف</text>
    <text x="740" y="112" font-size="21" fill="#cfdcf2" ${ar}>هل حافظت وحدة الصندوق على قوتها الشرائية؟</text><text x="60" y="70" font-size="24" fill="#cfdcf2" font-family="Segoe UI, Tahoma, Arial">ميزان الريع</text>
    <text x="400" y="218" font-size="30" font-weight="700" fill="#101828" text-anchor="middle" font-family="Segoe UI, Arial">${esc(f.fund_name)}</text>
    <text x="400" y="258" font-size="20" fill="#475467" text-anchor="middle" font-family="Segoe UI, Arial">${esc(f.manager)} · ${esc(f.symbol)}</text>
    <line x1="60" x2="740" y1="290" y2="290" stroke="#e1e5ee" stroke-width="2"/>${rows}
    <text x="740" y="762" font-size="23" font-weight="700" fill="#101828" ${ar}>${GRADE_TXT[f.grade]}</text>
    ${f.provisional ? `<text x="740" y="796" font-size="19" fill="#c0392b" ${ar}>درجة مبدئية: سجل الصندوق ${f.months} شهراً فقط (أقل من 36)</text>` : ''}
    ${cell(410, 820, 'نمو قيمة الوحدة سنوياً', pct(f.unit_growth))}${cell(60, 820, 'بعد خصم تضخم 2%', pct(f.real_unit_growth))}
    <text x="740" y="962" font-size="17" fill="#475467" ${ar}>الأساس: سعر الوحدة المنشور في السوق المالية السعودية (تداول) لمدة ${f.months} شهراً، حتى ${lastMonth}.</text>
    <text x="740" y="990" font-size="17" fill="#475467" ${ar}>تحليل مستقل لمسابقة تحليل البيانات للقطاع غير الربحي، وليس توصية استثمارية.</text>
    <text x="60" y="1016" font-size="16" fill="#8a94a6" font-family="Segoe UI, Arial">github.com/A-a-a124/mizan-alrai</text></svg>`;
}
function savePng(svgText, name) {
  const img = new Image();
  img.onload = () => { const c = document.createElement('canvas'); c.width = 1600; c.height = 2080; c.getContext('2d').drawImage(img, 0, 0, 1600, 2080);
    c.toBlob(b => { const a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 2000); }); };
  img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svgText);
}

function all() { drawMap(); drawRegion(); drawHeat(); drawManagers(); drawFunds(); drawFund(); }
document.addEventListener('mz-redraw', all);
fund = LAB.slice().sort((a, b) => (b.aum_sar || 0) - (a.aum_sar || 0))[0].symbol;
all();
$('foot').innerHTML = `المصادر: الهيئة العامة للأوقاف (${D.key.sector.waqf_designations.toLocaleString('en-US')} مصرفاً وقفياً) · السوق المالية السعودية، تداول (${D.key.index.funds_total} صندوقاً وقفياً) · حدود المناطق: ${MAP.source}. ` +
  `ترتيب المديرين وصفي من أسعار الوحدات المنشورة، وليس تقييماً لجودة الإدارة: الصناديق تختلف في أهدافها وأعمارها.`;
