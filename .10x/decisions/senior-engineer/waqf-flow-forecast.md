# Senior Engineer — waqf-flow-forecast
- Index: month-end regular grid; returns only where both months observed or imputed (flag); equal weight across available accumulating funds per month.
- Backtest: expanding window, origins every month with ≥ 36 months history, target = next-12-month log return; no future data in fit (unit-tested by truncation).
- Bootstrap: stationary bootstrap (geometric block length mean 6).
- Spending rule simulation monthly; spend paid quarterly from 12-quarter trailing average.
