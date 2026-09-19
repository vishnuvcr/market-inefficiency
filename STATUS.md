# Research Status

Last updated: 2026-09-19

## Overall phase

**Phase 11 — strategy library implemented; execution-data gate remains open**

Status: **PHASE 10 SOFTWARE-READY; PHASE 11 LIBRARY IMPLEMENTED; NO EXECUTABLE STRATEGY PROMOTED**

The research has now returned to the broader market-inefficiency objective. Direct next-day direction prediction did not survive the Phase 5 holdout, while 5-session volatility-expansion prediction showed materially stronger out-of-sample information. A fixed inverse-direction candidate briefly produced a positive final 10% settlement-based result at low assumed costs, but Phase 7 CPCV showed that effect is not stable in the development history.

## Phase tracker

| Phase | Status | Completion | Current gate |
|---|---|---:|---|
| 0. Governance & infrastructure | 🟢 Complete | 100% | Protocol and CI scaffolding |
| 1. Literature/source validation | 🟢 Complete | 100% | Exit gate passed |
| 2. Data engineering | 🟢 Core snapshot validated | 85% | Derivatives source acceptance |
| 3. Stylized facts/discovery | 🟢 Real-data discovery complete | 100% | Findings frozen as descriptive evidence |
| 4. Option-market hypotheses | 🟢 Formal PIT/IV + VRP + H-A2/H-B1/H-C1 gates passed | 85% | Economic/execution validation and multiplicity controls |
| 5. Multimodal prediction | 🟢 Completed | 100% | Direct direction rejected; volatility-expansion signal retained for further study |
| 6. Strategy translation | 🟡 Candidate screen completed | 60% | Translate volatility-state prediction into independently validated strategy families |
| 7. Statistical validation | 🟢 Current candidate stress-tested | 100% | Inverse-direction candidate rejected; CPCV/PBO/DSR diagnostics complete |
| 8. Fresh-forward + execution validation | 🟢 Fresh-forward research tests completed | 100% | No strategy promoted; Phase 8 exit conclusion recorded |
| 9A. Surface-relative-value execution validation | 🟡 Protocol defined | 10% | Historical bid/ask/order-trade acquisition and executable-price reconstruction |
| 9B. Frozen surface-signal settlement-proxy | 🟡 Completed / rejected | 70% | Direct 10Δ/50Δ skew vertical failed fresh-forward settlement-proxy gate; keep only as reproducible paper-monitoring rule |
| 10. Historical execution-data layer | 🟡 Software-ready / data-blocked | 40% | Licensed historical order/trade/quote data required for executable fills |
| 11. Surface strategy library | 🟡 Implemented / mechanically validated | 60% | Broad leg/exposure library ready; no strategy selection before execution data |
| 12. Execution simulator / quote audit | 🟡 Mechanically passed / economic data blocked | 70% | Public NIFTY top-of-book/L2 sample validates execution mechanics; bulk historical archive still required |
| 9. Ongoing governance | ⚪ Not started | 0% | Drift/revalidation automation |

## Phase 9A — execution-grade surface-relative-value validation

The Phase 8 conclusion is now frozen: no NIFTY strategy is promoted; the strongest surviving predictive signal is volatility-surface shape dynamics, especially 30D downside skew. Phase 9A converts that predictive signal into a broad, pre-registered strategy library without selecting a winner from realized P&L.

Protocol: `docs/PHASE9A_EXECUTION_PROTOCOL.md`.

The next hard gate is historical execution data. EOD settlement/IV data will not be treated as historical bid/ask data. The execution layer requires timestamped quotes and/or order/trade observations, leg synchronization, fill reconstruction, margin inputs and realistic transaction-cost modelling. No bid/ask history will be fabricated from OHLC or settlement.

The candidate library includes delta-matched skew verticals, risk reversals, butterflies, skew butterflies, calendars, four-leg surface structures, iron condors and straddle/strangle structures where their surface exposures can be explicitly mapped. Trade direction is determined from the frozen predicted surface move before realized P&L is observed.

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

## Phase 4A — official NIFTY 50 underlying gate

