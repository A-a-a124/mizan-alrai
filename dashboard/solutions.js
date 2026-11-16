// The three solutions (tables from src/waqf/solutions.py, exported in data.js).
const S = D.solutions, GR = ['A','B','C','D','E'];
const GRADE_TXT = {A:'الأصل محفوظ فعلياً: قيمة الوحدة نمت بمعدل التضخم أو أكثر', B:'محفوظ اسمياً فقط: قيمة الوحدة نمت أقل من التضخم',
  C:'تآكل طفيف: قيمة الوحدة نقصت حتى 2% سنوياً', D:'تآكل واضح: قيمة الوحدة نقصت بين 2% و5% سنوياً', E:'تآكل شديد: قيمة الوحدة نقصت أكثر من 5% سنوياً'};  // = solutions.GRADE_MEANING_AR
const LS = {inf:'grade', est:false, sel:null};
function drawLabel(){
  const rows = S.sustainability_label.filter(f => !LS.est || !f.provisional);
  const g = f => f[LS.inf] || f.grade;
  const aum = GR.map(x => rows.filter(f => g(f) === x).reduce((a,f) => a + (f.aum_sar || 0), 0));
  const cnt = GR.map(x => rows.filter(f => g(f) === x).length);
  const tot = aum.reduce((a,b) => a + b, 0) || 1;
  $('labSub').textContent = `${nFunds(rows.length)} · ${(tot/1e9).toFixed(2)} مليار ريال من الأصول المصنّفة`;
  $('energy').innerHTML = GR.map((x,i) => `<div class="row${LS.sel && LS.sel !== x ? ' off' : ''}" data-g="${x}" role="button" tabindex="0" aria-pressed="${LS.sel === x}" aria-label="الدرجة ${x}">
     <span class="g g${x}">${x}</span>
     <div><div class="arrow g${x}" style="width:${Math.max(8, aum[i]/tot*100).toFixed(1)}%">${pct(aum[i]/tot, 0)}</div></div>
     <span style="color:var(--text-secondary)">${nFunds(cnt[i])}</span></div>`).join('');
  const LB = D.key.label;
  $('labNote').innerHTML = `أكبر صندوق (${pct(LB.largest_fund_share_of_graded_aum, 0)} من الأصول المصنّفة) ${LB.largest_fund_is_provisional ? 'درجته مبدئية لقصر سجله' : 'سجله مكتمل'}. ` +
    `بين الصناديق المستقرة وحدها <b>${pct(LB.established_aum_share_A, 0)}</b> من الأصول بدرجة A. الدرجة A معيار موضوعي (مواكبة التضخم)، وحدود بقية الدرجات مقترحة منا وقابلة للتعديل.`;
  $('energy').querySelectorAll('.row').forEach(r => {
    const f = () => { LS.sel = LS.sel === r.dataset.g ? null : r.dataset.g; drawLabel(); };
    r.onclick = f; r.onkeydown = keyAct(f); });
  const shown = rows.filter(f => !LS.sel || g(f) === LS.sel)
    .sort((a,b) => GR.indexOf(g(a)) - GR.indexOf(g(b)) || (b.aum_sar || 0) - (a.aum_sar || 0));
  $('fundSub').textContent = LS.sel ? `الدرجة ${LS.sel}: ${GRADE_TXT[LS.sel]} (${nFunds(shown.length)})`
                                    : 'اضغط أي صندوق لتفاصيله · الإطار المتقطع = سجل أقل من 36 شهراً (درجة مبدئية)';
  $('fundGrid').innerHTML = shown.map(f => `<div class="fund${f.provisional ? ' prov' : ''}" role="button" tabindex="0" data-s="${f.symbol}">
     <span class="g g${g(f)}">${g(f)}</span><div><div class="nm">${f.fund_name}</div>
     <div class="mt">${f.months} شهراً · ${f.aum_sar ? (f.aum_sar/1e6).toFixed(0) + ' مليون ريال' : 'الأصول غير منشورة'}</div></div></div>`).join('')
     || '<div class="sub">لا توجد صناديق بهذه الدرجة.</div>';
  $('fundGrid').querySelectorAll('.fund').forEach(c => { const f = () => showFund(c.dataset.s); c.onclick = f; c.onkeydown = keyAct(f); });
}
function showFund(sym){
  const f = S.sustainability_label.find(x => x.symbol === sym), g = f[LS.inf] || f.grade, d = $('fundDetail');
  d.style.display = 'block';
  d.innerHTML = `<div style="display:flex;gap:8px;align-items:center"><span class="g g${g}">${g}</span><b class="ltr">${f.fund_name}</b></div>
   <div style="margin-top:6px">${GRADE_TXT[g]}${f.provisional ? ' <span class="pill">مبدئي: سجل قصير</span>' : ''}</div>
   <table class="t" style="margin-top:6px">
   <tr><td>نمو قيمة الوحدة سنوياً</td><td class="n">${pct(f.unit_growth)}</td></tr>
   <tr><td>بعد خصم تضخم 2%</td><td class="n">${pct(f.real_unit_growth)}</td></tr>
   <tr><td>التوزيع المقدَّر سنوياً</td><td class="n">${f.est_payout_rate == null ? '—' : pct(f.est_payout_rate)}</td></tr>
   <tr><td>أكبر تراجع من القمة</td><td class="n">${pct(f.max_drawdown)}</td></tr>
   <tr><td>مدير الصندوق</td><td class="n">${f.manager}</td></tr></table>`;
}
document.querySelectorAll('[data-inf]').forEach(b => b.onclick = () => {
  document.querySelectorAll('[data-inf]').forEach(x => x.setAttribute('aria-pressed', x === b));
  LS.inf = b.dataset.inf; drawLabel(); $('fundDetail').style.display = 'none'; });
