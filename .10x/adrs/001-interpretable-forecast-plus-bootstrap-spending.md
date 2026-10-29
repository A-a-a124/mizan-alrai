# ADR-001: Interpretable time-series forecast + block-bootstrap spending frontier

**Status:** Accepted
**Date:** 2026-10-29
**Feature:** waqf-flow-forecast
**Author:** 10x-Team (Architect + Staff Engineer)

## Context
The nazir needs a spending amount that protects real principal and a split across masarif. Return data are short (longest series ≈ 8 years, most < 4), monthly, noisy, and from a small universe (26 listed waqf funds). The rubric weights reproducibility/correctness (25) and responsible AI (15) heavily; judges must be able to verify every number.

## Decision
Forecast the equal-weight composite of accumulating waqf funds with simple, backtested models (mean, drift, damped ETS, small ARIMA), selected by rolling-origin MAE on 12-month cumulative return. Quantify risk with a stationary block bootstrap; derive spending from a frontier of P(real principal preserved at 10 y) vs spending rate under a smoothed (12-quarter) spending rule. Allocation is a deterministic, rule-ordered function (upkeep → reserve → masarif) with transparent weights.

## Alternatives Considered
| Alternative | Pros | Cons | Why Not |
|---|---|---|---|
| Gradient boosting / LSTM on returns | "AI" appeal | ~90 monthly points → overfit; hard to explain | Fails correctness + responsible-AI criteria |
| Parametric Monte Carlo (Normal returns) | Simple | Ignores fat tails & autocorrelation seen in 2020/2022 drawdowns | Bootstrap keeps empirical shape |
| LP optimiser for allocation | Optimal on paper | Needs measured need/impact data that do not exist publicly | Would fabricate precision |
| Per-fund forecasts | Granular | Most funds < 40 months | Composite pools information |

## Consequences
### Positive
- Every step is inspectable and testable; backtest proves the forecast beats naive or honestly says it does not.
- Spending frontier turns uncertainty into a single decision dial.
### Negative
- Forecast accuracy is bounded by short history; intervals will be wide.
### Risks
- Survivorship (only live funds listed) biases returns upward → disclosed; bootstrap also run on a stressed variant (returns shifted by −1 %/yr).

## Dependencies
pandas, numpy, statsmodels, matplotlib. Constrains: dashboard must reuse exported frontier tables (no second implementation of the model).
