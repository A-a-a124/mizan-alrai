// Shared helpers for every page. Every number shown comes from data.js (written by scripts/run_analysis.py).
const D = window.WAQF_DATA;
const $ = id => document.getElementById(id);
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const pct = (x, d = 1) => (x * 100).toFixed(d) + '%';
const sar = x => Math.round(x).toLocaleString('en-US');
const NS = 'http://www.w3.org/2000/svg';
const el = (tag, attrs = {}, parent) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; };
const rk = r => r.toFixed(3), ik = i => i.toFixed(3);
const path = pts => pts.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ');
const keyAct = f => e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); f(); } };
const nFunds = n => n === 0 ? 'لا صناديق' : n === 1 ? 'صندوق واحد' : n === 2 ? 'صندوقان' : n <= 10 ? n + ' صناديق' : n + ' صندوقاً';
const still = () => document.hidden || matchMedia('(prefers-reduced-motion: reduce)').matches;

// ---- top bar (same on every page) and the light/dark switch
const PAGES = [['story', 'القصة', ''], ['sim', 'المحاكي والحلول', 'dashboard/'], ['explore', 'استكشف البيانات', 'dashboard/explore.html'],
               ['plan', 'وقفك في دقيقة', 'dashboard/plan.html']];
function topbar(active, root) {
  const bar = document.createElement('div'); bar.className = 'topbar';
  bar.innerHTML = `<div class="in"><a class="brand" href="${root}">ميزان الريع</a><nav aria-label="صفحات الموقع">` +
    PAGES.map(([k, n, h]) => `<a href="${root}${h}"${k === active ? ' aria-current="page"' : ''}>${n}</a>`).join('') +
    `</nav><button id="themeBtn" type="button" aria-label="تبديل الوضع الفاتح والداكن">☀︎ / ☾</button></div>`;
  document.body.prepend(bar);
  let saved = null; try { saved = localStorage.getItem('mz-theme'); } catch (e) { /* storage may be blocked */ }
  if (saved) document.documentElement.dataset.theme = saved;
  $('themeBtn').onclick = () => {
    const dark = document.documentElement.dataset.theme ? document.documentElement.dataset.theme === 'dark'
                                                        : matchMedia('(prefers-color-scheme: dark)').matches;
    document.documentElement.dataset.theme = dark ? 'light' : 'dark';
    try { localStorage.setItem('mz-theme', document.documentElement.dataset.theme); } catch (e) { /* ignore */ }
    document.dispatchEvent(new Event('mz-redraw'));          // charts read their colours when drawn
  };
}

// ---- motion: numbers count up, charts glide between states
function countUp(node, to, fmt, ms = 600) {
  const from = typeof node._v === 'number' ? node._v : 0, t0 = performance.now();
  node._v = to; cancelAnimationFrame(node._raf);
  if (still() || from === to) { node.textContent = fmt(to); return; }
  const step = now => { const t = Math.min(1, (now - t0) / ms), e = 1 - Math.pow(1 - t, 3);
    node.textContent = fmt(from + (to - from) * e); if (t < 1) node._raf = requestAnimationFrame(step); };
  step(t0);
}
const _anim = {};
const _lerp = (a, b, t) => Array.isArray(b) ? b.map((x, i) => _lerp(Array.isArray(a) ? a[i] : undefined, x, t))
                         : typeof b === 'number' ? (typeof a === 'number' ? a + (b - a) * t : b) : b;
function animate(id, target, draw, ms = 450) {
  const prev = _anim[id], from = prev ? prev.cur : target, t0 = performance.now();
  if (prev) cancelAnimationFrame(prev.raf);
  if (still() || !prev) { _anim[id] = { cur: target, raf: 0 }; draw(target); return; }
  const step = now => { const t = Math.min(1, (now - t0) / ms), e = 1 - Math.pow(1 - t, 3), cur = {};
    for (const k in target) cur[k] = _lerp(from[k], target[k], e);
    _anim[id] = { cur, raf: 0 }; draw(cur); if (t < 1) _anim[id].raf = requestAnimationFrame(step); };
  step(t0);
}

