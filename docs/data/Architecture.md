# Data Platform Architecture

## Overview
- Lakehouse across bronze/silver/gold with governed access
- Streaming + batch ingestion with CDC where available

## Storage and Compute
- Object storage as system of record
- Warehouse/SQL engine for serving (e.g., Databricks, BigQuery, Snowflake)

## Interfaces
- ELT pipelines, dbt or equivalent for transformations
- Semantic layer for BI/portal
