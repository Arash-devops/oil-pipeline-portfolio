-- =============================================================================
-- 10-sample-queries.sql
-- Showcase analytical queries demonstrating advanced PostgreSQL / SQL skills.
-- These are READ-ONLY SELECT queries — safe to run at any time.
-- Run after loading data (see: warehouse.sp_process_staging()).
-- =============================================================================


-- -----------------------------------------------------------------------------
-- QUERY 01: Window Functions — Daily changes with LAG/LEAD
-- Demonstrates: LAG, LEAD, window frame, computed columns
-- Use case: Show each day's price alongside previous and next day for context
-- -----------------------------------------------------------------------------
-- [01] Daily price context with LAG and LEAD
SELECT
    d.full_date,
    c.commodity_name,
    f.price_close,
    LAG(f.price_close,  1) OVER w  AS prev_day_close,
    LEAD(f.price_close, 1) OVER w  AS next_day_close,
    f.daily_change,
    f.daily_change_pct,
    CASE
        WHEN f.daily_change > 0 THEN 'UP'
        WHEN f.daily_change < 0 THEN 'DOWN'
        ELSE 'FLAT'
    END                            AS direction
FROM   warehouse.fact_oil_prices f
JOIN   warehouse.dim_date        d ON d.date_key      = f.date_key
JOIN   warehouse.dim_commodity   c ON c.commodity_key = f.commodity_key
WHERE  c.commodity_id = 'CL=F'
  AND  d.full_date   >= CURRENT_DATE - INTERVAL '30 days'
WINDOW w AS (PARTITION BY f.commodity_key ORDER BY d.full_date)
ORDER BY d.full_date DESC;


-- -----------------------------------------------------------------------------
-- QUERY 02: Ranking — ROW_NUMBER, RANK, NTILE
-- Demonstrates: Multiple window functions in same SELECT, percentile buckets
-- Use case: Rank trading days by close price; bucket into quartiles
-- -----------------------------------------------------------------------------
-- [02] Price rankings and quartile buckets within a year
SELECT
    d.full_date,
    c.commodity_name,
    f.price_close,
    ROW_NUMBER() OVER (PARTITION BY d.year, f.commodity_key ORDER BY f.price_close DESC)  AS rank_by_price,
    RANK()       OVER (PARTITION BY d.year, f.commodity_key ORDER BY f.price_close DESC)  AS dense_rank_by_price,
    NTILE(4)     OVER (PARTITION BY d.year, f.commodity_key ORDER BY f.price_close ASC)   AS price_quartile  -- 1=lowest, 4=highest
FROM   warehouse.fact_oil_prices f
JOIN   warehouse.dim_date        d ON d.date_key      = f.date_key
JOIN   warehouse.dim_commodity   c ON c.commodity_key = f.commodity_key
WHERE  c.commodity_id = 'CL=F'
  AND  d.year         = EXTRACT(YEAR FROM CURRENT_DATE)::INT
ORDER BY d.full_date;


-- -----------------------------------------------------------------------------
-- QUERY 03: CTEs — 52-Week High/Low with distance from current price
-- Demonstrates: Multiple CTEs chained, self-referencing aggregate
-- Use case: Technical screen — is current price near its 52-week high or low?
-- -----------------------------------------------------------------------------
-- [03] 52-week high/low band with current price position
WITH
date_range AS (
    SELECT
        MAX(d.full_date)                           AS latest_date,
        MAX(d.full_date) - INTERVAL '52 weeks'    AS start_52w
    FROM warehouse.dim_date d
    JOIN warehouse.fact_oil_prices f ON f.date_key = d.date_key
),
rolling_52w AS (
    SELECT
        f.commodity_key,
        MIN(f.price_close) AS low_52w,
        MAX(f.price_close) AS high_52w
    FROM   warehouse.fact_oil_prices f
    JOIN   warehouse.dim_date        d  ON d.date_key  = f.date_key
    CROSS JOIN date_range dr
    WHERE  d.full_date BETWEEN dr.start_52w AND dr.latest_date
    GROUP BY f.commodity_key
),
latest_prices AS (
    SELECT DISTINCT ON (f.commodity_key)
        f.commodity_key,
        f.price_close AS current_close,
        d.full_date   AS latest_date
    FROM   warehouse.fact_oil_prices f
    JOIN   warehouse.dim_date        d ON d.date_key = f.date_key
    ORDER BY f.commodity_key, d.full_date DESC
)
SELECT
    c.commodity_name,
    lp.current_close,
    r.low_52w,
    r.high_52w,
    ROUND((r.high_52w - r.low_52w), 4)                                       AS range_52w,
    ROUND((lp.current_close - r.low_52w) / NULLIF(r.high_52w - r.low_52w, 0) * 100, 2) AS pct_of_range,
    CASE
        WHEN lp.current_close >= r.high_52w * 0.97 THEN 'NEAR 52W HIGH'
        WHEN lp.current_close <= r.low_52w  * 1.03 THEN 'NEAR 52W LOW'
        ELSE 'MID RANGE'
    END                                                                       AS range_position
