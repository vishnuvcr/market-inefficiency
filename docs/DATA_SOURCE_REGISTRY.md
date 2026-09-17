# Data Source Registry — Phase 2

Last reviewed: 2026-09-18

## Objective

Define a reproducible, point-in-time data stack before any formal strategy backtest. A source being publicly discoverable does **not** mean it contains every field required by a hypothesis.

## Source tiers

| Source ID | Provider | Data | Access | Phase 2 role | Status |
|---|---|---|---|---|---|
| DS-NSE-CM | NSE India | Equity/underlying historical price-volume and reports | Public historical pages/reports | Underlying OHLCV, volume, corporate-action reconciliation | READY FOR INGESTION DESIGN |
| DS-NSE-FO-EOD | NSE India | Equity-derivatives contract-wise price/volume, OI and reports | Public historical reports; some datasets are downloadable | Futures/options EOD baseline, OI, settlement/turnover | READY FOR INGESTION DESIGN |
| DS-NSE-CONTRACT | NSE India | Contract specifications, underlyings, lot-size/strike information | Public | Point-in-time contract master and instrument history | READY FOR INGESTION DESIGN |
| DS-NSE-VIX | NSE India | India VIX historical values and methodology | Public | Implied-volatility context variable | READY FOR INGESTION DESIGN |
| DS-NSE-OTC | NSE India | Historical order/trade data for F&O | Paid subscription | Intraday execution/microstructure; quote/trade reconstruction where licensed | ACCESS DECISION REQUIRED |
| DS-RBI-RF | RBI | Treasury-bill and related interest-rate observations | Public RBI publications/statistics | Risk-free-rate proxy curve | READY FOR INGESTION DESIGN |
| DS-VENDOR-OPTIONS | Approved market-data vendor | Historical option quotes/order book with bid/ask/depth | Paid/vendor licence | Full VRP/SABR/jump surface research when EOD public data are insufficient | VENDOR SELECTION REQUIRED |

## Evidence supporting source availability

- NSE's historical-report pages expose historical index data, India VIX history and derivatives archives. The derivatives reports include contract-wise price-volume data and daily/monthly reports. 
- NSE's current contract-information pages expose contract specifications and permitted lot-size information, which must be versioned because contract specifications change through time.
- NSE separately offers paid EOD and historical order/trade datasets for F&O and other segments. These are the candidate source for higher-resolution execution research.
- RBI publishes Treasury-bill auction yields and related interest-rate statistics that can supply a risk-free-rate proxy.

## Critical data-availability finding

The public NSE option-chain page is an interactive current-market interface and provides a downloadable current chain, but it should **not** be assumed to provide a complete historical bid/ask archive for every option timestamp needed by Tracks A–C. Therefore:

1. Public EOD derivatives data can support the first data-engineering and stylized-facts layer.
2. Full historical bid/ask/depth data required for rigorous surface calibration, executable VRP measurement and microstructure studies may require licensed NSE historical order/trade data and/or a licensed vendor dataset.
3. No Track A–C backtest should be labelled executable if it uses midpoint prices without a documented historical quote source and fill model.

## Minimum field contract

### Underlying

- `timestamp`
- `instrument_id`
- `open`, `high`, `low`, `close`
- `volume`
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

## Phase 2 acquisition sequence

1. Build ingestion interfaces for public NSE EOD/contract/VIX sources.
2. Build a source adapter for RBI rate observations.
3. Obtain a representative sample of historical option-chain/quote data and test whether it satisfies the field contract.
4. If not, evaluate licensed NSE historical order/trade data and approved vendors.
5. Freeze the first immutable dataset snapshot only after schema, timestamp, contract-master and quote-hygiene tests pass.

## Data acceptance gate

A dataset cannot enter formal experiments until:

- source/licence is documented;
- schema is versioned;
- timestamps are validated;
- duplicates are handled deterministically;
- contract identifiers and effective dates are reconciled;
- missing/stale/crossed quotes are measured;
- corporate actions and lot-size changes are handled;
- a point-in-time reconstruction test passes;
- a cryptographic snapshot identifier is recorded.
