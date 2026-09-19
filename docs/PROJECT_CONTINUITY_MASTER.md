# PROJECT CONTINUITY MASTER — Market Inefficiency

**Last updated:** 2026-09-19  
**Repository:** `vishnuvcr/market-inefficiency`  
**Working branch:** `research/phase9-surface-execution`  
**Purpose:** persistent research memory so work remains scientifically and procedurally continuous across new chats.

## 0. Mandatory continuity rule

**Before performing ANY new research step, code change, data acquisition, backtest, optimization, interpretation, or decision:**

1. Read this file first.
2. Read `STATUS.md`.
3. Read `RESEARCH_PLAN.md`.
4. Read the relevant phase protocol/results file(s).
5. Inspect the current branch state and latest workflow status.
6. Continue only from the frozen state recorded here.
7. Update this continuity record after every substantive phase update, result, decision, blocker, methodology change, or user instruction.

Do **not** rely on model memory as the source of project truth.

This file is the authoritative continuity summary. Detailed phase documents and raw artifacts remain the evidence source.

## 1. What this project is trying to establish

The research objective is not to find an attractive backtest. It is to determine whether structural market inefficiencies in Indian markets:

- exist under a clearly frozen hypothesis;
- survive point-in-time data controls;
- survive leakage controls;
- survive transaction-cost and execution constraints;
- survive CPCV / PBO / DSR / multiple-testing controls;
- survive an untouched later forward period;
- and can therefore support a scientifically defensible trading strategy.

A negative result is usable. The process must not be bent toward a positive result.

## 2. Non-negotiable research methodology

The project-wide lifecycle is:

**hypothesis → preregistration → data snapshot → feature construction → fixed baseline → single-mechanism screen → fixed-cost trading proxy → leakage audit → CPCV → multiple-testing control → stress tests → untouched prospective holdout → decision**

Rules:

- Never choose signal sign after seeing P&L.
- Never optimize lookback, threshold, holding period, strike geometry, leverage or portfolio weight during discovery.
- Never reuse the rejected 2026-05-15 → 2026-09-18 forward period to tune a replacement.
- Never infer bid/ask/depth from settlement or OHLC.
- Settlement-based results must be labelled **settlement proxy**, never executable.
- Microstructure claims require genuine timestamped quotes/order/trade observations.
- Option strategies that depend on execution require contract identity, quotes/depth, synchronization, fills, lot size, margin/risk inputs and realistic costs.
- Point-in-time membership and contract-specification history are mandatory.
- Negative controls must be retained.
- A combination cannot rescue a rejected component through post-hoc sign changes.
- No candidate may proceed to optimization merely because an early screen looks attractive.
- No live/paper promotion without the appropriate validation gate.

## 3. Phase map — frozen historical state

### Phase 0 — Governance & infrastructure
**Status:** complete.

Research protocols, CI scaffolding, reproducibility rules and evidence handling established.

### Phase 1 — Literature/source validation
**Status:** complete.

Foundational theory, India-market empirical references and methodology references were validated for the current research scope. Hurst/MFDFA is a candidate feature, not a standalone inefficiency classifier; estimator uncertainty and surrogate/random-walk controls are mandatory.

### Phase 2 — Data engineering
**Status:** core snapshot/PIT controls substantially complete.

Important state:
- canonical NSE F&O EOD normalization exists;
- point-in-time contract/lot reconciliation exists;
- immutable snapshot/hash infrastructure exists;
- option-chain/EOD acquisition exists;
- licensed historical execution data remains a separate external gate.

### Phase 3 — Stylized facts / discovery
**Status:** descriptive real-data discovery completed.

These findings are diagnostic only and do not prove tradability.

### Phase 4 — Option-market hypotheses
**Status:** current preregistered option hypotheses completed at the predictive/diagnostic level.

Key evidence:
- aggregate VRP diagnostic positive at 30D and 60D;
- high-volatility state effect not robust after holdout/multiplicity controls;
- tested jump-risk proxy adds no incremental holdout information;
- surface-shape dynamics, particularly downside and upside skew, are the strongest surviving predictive diagnostics.

