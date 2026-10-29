# Spec — ميزان الريع · Mizan Al-Rai (منصة التنبؤ الذكي بالتدفقات المالية للوقف)

**Date:** 2026-10-29 · **Status:** Approved by user (brainstorm, 4 decisions) · **Competition:** مسابقة تحليل البيانات للقطاع غير الربحي

## 1. Decision question (criterion 1 — 15 pts)
> "How much can a waqf nazir spend next year **without eroding the endowed principal in real terms**, and how should that amount be split across the Sharia disbursement channels (المصارف) given the waqif's conditions?"

Outputs a nazir can act on: (a) a sustainable spending rate with a stated risk level, (b) a 12-month return forecast with an interval, (c) an allocation table: asset upkeep (عمارة الوقف) → stability reserve → masarif.

## 2. Data (real, open, non-profit only — rule 5)
| Source | Content | Size | Access |
|---|---|---|---|
| GASA on open.data.gov.sa (18 datasets) | waqf disbursement categories by region (15,305 waqf records), certificates 2019-25, beneficiaries 2023-25, inspections, unknown-waqf reports & rewards | 18 tables | Portal preview API via browser (WAF blocks scripts) |
| Saudi Exchange (Tadawul) | 26 CMA-licensed public waqf funds: universe + month-end unit price history 2018-10 → 2026-10 | 1,053 obs | Chart-data endpoint via browser (WAF blocks scripts) |

Snapshots live in `data_raw/` with provenance + integrity checks (row counts per GASA table; count+price-sum checksum per fund). Pipeline is offline-reproducible from these snapshots.

## 3. Method
1. **Clean** (`clean.py`): BOM headers, Arabic orthographic normalisation of masraf labels (ه/ة, ا/أ, alias map), numeric parsing ("2022 وماقبلها", "8,514,665 "), trailing spaces; funds: drop par-stale pre-launch prices, flag repeated stale prices, regularise to month-end, mark quarterly-reporting gaps and interpolate log-linearly (flagged `imputed`), exclude funds with < 12 months, separate **accumulating (Growth)** from **distributing** funds (price ≠ total return for distributors).
2. **Composite index**: equal-weight chain-linked monthly log returns of accumulating funds = "Saudi Waqf Growth Index".
3. **Forecast** (`forecast.py`): candidates = historical mean, random-walk-with-drift, ETS (Holt, damped) on log index, ARIMA small grid on returns. Rolling-origin backtest of 12-month cumulative return; pick by MAE; report interval from residual bootstrap.
4. **Risk** (`risk.py`): stationary block bootstrap of monthly returns (block 6, 10,000 paths, 10-yr horizon, seed 2026).
5. **Spending** (`spending.py`): rule = rate × trailing 12-quarter average value (Yale-style smoothing). For each rate 0–8 % compute P(real value at 10 yr ≥ starting real value) with inflation parameter (default 2 %/yr, adjustable). Output the **spending frontier** and the recommended rate at the chosen confidence (default 60 %).
6. **Allocate** (`allocate.py`): budget = sustainable spend. Order (Sharia practice): عمارة الوقف (upkeep %) first → stability reserve (tops up when forecast lower band < plan) → masarif. Masarif shares: waqif-conditioned categories fixed (default profile = GASA regional/national mix); the flexible "أوجه البر" share allocated by transparent priority weights with diminishing returns and per-masraf floor. Invariants: sum == budget, no masraf below floor.
7. **Sector context**: registered-waqf growth trend (log-linear, 7 points — descriptive with caution), category concentration by region (HHI), flexible-share map.

## 4. Deliverables (competition folder structure)
`README.md` · `analysis.ipynb` (Arabic narrative, executed) · `scripts/run_analysis.py` (one-command rebuild) · `data_clean/` · `outputs/figures/` · `outputs/tables/` · `report/executive_summary.pdf` (Arabic, RTL, publication quality, 3-4 pp) · `ai_usage_log.md` · `tests/` · **bonus** `dashboard/index.html` (offline interactive decision simulator for the final presentation).

## 5. Error handling & reproducibility
Fixed seed; every report number read from `outputs/tables/*.csv|json`; ingest verifies integrity checks and fails loudly; no network needed to rebuild.

## 6. Testing
pytest: normalisation idempotence & alias coverage, integrity checks, return math, backtest has no look-ahead, allocation invariants (sum, floors, ordering), spending frontier monotonic in rate. End-to-end: `python scripts/run_analysis.py` from clean checkout.

## 7. Limitations (disclosed)
Listed waqf funds proxy waqf investment performance (not a specific family waqf's statements); short histories (longest ≈ 8 yrs, most < 4); distributing funds' price returns exclude payouts; GASA beneficiary data is national-only (3 years) so allocation uses waqif-condition mixes + transparent priority weights, not measured need; inflation is a parameter.

## Self-review
No TBDs. Consistent: decision ↔ outputs ↔ tests. Scope: one notebook-sized analysis + report + dashboard. Ambiguity resolved: "sustainable" = P(real principal preserved at 10 yrs) ≥ confidence level.
