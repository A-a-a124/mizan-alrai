# SRE — waqf-flow-forecast
Runbook: data refresh = re-capture snapshots via browser (portal WAF blocks scripts), update _checksums.json, rerun the three scripts, check tests. Failure modes: IntegrityError (snapshot edited) → restore from git; PDF not produced → script retries 3× and fails loudly; matplotlib < 3.11 → Arabic shaping breaks (pin in requirements).
