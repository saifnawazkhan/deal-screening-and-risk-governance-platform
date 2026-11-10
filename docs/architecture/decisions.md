# Architecture decisions

- Shared DuckDB warehouse, separate public and synthetic schemas.
- dbt for transformation and SQL quality tests.
- Prefect rather than Airflow for simpler local development.
- Tableau for dashboarding.
- All synthetic position tables use the `synthetic_` prefix.
- All illustrative thresholds and finance assumptions are stored in YAML.
- Phase 1 will validate technology issuer coverage, units and source provenance.
- No claim of regulatory compliance, production readiness or investment advice.
