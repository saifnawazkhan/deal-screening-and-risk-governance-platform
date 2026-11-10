"""SEC Company Facts: preserve reported tags, units, periods and filing lineage."""
from __future__ import annotations
import json
from ingestion.common import fetch

def sec_headers(user_agent: str) -> dict:
    if not user_agent or "example.com" in user_agent or "@" not in user_agent:
        raise ValueError("Set SEC_USER_AGENT to a real name and contact email in .env")
    return {"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate", "Accept": "application/json"}

def company_facts(cik: str, headers: dict, fetcher=fetch) -> tuple[list[dict], bytes, str]:
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{str(cik).zfill(10)}.json"
    body, final_url = fetcher(url, headers=headers)
    payload = json.loads(body)
    rows = []
    for taxonomy, concepts in payload.get("facts", {}).items():
        for tag, concept in concepts.items():
            for unit, observations in concept.get("units", {}).items():
                for obs in observations:
                    if obs.get("val") is None or not obs.get("end") or not obs.get("accn"):
                        continue
                    rows.append({"cik": str(cik).zfill(10), "taxonomy": taxonomy, "tag": tag,
                                 "unit": unit, "value": obs["val"], "start_date": obs.get("start"),
                                 "end_date": obs["end"], "filed_date": obs.get("filed"),
                                 "form": obs.get("form"), "fiscal_year": obs.get("fy"),
                                 "fiscal_period": obs.get("fp"), "frame": obs.get("frame"),
                                 "accession": obs["accn"], "source_url": final_url})
    return rows, body, final_url
