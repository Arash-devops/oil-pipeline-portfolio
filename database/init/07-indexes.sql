-- =============================================================================
-- 07-indexes.sql
-- All indexes defined separately for clarity and easy tuning.
-- Strategy:
--   - Foreign keys always indexed (prevents sequential scans on JOINs)
--   - Composite indexes ordered by cardinality: high-cardinality column first
--   - Partial indexes where full-table scans of a filtered subset are common
-- Note: COMMENT ON INDEX requires schema-qualified names because indexes live
--       in the same namespace as their table, not in 'public'.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- warehouse.dim_date
-- ---------------------------------------------------------------------------
CREATE INDEX idx_dim_date_full_date
    ON warehouse.dim_date (full_date);

CREATE INDEX idx_dim_date_year_month
    ON warehouse.dim_date (year, month);

CREATE INDEX idx_dim_date_is_trading_day
    ON warehouse.dim_date (is_trading_day)
    WHERE is_trading_day = TRUE;

COMMENT ON INDEX warehouse.idx_dim_date_full_date      IS 'Supports WHERE full_date = x lookups (e.g. from application layer sending ISO dates).';
COMMENT ON INDEX warehouse.idx_dim_date_year_month     IS 'Supports monthly aggregation queries filtering on year and month.';
COMMENT ON INDEX warehouse.idx_dim_date_is_trading_day IS 'Partial index for quickly counting or filtering only trading days.';


-- ---------------------------------------------------------------------------
-- warehouse.dim_commodity
-- ---------------------------------------------------------------------------
CREATE INDEX idx_dim_commodity_id
    ON warehouse.dim_commodity (commodity_id);

CREATE INDEX idx_dim_commodity_current
    ON warehouse.dim_commodity (commodity_id, commodity_key)
    WHERE is_current = TRUE;

COMMENT ON INDEX warehouse.idx_dim_commodity_id      IS 'Supports lookup by ticker symbol (e.g. CL=F).';
COMMENT ON INDEX warehouse.idx_dim_commodity_current IS 'Partial index for current-version lookups. Keeps sp_upsert_oil_price fast.';


-- ---------------------------------------------------------------------------
-- warehouse.fact_oil_prices
-- ---------------------------------------------------------------------------
CREATE INDEX idx_fact_date_key
    ON warehouse.fact_oil_prices (date_key);

CREATE INDEX idx_fact_commodity_key
    ON warehouse.fact_oil_prices (commodity_key);

CREATE INDEX idx_fact_commodity_date
    ON warehouse.fact_oil_prices (commodity_key, date_key DESC);

CREATE INDEX idx_fact_source_key
    ON warehouse.fact_oil_prices (source_key);

COMMENT ON INDEX warehouse.idx_fact_date_key       IS 'Supports date range scans across all commodities.';
COMMENT ON INDEX warehouse.idx_fact_commodity_key  IS 'Supports commodity-centric GROUP BY queries.';
COMMENT ON INDEX warehouse.idx_fact_commodity_date IS 'Primary composite index. Ordered DESC on date_key for most-recent-first queries.';
COMMENT ON INDEX warehouse.idx_fact_source_key     IS 'Supports data quality queries comparing prices across sources.';


-- ---------------------------------------------------------------------------
-- staging.stg_oil_prices
-- ---------------------------------------------------------------------------
CREATE INDEX idx_stg_unprocessed
    ON staging.stg_oil_prices (loaded_at)
    WHERE is_processed = FALSE;

CREATE INDEX idx_stg_symbol_date
    ON staging.stg_oil_prices (symbol, trade_date);

COMMENT ON INDEX staging.idx_stg_unprocessed IS 'Partial index on the processing queue. Only unprocessed rows are indexed; shrinks automatically as records are processed.';
COMMENT ON INDEX staging.idx_stg_symbol_date IS 'Supports de-duplication checks when loading new data.';


-- ---------------------------------------------------------------------------
-- analytics.monthly_summary
-- ---------------------------------------------------------------------------
CREATE INDEX idx_monthly_commodity_year_month
    ON analytics.monthly_summary (commodity_key, year, month);

COMMENT ON INDEX analytics.idx_monthly_commodity_year_month IS 'Supports time-series queries on monthly summaries per commodity.';


-- ---------------------------------------------------------------------------
-- analytics.price_metrics
-- ---------------------------------------------------------------------------
CREATE INDEX idx_metrics_commodity_date
    ON analytics.price_metrics (commodity_key, date_key DESC);

COMMENT ON INDEX analytics.idx_metrics_commodity_date IS 'Supports time-series retrieval of metrics ordered most-recent-first.';
