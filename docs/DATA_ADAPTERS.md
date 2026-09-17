# Phase 2 Data Adapter Interfaces

## Purpose

Define stable interfaces between source-specific ingestion code and the canonical research data contract. Adapters normalize source quirks without embedding source-specific assumptions in downstream research.

## Adapter contract

Each adapter must expose:

- `source_id`: registry identifier.
- `source_version`: source/report/API version when available.
- `fetch_window(start, end)`: retrieve a bounded source slice.
- `normalize(raw)`: map source fields to canonical fields.
- `validate(records)`: run schema and source-specific quality checks.
- `provenance()`: return source/licence metadata.

Adapters must be deterministic for a fixed raw-source snapshot and preprocessing version.

## Initial adapters

| Adapter | Source ID | Canonical layers | Access | State |
|---|---|---|---|---|
| NSE cash/EOD | DS-NSE-CM | `underlying_eod` | Public | Interface defined |
| NSE derivatives EOD | DS-NSE-FO-EOD | `option_eod` | Public historical reports | **Normalization path implemented; real-source sample pending** |
| NSE contract master | DS-NSE-CONTRACT | `contract_master` | Public | Interface defined |
| NSE India VIX | DS-NSE-VIX | `india_vix` | Public | Interface defined |
| RBI rates | DS-RBI-RF | `risk_free` | Public | Interface defined |
| NSE historical order/trade | DS-NSE-OTC | `intraday_quotes_trades` | Licensed | Access decision required |
| Vendor option quotes | DS-VENDOR-OPTIONS | `option_eod`, `intraday_quotes_trades` | Licensed | Vendor selection required |

## NSE F&O EOD normalization

`scripts/ingest_nse_fo_eod.py` accepts a bounded operator-supplied NSE historical CSV and emits a provenance-bearing canonical JSON slice. It:

- resolves documented NSE field-name variants;
- normalizes trade/expiry dates to UTC;
- requires an explicit `available_at` timestamp rather than inferring publication time;
- creates deterministic contract identifiers;
- preserves source row numbers and raw-file SHA-256;
- rejects duplicate `(timestamp, instrument_id)` records;
- carries LTP, settlement, volume, OI and underlying value when supplied;
- flags missing lot-size metadata for later contract-master as-of enrichment.

This is an ingestion/normalization implementation, **not** a `DATA-READY` declaration. A real NSE sample must still pass the full quality and point-in-time acceptance gate.

## Normalization rules

1. Normalize timestamps to UTC while retaining source timezone metadata.
2. Never overwrite raw source fields; normalized fields are derived outputs.
3. Apply contract metadata as-of its effective interval.
4. Preserve source identifiers for audit and reconciliation.
5. Do not infer bid/ask from last traded price.
6. Do not manufacture historical quote depth from EOD volume/OI.
7. Record every exclusion with a machine-readable reason code.

## Synthetic validation boundary

CI may validate adapter contracts using synthetic fixtures. No restricted exchange/vendor market data is committed to the repository.

## Promotion rule

An adapter becomes `DATA-READY` only after a real source sample passes schema, timestamp, contract, quality and point-in-time reconstruction tests. Interface existence or synthetic CI success alone does not qualify the source as research-ready.