$('estOnly').onclick = () => { LS.est = !LS.est; $('estOnly').setAttribute('aria-pressed', LS.est); drawLabel(); };

const OPT = {cautious:{n:'متحفظ', c:'--series-1'}, balanced:{n:'متوازن', c:'--series-3'}, recent_level:{n:'مستوى التوزيع الأخير', c:'--series-2'}};
const RS = {opt:'balanced', h:10};
function drawRule(){
  const menu = S.spending_menu, V = Math.max(0, +$('endow').value || 0);
  $('opts').innerHTML = Object.keys(OPT).map(o => { const r = menu.find(m => m.option === o);
    return `<button class="opt" data-o="${o}" aria-pressed="${o === RS.opt}"><div class="r" style="color:var(${OPT[o].c})">${pct(r.rate)}</div><div class="n">${OPT[o].n}</div></button>`; }).join('');
  $('opts').querySelectorAll('.opt').forEach(b => b.onclick = () => { RS.opt = b.dataset.o; drawRule(); });
  const m = menu.find(x => x.option === RS.opt && x.years === RS.h);
  $('big3').innerHTML = `<div><div class="v">${sar(V * m.cumulative_real_payout / 100)}</div><div class="l">ريال يصل للمستفيدين خلال ${RS.h === 10 ? '10 سنوات' : RS.h + ' سنة'} (بأسعار اليوم)</div></div>
    <div><div class="v" style="color:${m.median_real_value >= 100 ? css('--navy') : css('--series-2')}">${sar(V * m.median_real_value / 100)}</div><div class="l">قيمة الوقف الباقية للأجيال القادمة (الوسيط)</div></div>
    <div><div class="v">${pct(m.p_preserve_real, 0)}</div><div class="l">احتمال أن يبقى الأصل فوق قيمته الحقيقية اليوم</div></div>`;
  const sm = D.key.rule.smoothing;
  const bar = (v, c, l) => `<div><div style="font-size:12.5px;margin-bottom:3px">${l}: <b>${pct(v, 0)}</b></div><div class="meter"><i style="width:${(v*100).toFixed(1)}%;background:var(${c})"></i></div></div>`;
  $('smooth').innerHTML = bar(sm.unsmoothed_p_cut_over_5pct, '--series-2', 'الصرف من قيمة آخر سنة') + bar(sm.smoothed_p_cut_over_5pct, '--series-3', 'الصرف من متوسط 12 ربعاً (ميزان)');
  const L = D.key.legacy, per = x => V * x / 100;
  countUp($('impactV'), per(L.balanced_vs_recent_extra_payout_after), sar, 900);
  $('impactL').innerHTML = `ريال إضافية كل سنة يستطيع الوقف صرفها بعد ${L.years} سنة إذا اتبع المعدل المتوازن بدل مستوى التوزيع الأخير، لأن الأصل الباقي أكبر.`;
  $('impactRow').innerHTML = `<div>الأصل الباقي بالمعدل المتوازن<b>${sar(per(L.balanced_value_left))} ريال</b>يكفي لصرف ${sar(per(L.balanced_sustainable_payout_after))} ريال سنوياً بمعدل ${pct(L.sustainable_rate)}</div>
    <div>الأصل الباقي بمستوى التوزيع الأخير<b>${sar(per(L.recent_level_value_left))} ريال</b>يكفي لصرف ${sar(per(L.recent_level_sustainable_payout_after))} ريال سنوياً بالمعدل نفسه</div>`;
  const RB = S.menu_robustness.filter(x => x.years === 10), AS = { base: 'كما رُصد في التاريخ', lower_return: 'عائد أقل 1% سنوياً', harsh: 'عائد أقل 2% وتذبذب أعلى 50%' };
  $('robust').innerHTML = '<tr><th>الافتراض</th>' + Object.keys(OPT).map(o => `<th>${OPT[o].n} ${pct(menu.find(x => x.option === o).rate)}</th>`).join('') + '</tr>' +
    Object.entries(AS).map(([a, n]) => `<tr><td>${n}</td>` + Object.keys(OPT).map(o => { const v = RB.find(x => x.assumption === a && x.option === o).p_preserve_real;
      return `<td class="n" style="${o === RS.opt ? 'font-weight:700;color:var(--navy)' : ''}">${pct(v, 0)}</td>`; }).join('') + '</tr>').join('');
  $('robustNote').innerHTML = `<b>ما يثبت:</b> في كل افتراض، المعدل الأقل يحفظ أصلاً أكبر. <b>ما يتغير:</b> المستوى، فابدأ من الطرف المتحفظ وراجع المعدل كل سنة. ` +
    `السجل ${D.key.rule.history_months} شهراً فقط: القرار مبني على أفق 10 سنوات، وأرقام 20 إلى 40 سنة توضّح اتجاه المقايضة ولا تتنبأ.`;
  drawTradeoff();
}
document.querySelectorAll('[data-h]').forEach(b => b.onclick = () => {
  document.querySelectorAll('[data-h]').forEach(x => x.setAttribute('aria-pressed', x === b)); RS.h = +b.dataset.h; drawRule(); });
