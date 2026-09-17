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
| NSE derivatives EOD | DS-NSE-FO-EOD | `option_eod` | Public historical reports | Interface defined |
| NSE contract master | DS-NSE-CONTRACT | `contract_master` | Public | Interface defined |
| NSE India VIX | DS-NSE-VIX | `india_vix` | Public | Interface defined |
| RBI rates | DS-RBI-RF | `risk_free` | Public | Interface defined |
| NSE historical order/trade | DS-NSE-OTC | `intraday_quotes_trades` | Licensed | Access decision required |
| Vendor option quotes | DS-VENDOR-OPTIONS | `option_eod`, `intraday_quotes_trades` | Licensed | Vendor selection required |

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

An adapter becomes `DATA-READY` only after a real source sample passes schema, timestamp, contract, quality and point-in-time reconstruction tests. Interface existence alone does not qualify the source as research-ready.
