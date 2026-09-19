# Phase 14A.1 Results — First Broad Inefficiency Discovery Screen

## Research rule

This is a discovery screen, not an optimization pass. The development boundary is **2026-05-14**. The previously used **2026-05-15 through 2026-09-18** forward period remains frozen and is not used for signal, sign, threshold, holding-period, strike, or weight selection.

Every tested translation uses fixed rules, a predefined cost grid, non-overlap where the mechanism implies a holding period, CPCV diagnostics, and negative controls. EOD/settlement results are labelled as proxies rather than executable fills.

## Time-series equity

Three preregistered translations were screened: fixed 20-session momentum, fixed 5-session reversal, and an equal-risk combination that activates only when the two signs agree.

| Mechanism | Events | Gross mean/event | Gross event Sharpe | 0-cost one-sided p | CPCV median Sharpe | CPCV q10 | Positive paths | Mean at 5 bps/side | Mean at 10 bps/side | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Momentum | 297 | 0.148% | 0.50 | 0.113 | 0.59 | -0.78 | 67.9% | 0.048% | -0.052% | Rejected |
| 5D reversal | 297 | 0.024% | 0.08 | 0.421 | 0.09 | -0.51 | 53.6% | -0.076% | -0.176% | Rejected |
| TS combination | 100 | 0.256% | 0.79 | 0.136 | 0.46 | -0.77 | 60.7% | 0.156% | 0.056% | Rejected |

The momentum effect is positive before costs but does not produce a robust positive CPCV lower tail, and modest transaction costs remove the mean effect. Reversal is not supported. The simple momentum/reversal combination does not clear the discovery gate.

## Options — variance risk premium

The fixed signal was **30-day ATM implied volatility greater than trailing 20-session realised volatility**. The fixed translation was a **short nearest-30D ATM straddle held to expiry**, accepting the earliest eligible trade after the prior expiry so trades do not overlap. Strike selection was always the closest strike to spot; no strike, expiry window, lookback, threshold or holding period was optimized.

Among **69 non-overlapping development trades**, the settlement-proxy short-straddle strategy produced:

| Metric | Result |
|---|---:|
| Mean return per event, 0 bps | +0.966% |
| Event Sharpe | 1.04 |
| Win rate | 68.1% |
| One-sided t-test p | 0.00195 |
| CPCV median Sharpe | 0.97 |
| CPCV q10 Sharpe | 0.38 |
| Positive CPCV paths | 100% |
| Mean/event at 20 bps per side | +0.950% |

The sign-flipped long-straddle control is negative with mean **-0.966%**. A first unconditional non-overlapping short-straddle baseline is also positive (mean about **+0.849%**, event Sharpe about **1.02**), so the current evidence does **not** establish that the volatility-state filter adds most of the value. The more conservative interpretation is that the sample contains a broad short-volatility premium proxy, while the incremental timing contribution of the VRP signal still needs dedicated testing.

### Current status of VRP

**DISCOVERY_POSITIVE, not VALIDATED.**

It has not passed the remaining project gates: full multiple-testing correction across the entire Phase 14A registry, realistic executable costs and margin/risk constraints, genuine quote/trade reconstruction, and a later untouched forward period that has not already been used by the project.

## Already-known option-surface findings

The earlier surface-dynamics branch remains in the registry as a separate mechanism. Downside skew, upside skew and 30–60D term slope have shown predictive information about subsequent option-surface changes, but this is not automatically tradable P&L. The first frozen downside-skew monetization attempt was rejected on the later settlement-proxy period; no post-hoc sign reversal is being selected.

## What is next

1. Finish the PIT cross-sectional equity screen using the official NSE daily cash-market universe plus a secondary PIT NIFTY-50 membership reconstruction. The acquisition is intentionally retaining former constituents' price histories after they leave the index so exits do not introduce survivorship bias.
2. Run the remaining data-ready standalone families: futures basis/term structure/expiry effects where historical contract data pass PIT checks; additional option structures for VRP/surface/jump mechanisms; and cross-market lead/lag where synchronized historical sources can be frozen.
3. Only after standalone screens are frozen will preregistered equal-risk combinations be evaluated.
4. Only candidates surviving Phase 14A discovery will be eligible for a later optimization phase.

**Current broad-screen conclusion:** the first pass already gives a mixed result rather than one universal market-efficiency conclusion. The simple NIFTY momentum/reversal family does not survive the discovery gate, while the option variance-risk-premium family shows substantial historical settlement-proxy evidence but still needs to separate true incremental signal from the unconditional short-volatility premium and must pass execution-grade validation.
