# Data Platform and Governance

Design a lakehouse with strong governance, lineage, and quality SLAs.

## Architecture
- Medallion layers: bronze (ingest), silver (curate), gold (serve)
- Catalog/lineage: DataHub, OpenMetadata, or Unity Catalog
- Ingestion: connectors for custodians, banks, OMS/EMS, market data

## Governance
- Data classification and PII handling
- Retention schedules and legal holds
- Data quality checks, SLAs, and alerting

## Privacy and Access
- Row/column-level security, dynamic masking
- Differential privacy and privacy-preserving analytics where feasible