The official NSE NIFTY 50 underlying acquisition is now passed. Acquisition Run #22 produced the immutable artifact for **2020-04-13 through 2026-05-14** with **1,511 daily rows**, exact requested date bounds, no duplicate dates, positive closes, preserved raw JSON chunks, and a manifest hash. The implementation uses the official NSE historical-index endpoint with 60-calendar-day chunks to avoid silent response-size truncation.

## Phase 4A — cross-year reconciliation / PIT audit

The acquisition workflow now has a dedicated reconciliation script and workflow. The reconciler checks year coverage, manifest/file agreement, cross-year duplicate contract keys, route/date-boundary consistency, normalized schema errors, expiry/strike integrity, source-tier provenance, legacy-vs-UDiFF missingness, calendar-gap diagnostics, and the required `available_at` PIT field.

The reconciliation workflow is now on `research/v1.0-protocol` and is triggered both by research-branch updates and successful acquisition runs. It also now runs on research-branch updates and automatically selects the latest successful acquisition run when no explicit run ID is supplied, avoiding another market-data download.

Full reconciliation Run #12 (GitHub Actions run `35388053480`, commit `a9b29862105d6c9d61e7459226728d7364bc268b`) completed successfully against immutable Acquisition Run #17 (`35355477098`). The reconciliation report passed all hard gates: 7/7 year manifests present, 1,511 validated archive days, 1,511 normalized files/dates, 2,859,228 normalized rows, zero duplicate contract keys, zero file errors, zero route errors, zero missing/unexpected normalized dates, zero negative prices, zero expiry-before-trade rows, zero non-positive strikes, zero missing `available_at` rows, and zero `available_at)-before-trade rows. The report also records 85 weekday no-archive dates. Calendar audit work now classifies these explicitly; 2021-03-30 is a documented trading-day archive gap rather than a holiday and remains a coverage gap requiring exclusion or separate sourcing.

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

Official NSE lot-size provenance now covers the main NIFTY transitions: 75 to 50 for the 2021 contract cycles, 50 retained in 2023, 50 to 25 from April 26, 2024 contracts, 25 to 75 for new contracts introduced from November 20, 2024, and the subsequent 75 to 65 transition under the October 2025 circular. The 2025 rule is explicitly contract-cycle dependent: the last existing-lot weekly expiry is December 23, 2025; the last existing-lot monthly expiry is December 30, 2025; first revised weekly/monthly expiries are January 6/27, 2026; existing quarterly/half-yearly contracts revise EOD December 30, 2025. The reconciliation workflow now materializes **73,611 contract-lot intervals from 2,859,228 observations across 1,511 normalized files**, with zero duplicate contract/effective-from keys and PIT source availability before the mapped observation dates.

The Phase 4A PIT freeze has now passed. The immutable snapshot contains **2,857,735 PIT-join-passing option rows**; **1,493 rows on 2024-03-02** are explicitly excluded because NSE ran a special Saturday disaster-recovery session that the official NIFTY historical-index endpoint did not return. The earlier 2021-03-30 archive gap remains explicitly excluded. No underlying, lot-master, risk-free, or expiry-invalid rows remain in the included PIT sample. Contract-level transition rules mean lot size must be joined by contract/expiry, not merely by trade date. citeturn5search4turn6search15turn4view0 citeturn3search43turn3search42turn4search0turn3search45

RBI WSS/DBIE provides 91-day, 182-day and 364-day Treasury-bill primary auction yields. The source remains a candidate until the acquisition preserves publication/availability evidence and the interpolation/carry-forward rule is frozen for PIT use. citeturn5search3turn5search0


## Phase 4A — external PIT input layer implemented

The remaining external-input gate is now operationally specified without inventing missing market data:

- `data/phase4a/pit_external_source_registry.csv` records the authoritative source, period, PIT availability rule and current status for the legacy NIFTY index, lot-size mapping and RBI risk-free inputs.
- `docs/PHASE4A_EXTERNAL_INPUTS.md` freezes the acquisition/validation requirements, including publication-time handling and risk-free interpolation rules.
- `scripts/validate_phase4a_external_inputs.py` provides deterministic schema, coverage, duplicate and positivity checks and records SHA-256 hashes for the three external inputs.
- The validator deliberately does **not** infer, backfill or silently download data; the final PIT snapshot must be based on auditable source files.

