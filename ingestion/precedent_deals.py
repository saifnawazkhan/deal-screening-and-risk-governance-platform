"""Curated public deal evidence. Empty is honest; no invented deal consideration."""
from __future__ import annotations
import csv
from datetime import date
from pathlib import Path

FIELDS = {"acquirer", "target", "announcement_date", "source_url", "consideration_usd", "currency", "notes"}

def load_curated_deals(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not FIELDS.issubset(set(reader.fieldnames or [])):
            raise ValueError("Precedent file missing required fields")
        rows = []
        for rec in reader:
            date.fromisoformat(rec["announcement_date"])
            if not rec["source_url"].startswith("https://"):
                raise ValueError("Every deal requires an HTTPS public evidence URL")
            amount = rec["consideration_usd"].strip()
            if amount and float(amount) < 0:
                raise ValueError("Negative deal consideration")
            rec["consideration_usd"] = float(amount) if amount else None
            rows.append(rec)
        return rows