FROM   latest_prices   lp
JOIN   rolling_52w     r  ON r.commodity_key  = lp.commodity_key
JOIN   warehouse.dim_commodity c ON c.commodity_key = lp.commodity_key
WHERE  c.is_current = TRUE
ORDER BY c.commodity_name;


-- -----------------------------------------------------------------------------
-- QUERY 04: Recursive CTE — Compound return simulation
-- Demonstrates: WITH RECURSIVE, iterative accumulation
-- Use case: What would $10,000 invested become if returns matched actual prices?
-- -----------------------------------------------------------------------------
-- [04] Simulated $10,000 portfolio value using recursive compound returns
WITH RECURSIVE
daily_returns AS (
    SELECT
        d.full_date,
        f.daily_change_pct / 100.0 AS return_pct,
        ROW_NUMBER() OVER (ORDER BY d.full_date) AS rn
    FROM   warehouse.fact_oil_prices f
    JOIN   warehouse.dim_date        d ON d.date_key      = f.date_key
    JOIN   warehouse.dim_commodity   c ON c.commodity_key = f.commodity_key
    WHERE  c.commodity_id       = 'CL=F'
      AND  f.daily_change_pct IS NOT NULL
      AND  d.full_date         >= CURRENT_DATE - INTERVAL '365 days'
),
portfolio AS (
    -- Base case: start with $10,000 on day 1
    SELECT
        full_date,
        return_pct,
        rn,
        10000.00::NUMERIC AS portfolio_value
    FROM daily_returns WHERE rn = 1

    UNION ALL

    -- Recursive case: apply each day's return
    SELECT
        dr.full_date,
        dr.return_pct,
        dr.rn,
        ROUND(p.portfolio_value * (1 + dr.return_pct), 4)
    FROM daily_returns dr
    JOIN portfolio     p  ON p.rn = dr.rn - 1
)
SELECT
    full_date,
    ROUND(return_pct * 100, 4)  AS daily_return_pct,
    portfolio_value,
    ROUND(portfolio_value - 10000, 4)  AS total_gain_loss,
    ROUND((portfolio_value - 10000) / 10000 * 100, 2) AS total_return_pct
FROM  portfolio
ORDER BY full_date;


-- -----------------------------------------------------------------------------
-- QUERY 05: PIVOT / CROSSTAB — Monthly returns as a calendar grid
-- Demonstrates: crosstab() from tablefunc extension, conditional aggregation
-- Use case: Heat-map style monthly return table (rows=year, cols=month)
-- -----------------------------------------------------------------------------
-- [05a] Conditional aggregation pivot (runs without tablefunc)
SELECT
    year,
    ROUND(MAX(CASE WHEN month =  1 THEN monthly_return_pct END), 2) AS "Jan",
    ROUND(MAX(CASE WHEN month =  2 THEN monthly_return_pct END), 2) AS "Feb",
    ROUND(MAX(CASE WHEN month =  3 THEN monthly_return_pct END), 2) AS "Mar",
    ROUND(MAX(CASE WHEN month =  4 THEN monthly_return_pct END), 2) AS "Apr",
    ROUND(MAX(CASE WHEN month =  5 THEN monthly_return_pct END), 2) AS "May",
    ROUND(MAX(CASE WHEN month =  6 THEN monthly_return_pct END), 2) AS "Jun",
    ROUND(MAX(CASE WHEN month =  7 THEN monthly_return_pct END), 2) AS "Jul",
    ROUND(MAX(CASE WHEN month =  8 THEN monthly_return_pct END), 2) AS "Aug",
    ROUND(MAX(CASE WHEN month =  9 THEN monthly_return_pct END), 2) AS "Sep",
    ROUND(MAX(CASE WHEN month = 10 THEN monthly_return_pct END), 2) AS "Oct",
    ROUND(MAX(CASE WHEN month = 11 THEN monthly_return_pct END), 2) AS "Nov",
    ROUND(MAX(CASE WHEN month = 12 THEN monthly_return_pct END), 2) AS "Dec"
FROM  analytics.monthly_summary ms
JOIN  warehouse.dim_commodity   c  ON c.commodity_key = ms.commodity_key
WHERE c.commodity_id = 'CL=F'
GROUP BY year
ORDER BY year;


