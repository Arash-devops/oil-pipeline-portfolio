-- =============================================================================
-- 06-views.sql
-- Convenience views over the star schema.
-- Prefixed v_ to distinguish from base tables.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- warehouse.v_latest_prices
-- Most recent available price for each active commodity.
-- Used for dashboards showing "current" state.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW warehouse.v_latest_prices AS
SELECT
    c.commodity_id,
    c.commodity_name,
    c.category,
    c.currency,
    c.unit_of_measure,
    d.full_date                             AS trade_date,
    f.price_open,
    f.price_high,
    f.price_low,
    f.price_close,
    f.adj_close,
    f.volume,
    f.daily_change,
    f.daily_change_pct,
    s.source_name,
    f.created_at                            AS record_created_at
FROM warehouse.fact_oil_prices  f
JOIN warehouse.dim_date          d ON f.date_key       = d.date_key
JOIN warehouse.dim_commodity     c ON f.commodity_key  = c.commodity_key
JOIN warehouse.dim_source        s ON f.source_key     = s.source_key
WHERE c.is_current = TRUE
  AND f.date_key = (
      -- Scalar sub-query: latest date_key for this commodity
      SELECT MAX(f2.date_key)
      FROM   warehouse.fact_oil_prices f2
      WHERE  f2.commodity_key = f.commodity_key
  );

COMMENT ON VIEW warehouse.v_latest_prices IS 'Shows the most recent price record for every active commodity. Suitable for dashboard "current price" widgets.';


-- ---------------------------------------------------------------------------
-- warehouse.v_price_history
-- Full join of fact + dimensions with all human-readable columns.
-- Designed for API consumption and ad-hoc reporting.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW warehouse.v_price_history AS
SELECT
    f.price_key,
    -- Date attributes
    d.full_date                             AS trade_date,
    d.day_name,
    d.week_of_year,
    d.month_name,
    d.quarter,
    d.year,
    d.is_trading_day,
    -- Commodity attributes
    c.commodity_id,
    c.commodity_name,
    c.category,
    c.sub_category,
    c.currency,
    c.exchange,
    c.unit_of_measure,
    -- Source attributes
    s.source_name,
    s.source_type,
    s.reliability_score,
    -- Price measures
    f.price_open,
    f.price_high,
    f.price_low,
    f.price_close,
    f.adj_close,
    f.volume,
    f.daily_change,
    f.daily_change_pct,
    -- Metadata
    f.created_at                            AS fact_created_at
FROM warehouse.fact_oil_prices  f
JOIN warehouse.dim_date          d ON f.date_key       = d.date_key
JOIN warehouse.dim_commodity     c ON f.commodity_key  = c.commodity_key
JOIN warehouse.dim_source        s ON f.source_key     = s.source_key
WHERE c.is_current = TRUE;

COMMENT ON VIEW warehouse.v_price_history IS 'Full denormalised view of price history with all dimension attributes. Used for API endpoints and exports. Filtered to current commodity versions.';


-- ---------------------------------------------------------------------------
-- warehouse.v_price_with_metrics
-- Joins daily prices with pre-calculated technical indicators.
-- Use this view for charting / ML feature extraction.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW warehouse.v_price_with_metrics AS
SELECT
    d.full_date                             AS trade_date,
    d.year,
    d.month,
    d.quarter,
    c.commodity_id,
    c.commodity_name,
    c.currency,
    -- OHLCV
    f.price_open,
    f.price_high,
    f.price_low,
    f.price_close,
    f.volume,
    f.daily_change,
    f.daily_change_pct,
    -- Technical indicators (may be NULL for early rows lacking lookback data)
    m.ma_7,
    m.ma_30,
    m.ma_90,
    m.volatility_30d,
    m.rsi_14,
    m.price_vs_ma30_pct,
    -- Trend signal derived from MAs
    CASE
        WHEN m.ma_7 IS NOT NULL AND m.ma_30 IS NOT NULL THEN
            CASE
                WHEN m.ma_7 > m.ma_30 THEN 'BULLISH'
                WHEN m.ma_7 < m.ma_30 THEN 'BEARISH'
                ELSE 'NEUTRAL'
            END
        ELSE NULL
    END                                     AS ma_trend_signal,
    -- RSI zone
    CASE
        WHEN m.rsi_14 IS NULL THEN NULL
        WHEN m.rsi_14 >= 70   THEN 'OVERBOUGHT'
        WHEN m.rsi_14 <= 30   THEN 'OVERSOLD'
        ELSE 'NEUTRAL'
    END                                     AS rsi_zone
FROM warehouse.fact_oil_prices  f
JOIN warehouse.dim_date          d ON f.date_key       = d.date_key
JOIN warehouse.dim_commodity     c ON f.commodity_key  = c.commodity_key
LEFT JOIN analytics.price_metrics m
    ON  m.date_key      = f.date_key
    AND m.commodity_key = f.commodity_key
WHERE c.is_current = TRUE;

COMMENT ON VIEW warehouse.v_price_with_metrics IS 'Combines daily OHLCV with pre-calculated moving averages, volatility, and RSI. Includes derived trend signal and RSI zone columns.';
