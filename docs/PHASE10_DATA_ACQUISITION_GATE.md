# Phase 10 — Historical Execution-Data Acquisition Gate

## Current result

The research code can now consume normalized timestamped execution observations, but the repository does not contain a multi-month licensed historical NIFTY order/quote/trade archive.

The current NSE documentation distinguishes ordinary EOD/history from historical order-and-trade data. NSE lists historical F&O order/trade data as a separate historical product delivered through its historical-data infrastructure. The current page was updated on 2 September 2026. citeturn155499search5turn155499search11

## Public data found

Two public repositories provide small NIFTY execution-feed samples:

- TickBytes: representative Level-1/Level-2 option-feed samples with top-5 depth.
- OptionVault: representative Level-2/tick samples; the complete dataset is described as licensed.

These samples are preserved only as software fixtures. They are not large enough to support statistical profitability claims. citeturn692592search0turn841279search0

## What is still required

The economic backtest needs a sufficiently long historical dataset with:

1. timestamped executable bid/ask and displayed size;
2. deterministic contract identifiers;
3. executed trades and/or order events sufficient to reconstruct fills;
4. point-in-time lot-size/contract-master provenance;
5. enough history to create development CPCV paths and an untouched later validation period.

EOD settlement data cannot be converted into historical quotes without introducing assumptions that the current research protocol forbids.

## Decision

**DATA GATE OPEN / SOFTWARE GATE PASSED.**

Until the required archive is licensed or otherwise legally acquired, no executable strategy should be promoted.
