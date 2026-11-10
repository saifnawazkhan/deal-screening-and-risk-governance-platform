"""DuckDB raw-public storage with idempotent keys and audit logging."""
from __future__ import annotations
import json
import duckdb
from ingestion.common import utc_now, digest

SCHEMAS = {
"company_registry": "ticker VARCHAR PRIMARY KEY, cik VARCHAR, company_name VARCHAR, subsector VARCHAR, source_url VARCHAR, loaded_at VARCHAR",
"sec_company_facts": "fact_key VARCHAR PRIMARY KEY, cik VARCHAR, taxonomy VARCHAR, tag VARCHAR, unit VARCHAR, value DOUBLE, start_date VARCHAR, end_date VARCHAR, filed_date VARCHAR, form VARCHAR, fiscal_year INTEGER, fiscal_period VARCHAR, frame VARCHAR, accession VARCHAR, source_url VARCHAR, loaded_at VARCHAR",
"market_prices": "price_key VARCHAR PRIMARY KEY, ticker VARCHAR, price_date VARCHAR, close_price DOUBLE, adjusted_close_price DOUBLE, currency VARCHAR, source_url VARCHAR, loaded_at VARCHAR",
"macro_observations": "observation_key VARCHAR PRIMARY KEY, series_id VARCHAR, observation_date VARCHAR, value DOUBLE, unit VARCHAR, source_url VARCHAR, loaded_at VARCHAR",
"precedent_deal_sources": "deal_key VARCHAR PRIMARY KEY, acquirer VARCHAR, target VARCHAR, announcement_date VARCHAR, source_url VARCHAR, consideration_usd DOUBLE, currency VARCHAR, notes VARCHAR, loaded_at VARCHAR",
"ingestion_runs": "run_id VARCHAR, dataset VARCHAR, entity VARCHAR, status VARCHAR, row_count INTEGER, error_message VARCHAR, started_at VARCHAR, finished_at VARCHAR",
"source_snapshots": "snapshot_key VARCHAR PRIMARY KEY, dataset VARCHAR, entity VARCHAR, source_url VARCHAR, retrieved_at VARCHAR, sha256 VARCHAR, bytes_count INTEGER",
}
KEYS = {"company_registry": ("ticker",), "sec_company_facts": ("cik","taxonomy","tag","unit","start_date","end_date","filed_date","accession","form","frame","value"), "market_prices": ("ticker","price_date"), "macro_observations": ("series_id","observation_date"), "precedent_deal_sources": ("acquirer","target","announcement_date","source_url")}

def connect(path: str):
    conn = duckdb.connect(path)
    conn.execute("CREATE SCHEMA IF NOT EXISTS raw_public")
    for table, ddl in SCHEMAS.items():
        conn.execute(f"CREATE TABLE IF NOT EXISTS raw_public.{table} ({ddl})")
    return conn

def stable_key(values: list) -> str:
    return digest(json.dumps(values, default=str, separators=(",",":")).encode())

def upsert_rows(conn, table: str, rows: list[dict]) -> int:
    if table not in KEYS:
        raise ValueError("Unknown upsert table")
    if not rows:
        return 0
    cols = [c.strip().split()[0] for c in SCHEMAS[table].split(",")]
    pk = cols[0]
    inserted = 0
    for rec in rows:
        data = dict(rec)
        if pk not in data:
            data[pk] = stable_key([data.get(k) for k in KEYS[table]])
        data["loaded_at"] = utc_now()
        names = [col for col in cols if col in data]
        quoted = ", ".join(f'"{c}"' for c in names)
        placeholders = ", ".join("?" for _ in names)
        updates = ", ".join(f'"{c}" = excluded."{c}"' for c in names if c != pk)
        conn.execute(f"INSERT INTO raw_public.{table} ({quoted}) VALUES ({placeholders}) ON CONFLICT ({pk}) DO UPDATE SET {updates}", [data[c] for c in names])
        inserted += 1
    return inserted

def log_run(conn, run_id, dataset, entity, status, row_count, error_message, started_at):
    conn.execute("INSERT INTO raw_public.ingestion_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                 [run_id, dataset, entity, status, row_count, str(error_message)[:2000] if error_message else None, started_at, utc_now()])

def log_snapshot(conn, dataset, entity, url, body):
    checksum = digest(body)
    key = stable_key([dataset, entity, checksum])
    conn.execute("INSERT INTO raw_public.source_snapshots VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT (snapshot_key) DO NOTHING",
                 [key, dataset, entity, url, utc_now(), checksum, len(body)])
