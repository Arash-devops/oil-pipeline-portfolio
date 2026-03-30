-- =============================================================================
-- 05-analytics-tables.sql
-- Pre-aggregated analytics tables.
-- Populated / refreshed by stored procedures:
--   analytics.sp_aggregate_monthly()
--   analytics.sp_calculate_metrics()
-- =============================================================================

-- ---------------------------------------------------------------------------
-- analytics.monthly_summary
-- Pre-aggregated monthly stats per commodity.
-- ---------------------------------------------------------------------------
CREATE TABLE analytics.monthly_summary (
    summary_key         BIGSERIAL       NOT NULL,
    commodity_key       INTEGER         NOT NULL,
    year                SMALLINT        NOT NULL,
    month               SMALLINT        NOT NULL,
    avg_close           DECIMAL(12,4),
    min_close           DECIMAL(12,4),
    max_close           DECIMAL(12,4),
    avg_volume          BIGINT,
    total_volume        BIGINT,
    volatility          DECIMAL(8,4),   -- std dev of daily close prices within the month
    trading_days        SMALLINT,
    monthly_return_pct  DECIMAL(8,4),   -- (last_close - first_close) / first_close * 100
    updated_at          TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_monthly_summary
        PRIMARY KEY (summary_key),

    CONSTRAINT uq_monthly_summary_natural
        UNIQUE (commodity_key, year, month),

    CONSTRAINT fk_monthly_commodity
        FOREIGN KEY (commodity_key)
        REFERENCES warehouse.dim_commodity(commodity_key)
        ON DELETE CASCADE,

    CONSTRAINT chk_monthly_month CHECK (month BETWEEN 1 AND 12),
    CONSTRAINT chk_monthly_year  CHECK (year  BETWEEN 2000 AND 2100)
);

COMMENT ON TABLE  analytics.monthly_summary IS 'Pre-aggregated monthly OHLCV statistics per commodity. Refreshed by sp_aggregate_monthly().';
COMMENT ON COLUMN analytics.monthly_summary.volatility         IS 'Standard deviation of daily closing prices within the month. Higher = more volatile.';
COMMENT ON COLUMN analytics.monthly_summary.trading_days       IS 'Count of rows in fact_oil_prices for this commodity/month combination.';
COMMENT ON COLUMN analytics.monthly_summary.monthly_return_pct IS '(last_close_of_month - first_close_of_month) / first_close_of_month * 100.';


-- ---------------------------------------------------------------------------
-- analytics.price_metrics
-- Per-day derived technical indicators per commodity.
-- ---------------------------------------------------------------------------
CREATE TABLE analytics.price_metrics (
    metric_key          BIGSERIAL       NOT NULL,
    date_key            INTEGER         NOT NULL,
    commodity_key       INTEGER         NOT NULL,
    ma_7                DECIMAL(12,4),  -- 7-day simple moving average
    ma_30               DECIMAL(12,4),  -- 30-day simple moving average
    ma_90               DECIMAL(12,4),  -- 90-day simple moving average
    volatility_30d      DECIMAL(8,4),   -- 30-day rolling standard deviation
    rsi_14              DECIMAL(6,2),   -- 14-day Relative Strength Index (0–100)
    price_vs_ma30_pct   DECIMAL(8,4),   -- (close - ma_30) / ma_30 * 100
    updated_at          TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_price_metrics
        PRIMARY KEY (metric_key),

    CONSTRAINT uq_price_metrics_natural
        UNIQUE (date_key, commodity_key),

    CONSTRAINT fk_metrics_date
        FOREIGN KEY (date_key)
        REFERENCES warehouse.dim_date(date_key)
        ON DELETE CASCADE,

    CONSTRAINT fk_metrics_commodity
        FOREIGN KEY (commodity_key)
        REFERENCES warehouse.dim_commodity(commodity_key)
        ON DELETE CASCADE,

    CONSTRAINT chk_metrics_rsi CHECK (rsi_14 IS NULL OR rsi_14 BETWEEN 0 AND 100)
);

COMMENT ON TABLE  analytics.price_metrics IS 'Per-day technical indicators per commodity. Populated by sp_calculate_metrics(). Requires at least 90 rows of history for all columns to be non-NULL.';
COMMENT ON COLUMN analytics.price_metrics.ma_7             IS '7-day simple moving average of closing prices.';
COMMENT ON COLUMN analytics.price_metrics.ma_30            IS '30-day simple moving average. Commonly used as trend indicator.';
COMMENT ON COLUMN analytics.price_metrics.ma_90            IS '90-day simple moving average. Long-term trend.';
COMMENT ON COLUMN analytics.price_metrics.volatility_30d   IS '30-day rolling standard deviation of closing prices. Proxy for risk.';
COMMENT ON COLUMN analytics.price_metrics.rsi_14           IS '14-period Relative Strength Index. > 70 = overbought, < 30 = oversold.';
COMMENT ON COLUMN analytics.price_metrics.price_vs_ma30_pct IS 'Percentage distance of closing price from its 30-day MA. Positive = above MA.';
