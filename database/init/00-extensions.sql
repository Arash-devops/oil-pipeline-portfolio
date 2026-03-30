-- =============================================================================
-- 00-extensions.sql
-- Enable required PostgreSQL extensions
-- =============================================================================

-- Required for crosstab (PIVOT) queries in sample-queries.sql
CREATE EXTENSION IF NOT EXISTS tablefunc;

-- Required for UUID generation (future-proofing for API keys / correlation IDs)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Required for advanced statistical functions (percentile helpers, etc.)
-- pg_stat_statements for query performance monitoring
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- btree_gist for exclusion constraints on date ranges (useful for SCD Type 2)
CREATE EXTENSION IF NOT EXISTS btree_gist;

COMMENT ON EXTENSION tablefunc       IS 'Provides crosstab() function for pivot-style queries';
COMMENT ON EXTENSION "uuid-ossp"     IS 'UUID generation functions';
COMMENT ON EXTENSION pg_stat_statements IS 'Track query execution statistics';
COMMENT ON EXTENSION btree_gist      IS 'GiST index support for B-tree types, used for exclusion constraints';