-- -----------------------------------------------------------------------------
-- QUERY 06: Gap Detection — Find missing trading days
-- Demonstrates: generate_series + LEFT JOIN, set difference pattern
-- Use case: Data quality check — are there gaps in the price series?
-- -----------------------------------------------------------------------------
-- [06] Detect missing trading days in the fact table for WTI crude
WITH
expected_days AS (
    -- All weekdays in the last year that should have data
    SELECT full_date
    FROM   warehouse.dim_date
    WHERE  is_trading_day = TRUE
      AND  full_date BETWEEN CURRENT_DATE - INTERVAL '365 days' AND CURRENT_DATE - INTERVAL '1 day'
),
actual_days AS (
    SELECT DISTINCT d.full_date
    FROM   warehouse.fact_oil_prices f
    JOIN   warehouse.dim_date        d  ON d.date_key      = f.date_key
    JOIN   warehouse.dim_commodity   c  ON c.commodity_key = f.commodity_key
    WHERE  c.commodity_id = 'CL=F'
)
SELECT
    e.full_date                             AS missing_date,
    TO_CHAR(e.full_date, 'Day')             AS day_of_week,
    CURRENT_DATE - e.full_date              AS days_ago
FROM  expected_days e
WHERE NOT EXISTS (SELECT 1 FROM actual_days a WHERE a.full_date = e.full_date)
ORDER BY e.full_date;


-- -----------------------------------------------------------------------------
-- QUERY 07: Year-Over-Year Comparison
-- Demonstrates: DATE_TRUNC, LAG over yearly partition, calculated YoY delta
-- Use case: Compare annual performance across commodities
-- -----------------------------------------------------------------------------
-- [07] Year-over-year average close price comparison
WITH yearly_avg AS (
    SELECT
        c.commodity_name,
        d.year,
        ROUND(AVG(f.price_close), 4)        AS avg_close,
        COUNT(*)                            AS trading_days
    FROM   warehouse.fact_oil_prices f
    JOIN   warehouse.dim_date        d ON d.date_key      = f.date_key
    JOIN   warehouse.dim_commodity   c ON c.commodity_key = f.commodity_key
    WHERE  c.is_current = TRUE
    GROUP BY c.commodity_name, d.year
)
SELECT
    commodity_name,
    year,
    avg_close,
    trading_days,
    LAG(avg_close) OVER (PARTITION BY commodity_name ORDER BY year) AS prev_year_avg,
    ROUND(
        (avg_close - LAG(avg_close) OVER (PARTITION BY commodity_name ORDER BY year))
        / NULLIF(LAG(avg_close) OVER (PARTITION BY commodity_name ORDER BY year), 0) * 100,
        2
    )                                                               AS yoy_change_pct
FROM yearly_avg
ORDER BY commodity_name, year;


