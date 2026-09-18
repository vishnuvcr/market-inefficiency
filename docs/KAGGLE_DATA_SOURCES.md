# Kaggle Data Sources — Phase 2

Last reviewed: 2026-09-18

## Adopted Kaggle source

**Dataset:** `debashis74017/nifty-50-minute-data`

**Kaggle title:** `NSE - Nifty 50 Index Minute data (2015 to 2026)`

**Primary use in this project:** underlying NIFTY index OHLC data and India VIX context for Phase 2 validation and Phase 3 stylized-fact research.

Kaggle describes the dataset as containing NIFTY indices at multiple frequencies, including NIFTY 50 and India VIX minute data. The dataset page states that the files contain OHLC and datetime information and that the NIFTY index files do not contain volume. The publisher also states that the files were collected from internet/Google Drive sources and are provided for research purposes. Therefore provenance is recorded as Kaggle/uploader-provided rather than as a direct NSE archival feed.

Kaggle source page: https://www.kaggle.com/datasets/debashis74017/nifty-50-minute-data

## Research classification

| Layer | Kaggle source | Allowed use | Status |
|---|---|---|---|
| Underlying NIFTY OHLC | NIFTY 50 minute/day files | Descriptive statistics, realized-volatility estimators, stylized facts | ACCEPT AFTER LOCAL HASH + QUALITY CHECK |
| India VIX | INDIA VIX minute file | Volatility-regime/context features and descriptive analysis | ACCEPT AFTER LOCAL HASH + QUALITY CHECK |
| Options bid/ask/depth | Not supplied by this source | VRP execution, SABR quote calibration, microstructure | NOT PROVIDED |
| Historical F&O contract master | Not supplied by this source | Point-in-time contract reconciliation | NOT PROVIDED |

## Important limitation

Kaggle data are not automatically treated as point-in-time exchange data. The dataset's observation timestamp describes the market observation, while the Kaggle publication/download timestamp describes when the research copy was obtained. Those are different concepts.

For **stylized-fact research**, the Kaggle snapshot can be used after provenance and data-quality validation.

For **executable trading backtests**, a Kaggle snapshot must not be assumed to reproduce what was knowable to a trader at each historical decision time unless an independently documented historical availability mechanism is available.

## Option-data gap

The Kaggle NIFTY index dataset does not solve the project's historical option bid/ask/depth requirement. A separate option dataset must still be validated before Track A (VRP), Track C (SABR/surface) or Track G (microstructure) can be promoted to executable research.

A separate Kaggle F&O dataset may be used as an exploratory EOD source if its fields, provenance, contract identity, and licensing are independently validated; it cannot be assumed to contain reliable historical bid/ask/depth. Public Kaggle discussions also indicate that shared F&O datasets may lack bid/ask data.

## Required local snapshot procedure

1. Download the selected Kaggle dataset version.
2. Record the exact Kaggle dataset identifier and version number.
3. Record the download timestamp in UTC.
4. SHA-256 hash every source file used.
5. Run schema, chronology, duplicate, OHLC and missingness diagnostics.
6. Record all exclusions using machine-readable reason codes.
7. Create an immutable snapshot manifest containing source version, preprocessing version, code commit, hashes and row counts.
8. Do not commit the raw Kaggle dataset to this public repository.

## Promotion rule

Kaggle data can promote the **underlying/index and India-VIX layers** into the Phase 3 descriptive research universe after the above checks pass. It does **not** by itself promote the full derivatives dataset to `DATA-READY` for executable option strategies.
