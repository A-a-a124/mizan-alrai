// The landing page tells the finding as a scroll story. Each scene draws itself the first time it comes into view.
topbar('story', './');
const K = D.key;
const draw = (line, ms = 1400) => { if (still()) return; const len = line.getTotalLength(); line.style.strokeDasharray = len; line.style.strokeDashoffset = len;
  line.getBoundingClientRect(); line.style.transition = `stroke-dashoffset ${ms}ms ease`; line.style.strokeDashoffset = 0; };

const SCENES = {
  hero() {
    const svg = $('heroScale');
    const frame = a => { drawScale(svg, a, { name: 'هذا الجيل', value: '' }, { name: 'الأجيال القادمة', value: '' });
      svg.querySelectorAll('path,rect,line,circle').forEach(n => { if (n.getAttribute('fill') === css('--navy')) n.setAttribute('fill', '#cfdcf2'); if (n.getAttribute('stroke') === css('--navy')) n.setAttribute('stroke', '#cfdcf2'); }); };
    if (still()) { frame(0); return; }
    const t0 = performance.now();                                   // swing, then settle level
    const tick = now => { const t = (now - t0) / 1000, a = 12 * Math.exp(-t * .55) * Math.cos(t * 2.4); frame(a); if (t < 7) requestAnimationFrame(tick); else frame(0); };
    tick(t0);
  },
  data() { document.querySelectorAll('#s-data [data-to]').forEach(n => countUp(n, +n.dataset.to, v => Math.round(v).toLocaleString('en-US'), 1600)); },
  index() {
    const svg = $('stIndex'); svg.innerHTML = '';
    const I = D.index, xs = I.month.map((_, i) => i), lo = Math.floor(Math.min(...I.price) / 10) * 10, hi = Math.ceil(Math.max(...I.total) / 10) * 10, yt = [];
    for (let v = lo; v <= hi; v += 10) yt.push(v);
    const pad = { l: 40, r: 60, t: 12, b: 30 }, a = axes(svg, 0, xs.length - 1, lo, hi, xs.filter(i => I.month[i].endsWith('-01')), yt, i => I.month[i].slice(0, 4), v => v, pad);
    const last = xs.length - 1;
    const p = el('path', { d: path(xs.map(i => [a.sx(i), a.sy(I.price[i])])), fill: 'none', stroke: css('--series-2'), 'stroke-width': 2.4 }, svg);
    const t = el('path', { d: path(xs.map(i => [a.sx(i), a.sy(I.total[i])])), fill: 'none', stroke: css('--series-1'), 'stroke-width': 2.8 }, svg);
    el('text', { x: a.sx(last) + 6, y: a.sy(I.total[last]) + 4, 'text-anchor': 'end', fill: css('--series-1'), style: `fill:${css('--series-1')};font-weight:700` }, svg).textContent = 'مع التوزيعات';
    el('text', { x: a.sx(last) + 6, y: a.sy(I.price[last]) + 4, 'text-anchor': 'end', style: `fill:${css('--series-2')};font-weight:700` }, svg).textContent = 'السعر فقط';
    draw(p, 2200); draw(t, 2200);
  },
  payouts() {
    const svg = $('stPayouts'); svg.innerHTML = '';
    const T = D.solutions.payout_trend, max = Math.max(...T.map(r => r.events)), W = 560, H = 300, bw = (W - 60) / T.length;
    const recent = T[T.length - 1].year - 2;
    T.forEach((r, i) => { const h = r.events / max * (H - 80), x = 30 + i * bw + 8, y = H - 36 - h;
      const bar = el('rect', { x, y: still() ? y : H - 36, width: bw - 16, height: still() ? h : 0, rx: 5, fill: r.year >= recent ? css('--series-2') : css('--text-muted') }, svg);
      if (!still()) { bar.style.transition = `y .8s ease ${i * 90}ms, height .8s ease ${i * 90}ms`; bar.getBoundingClientRect(); bar.setAttribute('y', y); bar.setAttribute('height', h); bar.style.y = y + 'px'; bar.style.height = h + 'px'; }
      el('text', { x: x + (bw - 16) / 2, y: H - 16, 'text-anchor': 'middle' }, svg).textContent = r.year;
      el('text', { x: x + (bw - 16) / 2, y: y - 6, 'text-anchor': 'middle', style: 'font-weight:700;font-size:14px' }, svg).textContent = r.events; });
  },
  frontier() {
    const svg = $('stFrontier'), grid = D.scenarios.base.grid, infl = ik(D.defaults.inflation), ps = D.rates.map(r => grid[rk(r)][infl].p);
    const stops = [K.rule.rate_recent_level, K.rule.rate_balanced, K.rule.rate_cautious];
    const frame = rate => { svg.innerHTML = '';
      const pad = { l: 44, r: 12, t: 12, b: 30 }, a = axes(svg, 0, .08, 0, 1, [0, .02, .04, .06, .08], [0, .25, .5, .75, 1], v => pct(v, 0), v => pct(v, 0), pad);
      const i = Math.min(D.rates.length - 2, Math.floor(rate / .005)), p = ps[i] + (ps[i + 1] - ps[i]) * (rate - D.rates[i]) / .005;
      el('path', { d: path(D.rates.map((r, j) => [a.sx(r), a.sy(ps[j])])) + `L${a.sx(.08)} ${a.sy(0)} L${a.sx(0)} ${a.sy(0)}Z`, fill: css('--band-1') }, svg);
      el('path', { d: path(D.rates.map((r, j) => [a.sx(r), a.sy(ps[j])])), fill: 'none', stroke: css('--series-1'), 'stroke-width': 2.6 }, svg);
      el('line', { x1: a.sx(rate), x2: a.sx(rate), y1: a.sy(p), y2: a.sy(0), stroke: css('--series-2'), 'stroke-dasharray': '4 3' }, svg);
      el('circle', { cx: a.sx(rate), cy: a.sy(p), r: 10, fill: css('--series-2'), stroke: css('--card'), 'stroke-width': 2.5 }, svg);
      $('stRate').textContent = pct(rate); $('stProb').textContent = pct(p, 0); $('stProb').style.color = p >= .5 ? css('--series-3') : css('--series-2'); };
    if (still()) { frame(stops[1]); return; }
    let n = 0; frame(stops[0]);
    const go = () => { const from = stops[n], to = stops[n + 1], t0 = performance.now();
      const tick = now => { const t = Math.min(1, (now - t0) / 1300), e = t < .5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2; frame(from + (to - from) * e);
        if (t < 1) requestAnimationFrame(tick); else if (++n < stops.length - 1) setTimeout(go, 1100); };
      tick(t0); };
    setTimeout(go, 1300);
  },
  gaps() {
    const svg = $('stMap'), MAP = window.WAQF_MAP, MX = D.explore.matrix, j = MX.masarif.findIndex(m => m.key === 'orphans');
    svg.setAttribute('viewBox', `0 0 ${MAP.width} ${MAP.height}`); svg.innerHTML = '';
    MX.regions.forEach((r, i) => { const none = MX.counts[i][j] === 0, s = MAP.regions[r.key];
      const p = el('path', { d: s.d, fill: css('--surface-1') }, svg);
      if (none) { if (still()) p.setAttribute('fill', css('--critical')); else setTimeout(() => p.setAttribute('fill', css('--critical')), 500 + i * 160); } });
    MX.regions.forEach(r => { const s = MAP.regions[r.key]; el('text', { x: s.cx, y: s.cy + 3, 'text-anchor': 'middle' }, svg).textContent = r.ar; });
  },
  shock() { document.querySelectorAll('#s-shock [data-to]').forEach(n => countUp(n, +n.dataset.to, v => '-' + v.toFixed(1) + '%', 1500)); },
};

