# Phase 4A — Point-in-Time Input Audit

## Decision

**Status: PIT-AUDIT-BLOCKED**

The NIFTY OPTIDX EOD archive passes structural reconciliation, but the research snapshot is **not yet frozen for formal IV/VRP testing** because three external PIT inputs still require source-level validation:

1. historical NIFTY contract lot size at the **contract/expiry level**;
2. point-in-time NIFTY underlying/index value for legacy 2020–2024-07-07 rows;
3. point-in-time risk-free term structure.

### Verified facts

- NSE states that its EOD files are generated once at EOD and contain F&O bhavcopy information. This supports treating the archive as an EOD research layer, but does **not** establish an exact intraday publication timestamp. Therefore the current `available_at = trade date 23:59:59 IST` remains a conservative EOD availability convention, not an observed publication timestamp.
- NSE's public F&O reports identify the legacy bhavcopy as discontinued from July 8, 2024 and replaced by UDiFF Common Bhavcopy. The current acquisition route follows that boundary.
- UDiFF provides `NewBrdLotQty` and `UndrlygPric`; the legacy files do not provide those fields consistently and the acquisition deliberately preserves them as NA rather than substituting inferred values.

### Lot-size history relevant to NIFTY

The following official NSE changes are frozen as external provenance, but they do **not** by themselves replace a contract-level master:

| Effective contract regime | NIFTY lot | Evidence |
|---|---:|---|
| Through June 2021 expiries | 75 | NSE FAOP47854 |
| July 2021 onward | 50 | NSE FAOP47854 |
| July 2023 review | 50 | NSE FAOP56233 |
| April 25, 2024 expiry exception | 50 | NSE FAOP61415 |
| Contracts available from April 26, 2024 | 25 | NSE FAOP61415 |
| New index contracts introduced from Nov 20, 2024 | 75 | NSE FAOP64625 |

Because NSE explicitly uses contract-introduction/expiry transition rules, lot size must be joined at contract level rather than assigned solely from trade date.

### Risk-free input

RBI documents Treasury Bills as Government short-term instruments and publishes auction cut-off yields. A 91-day T-bill series is therefore a defensible **candidate** risk-free input, but auction publication/availability timing and interpolation/carry-forward rules must be frozen before it is used in a PIT feature. The audit will not silently treat a later-published auction result as available at the same-session decision time.

### Freeze rule

Formal Phase 4B reconstruction may begin only after:

- contract-level lot-size mapping is available for every included option contract;
- legacy underlying prices have an independently documented PIT source;
- risk-free observations have documented availability timestamps and a fixed interpolation rule;
- the 2021-03-30 option-data coverage gap remains explicitly excluded unless separately sourced;
- the final included-date/contract mask is written to an immutable snapshot manifest.

## Research consequence

The current public EOD archive is **usable for structural/data engineering work**, but **not yet sufficient for a frozen PIT implied-volatility dataset**.

No VRP/jump-premium conclusion should be drawn until this gate is passed.
