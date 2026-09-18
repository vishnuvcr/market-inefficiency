# Phase 4A — External PIT Input Acquisition Plan

## Purpose

Close the remaining point-in-time data gate without substituting convenient but non-authoritative series.

## Input A — Legacy NIFTY underlying

Use the official NSE/NSE Indices Historical Index Data route for the NIFTY 50 close covering the legacy option period through 2024-07-07. NSE documents historical NIFTY 50 data through its Historical Index Data interface. The current project option archive begins the UDiFF route on 2024-07-08, so the external underlying is required primarily for legacy rows.

**PIT rule:** retain the observation date and source metadata. The close may be paired with an EOD option observation only under the preregistered EOD decision convention. Do not backfill missing sessions from a later revised series.

## Input B — Contract-level lot size

The project has already frozen official NSE lot-size transition provenance. The remaining task is to materialize a contract/expiry mapping and validate it against every included option expiry.

The mapping must not be implemented as a simple trade-date lookup because several transitions are defined by contract introduction or expiry.

## Input C — Risk-free term structure

RBI's Database on Indian Economy is the candidate authoritative source for historical Government-security/T-bill observations. A single 91-day series is not automatically sufficient for every option maturity.

Before IV reconstruction, freeze:

1. selected instruments/tenors;
2. observation date convention;
3. publication/availability timestamp rule;
4. interpolation rule between available tenors;
5. treatment of holidays and missing observations;
6. day-count convention;
7. rate-to-continuous-compounding conversion.

No later-published auction result may be used merely because its observation date precedes the option trade date.

## Input D — 2021-03-30 gap

2021-03-30 is retained as an explicit exclusion because the three tested option-archive routes did not provide the historical archive. No interpolation or synthetic option data is permitted.

## Gate

Phase 4B remains blocked until A, B and C are frozen and validated. The output must include a deterministic inclusion mask and hashes for every external input file.
