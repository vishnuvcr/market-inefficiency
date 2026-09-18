# Research Status

Last updated: 2026-09-18

## Overall phase

**Phase 4 — Preregistered option-market hypothesis testing**

Status: **PHASE 4A — NIFTY OPTIDX DATA ACQUISITION / VALIDATION: HISTORICAL BUILD ACTIVE**

Phase 3 real-data discovery is complete as a descriptive layer. Phase 4 is now building the point-in-time option dataset required for falsifiable VRP, jump-risk and surface-shape tests.

## Phase tracker

| Phase | Status | Completion | Current gate |
|---|---|---:|---|
| 0. Governance & infrastructure | 🟢 Complete | 100% | Protocol and CI scaffolding |
| 1. Literature/source validation | 🟢 Complete | 100% | Exit gate passed |
| 2. Data engineering | 🟢 Core snapshot validated | 85% | Derivatives source acceptance |
| 3. Stylized facts/discovery | 🟢 Real-data discovery complete | 100% | Findings frozen as descriptive evidence |
| 4. Option-market hypotheses | 🟡 In progress | 25% | Historical NIFTY OPTIDX snapshot |
| 5. Multimodal regime model | ⚪ Not started | 0% | Leakage-safe option/underlying regime dataset |
| 6. Portfolio/execution | ⚪ Not started | 0% | Net-of-cost simulator |
| 7. Statistical validation | ⚪ Not started | 0% | CPCV + DSR + PBO |
| 8. Paper trading | ⚪ Not started | 0% | Post-validation only |
| 9. Ongoing governance | ⚪ Not started | 0% | Drift/revalidation automation |

## Validated Phase 3 snapshot

The Kaggle snapshot is immutable and hashed. The clean NIFTY baseline contains **2,799 daily bars / 2,798 return observations**, ending 2026-05-14 after excluding the incomplete 2026-05-15 session.

Phase 3 findings remain diagnostic only. None is treated as proof of exploitable inefficiency.

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

The NSE runner has validated access to both the public historical contract-wise interface and the daily UDiFF archive route. A 2026-05-14 UDiFF archive returned HTTP 200 and contained 1,950 NIFTY option rows in the probe.

The fixed-contract probe returned zero rows for its particular test parameters. This is treated only as a contract-query result, not as evidence that NIFTY option data is unavailable. The daily archive is therefore the primary acquisition route.

Implemented:
- `scripts/probe_nse_fno_historical.py`
- `scripts/probe_nse_option_surface.py`
- `scripts/probe_nse_udiff_bhavcopy.py`
- `scripts/probe_nse_archive_boundary.py`
- `scripts/acquire_nse_nifty_optidx.py`
- `.github/workflows/acquire-nifty-optidx.yml`

The acquisition layer preserves original ZIP files, validates schemas, extracts NIFTY CE/PE rows, normalizes common fields, records SHA-256 hashes and creates an immutable snapshot manifest. Legacy and UDiFF formats are explicitly handled separately rather than silently assumed identical.

The bounded pilot for **2026-05-01 through 2026-05-14 has passed**. It produced 17,482 normalized NIFTY CE/PE rows across 9 trading days with no duplicate contract keys or hard schema-quality failures. The historical build is now partitioned by calendar year to keep artifacts reproducible and bounded. The first historical run exposed a legacy-route URL construction defect: the URL builder uppercased the complete base URL while preserving the file prefix. This has been corrected to construct the legacy NSE path with exact path casing. The 2020 partition is scoped from 2020-04-13, matching the currently validated public archive coverage boundary used for this acquisition build.

## Immediate next gates

1. Rerun and complete the corrected 2020–2026 historical partitions.
2. Reconcile validated days, no-archive days and daily NIFTY contract counts.
3. Validate the legacy/UDiFF historical boundary and freeze the normalized option-EOD snapshot.
4. Add point-in-time lot-size and risk-free inputs.
5. Begin Phase 4B implied-volatility/surface reconstruction.
