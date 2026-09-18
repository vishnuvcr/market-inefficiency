# Phase 6 — Strategy Translation Screen

Phase 5 found little evidence for direct next-day direction prediction but a materially stronger ability to classify **next-5-session volatility expansion**.

Phase 6 asks whether that predictive state information can be translated into a simple, pre-specified trading rule without reusing the final holdout for tuning.

## Design

- 80% development/training.
- next 10% validation: choose exactly one candidate from a fixed six-rule set using 10 bps/side.
- final 10%: untouched until the candidate and selection rule are frozen.
- the same Phase 5 multimodal model specification is used.
- final results are reported at 5, 10 and 20 bps/side.
- no parameter search is performed.

Candidate rules:

1. model direction;
2. inverse model direction;
3. 20-session trend only during predicted high volatility;
4. 20-session mean reversion only during predicted high volatility;
5. one-session breakout direction only during predicted high volatility;
6. 20-session trend only during predicted low volatility.

A positive final result is still a **candidate edge**, not a validated live strategy. CPCV, DSR, PBO, stress tests and execution-grade data remain required.
