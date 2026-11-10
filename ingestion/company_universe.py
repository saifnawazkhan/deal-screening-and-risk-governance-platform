"""Config-driven 40-company technology universe with authoritative SEC CIK lookup."""
from __future__ import annotations
import json
from ingestion.common import config, fetch

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

def requested_tickers() -> list[tuple[str, str]]:
    groups = config("company_universe.yaml")["companies"]
    items = [(ticker.upper(), subsector) for subsector, tickers in groups.items() for ticker in tickers]
    if len(items) != len({ticker for ticker, _ in items}):
        raise ValueError("Duplicate company ticker in universe")
    if not 30 <= len(items) <= 50:
        raise ValueError("Company universe must contain 30–50 tickers")
    return items

def resolve_registry(sec_headers: dict, fetcher=fetch) -> tuple[list[dict], list[str], bytes, str]:
    body, url = fetcher(TICKERS_URL, headers=sec_headers)
    registry = json.loads(body)
    lookup = {entry["ticker"].upper(): entry for entry in registry.values()}
    resolved, missing = [], []
    for ticker, subsector in requested_tickers():
        item = lookup.get(ticker)
        if item is None:
            missing.append(ticker)
        else:
            resolved.append({"ticker": ticker, "cik": str(item["cik_str"]).zfill(10),
                             "company_name": item["title"], "subsector": subsector,
                             "source_url": url})
    return resolved, missing, body, url