-- -----------------------------------------------------------------------------
-- QUERY 08: Moving Averages in Pure SQL (no pre-computed analytics table)
-- Demonstrates: Window frames with ROWS BETWEEN, multiple windows in one query
-- Use case: On-the-fly MA calculation without relying on analytics.price_metrics
-- -----------------------------------------------------------------------------
-- [08] On-the-fly 7/30-day moving averages via window functions
SELECT
    d.full_date,
    c.commodity_name,
    f.price_close,
    ROUND(AVG(f.price_close) OVER (
        PARTITION BY f.commodity_key
        ORDER BY d.full_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 4)                                                           AS ma_7,
    ROUND(AVG(f.price_close) OVER (
        PARTITION BY f.commodity_key
        ORDER BY d.full_date
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ), 4)                                                           AS ma_30,
    ROUND(STDDEV_SAMP(f.price_close) OVER (
        PARTITION BY f.commodity_key
        ORDER BY d.full_date
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ), 4)                                                           AS volatility_30d,
    -- Bollinger Band bounds (price ± 2σ)
    ROUND(AVG(f.price_close) OVER (
        PARTITION BY f.commodity_key ORDER BY d.full_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) + 2 * STDDEV_SAMP(f.price_close) OVER (
        PARTITION BY f.commodity_key ORDER BY d.full_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ), 4)                                                           AS bollinger_upper,
    ROUND(AVG(f.price_close) OVER (
        PARTITION BY f.commodity_key ORDER BY d.full_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) - 2 * STDDEV_SAMP(f.price_close) OVER (
        PARTITION BY f.commodity_key ORDER BY d.full_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ), 4)                                                           AS bollinger_lower
FROM   warehouse.fact_oil_prices f
JOIN   warehouse.dim_date        d ON d.date_key      = f.date_key
JOIN   warehouse.dim_commodity   c ON c.commodity_key = f.commodity_key
WHERE  c.commodity_id = 'CL=F'
  AND  d.full_date   >= CURRENT_DATE - INTERVAL '6 months'
ORDER BY d.full_date;


-- -----------------------------------------------------------------------------
-- QUERY 09: Percentile Calculations
-- Demonstrates: PERCENTILE_CONT (ordered-set aggregate), WIDTH_BUCKET
-- Use case: Distribution analysis — is today's price historically cheap or expensive?
-- -----------------------------------------------------------------------------
-- [09] Price distribution percentiles and histogram buckets
WITH all_closes AS (
    SELECT f.price_close, d.full_date
    FROM   warehouse.fact_oil_prices f
    JOIN   warehouse.dim_date        d ON d.date_key      = f.date_key
    JOIN   warehouse.dim_commodity   c ON c.commodity_key = f.commodity_key
    WHERE  c.commodity_id = 'CL=F'
),
distribution AS (
    SELECT
        ROUND(PERCENTILE_CONT(0.10) WITHIN GROUP (ORDER BY price_close)::DECIMAL, 2) AS p10,
        ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price_close)::DECIMAL, 2) AS p25,
        ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY price_close)::DECIMAL, 2) AS median,
        ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price_close)::DECIMAL, 2) AS p75,
        ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY price_close)::DECIMAL, 2) AS p90,
        ROUND(PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY price_close)::DECIMAL, 2) AS p99,
        ROUND(AVG(price_close)::DECIMAL, 2)     AS mean,
        ROUND(STDDEV(price_close)::DECIMAL, 2)  AS std_dev,
        MIN(price_close)                        AS min_price,
        MAX(price_close)                        AS max_price,
        COUNT(*)                                AS total_observations
    FROM all_closes
)
SELECT * FROM distribution;

-- Histogram: count observations in 10 equal-width buckets
WITH all_closes AS (
    SELECT f.price_close
    FROM   warehouse.fact_oil_prices f
    JOIN   warehouse.dim_date        d ON d.date_key      = f.date_key
    JOIN   warehouse.dim_commodity   c ON c.commodity_key = f.commodity_key
    WHERE  c.commodity_id = 'CL=F'
),
bounds AS (SELECT MIN(price_close) AS lo, MAX(price_close) AS hi FROM all_closes)
SELECT
    WIDTH_BUCKET(price_close, b.lo, b.hi + 0.01, 10)   AS bucket,
    ROUND(b.lo + (WIDTH_BUCKET(price_close, b.lo, b.hi + 0.01, 10) - 1)
          * (b.hi - b.lo) / 10, 2)                     AS bucket_lower,
    ROUND(b.lo + WIDTH_BUCKET(price_close, b.lo, b.hi + 0.01, 10)
          * (b.hi - b.lo) / 10, 2)                     AS bucket_upper,
    COUNT(*)                                            AS frequency,
    REPEAT('■', (COUNT(*) * 40 / MAX(COUNT(*)) OVER ())::INT) AS bar
FROM  all_closes
CROSS JOIN bounds b
GROUP BY bucket, b.lo, b.hi
ORDER BY bucket;


-- -----------------------------------------------------------------------------
-- QUERY 10: Correlated Subquery — Price rank within its calendar year
-- Demonstrates: Correlated subquery for percentile rank computation
-- Use case: "Where does today's price sit relative to all prices in its year?"
-- -----------------------------------------------------------------------------
-- [10] Historical percentile rank of each daily close within its calendar year
SELECT
    d.full_date,
    c.commodity_name,
    f.price_close,
    d.year,
    (
        SELECT COUNT(*)
        FROM   warehouse.fact_oil_prices  f2
        JOIN   warehouse.dim_date         d2 ON d2.date_key      = f2.date_key
        WHERE  f2.commodity_key = f.commodity_key
          AND  d2.year          = d.year
          AND  f2.price_close  <= f.price_close
    )::DECIMAL
    /
    NULLIF((
        SELECT COUNT(*)
        FROM   warehouse.fact_oil_prices  f3
        JOIN   warehouse.dim_date         d3 ON d3.date_key      = f3.date_key
        WHERE  f3.commodity_key = f.commodity_key
          AND  d3.year          = d.year
    ), 0)
    * 100                                               AS yearly_percentile_rank
FROM   warehouse.fact_oil_prices f
JOIN   warehouse.dim_date        d ON d.date_key      = f.date_key
JOIN   warehouse.dim_commodity   c ON c.commodity_key = f.commodity_key
WHERE  c.commodity_id = 'CL=F'
  AND  d.full_date   >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY d.full_date DESC;