function drawTradeoff(){
  const svg = $('tradeoff'); svg.innerHTML = '';
  const Y = S.spending_menu_yearly, opts = Object.keys(OPT), years = [...new Set(Y.map(r => r.year))].sort((a,b) => a - b);
  const ser = o => Y.filter(r => r.option === o).sort((a,b) => a.year - b.year).map(r => r.median_real_payout);
  const S3 = opts.map(ser), hi = Math.ceil(Math.max(...S3.flat()));
  const pad = {l:36, r:14, t:12, b:30}, yt = []; for (let v = 0; v <= hi; v += 1) yt.push(v);
  const last = years[years.length - 1];
  const a = axes(svg, years[0], last, 0, hi, [1,10,20,30,40].filter(x => x <= last), yt, v => v + ' سنة', v => v.toFixed(0), pad);
  el('rect', {x:a.sx(years[0]), y:pad.t, width:a.sx(RS.h) - a.sx(years[0]), height:300 - pad.t - pad.b, fill:css('--band-1')}, svg);
  opts.forEach((o,j) => el('path', {d:path(S3[j].map((v,i) => [a.sx(years[i]), a.sy(v)])), fill:'none', stroke:css(OPT[o].c),
     'stroke-width':o === RS.opt ? 3.2 : 1.6, opacity:o === RS.opt ? 1 : .45}, svg));
  const be = D.key.rule.breakeven_year_balanced;
  if (be){ el('line', {x1:a.sx(be), x2:a.sx(be), y1:pad.t, y2:300 - pad.b, stroke:css('--text-muted'), 'stroke-dasharray':'4 3'}, svg);
    el('text', {x:a.sx(be) - 4, y:pad.t + 12, 'text-anchor':'start'}, svg).textContent = 'السنة ' + be + ': المتوازن يتجاوز'; }
  $('tradeLeg').innerHTML = opts.map(o => `<span><i style="background:var(${OPT[o].c})"></i>${OPT[o].n} ${pct(S.spending_menu.find(m => m.option === o).rate)}</span>`).join('');
  hover(svg, $('tipT'), years, a.sx, i => `السنة ${years[i]}<br>` + opts.map((o,j) => `${OPT[o].n}: <b>${S3[j][i].toFixed(2)}</b>`).join('<br>'));
  const r = o => S.spending_menu.find(m => m.option === o && m.years === 30);
  $('tradeNote').innerHTML = `<b>المقايضة بصراحة:</b> الصرف الأعلى يعطي أكثر في العقود الأولى (مجموع 30 سنة: ${r('recent_level').cumulative_real_payout.toFixed(0)} مقابل ${r('balanced').cumulative_real_payout.toFixed(0)} للمتوازن) لكنه يترك أصلاً قيمته ${r('recent_level').median_real_value.toFixed(0)} بدل ${r('balanced').median_real_value.toFixed(0)}، ويتناقص صرفه السنوي عاماً بعد عام.`;
}