This engineering layer was subsequently completed by the immutable external-input acquisition, PIT join, and Phase 4A snapshot freeze. Phase 4B is therefore no longer blocked by the external-input gate.

## Phase 4B — IV reconstruction PASSED

GitHub Actions run **#9** (`35393747845`) completed successfully.

Reconstruction used NSE EOD settlement prices, PIT NIFTY 50 close, PIT RBI 91/182/364-day simple yields with linear interpolation, ACT/365, and median same-day put-call-parity forwards from paired CE/PE strikes with strike/spot moneyness in **0.80–1.20**. IV was bounded to **(1e-6, 5.0]** and the documented gap dates remained excluded.

Validation results:
- **2,859,228** input option rows.
- **2,641,708** valid IV rows.
- **28,883** daily expiry surfaces.
- **1,510** unique option-observation dates.
- **349** unique expiries.
- **0** duplicate trade-date/expiry surface keys.
- ATM IV range **4.01%–71.86%**, median **16.88%**.
- Median parity-pair count **12**.
- Explicit gap exclusions remain **2021-03-30** and **2024-03-02**.

The corrected yearly IV partitions were uploaded as an immutable Phase 4B artifact.

## Phase 4C — variance-risk-premium diagnostic PASSED

GitHub Actions run **#7** (`35394486561`) completed successfully.

The diagnostic constructs constant-maturity ATM implied variance by linear interpolation in total variance and compares it with subsequent NIFTY realized variance over the matched calendar horizon. The regime variable is a 20-session trailing realized-volatility measure using only information available through the trade date.

### 30-calendar-day horizon
- **n = 1,489** matched observations.
- Mean implied-minus-realized variance: **0.01614**.
- Newey-West SE: **0.00305**; 95% CI **0.01016 to 0.02213**.
- HAC t-statistic: **5.29**.
- Positive variance premium in **81.5%** of observations.
- Mean implied-minus-realized volatility: **4.28 percentage points**; 95% CI **3.18–5.37 pp**.
- Mean variance premium by prior-volatility regime: **0.00820 LOW**, **0.01019 MID**, **0.02159 HIGH**.

### 60-calendar-day horizon
- **n = 1,471** matched observations.
- Mean implied-minus-realized variance: **0.01867**.
- Newey-West SE: **0.00478**; 95% CI **0.00930 to 0.02805**.
- HAC t-statistic: **3.90**.
- Positive variance premium in **80.8%** of observations.
- Mean implied-minus-realized volatility: **4.60 percentage points**; 95% CI **2.93–6.27 pp**.
- Mean variance premium by prior-volatility regime: **0.00868 LOW**, **0.00998 MID**, **0.02632 HIGH**.

### Usable research conclusion

Within the current **2020-04-13 to 2026-05-14** PIT sample, the first formal diagnostic supports a **persistent positive variance risk premium**: option-implied variance was, on average, above subsequently realized NIFTY variance at both 30- and 60-calendar-day horizons. The diagnostic also shows larger average variance premia in the pre-existing high-volatility regime.

This is **not yet evidence of a tradable strategy**. The estimate uses overlapping future-return outcomes, settlement-based option IVs, and a descriptive regime split. Next-stage work must test economic costs, leverage/risk limits, state-transition robustness, surface-shape effects, cross-validation/holdout performance, and multiple-testing controls (CPCV/DSR/PBO) before any strategy-level conclusion.

## Phase 4D — formal H-A2/H-B1/H-C1 diagnostics PASSED

GitHub Actions run **#6** (35395984072), job 105764794682, completed successfully on the frozen Phase 4B IV artifact and official NIFTY underlying. Artifact **10567498551** has digest sha256:e574406bb2a47dd54d4f5c8c192c9a333c8ad14cb1020f615c5bade1eacd181c.

The test uses a chronological 80/20 split with all regime cut points, standardization constants and calibration coefficients estimated from the first 80% only.

### H-A2 — state dependence
- 30D holdout VRP means: LOW **0.00742**, MID **-0.01382**, HIGH **-0.00348**.
- 30D MID−LOW = **-0.02125**, HAC SE **0.00742**, p **0.00419**; this is the only one of the four preregistered state contrasts surviving Bonferroni alpha **0.0125**.
- 30D HIGH−LOW p **0.12249**.
- 60D MID−LOW = **-0.01231**, p **0.03527**; it does not survive Bonferroni.
- 60D HIGH−LOW p **0.91656**.

