import io
import json
from pathlib import Path
import pandas as pd
import pytest
from ingestion.company_universe import requested_tickers, resolve_registry
from ingestion.sec_edgar import company_facts, sec_headers
from ingestion.fred import parse_fred_csv
from ingestion.market_data import normalize_prices
from ingestion.precedent_deals import load_curated_deals
from ingestion.warehouse import connect, upsert_rows
from quality.public_data_checks import coverage

def test_full_universe_has_unique_40_companies():
    tickers = [t for t, _ in requested_tickers()]
    assert len(tickers) == 40
    assert len(set(tickers)) == 40

def test_sec_headers_reject_placeholder():
    with pytest.raises(ValueError):
        sec_headers("Your Name your-email@example.com")

def test_cik_mapping_and_missing_ticker():
    body = json.dumps({"0": {"ticker": "MSFT", "cik_str": 789019, "title": "Microsoft Corp"}}).encode()
    mapped, missing, _, _ = resolve_registry({"User-Agent": "Test test@domain.org"}, lambda *a, **k: (body, "https://www.sec.gov/test"))
    assert mapped[0]["cik"] == "0000789019"
    assert len(missing) == 39

def test_sec_preserves_filing_and_units():
    payload = {"facts":{"us-gaap":{"Revenues":{"units":{"USD":[{"val":100,"start":"2024-01-01","end":"2024-12-31","accn":"123","filed":"2025-01-31"}]}}}}}
    rows, _, _ = company_facts("789019", {}, lambda *a, **k: (json.dumps(payload).encode(), "https://data.sec.gov/test"))
    assert rows[0]["unit"] == "USD" and rows[0]["accession"] == "123"

def test_fred_missing_dot_and_units():
    rows = parse_fred_csv("DGS10", b"DATE,DGS10\n2025-01-01,.\n2025-01-02,4.5\n", "https://fred.stlouisfed.org/")
    assert len(rows) == 1 and rows[0]["value"] == 4.5 and rows[0]["unit"] == "percent"

def test_price_rejects_empty_and_bad_values():
    with pytest.raises(ValueError):
        normalize_prices("MSFT", pd.DataFrame())
    frame = pd.DataFrame({"Close":[0,100.0],"Adj Close":[0,99.0]},index=pd.to_datetime(["2025-01-01","2025-01-02"]))
    assert normalize_prices("MSFT", frame)[0]["adjusted_close_price"] == 99.0

def test_missing_curated_deals_are_not_fabricated(tmp_path):
    assert load_curated_deals(tmp_path / "not-present.csv") == []

def test_idempotent_duckdb_ingestion(tmp_path):
    conn = connect(str(tmp_path / "test.duckdb"))
    rec = {"ticker":"MSFT","cik":"0000789019","company_name":"Microsoft","subsector":"software","source_url":"https://sec.gov/"}
    upsert_rows(conn,"company_registry",[rec])
    upsert_rows(conn,"company_registry",[rec])
    assert conn.execute("SELECT COUNT(*) FROM raw_public.company_registry").fetchone()[0] == 1
    assert coverage(conn)["expected_companies"] == 40

def test_duplicate_sec_fact_is_idempotent(tmp_path):
    conn = connect(str(tmp_path / "test.duckdb"))
    fact = {"cik":"0000789019","taxonomy":"us-gaap","tag":"Revenues","unit":"USD","value":100.0,"start_date":"2024-01-01","end_date":"2024-12-31","filed_date":"2025-01-31","form":"10-K","fiscal_year":2024,"fiscal_period":"FY","frame":None,"accession":"123","source_url":"https://data.sec.gov/"}
    upsert_rows(conn,"sec_company_facts",[fact])
    upsert_rows(conn,"sec_company_facts",[fact])
    assert conn.execute("SELECT COUNT(*) FROM raw_public.sec_company_facts").fetchone()[0] == 1