Important numerical results from frozen Phase 4D:
- 30D downside skew holdout OOS R² 0.3645, p 9.71e-7;
- 30D upside skew OOS R² 0.1095, p 0.00296;
- 30D–60D term slope OOS R² 0.0205, p 0.07768.

### Phase 5 — Multimodal prediction
**Status:** complete for first specification.

Historical holdout:
- direct next-day direction AUC 0.4584;
- 5-session return OOS R² -0.1038;
- 5-session volatility expansion AUC 0.6879.

The volatility-expansion signal was retained for further testing but was not assumed tradable.

### Phase 6 — Strategy translation
**Status:** candidate screen completed.

A fixed six-family volatility-conditioned NIFTY settlement-proxy screen was run.

### Phase 7 — Statistical validation
**Status:** complete for the then-current directional candidate.

28-path CPCV, PBO and approximate DSR rejected the inverse-direction candidate.

### Phase 8 — Fresh-forward validation
**Status:** complete for the tested frozen families.

Fresh forward: 2026-05-15 → 2026-09-17/18.

The frozen multimodal volatility-expansion strategy families all failed the 20-bps promotion gate. The price/volatility-only branch also failed.

Phase 8C strengthened the surface-dynamics predictive result:
- downside skew median CPCV OOS R² 0.3166, positive on 100% of 28 paths;
- upside skew median OOS R² 0.1068, positive on 89.3%;
- 30–60D term slope median OOS R² 0.1543, positive on 96.4%.

These are predictive surface-evolution results, not trading P&L.

### Phase 9A — Execution-grade surface-relative-value protocol
**Status:** protocol frozen; economic execution data blocked.

Candidate library deliberately broad:
- delta-matched skew verticals;
- risk reversals;
- butterflies;
- skew butterflies;
- calendars;
- four-leg surface boxes;
- iron condors;
- straddles/strangles.

No winner is to be selected by realized P&L before the data and statistical gates.

### Phase 9B — Frozen surface-signal settlement-proxy
**Status:** completed and rejected.

Frozen model:
- expanding Ridge;
- features: 30D downside skew, upside skew, term slope, ATM IV, trailing vol, trailing return;
- target: future 30D downside-skew change;
- alpha 10;
- forward coefficients frozen 2026-05-14.

Forecast still worked forward:
- forward R² 0.3029;
- forward correlation 0.5695.

Strategy:
- 45–75D maturity;
- approx 10Δ/50Δ put skew vertical;
- one entry delta hedge;
- 30-calendar-day hold;
- no overlap;
- EOD settlement proxy.

Fresh forward:
- 4 trades;
- total P&L -₹14,828;
- mean -₹3,707;
- win rate 25%;
- approximate event annualized Sharpe -0.87;
- mean P&L / entry-risk proxy -7.9%.

Decision: **REJECTED for capital trading and paper-trading promotion.**

The reverse-sign result was positive on the same four observations, but is a control, not a promoted strategy. One-day delay and random-entry controls were also unstable.

### Phase 10 — Historical execution-data layer
**Status:** software-ready / data-blocked.

Implemented:
- current/historical NSE F&O order/trade layouts;
- jiffy → UTC conversion;
- record-length/layout validation;
- normalization;
- raw-file hashing;
- hard rejection of unsupported formats.

Economic gate remains genuine timestamped execution history.

### Phase 11 — Surface strategy library
**Status:** structure/exposure software pass.

Implemented:
- skew verticals;
- risk reversals;
- butterflies;
- iron condors;
- ATM calendars;
- skew butterflies;
- four-leg surface boxes;
- straddle/strangle structures;
- deterministic delta-hedge helper;
- exposure/payoff diagnostics.

No theoretical Black–Scholes price is ever treated as a historical fill.

### Phase 12 — Execution simulator / quote audit
**Status:** mechanical pass; economic data blocked.

Public NIFTY fixtures:
- TickBytes sample: 50 rows, 49 valid;
- OptionVault sample: 13 rows, all valid.

Simulator:
- rejects non-finite/non-positive/crossed quotes;
- buys at ask, sells at bid;
- enforces displayed size;
- enforces synchronization window;
- computes quoted cash flow.

Fixtures are software tests only, not economic performance evidence.

