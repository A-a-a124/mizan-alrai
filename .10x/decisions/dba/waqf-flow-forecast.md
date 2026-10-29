# DBA — waqf-flow-forecast
No database: flat files. Raw = immutable snapshots with integrity checks (data_raw/). Clean = UTF-8-SIG CSVs keyed by (region, masraf) and (symbol, month[Period M]). Month grid regular per fund; flag column ∈ {observed, imputed, stale_fixed}. Idempotent rebuild verified (byte-identical outputs across runs).
