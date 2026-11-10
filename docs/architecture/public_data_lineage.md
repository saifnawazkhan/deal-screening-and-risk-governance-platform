# Phase 1 public-data lineage

| Dataset | Source | Original provenance |
|---|---|---|
| Company registry | SEC company_tickers.json | source URL, retrieved timestamp, SHA256 |
| Company facts | SEC companyfacts API | taxonomy, tag, unit, period, filing accession, source URL |
| Prices | yfinance/Yahoo | ticker, observation date, raw close and adjusted close (if supplied) |
| Rates | FRED CSV | series ID, observation date, percent unit, URL |
| Deals | Curated public announcement CSV | announcement date and required HTTPS evidence URL |

Data is written only to `raw_public`. Each attempt is recorded in `ingestion_runs`; successful SEC/FRED responses are hashed in `source_snapshots`. Yahoo history is third-party data, so do not infer that its data is exchange-certified.

Run `python -m ingestion.run_ingestion` for offline warehouse creation and coverage. Run `python -m ingestion.run_ingestion --live` only after setting a valid SEC_USER_AGENT. Internet-dependent execution can take time and encounter throttling.

**No issuer facts, prices, deal amounts or missing observations are generated or filled.** These are raw reported values, not comparable or restatement-adjusted analytical metrics.
