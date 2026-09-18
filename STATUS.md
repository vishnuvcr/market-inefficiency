# Research Status

Last updated: 2026-09-18

## Overall phase

**Phase 4 — Preregistered option-market hypothesis testing**

Status: **PHASE 4A — NIFTY OPTIDX ACQUISITION + RECONCILIATION PASSED; PIT INPUT AUDIT BLOCKED PENDING EXTERNAL INPUTS**

Phase 3 real-data discovery is complete as a descriptive layer. Phase 4 is now building the point-in-time option dataset required for falsifiable VRP, jump-risk and surface-shape tests.

## Phase tracker

| Phase | Status | Completion | Current gate |
|---|---|---:|---|
| 0. Governance & infrastructure | 🟢 Complete | 100% | Protocol and CI scaffolding |
| 1. Literature/source validation | 🟢 Complete | 100% | Exit gate passed |
| 2. Data engineering | 🟢 Core snapshot validated | 85% | Derivatives source acceptance |
| 3. Stylized facts/discovery | 🟢 Real-data discovery complete | 100% | Findings frozen as descriptive evidence |
| 4. Option-market hypotheses | 🟡 In progress | 40% | Phase 4A PIT audit |
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

The bounded pilot for **2026-05-01 through 2026-05-14 has passed**. It produced 17,482 normalized NIFTY CE/PE rows across 9 trading days with no duplicate contract keys or hard schema-quality failures. Run #17 completed successfully for all seven yearly partitions (2020–2026). It produced 1,511 validated archive days and 2,859,228 normalized NIFTY CE/PE rows across the immutable yearly artifacts. The historical build is partitioned by calendar year to keep artifacts reproducible and bounded. The first historical runs exposed a legacy-source acquisition problem after the URL casing correction: acquisition could complete without producing normalized files because source-level outcomes were not sufficiently visible. The downloader now records per-source HTTP/error diagnostics, performs ZIP integrity checks, uses clean headers for the secondary mirror, and fails explicitly on ERROR days or zero validated days. The workflow now runs a real one-session legacy smoke test (2020-04-13) before allowing 2020–2024 partitions to start; 2025–2026 remain independently eligible. The 2020 partition is scoped from 2020-04-13, matching the currently validated public archive coverage boundary used for this acquisition build. The legacy CSV does not contain the `LTP` column. This is treated as a schema limitation: `last_price` remains NA rather than substituting `CLOSE`. The raw ZIP is still preserved and the normalized record exposes provenance.

## Phase 4A — cross-year reconciliation / PIT audit

The acquisition workflow now has a dedicated reconciliation script and workflow. The reconciler checks year coverage, manifest/file agreement, cross-year duplicate contract keys, route/date-boundary consistency, normalized schema errors, expiry/strike integrity, source-tier provenance, legacy-vs-UDiFF missingness, calendar-gap diagnostics, and the required `available_at` PIT field.

The reconciliation workflow was added to the research branch and the protocol PR was merged into `main` so the workflow is eligible for GitHub's `workflow_run` event. It also now runs on research-branch updates and automatically selects the latest successful acquisition run when no explicit run ID is supplied, avoiding another market-data download.

Full reconciliation Run #3 (GitHub Actions run `35374383806`, commit `2d2a684f2d7498cbbfefbe406a6fb06e00dc6e6f`) completed successfully against immutable Acquisition Run #17 (`35355477098`). The reconciliation report passed all hard gates: 7/7 year manifests present, 1,511 validated archive days, 1,511 normalized files/dates, 2,859,228 normalized rows, zero duplicate contract keys, zero file errors, zero route errors, zero missing/unexpected normalized dates, zero negative prices, zero expiry-before-trade rows, zero non-positive strikes, zero missing `available_at` rows, and zero `available_at)-before-trade rows. The report also records 85 weekday no-archive dates. Calendar audit work now classifies these explicitly; 2021-03-30 is a documented trading-day archive gap rather than a holiday and remains a coverage gap requiring exclusion or separate sourcing.

The previous Run #2 failure was a timezone-comparison implementation error rather than a data-quality failure: `available_at` was timezone-aware while `trade_date` was timezone-naive. The reconciler now compares their calendar dates for the current PIT gate.

A local spot validation of the downloaded 2020–2023 artifacts found:
- 1,902,031 normalized rows across 924 files;
- zero missing `available_at` values;
- zero `available_at` timestamps before trade date;
- zero duplicate contract keys;
- zero negative-price rows;
- zero expiry-before-trade rows;
- zero non-positive strikes.

These are partial checks only; they do **not** replace the full 2020–2026 GitHub reconciliation.

Weekday no-archive dates are reported rather than automatically failed because authoritative NSE holiday/calendar reconciliation is still required. The PIT audit will review the conservative EOD `available_at` assumption before any forward-looking hypothesis test.

## PIT input audit

`docs/PHASE4A_PIT_AUDIT.md` and `data/phase4a/pit_input_registry.csv` now freeze the remaining PIT requirements. The structural EOD reconciliation is passed, but the formal IV/VRP dataset is not yet frozen because legacy underlying values and historical contract-level lot sizes require independent PIT sources, and the risk-free interpolation/availability rule is not yet frozen. NSE documents EOD generation once per trading day, which supports an EOD convention but does not establish an exact publication timestamp. UDiFF contains `UndrlygPric` and `NewBrdLotQty`; legacy rows preserve these fields as NA rather than inferred substitutions. citeturn0search0turn0search2

Official NSE lot-size provenance now covers the main NIFTY transitions: 75 to 50 for July 2021 contracts, 50 retained in 2023, 50 to 25 from April 26, 2024 contracts, 25 to 75 for new contracts introduced from November 20, 2024, and the subsequent 75 to 65 transition beginning with revised 2026 expiries under the October 2025 circular. The 2025 rule is explicitly contract-cycle dependent: weekly/monthly existing contracts retain 75 through the December 30, 2025 expiry, while the first revised weekly/monthly expiries are January 6/27, 2026; existing quarterly/half-yearly contracts revise EOD December 30, 2025. Contract-level transition rules mean lot size must be joined by contract/expiry, not merely by trade date. citeturn5search4turn6search15turn4view0 citeturn3search43turn3search42turn4search0turn3search45

RBI documents 91-day Treasury Bills as short-term Government instruments and publishes auction cut-off yields. These are a candidate risk-free source, but publication timing and the interpolation/carry-forward rule must be frozen before use in a PIT feature. citeturn5search3turn5search0

## Immediate next gates

1. Acquire/validate a contract-level historical NIFTY lot-size master covering all included expiries.
2. Acquire/validate a PIT underlying/index close series for legacy option rows before 2024-07-08.
3. Freeze a PIT risk-free curve source and availability/interpolation rule.
4. Convert the 2021-03-30 trading-day archive gap into an explicit exclusion mask unless independently sourced.
5. Freeze the normalized option-EOD research snapshot and included-contract/date manifest.
6. Begin Phase 4B implied-volatility/surface reconstruction only after the PIT input gate passes.
