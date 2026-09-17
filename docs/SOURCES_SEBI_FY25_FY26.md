# SEBI FY25–FY26 Source Registry — Indian Equity Derivatives

Last reviewed: 2026-09-18

## Purpose

This registry records the current primary Indian-market evidence used as background/context for the research program. These observations **do not establish that any research hypothesis is true or tradable**. They define the market population, period, behaviour and cost environment that the repository must respect.

## Source S1 — SEBI profitability study

- **Source ID:** S1
- **Title:** Study - Profitability of Individual Traders in the Equity Derivatives Segment (FY25–FY26)
- **Publisher:** Securities and Exchange Board of India (SEBI), Department of Economic and Policy Analysis
- **Publication date:** 20 August 2026
- **Official landing page:** https://www.sebi.gov.in/reports-and-statistics/research/aug-2026/study-profitability-of-individual-traders-in-the-equity-derivatives-segment-fy25-fy26-_103835.html
- **Primary PDF:** https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1787233506209.pdf
- **Population/sample:** profitability study based on information collected from the top 15 brokers; SEBI's press release states this sample represents approximately 90% of individual investors in the segment.
- **Period:** FY25–FY26, with selected historical comparisons.

### Claim-level extraction

| Claim ID | Statistic / finding | Definition / caveat | Research use |
|---|---|---|---|
| S1-C01 | Active individual traders declined 18% YoY, from 106.2 lakh in FY25 to 87.5 lakh in FY26. | Active individual traders; the report notes individual traders include retail and HNI categories and specified individual entities. | Market participation context; data-universe planning |
| S1-C02 | Aggregate net losses declined 18% to ₹91,685 crore in FY26 from revised ₹1.12 lakh crore in FY25. | FY25 revised because broker sample expanded from 13 to 15. | Cost/outcome context; not a strategy-performance benchmark |
| S1-C03 | 87.7% of individual traders were loss-making in FY26 versus 90.9% in FY25. | Loss-maker definition is report-specific; do not generalize to all market participants or all trading strategies. | Market outcome context |
| S1-C04 | Average loss per person increased 2% from ₹1.13 lakh to ₹1.17 lakh. | Average loss per individual trader as reported. | Outcome context |
| S1-C05 | Options accounted for 92% of aggregate individual losses. | Individual EDS losses; product-level attribution. | Track A/B/C market-structure context |
| S1-C06 | Individual transaction costs were about ₹25,000 crore in each of FY25 and FY26. | Reported transaction costs; exact cost composition varies by year. | Track G cost-model calibration/context |
| S1-C07 | STT paid by individuals rose 35%, from ₹4,920 crore in FY25 to ₹6,645 crore in FY26. | Statutory transaction cost; STT increased effective 1 Oct 2024. | Track G cost model |
| S1-C08 | About 59% of index-options turnover occurred on 0DTE in FY26; 75% within 1DTE and 97% within 7DTE. | 0DTE = contracts traded on expiry date; these are turnover shares, not trader shares. | Option data prioritisation; expiry-aware execution modelling |
| S1-C09 | About 35% of FY25–FY26 EDS traders had no underlying equity portfolio; around 78% had portfolios below ₹1 lakh. | Equity portfolio means market value of equity shares and equity-oriented mutual funds in demat form. | Participant segmentation context |
| S1-C10 | Small-portfolio traders below ₹1 lakh accounted for about 70% of total losses while contributing about 51% of turnover. | Combined FY25–FY26 finding. | Participant segmentation; robustness stratification |
| S1-C11 | Loss incidence declined with portfolio size: 93% for traders with no equity holding versus 58% for those above ₹10 crore. | Association; not a causal estimate. | Stratified analysis; hypothesis generation only |
| S1-C12 | 99.3% of individuals traded options at least once; 93% traded only options. | FY26 product participation. | Universe design / option-market focus |

## Source S2 — SEBI trading-behaviour study

- **Source ID:** S2
- **Title:** Study - Trading Behaviour of Individual Traders in the Equity Derivatives Segment (FY25–FY26)
- **Publisher:** Securities and Exchange Board of India (SEBI), Department of Economic and Policy Analysis
- **Publication date:** 20 August 2026
- **Official landing page:** https://www.sebi.gov.in/reports-and-statistics/research/aug-2026/study-trading-behaviour-of-individual-traders-in-the-equity-derivatives-segment-fy25-fy26-_103836.html
- **Primary report PDF:** https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1787233601328.pdf
- **Study design:** SEBI's official press release states that the trading-behaviour study is primarily based on a random sample of 5,000 individual traders, alongside the profitability sample from the top 15 brokers.

### Claim-level extraction from SEBI's official press release summarising S2

| Claim ID | Statistic / finding | Definition / caveat | Research use |
|---|---|---|---|
| S2-C01 | Nearly 97% of traders predominantly followed option-buying strategies; around 2% were classified as majorly options sellers. | Strategy classification is SEBI's study-specific classification. | Track A/C hypothesis stratification |
| S2-C02 | Options sellers were the only strategy group with positive median returns on capital employed in FY26. | Median return on capital employed; not proof of causal superiority or future profitability. | Hypothesis-generation context only |
| S2-C03 | Higher trading intensity was associated with higher loss rates across several dimensions. | Trading intensity includes days traded, turnover, turnover relative to capital and turnover relative to equity portfolio. Association, not causal proof. | Track G / behavioural covariates |
| S2-C04 | Younger, lower-income and smaller-portfolio traders showed higher trading intensity relative to financial resources. | Demographic/portfolio association; income analysis has study-specific data availability limitations. | Stratification / robustness |
| S2-C05 | Among traders with losses in two consecutive years who continued trading, around 90% incurred losses again the following year. | Persistence statistic for the study population; not a universal individual prediction. | Behavioural persistence context |
| S2-C06 | Approximately 85% of trader-quarter observations were loss-making and around 15% profitable. | Trader-quarter observation unit. | Avoid confusing with unique-trader loss rate |
| S2-C07 | Among traders with both profitable and loss-making quarters, nearly 79% had average gains in profitable quarters smaller than average losses in loss-making quarters. | Conditional subgroup. | Distributional outcome context |
| S2-C08 | Between 28–40% of traders active in one quarter did not trade in the immediately following quarter; among discontinuers, about 86–89% had lost in the previous quarter. | Range varies by quarter. | Participation/persistence modelling |

## Source S3 — SEBI official press release

- **Source ID:** S3
- **Title:** PR No.50/2026 — SEBI Studies Indicate Key Trends in Retail Participation, Trading Behaviour and Profitability in the Equity Derivatives
- **Publication date:** 20 August 2026
- **Primary PDF:** https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1787236407005.pdf
- **Role:** Primary SEBI summary source used to record the trading-behaviour findings above while preserving the exact study-design caveats.

## Interpretation rules

1. These are **descriptive/associational findings**, unless the source explicitly establishes a causal design.
2. FY25 and FY26 figures must remain year-specific; do not combine or relabel them without the report's definition.
3. Individual traders are not equivalent to all market participants.
4. Gross trading P&L is not net investable return; transaction costs, open positions and product definitions matter.
5. These findings motivate data segmentation and cost modelling but cannot be used as evidence that any Track A–H strategy has positive expectancy.
6. Where a statistic is from the press release rather than direct extraction from the S2 PDF, the registry labels that provenance explicitly.
