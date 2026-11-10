"""Shared network, config and provenance utilities."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]

def config(name: str) -> dict:
    with (ROOT / "config" / name).open(encoding="utf-8") as f:
        return yaml.safe_load(f)

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def fetch(url: str, *, headers: dict | None = None, attempts: int = 3, timeout: int = 30) -> tuple[bytes, str]:
    """HTTP fetch with bounded retries; raise rather than fabricate fallback data."""
    last = None
    for attempt in range(attempts):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            if response.status_code in (429, 500, 502, 503, 504):
                response.raise_for_status()
            response.raise_for_status()
            return response.content, response.url
        except requests.RequestException as exc:
            last = exc
            if attempt + 1 < attempts:
                time.sleep(min(2 ** attempt, 4))
    raise RuntimeError(f"Unable to retrieve {url}: {last}")

def json_bytes(data: object) -> bytes:
    return json.dumps(data, sort_keys=True, default=str).encode("utf-8")