### Phase 13 — Executable CPCV/PBO/DSR
**Status:** protocol frozen; harness implemented; economic run blocked by genuine execution history.

Frozen:
- Phase 8C predictors;
- Phase 11 candidate structures;
- timing;
- synchronization;
- cost grid;
- purge 30 calendar days;
- embargo 5 trading days;
- candidate-selection rule;
- capital normalization.

Executable trade schema requires contract identity, decision/entry/exit times, side, quantity, fills, fees/taxes, net P&L and capital-at-risk; multi-leg trades must preserve leg-level timestamps/fills/synchronization.

## 4. Phase 14A — Broad inefficiency discovery

**This is the current research branch.**

Purpose: test each previously identified inefficiency alone first, then test only preregistered combinations. **Optimization comes later, after discovery.**

Frozen registry:
`data/phase14/inefficiency_hypothesis_registry.csv`

Frozen protocol:
`docs/PHASE14_BROAD_INEFFICIENCY_DISCOVERY.md`

Covered families:

1. Time-series equity: momentum, short-term reversal, volatility-state effects, volume shocks.
2. Cross-sectional equity: momentum, reversal, liquidity/size, abnormal turnover.
3. Futures: cash-futures basis, term-structure dislocation, expiry effects.
4. Options: VRP, jump-risk pricing, surface skew, term slope, vol-of-vol.
5. Index-relative: dispersion/correlation, breadth.
6. Events: announcement drift, rebalancing drift, expiry flow.
7. Microstructure: spread/depth imbalance, order imbalance, impact decay.
8. Cross-market: global lead/lag, USD/INR, rates.
9. Dependence/regime: memory/regime effects.

Discovery decision taxonomy:
- DATA_BLOCKED
- REJECTED_NO_SIGNAL
- REJECTED_AFTER_COST
- REJECTED_CPCV
- REJECTED_MULTIPLE_TESTING
- DISCOVERY_POSITIVE
- ECONOMIC_CANDIDATE
- VALIDATED

## 5. Phase 14A.1 results already established

### Time-series equity
Frozen tests:
- 20-session momentum;
- 5-session reversal;
- simple agreement-only momentum/reversal combination.

Results:
- Momentum: 297 events; gross mean 0.148%; Sharpe 0.50; CPCV median 0.59; CPCV q10 -0.78; 67.9% positive paths; mean at 5 bps/side 0.048%; mean at 10 bps/side -0.052%.
- Reversal: 297 events; gross mean 0.024%; Sharpe 0.08; CPCV median 0.09; CPCV q10 -0.51; mean at 5 bps/side -0.076%.
- TS combination: 100 events; gross mean 0.256%; Sharpe 0.79; CPCV median 0.46; CPCV q10 -0.77; 60.7% positive paths.

Current conclusion:
- momentum: not robust enough;
- reversal: no meaningful evidence;
- simple combination: not robust.

### Options — VRP discovery correction

An initial short-ATM-straddle screen looked strong:
- 69 non-overlapping trades;
- mean settlement-proxy return +0.966%;
- event Sharpe 1.04;
- win rate 68.1%;
- one-sided p 0.00195;
- CPCV median Sharpe 0.97;
- CPCV q10 0.38;
- positive CPCV paths 100%;
- mean at 20 bps/side about +0.950%.

However, a crucial diagnostic showed the putative signal:
**30D ATM IV > trailing 20-session realized volatility**
was effectively always ON in this opportunity set.

Therefore this is not evidence that the state filter times the premium. The safer conclusion is:
**a broad short-volatility premium proxy is present in this settlement-based sample, while incremental timing/value from the VRP state filter is not yet established.**

An unconditional non-overlapping short-straddle baseline was also positive at roughly +0.849% mean event return and Sharpe about 1.02.

Current VRP status:
**DISCOVERY_POSITIVE as a short-volatility premium observation; NOT VALIDATED as a timing signal or executable strategy.**

No optimization is allowed on this observation.

## 6. Phase 14A engineering in progress

