# Public precedent deals (curated, not invented)

An optional `precedent_deals.csv` may be added with columns:

`acquirer,target,announcement_date,source_url,consideration_usd,currency,notes`

Only enter documented deals from public filings or press releases. Leave `consideration_usd` blank if the source does not provide a defensible amount. The ingestion pipeline accepts an absent file as zero deals, never fabricates transactions. Phase 3 will provide valuation-ready precedent analysis.