The high-volatility state therefore does **not** show a robust monotonic increase in VRP in the untouched holdout. The state pattern is non-monotonic and horizon-sensitive.

### H-B1 — jump-risk
- Holdout residual mean **-0.000696**, HAC SE **0.001212**, 95% CI **[-0.003071, 0.001680]**, p **0.566**.
- OOS RMSE with downside-wing tail proxy **0.007189** versus **0.007170** for controls only.

The tested downside-wing proxy adds no incremental holdout information about subsequent jump variance in this specification.

### H-C1 — surface shape
- 30D downside skew: OOS R² **0.3645**, holdout coefficient p **9.71×10⁻⁷**.
- 30D upside skew: OOS R² **0.1095**, p **0.00296**.
- 30D–60D ATM term slope: OOS R² **0.0205**, p **0.07768**.
- Bonferroni alpha for the three surface-feature coefficient checks: **0.0167**; downside and upside skew survive, term slope does not.

### Usable Phase 4 conclusion

The Phase 4D holdout materially refines the research direction. **Aggregate VRP remains supported, but the previously observed high-volatility-state effect is not robust after a frozen chronological holdout and multiplicity correction. The tested jump-risk proxy adds no incremental predictive evidence. Surface shape—especially downside and upside skew—shows the strongest surviving out-of-sample signal, predicting later changes in the option surface itself.** This is not yet evidence of a profitable trading strategy because the target is surface evolution rather than executable returns.

Detailed reproducible results are recorded in docs/PHASE4D_RESULTS.md.

## Phase 5 — broad market prediction

The multimodal model used price, volatility, memory and the frozen option surface. On the untouched 20% holdout, next-day direction AUC was **0.4584**, accuracy **48.2%**, and 5-session return OOS R² **-0.1038**. In contrast, 5-session volatility expansion had AUC **0.6879** and accuracy **61.1%**. This is the most useful broad-prediction result so far.

## Phase 6 — strategy translation

A fixed six-rule family was screened with an 80/10/10 chronology. The validation-selected inverse-direction rule was positive on the final 10% at 5 bps/side (Sharpe **0.417**) and 10 bps/side (Sharpe **0.129**) but negative at 20 bps/side (Sharpe **-0.437**). These are settlement-to-settlement proxies, not observed fills.

## Phase 7 — current usable conclusion

CPCV over the first 90% produced **28 paths**. For the frozen inverse-direction candidate at 10 bps/side, median Sharpe was **-0.419** and only **28.6%** of paths were positive. The six-candidate CSCV-style PBO proxy was **0.464**. The approximate DSR diagnostic was effectively zero (**7.49e-62**). The current directional candidate is therefore **rejected for promotion**.

The research direction is now clear: do not spend further effort optimizing this inverse-direction strategy. The next independent branch should exploit the stronger **volatility-expansion prediction** and test strategy families conditionally on predicted volatility state. Option-surface skew remains a parallel predictive branch, but executable options claims still require quote/order-trade data.

See docs/PHASE5_RESULTS.md, docs/PHASE6_RESULTS.md, and docs/PHASE7_RESULTS.md.


## Phase 8 — fresh-forward validation

The frozen Phase 5 multimodal specification was tested on a genuinely later period, **2026-05-15 through 2026-09-17**, with fresh NIFTY underlying and fresh option-surface data. Development contained 1,449 observations through 2026-05-14; the fresh forward evaluation contained 87 observations.

Fresh-forward five-session volatility-expansion AUC was **0.5744**. None of the six preregistered volatility-conditioned NIFTY strategy families passed the 20-bps promotion gate. At 20 bps, forward Sharpe values ranged from **-3.08 to +0.16**, and every development CPCV median Sharpe was negative.

Phase 8B independently tested the same idea using only price/volatility features. It also failed promotion, confirming that the stronger historical multimodal result does not generalize as a generic underlying-only effect.

## Phase 8C — volatility-surface dynamics CPCV

A 28-path CPCV with a 30-calendar-day purge and 5-day embargo strengthened the H-C1 surface-dynamics finding:

