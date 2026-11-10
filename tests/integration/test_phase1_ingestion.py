from ingestion.warehouse import connect, log_run, log_snapshot
from quality.public_data_checks import assert_integrity

def test_run_and_snapshot_audit(tmp_path):
    conn = connect(str(tmp_path / "warehouse.duckdb"))
    log_run(conn, "test-run", "sec_company_facts", "MSFT", "failed", 0, "simulated HTTP 503", "2025-01-01T00:00:00Z")
    log_snapshot(conn, "company_registry", "SEC", "https://www.sec.gov", b"example")
    log_snapshot(conn, "company_registry", "SEC", "https://www.sec.gov", b"example")
    assert conn.execute("SELECT COUNT(*) FROM raw_public.ingestion_runs WHERE status='failed'").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM raw_public.source_snapshots").fetchone()[0] == 1
    assert_integrity(conn)
