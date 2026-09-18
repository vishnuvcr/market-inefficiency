# Phase 7 — Statistical Validation Results

Workflow run 35398734390 passed; artifact 10570261819 (sha256:676868699bfa2fefd12b53ba91fea4087dda984017d04b79eb09314ece8e6f1a).

The Phase 6 candidate set was frozen and the final 10% chronological holdout was excluded from all CPCV calculations.

## CPCV

The first 90% of the aligned sample was divided into 8 chronological blocks. Every 2-of-8 test-block combination was evaluated, with a one-observation purge and one-observation embargo.

This produced 28 CPCV paths.

For the frozen Phase 6 inverse-direction candidate at 10 bps/side:

- mean CPCV Sharpe: -0.4500
- median CPCV Sharpe: -0.4194
- 10th percentile: -1.1934
- 90th percentile: +0.4126
- positive-Sharpe path fraction: 28.6%

Thus the candidate's single final holdout positive result does not resemble a stable development-period edge.

## PBO diagnostic

A CSCV-style selection-risk proxy was calculated across the six frozen candidate rules.

- candidate count: 6
- PBO proxy: 0.4643

Interpretation: in about 46% of the CPCV paths, the candidate that looked best in-sample landed in the worse half of the OOS candidate ranking. This is substantial selection instability.

## DSR diagnostic

An explicitly labelled approximate DSR diagnostic was computed for the frozen inverse-direction candidate using six effective candidate trials.

- expected-max-Sharpe hurdle: 0.0355
- CPCV mean Sharpe: -0.4500
- approximate probability of exceeding the hurdle: 7.49e-62

This implementation is a diagnostic approximation, not a claim that the exact canonical DSR has this numerical value.

## Additional observation

Among the six fixed candidates, trend_lowvol had the most stable CPCV distribution at 10 bps (median Sharpe +0.1513, positive on 60.7% of paths), but it was not the candidate selected in Phase 6 validation. Its final-holdout performance must not be examined to choose it after the fact; the Phase 6 final 10% is already consumed and must remain untouched.

## Decision

The inverse-direction candidate is rejected for promotion under the current specification.

The broad research objective remains alive: the direct direction problem did not produce a robust edge, while the Phase 5 volatility-expansion classifier (AUC 0.688) provides a more promising prediction target. The next research branch should translate predicted volatility state into independently validated strategy families, while the existing options-surface signals remain a parallel branch.

Execution-grade option studies still require quote/order-trade data.
