# Data Source Registry — Phase 2

Last reviewed: 2026-09-18

## Objective

Define a reproducible, point-in-time data stack before any formal strategy backtest. A source being publicly discoverable does **not** mean it contains every field required by a hypothesis.

## Source tiers

| Source ID | Provider | Data | Access | Phase 2 role | Status |
|---|---|---|---|---|---|
| DS-NSE-CM | NSE India | Equity/underlying historical price-volume and reports | Public historical pages/reports | Underlying OHLCV, volume, corporate-action reconciliation | READY FOR INGESTION DESIGN |
| DS-KAGGLE-NIFTY | Kaggle / uploader-provided research snapshot | NIFTY index OHLC and India VIX minute/daily files | Public Kaggle dataset | Underlying and volatility-context layer for descriptive/stylized-fact research | ACCEPT AFTER LOCAL HASH + QUALITY CHECK |
| DS-NSE-FO-EOD | NSE India | Equity-derivatives contract-wise price/volume, OI and reports | Public historical reports; some datasets are downloadable | Futures/options EOD baseline, OI, settlement/turnover | READY FOR INGESTION DESIGN |
| DS-NSE-CONTRACT | NSE India | Contract specifications, underlyings, lot-size/strike information | Public | Point-in-time contract master and instrument history | READY FOR INGESTION DESIGN |
| DS-NSE-VIX | NSE India | India VIX historical values and methodology | Public | Implied-volatility context variable | READY FOR INGESTION DESIGN |
| DS-NSE-OTC | NSE India | Historical order/trade data for F&O | Paid subscription | Intraday execution/microstructure; quote/trade reconstruction where licensed | ACCESS DECISION REQUIRED |
| DS-RBI-RF | RBI | Treasury-bill and related interest-rate observations | Public RBI publications/statistics | Risk-free-rate proxy curve | READY FOR INGESTION DESIGN |
| DS-VENDOR-OPTIONS | Approved market-data vendor | Historical option quotes/order book with bid/ask/depth | Paid/vendor licence | Full VRP/SABR/jump surface research when EOD public data are insufficient | VENDOR SELECTION REQUIRED |

## Kaggle source policy

The adopted Kaggle research source is `debashis74017/nifty-50-minute-data` (title: `NSE - Nifty 50 Index Minute data (2015 to 2026)`). The dataset includes NIFTY indices at multiple frequencies and an India VIX minute file. Its publisher states that the files were collected from internet/Google Drive sources and are supplied for research purposes; therefore it is classified as a third-party research snapshot rather than a direct NSE archival feed.

Kaggle data are suitable for the underlying/index and India-VIX descriptive/stylized-fact layer after local hash, schema, chronology and quality checks. They do not establish historical option bid/ask/depth provenance or original exchange publication timing. Do not promote the Kaggle snapshot to executable option-strategy data merely because it contains historical prices.

## Evidence supporting source availability

- NSE's historical-report pages expose historical index data, India VIX history and derivatives archives. The derivatives reports include contract-wise price-volume data and daily/monthly reports.
- NSE's current contract-information pages expose contract specifications and permitted lot-size information, which must be versioned because contract specifications change through time.
- NSE separately offers paid EOD and historical order/trade datasets for F&O and other segments. These are the candidate source for higher-resolution execution research.
- RBI publishes Treasury-bill auction yields and related interest-rate statistics that can supply a risk-free-rate proxy.
- The Kaggle NIFTY dataset provides NIFTY index and India VIX files suitable for a separate descriptive/stylized-fact research layer, subject to provenance and quality checks.

## Critical data-availability finding

The public NSE option-chain page is an interactive current-market interface and provides a downloadable current chain, but it should **not** be assumed to provide a complete historical bid/ask archive for every option timestamp needed by Tracks A–C. Therefore:

1. Public EOD derivatives data can support the first data-engineering and stylized-facts layer.
2. Kaggle can supplement the underlying/index and India-VIX layers for descriptive research after snapshot validation.
3. Full historical bid/ask/depth data required for rigorous surface calibration, executable VRP measurement and microstructure studies may require licensed NSE historical order/trade data and/or a licensed vendor dataset.
4. No Track A–C backtest should be labelled executable if it uses midpoint prices without a documented historical quote source and fill model.

## Minimum field contract

### Underlying

- `timestamp`
- `instrument_id`
- `open`, `high`, `low`, `close`
- `volume` when available
- corporate-action-adjustment metadata
- trading-session/calendar identifier

### Options

- `timestamp`
- `underlying_id`
- `expiry`
- `strike`
- `option_type`
- `bid`, `ask`, `mid`
- `last_price`
- `volume`
- `open_interest`
- `quote_size` / depth when available
- `contract_multiplier` / lot size with effective date
- settlement price
- data-source timestamp and availability timestamp

### Rates / volatility context

- risk-free rate term structure or documented proxy
- India VIX
- trading calendar
- corporate/event calendar where used

### Execution

- bid/ask spread
- quote depth when available
- trade prints where licensed
- transaction taxes/fees
- brokerage schedule
- latency assumption
- impact model inputs
- partial-fill assumptions

## Point-in-time rule

Every observation must have an `available_at` timestamp. Features and decisions may use only information whose `available_at` is not later than the simulated decision time. Contract metadata must also be joined as-of its effective date.

For Kaggle snapshots, the dataset download/availability timestamp is recorded separately from the observation timestamp. The latter must never be interpreted as proof of when the observation was publicly knowable in the original market.

## Phase 2 acquisition sequence

1. Adopt the Kaggle NIFTY/India-VIX snapshot as the first external research source for the underlying/context layer.
2. Download the exact Kaggle dataset version locally and record its hash and acquisition timestamp.
3. Run the Kaggle adapter, quality diagnostics and immutable snapshot manifest.
4. Continue NSE F&O EOD and contract-master validation for derivatives-specific fields.
5. Obtain a representative sample of historical option-chain/quote data and test whether it satisfies the field contract.
6. If not, evaluate licensed NSE historical order/trade data and approved vendors.
7. Freeze the first immutable research snapshot only after schema, timestamp, contract-master and quote-hygiene tests pass.

## Data acceptance gate

A dataset cannot enter formal experiments until:

- source/licence is documented;
- schema is versioned;
- timestamps are validated;
- duplicates are handled deterministically;
- contract identifiers and effective dates are reconciled;
- missing/stale/crossed quotes are measured where quote data exist;
- corporate actions and lot-size changes are handled;
- a point-in-time reconstruction test passes or the source is explicitly classified as descriptive-only;
- a cryptographic snapshot identifier is recorded.
