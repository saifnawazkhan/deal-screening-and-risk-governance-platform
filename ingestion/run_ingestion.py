"""CLI entrypoint. Network calls are opt-in and failures are audited."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import uuid
from datetime import date, timedelta
from ingestion.common import config, utc_now
from ingestion.company_universe import resolve_registry
from ingestion.sec_edgar import sec_headers, company_facts
from ingestion.market_data import download_prices
from ingestion.fred import download_fred, SERIES
from ingestion.precedent_deals import load_curated_deals
from ingestion.warehouse import connect, upsert_rows, log_run, log_snapshot
from quality.public_data_checks import coverage, assert_integrity

def execute(conn, run_id, dataset, entity, work):
    start = utc_now()
    try:
        rows, raw, url = work()
        n = upsert_rows(conn, dataset, rows)
        if raw is not None:
            log_snapshot(conn, dataset, entity, url, raw)
        log_run(conn, run_id, dataset, entity, "success", n, None, start)
        return True
    except Exception as exc:
        log_run(conn, run_id, dataset, entity, "failed", 0, repr(exc), start)
        print(f"FAILED {dataset}/{entity}: {exc}")
        return False

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=os.getenv("DUCKDB_PATH", "local_warehouse.duckdb"))
    parser.add_argument("--live", action="store_true", help="Explicitly allow public network retrieval")
    parser.add_argument("--skip-prices", action="store_true")
    parser.add_argument("--skip-fred", action="store_true")
    parser.add_argument("--skip-sec", action="store_true")
    parser.add_argument("--max-companies", type=int, default=40)
    args = parser.parse_args(argv)
    conn = connect(args.db)
    if not args.live:
        print("No network requests made. Pass --live to ingest public data.")
        print(json.dumps(coverage(conn), indent=2))
        return 0
    user_agent = os.getenv("SEC_USER_AGENT", "")
    try:
        headers = sec_headers(user_agent)
    except ValueError as exc:
        print(exc)
        return 2
    run_id = str(uuid.uuid4())
    start = utc_now()
    try:
        companies, missing, raw, url = resolve_registry(headers)
        upsert_rows(conn, "company_registry", companies)
        log_snapshot(conn, "company_registry", "SEC", url, raw)
        log_run(conn, run_id, "company_registry", "SEC", "success", len(companies), None, start)
        for ticker in missing:
            log_run(conn, run_id, "company_registry", ticker, "failed", 0, "Ticker absent from SEC registry", start)
    except Exception as exc:
        log_run(conn, run_id, "company_registry", "SEC", "failed", 0, repr(exc), start)
        print(f"Company registry retrieval failed: {exc}")
        return 1
    companies = companies[:args.max_companies]
    for company in companies:
        ticker, cik = company["ticker"], company["cik"]
        if not args.skip_sec:
            execute(conn, run_id, "sec_company_facts", ticker,
                    lambda cik=cik: company_facts(cik, headers))
        if not args.skip_prices:
            def get_prices(ticker=ticker):
                end = date.today() + timedelta(days=1)
                start_date = end - timedelta(days=365 * 4)
                rows = download_prices(ticker, start_date.isoformat(), end.isoformat())
                return rows, None, f"https://finance.yahoo.com/quote/{ticker}/history/"
            execute(conn, run_id, "market_prices", ticker, get_prices)
    if not args.skip_fred:
        for series in SERIES:
            execute(conn, run_id, "macro_observations", series,
                    lambda series=series: download_fred(series))
    try:
        deals = load_curated_deals(Path("data/reference/precedent_deals.csv"))
        upsert_rows(conn, "precedent_deal_sources", deals)
        log_run(conn, run_id, "precedent_deal_sources", "curated_csv", "success", len(deals), None, utc_now())
    except Exception as exc:
        log_run(conn, run_id, "precedent_deal_sources", "curated_csv", "failed", 0, repr(exc), utc_now())
    assert_integrity(conn)
    result = coverage(conn)
    print(json.dumps(result, indent=2))
    return 1 if result["failed_jobs"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