function drawCompass(){
  const R = S.compass_regions.slice().sort((a,b) => b.social_share_after - a.social_share_after), svg = $('regions'); svg.innerHTML = '';
  const W = 560, rowH = 300 / R.length, x0 = 130, sx = v => x0 + v * (W - x0 - 50);
  [0, .25, .5, .75].forEach(v => { el('line', {x1:sx(v), x2:sx(v), y1:6, y2:310, stroke:css('--rule')}, svg);
    el('text', {x:sx(v), y:324, 'text-anchor':'middle'}, svg).textContent = pct(v, 0); });
  R.forEach((r,i) => { const y = 8 + i * rowH;
    el('text', {x:x0 - 8, y:y + rowH * .62, 'text-anchor':'start'}, svg).textContent = r.region_ar;
    el('rect', {x:x0, y:y + 2, width:Math.max(1, sx(r.social_share_after) - x0), height:rowH - 5, rx:3, fill:css('--series-3')}, svg);
    el('rect', {x:x0, y:y + 2, width:Math.max(1, sx(r.social_share) - x0), height:rowH - 5, rx:3, fill:css('--text-muted')}, svg);
    el('text', {x:sx(r.social_share_after) + 4, y:y + rowH * .62, 'text-anchor':'end'}, svg).textContent = pct(r.social_share_after, 0); });
  const ov = el('rect', {x:0, y:0, width:560, height:310, fill:'transparent'}, svg);
  ov.addEventListener('mousemove', ev => { const b = svg.getBoundingClientRect(), y = (ev.clientY - b.top) / b.height * 330;
    const r = R[Math.max(0, Math.min(R.length - 1, Math.floor((y - 8) / rowH)))], tip = $('tipR');
    tip.innerHTML = `<b>${r.region_ar}</b> · ${r.waqf_designations.toLocaleString('en-US')} مصرف وقفي<br>الرعاية الاجتماعية اليوم: <b>${pct(r.social_share)}</b><br>بعد البوصلة: <b>${pct(r.social_share_after)}</b> (+${(r.gain_points*100).toFixed(0)} نقطة)`;
    tip.style.display = 'block'; const card = svg.parentElement.getBoundingClientRect();
    tip.style.left = Math.min(ev.clientX - card.left + 12, card.width - tip.offsetWidth - 8) + 'px'; tip.style.top = (ev.clientY - card.top - 10) + 'px'; });
  ov.addEventListener('mouseleave', () => $('tipR').style.display = 'none');

  const V = Math.max(0, +$('endow').value || 0), scale = V / D.key.allocation.endowment;
  const C = S.compass_case.filter(r => r.total > 0).sort((a,b) => b.total - a.total).slice(0, 10), mx = Math.max(...C.map(r => r.total));
  $('caseSub').textContent = `صرف سنة لوقف قيمته ${sar(V)} ريال (بمعدل ${pct(D.key.allocation.budget / D.key.allocation.endowment)}) بالمزيج الوطني: الرمادي من شروط الواقفين، والأخضر ما تضيفه البوصلة من الحصة المرنة`;
  $('caseBars').innerHTML = C.map(r => `<div class="alloc-row"><span>${r.label_ar}${r.multiple > 1.5 ? ` <span class="pill">×${r.multiple.toFixed(0)}</span>` : ''}</span>
    <div style="display:flex;height:14px"><div style="width:${(r.from_waqif_conditions/mx*100).toFixed(1)}%;background:var(--text-muted)"></div><div style="width:${(r.from_flexible_share/mx*100).toFixed(1)}%;background:var(--series-3)"></div></div>
    <span class="amt">${sar(r.total * scale)}</span></div>`).join('');
}
$('endow').addEventListener('input', () => { drawRule(); drawCompass(); });
document.addEventListener('mz-redraw', () => { drawLabel(); drawRule(); drawCompass(); });
drawLabel(); drawRule(); drawCompass();
