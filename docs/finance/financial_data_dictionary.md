# Raw financial data dictionary

- `cik`: SEC company identifier, 10-digit zero-padded text.
- `taxonomy` / `tag`: SEC XBRL namespace and original financial concept.
- `unit`: Original reported unit, e.g. USD or shares.
- `value`: Original numeric fact, not a standardized EBITDA calculation.
- `start_date` / `end_date`: Reported observation interval; a missing start can indicate an instant balance-sheet fact.
- `filed_date` / `accession`: Filing provenance and restatement traceability.
- `frame`: SEC frame where supplied; do not assume a missing frame is an error.
- `close_price`: Historical unadjusted close returned by Yahoo Finance.
- `adjusted_close_price`: Yahoo-adjusted close where supplied; not interchangeable with raw close.
- `macro_observations.value`: FRED rates stored in percentage points, not decimal fractions.
- `consideration_usd`: Only publicly supported deal consideration, not necessarily enterprise value.

Phase 2 will select comparable concepts, periods, as-of filing policies, and calculate annual metrics with documented logic.
