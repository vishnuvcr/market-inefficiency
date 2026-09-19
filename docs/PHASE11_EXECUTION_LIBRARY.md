# Phase 11 — Executable Surface Strategy Library

The Phase 11 library is now complete at the **structure/exposure** level for the preregistered surface-relative-value families. It intentionally does not select a winner and does not estimate historical performance without execution data.

Implemented structures include:

- delta/skew verticals;
- put/call risk reversals with an explicit delta-hedge diagnostic;
- put and call butterflies;
- iron condors;
- same-strike calendars for term-slope exposure;
- downside skew butterflies;
- four-leg maturity-spread surface boxes;
- straddle/strangle variance structures.

Every structure is represented as explicit option legs and can be evaluated for Black–Scholes diagnostic price, delta, gamma, vega, theta, and terminal payoff. The new delta-hedge helper converts the option delta into the underlying units required for a first-order hedge.

These are **exposure diagnostics only**. The library never substitutes theoretical Black–Scholes prices for historical fills.

## Execution-data compatibility

The same leg representation is designed to feed Phase 12 once genuine timestamped quotes/order-trade observations are available. The execution layer will determine entry/exit prices, displayed-size capacity, synchronization, fees, and slippage; it will not infer them from theoretical prices.

## Decision

**PHASE 11 SOFTWARE PASS; ECONOMIC SELECTION NOT STARTED.**

No candidate has been promoted based on the current public samples or the rejected 2026 forward settlement-proxy period.
