"""Simple coverage and integrity checks on raw public facts."""
from __future__ import annotations
from ingestion.company_universe import requested_tickers

def coverage(conn) -> dict:
    expected = len(requested_tickers())
    mapped = conn.execute("SELECT COUNT(*) FROM raw_public.company_registry").fetchone()[0]
    facts = conn.execute("SELECT COUNT(*) FROM raw_public.sec_company_facts").fetchone()[0]
    prices = conn.execute("SELECT COUNT(*) FROM raw_public.market_prices").fetchone()[0]
    errors = conn.execute("SELECT COUNT(*) FROM raw_public.ingestion_runs WHERE status='failed'").fetchone()[0]
    return {"expected_companies": expected, "mapped_companies": mapped,
            "sec_facts": facts, "market_prices": prices, "failed_jobs": errors,
            "unmapped_companies": max(0, expected-mapped)}

def assert_integrity(conn):
    for table, key in [("company_registry","ticker"),("sec_company_facts","fact_key"),("market_prices","price_key"),("macro_observations","observation_key")]:
        n = conn.execute(f"SELECT COUNT(*) FROM raw_public.{table} WHERE {key} IS NULL").fetchone()[0]
        if n:
            raise ValueError(f"{table} has {n} null primary keys")
