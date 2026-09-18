# Research Status

Last updated: 2026-09-18

## Overall phase

**Phase 3 — Stylized facts and inefficiency discovery**

Status: **SCAFFOLD IMPLEMENTED; REAL-DATA GATE OPEN**

Overall Phase 2 completion: **~55%**  
Phase 3.1–3.4 implementation: **complete as deterministic diagnostic scaffolds; 0% real-market evidence until the validated Kaggle snapshot is acquired.**

## Phase tracker

| Phase | Status | Completion | Current gate |
|---|---|---:|---|
| 0. Governance & infrastructure | 🟢 Complete | 100% | Passed CI |
| 1. Literature/source validation | 🟢 Complete | 100% | Exit gate passed |
| 2. Data engineering | 🟡 In progress | 55% | Real Kaggle snapshot + derivatives source acceptance |
| 3. Stylized facts | 🟡 Scaffold implemented | 40% | Run Phase 3.1–3.4 against validated NIFTY/VIX snapshot |
| 4. Single-hypothesis research | ⚪ Not started | 0% | Independent Track A–D experiments |
| 5. Multimodal regime model | ⚪ Not started | 0% | Leakage-safe regime dataset |
| 6. Portfolio/execution | ⚪ Not started | 0% | Net-of-cost simulator |
| 7. Statistical validation | ⚪ Not started | 0% | CPCV + DSR + PBO |
| 8. Paper trading | ⚪ Not started | 0% | Post-validation only |
| 9. Ongoing governance | ⚪ Not started | 0% | Drift/revalidation automation |

## Phase 3.1 implementation

Added scripts/phase3_stylized_facts.py and its deterministic test.

The baseline reports:
- observation coverage and chronology
- simple and log return dispersion
- skewness and excess kurtosis
- absolute-return autocorrelation at lags 1 and 5
- close-price maximum drawdown

The module is explicitly diagnostic-only. It does not fit a trading strategy and does not authorize execution backtesting.

## Phase 3.2 implementation

Added `scripts/phase3_realized_volatility.py` and its deterministic CI test. The diagnostic compares close-to-close, Parkinson, Garman–Klass and Yang–Zhang variance/volatility estimators, with explicit annualization-period control and OHLC consistency checks. It remains descriptive-only and does not authorize strategy or execution backtesting.

## Data evidence boundary

The selected Kaggle source is debashis74017/nifty-50-minute-data, described by its publisher as NIFTY 50 index OHLC minute/daily data with India VIX available in the dataset. Kaggle discussion material also states that F&O intraday data are not provided there and that bid/ask data require a separate data source. These observations reinforce the repository's existing boundary: Kaggle can support underlying/context diagnostics, but cannot satisfy the option quote/depth execution-data requirement. citeturn0search0turn0search1

No real-market statistic is reported yet because the exact external snapshot bytes have not been acquired and hashed in the research runtime.

## Phase 3.3 implementation

Added `scripts/phase3_volatility_persistence.py` and its deterministic CI test. The diagnostic reports return/absolute-return/squared-return ACFs, Durbin–Levinson PACF, rolling volatility summaries, clustering indicators, and an explicit IID reference interval. The uncertainty interval is labelled as a benchmark rather than a robust time-series confidence interval. The module remains descriptive-only.

## Phase 3.4 implementation

Added `scripts/phase3_jump_diagnostics.py` and its deterministic CI test. The diagnostic provides a robust standardized-return jump proxy, a bipower-variation-style excess-variation proxy, and a Parkinson range-based excess-variation proxy. A dedicated six-observation fixture now keeps the jump test independent of the five-row baseline fixture. The implementation remains descriptive-only; a jump proxy is not evidence of tradable mispricing.

## Phase 3 roadmap

1. 3.1 Stylized-fact baseline — scaffold complete.
2. 3.2 Realized volatility — close-to-close, Parkinson, Garman–Klass and Yang–Zhang comparison where fields support them.
3. 3.3 Volatility persistence — ACF/PACF, rolling volatility, clustering diagnostics and explicit uncertainty benchmark.
4. 3.4 Jump diagnostics — multiple jump estimators and sensitivity to sampling frequency. Scaffold complete; real-data and frequency-sensitivity validation pending.
5. 3.5 Memory/dependence — Hurst/MFDFA plus estimator uncertainty and surrogate/random-walk controls.
6. 3.6 Regime segmentation — descriptive, non-predictive segmentation before HMM/GMM.
7. 3.7 Discovery report — translate only robust, pre-specified findings into Phase 4 hypotheses.

## Mandatory guardrail

Phase 3 findings are descriptive evidence only. No apparent pattern will be labelled an exploitable inefficiency until it passes the Phase 4+ lifecycle.

## Immediate next tasks

1. Acquire/hash the exact Kaggle snapshot.
2. Normalize NIFTY and India VIX with the existing adapter.
3. Run quality/exclusion diagnostics and snapshot-manifest generation.
4. Execute Phase 3.1 on the validated real snapshot.
5. Execute Phase 3.2–3.4 on the validated real snapshot after explicit sessionization/sampling choices are fixed.
6. Implement Phase 3.5 memory/dependence diagnostics with estimator and surrogate controls.
7. In parallel, continue validation of historical option EOD/quote data for Tracks A–C/G.
