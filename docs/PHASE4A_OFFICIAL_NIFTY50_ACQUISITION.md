# Phase 4A — Official NIFTY 50 Underlying Acquisition

## Objective

Acquire the NIFTY 50 underlying from the official NSE Indices Historical Index Data source for the Phase 4A point-in-time join. No vendor or third-party fallback is permitted for this gate.

The official historical-data page exposes daily index OHLC fields and a CSV-oriented historical-data interface. The implementation uses the underlying official endpoint behind that page and preserves raw responses plus SHA-256 hashes.

## PIT convention

The observation date is the NIFTY session date. For the current EOD research design, `available_at` is assigned **23:59:59 Asia/Kolkata on the observation date** as a conservative, pre-registered EOD availability convention. This is not interpreted as an observed exact publication timestamp.

## Validation gates

The acquisition must show:

- complete requested date coverage across the underlying history, allowing weekends/NSE holidays to be absent;
- unique observation dates;
- positive OHLC values and valid OHLC ranges;
- source metadata preserved on every row;
- raw yearly response preservation and SHA-256 hashes;
- deterministic normalized CSV and manifest.

The resulting file is an external PIT input. It does **not** by itself freeze the full Phase 4A snapshot: lot-size mapping and RBI risk-free inputs remain separate mandatory gates.

## Source

NSE Indices, Historical Data Reports: https://niftyindices.com/reports/historical-data

NIFTY 50 index page: https://www.niftyindices.com/indices/equity/broad-based-indices/nifty--50
