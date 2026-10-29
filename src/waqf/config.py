"""Single source of truth for paths and analysis parameters."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data_raw"
DATA_CLEAN = ROOT / "data_clean"
FIGURES = ROOT / "outputs" / "figures"
TABLES = ROOT / "outputs" / "tables"
DASHBOARD = ROOT / "dashboard"

GASA_SNAPSHOT = DATA_RAW / "gasa" / "gasa_open_data_snapshot.json"
FUND_UNIVERSE = DATA_RAW / "tadawul" / "waqf_funds_universe.csv"
FUND_PRICES = DATA_RAW / "tadawul" / "waqf_funds_month_end_prices.csv"
FUND_CHECKSUMS = DATA_RAW / "tadawul" / "_checksums.json"

SEED = 2026

# Fund cleaning
PAR_PRICES = (1.0, 10.0)          # launch prices; repeated par values before first move = not yet invested
MIN_FUND_MONTHS = 12              # shorter histories are excluded from the composite
MAX_IMPUTE_GAP_MONTHS = 3         # quarterly reporting gaps are log-linearly interpolated (flagged)
ACCUMULATING_TYPES = ("Growth",)  # price return ~ total return only for non-distributing funds

# Forecast / backtest
HORIZON_MONTHS = 12
MIN_TRAIN_MONTHS = 36

# Risk / spending
N_PATHS = 10_000
SIM_YEARS = 10
BLOCK_MEAN = 6                    # stationary bootstrap mean block length (months)
INFLATION = 0.02                  # annual CPI assumption (parameter, adjustable in dashboard)
STRESS_SHIFT = -0.01              # annual return haircut for the survivorship stress test
SPEND_RATES = tuple(round(0.005 * i, 3) for i in range(0, 17))  # 0% .. 8%
SMOOTHING_QUARTERS = 12
CONFIDENCE = 0.60                 # default P(real principal preserved) the nazir requires

# Allocation (shares of the annual distributable budget)
UPKEEP_SHARE = 0.10               # عمارة الوقف — maintenance precedes distribution
RESERVE_TARGET_YEARS = 1.0        # stability reserve target = 1 year of planned distribution
MASRAF_FLOOR = 0.02               # minimum share for any active masraf
