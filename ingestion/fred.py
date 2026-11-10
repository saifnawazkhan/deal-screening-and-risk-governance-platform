"""Public FRED CSV observations; no API key required for graph CSV endpoint."""
from __future__ import annotations
import csv
import io
from datetime import date
from ingestion.common import fetch

SERIES = {"DGS10": "10-year US Treasury constant maturity yield", "DGS2": "2-year US Treasury constant maturity yield", "DFF": "Effective federal funds rate"}

def parse_fred_csv(series_id: str, content: bytes, source_url: str) -> list[dict]:
    if series_id not in SERIES:
        raise ValueError("Unsupported FRED series")
    rows = []
    for rec in csv.DictReader(io.StringIO(content.decode("utf-8-sig"))):
        day = rec.get("DATE") or rec.get("observation_date")
        value = rec.get(series_id)
        if not day or value in (None, "", "."):
            continue
        date.fromisoformat(day)
        rows.append({"series_id": series_id, "observation_date": day, "value": float(value),
                     "unit": "percent", "source_url": source_url})
    return rows

def download_fred(series_id: str, fetcher=fetch) -> tuple[list[dict], bytes, str]:
    if series_id not in SERIES:
        raise ValueError("Unsupported FRED series")
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    body, final_url = fetcher(url)
    return parse_fred_csv(series_id, body, final_url), body, final_url