Implemented / attempted:
- `docs/PHASE14_BROAD_INEFFICIENCY_DISCOVERY.md`
- `data/phase14/inefficiency_hypothesis_registry.csv`
- `data/phase14/nifty50_pit_membership.csv`
- `data/phase14/symbol_renames.json`
- `scripts/phase14a_ts_screen.py`
- `scripts/phase14a_acquire_pit_nifty50.py`
- `scripts/phase14a_cross_section_screen.py`
- `scripts/phase14a_vrp_screen.py`
- `scripts/phase14a_fno_acquire.py`
- `scripts/phase14a_futures_screen.py`
- associated tests/workflows.

PIT NIFTY membership source currently used:
`aditya-jha/nse-historical-membership` redistributed data, CC BY 4.0, with primary NSE source references. This is a secondary reconstruction and must not be represented as an official NSE membership feed.

Current cross-sectional workflow status:
- several workflow attempts failed in the test-validation step during engineering cleanup;
- failures identified included test environment/sample issues and script formatting/raw-symbol handling;
- latest fixes were made, but **do not claim the cross-sectional workflow is clean until a new successful run is observed**.

Current futures workflow:
- official-NSE acquisition path added;
- frozen futures basis/term/expiry discovery screen added;
- latest workflow has been observed running; **do not claim success until the run and artifact are verified**.

## 7. Current external-data status

### Available
- validated historical NIFTY EOD/index and option-surface history;
- PIT option IV snapshot;
- risk-free input history as used by Phase 4;
- public NIFTY Level-2 software fixtures;
- secondary PIT NIFTY membership reconstruction;
- official-NSE futures/index acquisition path.

### Not yet sufficient for executable trading claims
- bulk historical NIFTY bid/ask/depth/order/trade archive with PIT contract identity;
- complete execution/margin/fee/impact history;
- sufficiently synchronized microstructure history.

Never infer the missing layer.

## 8. Frozen forward periods and contamination rules

The 2026-05-15 → 2026-09-18 forward period has already been used.

It is permanently frozen for:
- replacement strategy selection;
- sign reversal;
- strike geometry selection;
- holding period selection;
- threshold selection;
- combination weighting.

Any later validation must use genuinely newer observations.

## 9. Current branch/repository state

Working branch:
`research/phase9-surface-execution`

Open draft PR:
**#11**

The current work is a broad research continuation, not a replacement of Phase 9A–13.

Always inspect:
- branch state;
- latest workflow runs;
- changed files;
before taking the next research step.

## 10. Evidence hierarchy

When sources conflict, use:
1. primary exchange/regulator/vendor source with explicit PIT evidence;
2. immutable acquired artifact + manifest/hash;
3. reproducible repository result;
4. secondary public reconstruction;
5. model/inference.

Secondary datasets are inputs with provenance, not primary facts.

## 11. How to record new work

After every substantive action, update this file with:
- date;
- phase/subphase;
- hypothesis;
- data source;
- exact fixed rule;
- result;
- control result;
- statistical result;
- decision;
- blocker;
- workflow/artifact identifiers where applicable;
- whether the result is executable or settlement proxy;
- what is frozen against future tuning.

Also append the substantive conversation/decision to:
`docs/CHAT_DECISION_LOG.md`

## 12. Conversation continuity rule

The user explicitly requested that the repository, rather than model memory, carry the project continuity.

The substantive chat record should preserve:
- user research requirements;
- methodological constraints;
- decisions already made;
- corrections to earlier mistakes;
- conclusions;
- unresolved questions;
- next-step gates.

**Hidden chain-of-thought is not stored or exported.** The continuity file stores the actionable reasoning summary, evidence, decision rationale, and methodological constraints needed to reproduce the research safely.

## 13. Current decision / next gate

**Do not optimize anything yet.**

The current gate is:

**finish 14A.0 data readiness → finish standalone 14A.1 screens across data-ready families → apply multiple testing/CPCV/cost controls → only then run preregistered combinations → only then open a separately frozen optimization phase → then untouched later validation.**

The most important currently open empirical questions are:
1. whether cross-sectional NIFTY effects survive survivorship-safe PIT data;
2. whether futures basis/term/expiry effects survive fixed-cost CPCV;
3. whether the broad short-volatility premium survives risk/margin/execution constraints and contains any incremental timing information;
4. whether additional option structures monetize the surviving surface predictors;
5. whether any cross-mechanism combination provides robustness without fitted weights.

