// "Your waqf in a minute": three answers -> a one-page spending plan. Uses the same grid and tables as the simulator.
topbar('plan', '../');
const MXP = D.explore.matrix, SOCP = new Set(D.explore.social), RULE = D.key.rule;
const TYPES = { charity: 'وقف خيري عام (على مصارف المنطقة)', family: 'وقف ذُرّي (على الذرية)', mixed: 'وقف مشترك (60% ذرية + 40% أوجه البر)' };
const RATES = { cautious: ['متحفظ', RULE.rate_cautious], balanced: ['متوازن', RULE.rate_balanced] };
let option = 'cautious';

for (const [k, v] of Object.entries(TYPES)) $('ptype').add(new Option(v, k));
$('pregion').add(new Option('المملكة (المزيج الوطني)', 'national'));
MXP.regions.forEach(r => $('pregion').add(new Option(r.ar, r.key)));
const asked = new URLSearchParams(location.search).get('region');
if (asked && [...$('pregion').options].some(o => o.value === asked)) $('pregion').value = asked;

function profileFor(type, region) {
  if (type === 'family') return { family: 1 };
  if (type === 'mixed') return D.profiles.family_mixed;
  return D.profiles[region];
}
function drawPlan() {
  const V = Math.max(0, +$('pvalue').value || 0), type = $('ptype').value, region = $('pregion').value, rate = RATES[option][1];
  const regionName = region === 'national' ? 'المملكة' : MXP.regions.find(r => r.key === region).ar;
  const cell = D.scenarios.base.grid[rk(rate)][ik(D.defaults.inflation)], yearly = V * rate, m = D.solutions.spending_menu.find(x => x.option === option && x.years === 10);
  $('planChips').innerHTML = Object.entries(RATES).map(([k, [n, r]]) => `<button class="chip" data-k="${k}" aria-pressed="${k === option}">${n}: ${pct(r)} سنوياً</button>`).join('');
  $('planChips').querySelectorAll('.chip').forEach(b => b.onclick = () => { option = b.dataset.k; drawPlan(); });
  $('planHead').innerHTML = `وقف قيمته <b>${sar(V)}</b> ريال · ${TYPES[type]} · ${regionName}`;
  $('planBig').innerHTML = `<div><div class="v">${sar(yearly)}</div><div class="l">ريال للصرف في السنة الأولى (${pct(rate)})</div></div>
    <div><div class="v">${sar(yearly / 4)}</div><div class="l">ريال كل ربع سنة</div></div>
    <div><div class="v">${pct(cell.p, 0)}</div><div class="l">احتمال أن يحفظ الوقف قيمته الحقيقية بعد 10 سنوات</div></div>`;
  $('planRule').innerHTML = `اصرف كل ربع سنة <b>${(rate * 100 / 4).toFixed(3).replace(/0+$/, '')}%</b> من <b>متوسط قيمة الوقف في آخر 12 ربعاً</b>، لا من قيمته اليوم. ` +
    `بهذا لا يقفز الصرف في السنة الجيدة ولا ينهار في السيئة: احتمال أن ينخفض الصرف أكثر من 5% في سنة ما ينزل من ${pct(RULE.smoothing.unsmoothed_p_cut_over_5pct, 0)} إلى ${pct(RULE.smoothing.smoothed_p_cut_over_5pct, 0)}. ` +
    `النطاق المقترح للمعدل بين ${pct(RULE.rate_cautious)} و${pct(RULE.rate_balanced)} سنوياً.`;
  $('planAlloc').innerHTML = allocRows(V, rate, profileFor(type, region), 0, 12);
  const years = Math.ceil(1 / D.defaults.reserve_share);
  $('planReserve').innerHTML = `احتجز <b>${pct(D.defaults.reserve_share, 0)}</b> من مبلغ الصرف كل سنة (<b>${sar(yearly * D.defaults.reserve_share)}</b> ريال) حتى يبلغ الاحتياطي صرف سنة كاملة (<b>${sar(yearly)}</b> ريال)، ` +
    `أي خلال نحو ${years} سنوات. يُستعمل الاحتياطي لتثبيت الصرف في سنة العائد السالب، واحتمالها في المحاكاة ${pct(D.key.forecast.bootstrap_p_loss, 0)}. ` +
    `وقدّم <b>${pct(D.defaults.upkeep_share, 0)}</b> لعمارة الوقف وصيانته قبل أي توزيع.`;
  let gapHtml = '';
  if (type !== 'family') {
    if (region === 'national') gapHtml = 'اختر منطقة لترى مصارف الرعاية الاجتماعية الغائبة عنها.';
    else {
      const i = MXP.regions.findIndex(r => r.key === region), gone = MXP.masarif.filter((mm, j) => SOCP.has(mm.key) && MXP.counts[i][j] === 0);
      gapHtml = gone.length ? `في ${regionName} لا يوجد مصرف وقفي مسجّل لـ <b>${gone.map(g => g.ar).join('، ')}</b>. إن كان في شرط الواقف حصة لـ«أوجه البر»، فهذه أولى المصارف بها.`
                            : `مصارف الرعاية الاجتماعية الخمسة كلها ممثّلة في ${regionName}. وجّه الحصة المرنة حسب أوزان الأولوية المعلنة.`;
    }
  } else gapHtml = 'الوقف الذرّي يُصرف على الذرية بشرط الواقف، فلا حصة مرنة فيه. إن أراد الواقف نفعاً عاماً فليخصّص حصة لـ«أوجه البر».';
  $('planGaps').innerHTML = gapHtml;
  const b = cell.bands;
  $('planOutlook').innerHTML = `بعد 10 سنوات، وبأسعار اليوم: القيمة المتوقعة للوقف <b>${sar(V * b[1][10] / 100)}</b> ريال (الوسيط)، ` +
    `وفي 8 حالات من 10 تقع بين <b>${sar(V * b[0][10] / 100)}</b> و<b>${sar(V * b[2][10] / 100)}</b> ريال. ` +
    `ومجموع ما يصل للمستفيدين في العشر سنوات نحو <b>${sar(V * m.cumulative_real_payout / 100)}</b> ريال.`;
}
['pvalue', 'ptype', 'pregion'].forEach(id => $(id).addEventListener('input', drawPlan));
$('printBtn').onclick = () => window.print();
document.addEventListener('mz-redraw', drawPlan);
drawPlan();
$('planFoot').innerHTML = `الأرقام من محاكاة ${D.key.spending.paths.toLocaleString('en-US')} مسار مبنية على ${RULE.history_months} شهراً من تاريخ ${D.key.index.funds_total} صندوقاً وقفياً مدرجاً، بافتراض تضخم ${pct(D.defaults.inflation, 0)}. ` +
  `الصناديق المدرجة وكيل لأداء الاستثمار الوقفي وليست وقفك بعينه، فالخطة نقطة بداية لمجلس النظارة وليست فتوى ولا توصية استثمارية. شرط الواقف مقدَّم دائماً.`;
