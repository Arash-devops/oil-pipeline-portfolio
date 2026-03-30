-- =============================================================================
-- 01-schemas.sql
-- Create logical schemas for separation of concerns:
--   staging   → raw data landing zone (ingest, validate here)
--   warehouse → dimensional model (cleaned, conformed data)
--   analytics → pre-aggregated metrics and materialized views
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS warehouse;
CREATE SCHEMA IF NOT EXISTS analytics;

COMMENT ON SCHEMA staging   IS 'Raw data landing zone. Data arrives here first, gets validated, then promoted to warehouse.';
COMMENT ON SCHEMA warehouse IS 'Dimensional model (star schema). Fact tables and dimension tables. Source of truth for all reporting.';
COMMENT ON SCHEMA analytics IS 'Pre-aggregated summaries and derived metrics. Optimised for fast dashboard and API queries.';