// ---- charts (560 x 300 canvas)
function axes(svg, x0, x1, y0, y1, xt, yt, fx, fy, pad) {
  const W = 560, H = 300; const sx = v => pad.l + (v - x0) / (x1 - x0) * (W - pad.l - pad.r), sy = v => H - pad.b - (v - y0) / (y1 - y0) * (H - pad.t - pad.b);
  yt.forEach(v => { el('line', { x1: pad.l, x2: W - pad.r, y1: sy(v), y2: sy(v), stroke: css('--rule'), 'stroke-width': 1 }, svg);
                    el('text', { x: pad.l - 6, y: sy(v) + 4, 'text-anchor': 'end' }, svg).textContent = fy(v); });
  xt.forEach(v => { el('text', { x: sx(v), y: H - pad.b + 16, 'text-anchor': 'middle' }, svg).textContent = fx(v); });
  return { sx, sy, W, H };
}
function placeTip(tip, ev, host) {
  tip.style.display = 'block';
  const card = host.getBoundingClientRect();
  tip.style.left = Math.max(4, Math.min(ev.clientX - card.left + 12, card.width - tip.offsetWidth - 8)) + 'px';
  tip.style.top = (ev.clientY - card.top - 10) + 'px';
}
function hover(svg, tip, xs, sx, render) {
  const ov = el('rect', { x: 0, y: 0, width: 560, height: 300, fill: 'transparent' }, svg);
  const guide = el('line', { y1: 10, y2: 270, stroke: css('--text-muted'), 'stroke-dasharray': '3 3', visibility: 'hidden' }, svg);
  ov.addEventListener('mousemove', ev => {
    const b = svg.getBoundingClientRect(), x = (ev.clientX - b.left) / b.width * 560;
    let i = 0, best = 1e9; xs.forEach((v, j) => { const d = Math.abs(sx(v) - x); if (d < best) { best = d; i = j; } });
    guide.setAttribute('x1', sx(xs[i])); guide.setAttribute('x2', sx(xs[i])); guide.setAttribute('visibility', 'visible');
    tip.innerHTML = render(i); placeTip(tip, ev, svg.parentElement);
  });
  ov.addEventListener('mouseleave', () => { tip.style.display = 'none'; guide.setAttribute('visibility', 'hidden'); });
}
// colour between two hex colours (t in 0..1), for the map and the heat table
function mix(a, b, t) {
  const h = c => [1, 3, 5].map(i => parseInt(c.slice(i, i + 2), 16)), A = h(a), B = h(b);
  return 'rgb(' + A.map((v, i) => Math.round(v + (B[i] - v) * t)).join(',') + ')';
}