const seen = new Set();
function play(id) { if (seen.has(id)) return; seen.add(id); const node = document.querySelector(`[data-scene="${id}"]`); if (node) node.classList.add('seen'); if (SCENES[id]) SCENES[id](); }
const nodes = [...document.querySelectorAll('[data-scene]')];
// A scene plays once it is inside the window. Checked directly on scroll, resize and a slow timer,
// so nothing stays hidden if one browser event never arrives.
function check() {
  const h = window.innerHeight || document.documentElement.clientHeight;
  nodes.forEach(n => { const b = n.getBoundingClientRect(); if (b.top < h * 0.82 && b.bottom > h * 0.12) play(n.dataset.scene); });
  if (seen.size >= nodes.length) { clearInterval(timer); removeEventListener('scroll', check); removeEventListener('resize', check); }
}
let timer = 0;
if (still()) nodes.forEach(n => play(n.dataset.scene));
else { document.documentElement.classList.add('anim'); addEventListener('scroll', check, { passive: true }); addEventListener('resize', check);
  addEventListener('load', check); timer = setInterval(check, 500); check(); }
document.addEventListener('mz-redraw', () => seen.forEach(id => { if (SCENES[id] && id !== 'hero' && id !== 'data' && id !== 'shock') SCENES[id](); }));