-- -----------------------------------------------------------------------------
-- QUERY 11: Full Pipeline Demo — Run all procedures in sequence
-- Demonstrates: PERFORM, SELECT ... FROM function(), DO block orchestration
-- Use case: End-to-end pipeline test from a single SQL session
-- NOTE: This is a demonstration block. Uncomment and run manually.
-- -----------------------------------------------------------------------------
-- [11] Full pipeline execution demo
/*
DO $$
DECLARE
    v_validation    RECORD;
    v_processing    RECORD;
    v_commodity     RECORD;
BEGIN
    RAISE NOTICE '=== OIL WAREHOUSE PIPELINE START ===';

    -- Step 1: Insert a sample staging record
    INSERT INTO staging.stg_oil_prices
        (symbol, trade_date, price_open, price_high, price_low, price_close, adj_close, volume, source_name)
    VALUES
        ('CL=F', CURRENT_DATE - 1, 72.50, 74.20, 71.80, 73.45, 73.45, 450000, 'Yahoo Finance');

    RAISE NOTICE 'Step 1: Inserted sample staging record.';

    -- Step 2: Validate staging data
    SELECT * INTO v_validation FROM staging.sp_validate_staging_data();
    RAISE NOTICE 'Step 2: Validation — Total: %, Valid: %, Invalid: %',
                 v_validation.total_records, v_validation.valid_records, v_validation.invalid_records;

    -- Step 3: Process staging → warehouse
    SELECT * INTO v_processing FROM warehouse.sp_process_staging();
    RAISE NOTICE 'Step 3: Processing — Promoted: %, Skipped: %, Errors: %',
                 v_processing.processed, v_processing.skipped, v_processing.errors;

    -- Step 4: Calculate technical metrics for all active commodities
    FOR v_commodity IN
        SELECT DISTINCT commodity_key FROM warehouse.dim_commodity WHERE is_current = TRUE
    LOOP
        PERFORM analytics.sp_calculate_metrics(v_commodity.commodity_key);
        RAISE NOTICE 'Step 4: Metrics calculated for commodity_key=%', v_commodity.commodity_key;
    END LOOP;

    -- Step 5: Aggregate monthly stats
    PERFORM analytics.sp_aggregate_monthly();
    RAISE NOTICE 'Step 5: Monthly aggregation complete.';

    RAISE NOTICE '=== OIL WAREHOUSE PIPELINE COMPLETE ===';
END;
$$;
*/


-- -----------------------------------------------------------------------------
-- QUERY 12: Multi-commodity Correlation (bonus — advanced analytics)
-- Demonstrates: Self-join, Pearson correlation coefficient in pure SQL
-- Use case: Are WTI and Brent moving together? Measure their correlation.
-- -----------------------------------------------------------------------------
-- [12] Price correlation between two commodities over the last year
WITH
wti AS (
    SELECT d.full_date, f.price_close AS wti_close
    FROM   warehouse.fact_oil_prices f
    JOIN   warehouse.dim_date        d ON d.date_key      = f.date_key
    JOIN   warehouse.dim_commodity   c ON c.commodity_key = f.commodity_key
    WHERE  c.commodity_id = 'CL=F'
      AND  d.full_date   >= CURRENT_DATE - INTERVAL '365 days'
),
brent AS (
    SELECT d.full_date, f.price_close AS brent_close
    FROM   warehouse.fact_oil_prices f
    JOIN   warehouse.dim_date        d ON d.date_key      = f.date_key
    JOIN   warehouse.dim_commodity   c ON c.commodity_key = f.commodity_key
    WHERE  c.commodity_id = 'BZ=F'
      AND  d.full_date   >= CURRENT_DATE - INTERVAL '365 days'
),
paired AS (
    SELECT
        w.full_date,
        w.wti_close,
        b.brent_close,
        b.brent_close - w.wti_close AS wti_brent_spread
    FROM wti w
    JOIN brent b USING (full_date)
)
SELECT
    COUNT(*)                                        AS trading_days,
    ROUND(CORR(wti_close, brent_close)::DECIMAL, 4) AS pearson_correlation,
    ROUND(AVG(wti_brent_spread)::DECIMAL, 4)        AS avg_spread_usd,
    ROUND(STDDEV(wti_brent_spread)::DECIMAL, 4)     AS spread_volatility,
    ROUND(MIN(wti_brent_spread)::DECIMAL, 4)        AS min_spread,
    ROUND(MAX(wti_brent_spread)::DECIMAL, 4)        AS max_spread
FROM paired;