// ---- allocation: mirrors src/waqf/allocate.py (upkeep -> reserve -> waqif conditions -> flexible)
function allocate(V, rate, profile, reserveBalance) {
  const d = D.defaults, budget = V * rate, upkeep = budget * d.upkeep_share;
  const reserve = Math.min(budget * d.reserve_share, Math.max(0, budget - reserveBalance));
  const masarif = budget - upkeep - reserve;
  const tot = Object.values(profile).reduce((a, b) => a + b, 0);
  const lines = [{ line: 'upkeep', kind: 'waterfall', amount: upkeep }, { line: 'reserve', kind: 'waterfall', amount: reserve }];
  for (const [m, s] of Object.entries(profile)) if (m !== 'general_charity' && s > 0) lines.push({ line: m, kind: 'waqif', amount: s / tot * masarif });
  const flex = (profile.general_charity || 0) / tot * masarif;
  const w = Object.entries(D.priorities).filter(([, v]) => v > 0);
  if (flex > 0 && w.length) {
    const base = Math.min(d.floor * masarif, flex / w.length), rest = flex - base * w.length, ws = w.reduce((a, [, v]) => a + v, 0);
    for (const [m, v] of w) lines.push({ line: m, kind: 'flex', amount: base + rest * v / ws });
  }
  return { budget, lines };
}
const lineLabel = k => k === 'upkeep' ? 'عمارة الوقف وصيانته' : k === 'reserve' ? 'احتياطي استقرار الصرف' : (D.masraf_labels[k] || k);
function allocRows(V, rate, profile, reserve, top = 14) {
  const { budget, lines } = allocate(V, rate, profile, reserve);
  const merged = {}; lines.forEach(l => { const k = l.line; merged[k] = merged[k] || { line: k, amount: 0, kinds: new Set() }; merged[k].amount += l.amount; merged[k].kinds.add(l.kind); });
  const rows = Object.values(merged).filter(r => r.amount > 0).sort((a, b) => b.amount - a.amount);
  const max = Math.max(...rows.map(r => r.amount), 1);
  const color = r => r.kinds.has('waterfall') ? css('--text-muted') : (r.kinds.has('flex') && !r.kinds.has('waqif') ? css('--series-3') : css('--series-1'));
  return rows.slice(0, top).map(r => `<div class="alloc-row"><span>${lineLabel(r.line)}${r.kinds.has('flex') && r.kinds.has('waqif') ? ' <span class="pill">+مرن</span>' : ''}</span>
     <div class="track"><div class="bar" style="width:${(r.amount / max * 100).toFixed(1)}%;background:${color(r)}"></div></div>
     <span class="amt">${sar(r.amount)}</span></div>`).join('')
    + (rows.length > top ? `<div class="alloc-row"><span>مصارف أخرى (${rows.length - top})</span><div></div><span class="amt">${sar(rows.slice(top).reduce((a, r) => a + r.amount, 0))}</span></div>` : '')
    + `<div class="alloc-row" style="border-top:1px solid var(--rule);padding-top:4px"><b>الإجمالي</b><div></div><b class="amt">${sar(budget)}</b></div>`;
}

// ---- the scale: tilts toward the side that takes more than the sustainable rate allows
function drawScale(svg, angle, right, left) {
  svg.innerHTML = '';
  const cx = 210, cy = 62, L = 132, a = angle * Math.PI / 180, ink = css('--navy') || '#17263f';
  const ex = s => cx + s * L * Math.cos(a), ey = s => cy + s * L * Math.sin(a);          // s = +1 right end, -1 left end
  el('path', { d: `M${cx - 46} 206 H${cx + 46} L${cx + 30} 192 H${cx - 30} Z`, fill: ink }, svg);
  el('rect', { x: cx - 5, y: cy, width: 10, height: 134, rx: 3, fill: ink }, svg);
  el('line', { x1: ex(-1), y1: ey(-1), x2: ex(1), y2: ey(1), stroke: ink, 'stroke-width': 7, 'stroke-linecap': 'round' }, svg);
  el('circle', { cx, cy, r: 11, fill: ink }, svg); el('circle', { cx, cy, r: 4, fill: css('--card') || '#fff' }, svg);
  for (const [s, side, col] of [[1, right, css('--series-2')], [-1, left, css('--series-3')]]) {
    const x = ex(s), y = ey(s), py = y + 66;
    el('path', { d: `M${x} ${y} L${x - 40} ${py} M${x} ${y} L${x + 40} ${py}`, stroke: ink, 'stroke-width': 1.6, fill: 'none' }, svg);
    el('path', { d: `M${x - 50} ${py} H${x + 50} Q${x} ${py + 34} ${x - 50} ${py} Z`, fill: col }, svg);
    el('text', { x, y: py + 54, 'text-anchor': 'middle', 'font-weight': 700 }, svg).textContent = side.name;
    el('text', { x, y: py + 72, 'text-anchor': 'middle' }, svg).textContent = side.value;
  }
}
