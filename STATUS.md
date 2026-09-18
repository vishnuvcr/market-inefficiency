# Research Status

Last updated: 2026-09-18

## Overall phase

**Phase 4 — Preregistered option-market hypothesis testing**

Status: **PHASE 4A DATA-ACCESS PROBE IN PROGRESS**

Phase 3 real-data discovery has been completed on the immutable Kaggle snapshot. Phase 4 is now converting those descriptive observations into preregistered, falsifiable option-market hypotheses.

## Phase tracker

| Phase | Status | Completion | Current gate |
|---|---|---:|---|
| 0. Governance & infrastructure | 🟢 Complete | 100% | Protocol and CI scaffolding |
| 1. Literature/source validation | 🟢 Complete | 100% | Exit gate passed |
| 2. Data engineering | 🟢 Core snapshot validated | 85% | Derivatives source acceptance |
| 3. Stylized facts/discovery | 🟢 Real-data discovery complete | 100% | Findings frozen as descriptive evidence |
| 4. Option-market hypotheses | 🟡 In progress | 10% | Phase 4A NSE OPTIDX EOD access/data-quality gate |
| 5. Multimodal regime model | ⚪ Not started | 0% | Leakage-safe option/underlying regime dataset |
| 6. Portfolio/execution | ⚪ Not started | 0% | Net-of-cost simulator |
| 7. Statistical validation | ⚪ Not started | 0% | CPCV + DSR + PBO |
| 8. Paper trading | ⚪ Not started | 0% | Post-validation only |
| 9. Ongoing governance | ⚪ Not started | 0% | Drift/revalidation automation |

## Validated Phase 3 snapshot

The Kaggle snapshot is immutable and hashed. The clean NIFTY baseline contains **2,799 daily bars / 2,798 return observations**, ending 2026-05-14 after excluding the incomplete 2026-05-15 session.

Phase 3 findings remain diagnostic only:
- return distribution is negatively skewed and fat-tailed;
- absolute-return dependence is persistent;
- realized-volatility estimators differ materially;
- jump proxies identify a small subset of unusually large moves;
- DFA Hurst and MFDFA diagnostics require estimator/surrogate controls;
- India VIX has a descriptive positive association with same-session absolute NIFTY returns;
- none of these observations is treated as proof of exploitable inefficiency.

## Phase 4 preregistration

`docs/PHASE4_PREREGISTRATION.md` freezes the initial candidate hypotheses:
- H-A1 aggregate variance-risk premium;
- H-A2 state dependence of VRP;
- H-B1 jump-risk premium;
- H-C1 surface-shape predictability;
- H-D1 regime-conditioned efficiency.

The formal lifecycle remains:

**hypothesis → PIT data snapshot → feature construction → baseline → formal test → leakage audit → cost model → CPCV → DSR/PBO → stress tests → untouched holdout → decision**

## Phase 4A — NSE option EOD data gate

Implemented:
- `scripts/probe_nse_fno_historical.py`
- `.github/workflows/probe-nse-option-eod.yml`

The probe targets NSE's public historical F&O contract-wise interface for a fixed NIFTY OPTIDX contract/date and records HTTP status, response schema, row count and sample payload without interpreting an empty response as evidence of market-data absence.

NSE's official reports page identifies the F&O UDiFF Common Bhavcopy Final as the current post-2024 daily F&O bhavcopy and states that the older F&O bhavcopy was discontinued from 2024-07-08. The official UDiFF documentation provides the standardized file format. The project will therefore test both the public contract-wise interface and the daily UDiFF route before selecting the acquisition layer.

## Immediate next gates

1. Verify the GitHub Actions NSE probe result.
2. Identify a reproducible daily F&O UDiFF download route and validate one trading day.
3. Parse NIFTY OPTIDX fields and reconcile them against the contract-wise interface.
4. Freeze the historical coverage, contract identity, price-field and missing-data rules.
5. Add point-in-time risk-free and lot-size inputs.
6. Only then begin Phase 4B IV/surface reconstruction.