- 30D downside skew: median OOS R² **0.3166**, positive on **100%** of paths.
- 30D upside skew: median OOS R² **0.1068**, positive on **89.3%** of paths.
- 30–60D term slope: median OOS R² **0.1543**, positive on **96.4%** of paths.

These are predictive diagnostics for future surface evolution, not executable option-strategy returns.

## Current research decision

**No current NIFTY strategy is promoted to paper trading.**

The direct-direction and volatility-state directional strategies have failed robustness/fresh-forward promotion gates. The reproducible remaining signal is the **option-volatility surface**, especially 30D downside skew. The next scientific gate is execution-grade surface-relative-value testing using historical bid/ask, order/trade timing, depth, leg synchronization, margin and realistic transaction costs.

Detailed Phase 8 results: docs/PHASE8_RESULTS.md.


## Phase 9B — frozen surface-signal settlement-proxy

Phase 9B is complete. GitHub Actions run 35442399330 passed all acquisition, reconstruction, execution of the research script, validation and artifact-upload steps.

Fresh-forward coverage is 2026-05-15 through 2026-09-18 with 135,243 valid IV observations and 88 validated option sessions. The leakage-controlled expanding Ridge forecast continued to predict the subsequent 30D downside-skew change out of sample: forward R² 0.3029 and correlation 0.5695.

The direct mechanism-first strategy was a same-expiry approximately 10-delta/50-delta put vertical, entry 45–75 days to expiry, 30-calendar-day hold, one entry delta hedge, no overlapping positions, and EOD settlement proxy pricing.

Fresh-forward result: 4 non-overlapping trades; −₹14,828 total settlement-proxy P&L; 25% win rate; approximate event annualized Sharpe −0.87; mean P&L / entry-risk proxy −7.9%.

Therefore the direct strategy is rejected for paper-trading promotion.

The reverse-direction result is retained only as a negative control. It happened to be positive on the same four forward trades, but selecting it now would be post-hoc selection. A one-day delay and random-entry controls also produced unstable results, reinforcing that the four-trade forward sample cannot be used to tune the strategy.

Detailed reproducible results are in docs/PHASE9B_RESULTS.md.

Usable current conclusion: the option-surface predictor remains informative about future surface shape, but Phase 9B did not establish a profitable settlement-proxy trading strategy. The reproducible rule can be used for paper monitoring only, not capital deployment. Execution-grade validation still requires historical bid/ask/order-trade data, executable multi-leg reconstruction, realistic costs and an untouched validation gate.


## Phase 10 — historical execution-data layer

The execution-data parser and protocol are now implemented and validated in CI. The parser supports the documented current FAO trim layouts and historically relevant full-layout lengths, with exact jiffy conversion and deterministic normalization. The critical external gate remains: the repository does not contain licensed historical F&O order/trade/quote files, so executable P&L cannot yet be measured.

Detailed protocol/results: docs/PHASE10_EXECUTION_DATA_PROTOCOL.md and docs/PHASE10_RESULTS.md.

## Phase 11 — surface strategy library

A broad strategy/exposure library is implemented for skew verticals, risk reversals, butterflies, iron condors and reserved additional surface structures. It computes deterministic theoretical exposure diagnostics and terminal payoffs only. It does not rank structures or use theoretical prices as historical fills.

Detailed design: docs/PHASE11_EXECUTION_LIBRARY.md.


## Phase 12 — execution simulator and quote audit

A public NIFTY option top-of-book/L2 sample from the TickBytes repository was acquired and added only as a test fixture. It contains timestamped best bid/ask, quantities and five visible depth levels. The simulator now rejects missing/zero-size/non-finite/crossed quotes, executes buys at contemporaneous ask and sells at contemporaneous bid, rejects insufficient displayed size, and requires synchronized multi-leg timestamps in the sample mode.

CI run 35448534215 passed all Phase 10–12 unit tests and the quote audit.

This does **not** unlock a historical economic backtest. The public sample is representative data, not a multi-month licensed archive. Official NSE historical F&O order/trade data remain the required source for full execution-grade reconstruction. Therefore no executable trading strategy has been promoted.

The current strongest reproducible rule remains the frozen Phase 9B surface-monitoring specification, but its fresh settlement-proxy P&L was negative and it is not validated for capital trading.
