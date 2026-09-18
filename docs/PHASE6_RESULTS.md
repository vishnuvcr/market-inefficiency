# Phase 6 — Results

Workflow run 35398267262 passed; artifact 10569136734 (sha256:905f30a0f93cfdb47fc2bebe9a845eda301c74557714ce650ab98413689c7de8).

A fixed six-candidate strategy family was screened. Candidate selection used the first 80% development block plus a separate 10% validation block. The final 10% was frozen until the selection rule was locked.

Validation selected the inverse of the model direction signal because the direction model's holdout probabilities had been below random-order performance. The selection was made before touching the final 10%.

Final 10% chronological holdout:

| Assumed cost | Mean daily net return | Sharpe | Max drawdown |
|---:|---:|---:|---:|
| 5 bps/side | +0.0001999 | +0.417 | -5.89% |
| 10 bps/side | +0.0000624 | +0.129 | -6.14% |
| 20 bps/side | -0.0002128 | -0.437 | -8.92% |

The candidate therefore does not qualify as a validated trading edge. Its apparent positive final-holdout result is small, cost-sensitive and based on a close-to-close proxy rather than observed executable fills.

The final holdout is now considered consumed for this candidate and must not be reused for further tuning.
