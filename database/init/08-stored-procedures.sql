-- =============================================================================
-- 08-stored-procedures.sql
-- All PL/pgSQL stored procedures for the oil price data warehouse.
--
-- Execution order (full pipeline):
--   1. Load raw data into staging.stg_oil_prices (external step)
--   2. staging.sp_validate_staging_data()    → validate raw rows
--   3. warehouse.sp_process_staging()        → promote to fact table
--   4. analytics.sp_calculate_metrics()      → compute technical indicators
--   5. analytics.sp_aggregate_monthly()      → compute monthly summaries
--
-- Ad-hoc / DQ:
--   warehouse.sp_upsert_oil_price()          → single-row upsert
--   warehouse.sp_manage_scd2()               → handle dimension changes
-- =============================================================================


-- =============================================================================
-- 1. staging.sp_validate_staging_data
-- Validates all unprocessed, not-yet-validated staging rows.
-- Applies five business rules in sequence; collects all failures per row.
-- Returns a summary table: total / valid / invalid counts.
-- =============================================================================
CREATE OR REPLACE FUNCTION staging.sp_validate_staging_data()
RETURNS TABLE(
    total_records   INT,
    valid_records   INT,
    invalid_records INT
)
LANGUAGE plpgsql AS $$
DECLARE
    v_rec           RECORD;
    v_errors        TEXT;
    v_is_valid      BOOLEAN;
    v_total         INT := 0;
    v_valid         INT := 0;
    v_invalid       INT := 0;
BEGIN
    RAISE NOTICE '[sp_validate_staging_data] Starting validation of unprocessed staging rows.';

    FOR v_rec IN
        SELECT  staging_id,
                symbol,
                trade_date,
                price_open,
                price_high,
                price_low,
                price_close,
                adj_close,
                volume
        FROM    staging.stg_oil_prices
        WHERE   is_processed = FALSE
          AND   is_valid IS NULL       -- Only rows not yet validated
        ORDER BY staging_id
    LOOP
        v_total  := v_total + 1;
        v_errors := '';
        v_is_valid := TRUE;

        -- Rule 1: symbol must not be null or blank
        IF v_rec.symbol IS NULL OR TRIM(v_rec.symbol) = '' THEN
            v_errors   := v_errors || 'symbol is NULL or blank; ';
            v_is_valid := FALSE;
        END IF;

        -- Rule 2: trade_date must not be in the future
        IF v_rec.trade_date IS NULL THEN
            v_errors   := v_errors || 'trade_date is NULL; ';
            v_is_valid := FALSE;
        ELSIF v_rec.trade_date > CURRENT_DATE THEN
            v_errors   := v_errors || 'trade_date ' || v_rec.trade_date::TEXT || ' is in the future; ';
            v_is_valid := FALSE;
        END IF;

        -- Rule 3: price_close must be positive
        IF v_rec.price_close IS NULL OR v_rec.price_close <= 0 THEN
            v_errors   := v_errors || 'price_close must be > 0 (got ' || COALESCE(v_rec.price_close::TEXT, 'NULL') || '); ';
            v_is_valid := FALSE;
        END IF;

        -- Rule 4: price_close sanity ceiling (oil > $500/barrel is extraordinary)
        IF v_rec.price_close IS NOT NULL AND v_rec.price_close > 500 THEN
            v_errors   := v_errors || 'price_close ' || v_rec.price_close::TEXT || ' exceeds $500 sanity limit; ';
            v_is_valid := FALSE;
        END IF;

        -- Rule 5: price_high must be >= price_low when both are present
        IF v_rec.price_high IS NOT NULL AND v_rec.price_low IS NOT NULL
           AND v_rec.price_high < v_rec.price_low THEN
            v_errors   := v_errors || 'price_high (' || v_rec.price_high::TEXT || ') < price_low (' || v_rec.price_low::TEXT || '); ';
            v_is_valid := FALSE;
        END IF;

        -- Persist validation result
        UPDATE staging.stg_oil_prices
        SET    is_valid          = v_is_valid,
               validation_errors = CASE WHEN v_errors = '' THEN NULL ELSE RTRIM(v_errors, '; ') END
        WHERE  staging_id = v_rec.staging_id;

        IF v_is_valid THEN
            v_valid   := v_valid + 1;
        ELSE
            v_invalid := v_invalid + 1;
            RAISE NOTICE '[sp_validate_staging_data] staging_id=% INVALID: %', v_rec.staging_id, v_errors;
        END IF;

    END LOOP;

    RAISE NOTICE '[sp_validate_staging_data] Complete. Total=%, Valid=%, Invalid=%',
                 v_total, v_valid, v_invalid;

    total_records   := v_total;
    valid_records   := v_valid;
    invalid_records := v_invalid;
    RETURN NEXT;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION '[sp_validate_staging_data] Unexpected error: %  (SQLSTATE: %)', SQLERRM, SQLSTATE;
END;
$$;

COMMENT ON FUNCTION staging.sp_validate_staging_data() IS
'Validates unprocessed staging rows against 5 business rules: non-null symbol, non-future date, positive close, $500 ceiling, high >= low. Updates is_valid and validation_errors in-place. Returns summary counts.';


-- =============================================================================
-- 2. warehouse.sp_upsert_oil_price
-- Single-row upsert for a price observation.
-- Resolves surrogate keys, auto-registers unknown commodities/sources,
-- calculates daily_change and daily_change_pct, then INSERT ... ON CONFLICT.
-- =============================================================================
CREATE OR REPLACE FUNCTION warehouse.sp_upsert_oil_price(
    p_symbol        VARCHAR(20),
    p_trade_date    DATE,
    p_open          DECIMAL(12,4),
    p_high          DECIMAL(12,4),
    p_low           DECIMAL(12,4),
    p_close         DECIMAL(12,4),
    p_adj_close     DECIMAL(12,4),
    p_volume        BIGINT,
    p_source_name   VARCHAR(100)
)
RETURNS VOID
LANGUAGE plpgsql AS $$
DECLARE
    v_date_key          INTEGER;
    v_commodity_key     INTEGER;
    v_source_key        INTEGER;
    v_prev_close        DECIMAL(12,4);
    v_daily_change      DECIMAL(12,4);
    v_daily_change_pct  DECIMAL(8,4);
BEGIN
    -- -------------------------------------------------------------------------
    -- Step 1: Resolve date_key (must exist — dim_date is pre-populated)
    -- -------------------------------------------------------------------------
    v_date_key := TO_CHAR(p_trade_date, 'YYYYMMDD')::INTEGER;

    IF NOT EXISTS (SELECT 1 FROM warehouse.dim_date WHERE date_key = v_date_key) THEN
        RAISE EXCEPTION '[sp_upsert_oil_price] date_key % (%) not found in dim_date. Ensure 09-seed-data.sql covers this date.',
                        v_date_key, p_trade_date;
    END IF;

    -- -------------------------------------------------------------------------
    -- Step 2: Resolve or auto-register commodity
    -- -------------------------------------------------------------------------
    SELECT commodity_key
    INTO   v_commodity_key
    FROM   warehouse.dim_commodity
    WHERE  commodity_id = p_symbol
      AND  is_current   = TRUE;

    IF NOT FOUND THEN
        INSERT INTO warehouse.dim_commodity (commodity_id, commodity_name, category)
        VALUES (p_symbol, p_symbol, 'Energy')
        RETURNING commodity_key INTO v_commodity_key;
        RAISE NOTICE '[sp_upsert_oil_price] Auto-registered commodity: % (key=%)', p_symbol, v_commodity_key;
    END IF;

    -- -------------------------------------------------------------------------
    -- Step 3: Resolve or auto-register source
    -- -------------------------------------------------------------------------
    SELECT source_key
    INTO   v_source_key
    FROM   warehouse.dim_source
    WHERE  source_name = p_source_name;

    IF NOT FOUND THEN
        INSERT INTO warehouse.dim_source (source_name, source_type, reliability_score)
        VALUES (p_source_name, 'API', 0.80)
        RETURNING source_key INTO v_source_key;
        RAISE NOTICE '[sp_upsert_oil_price] Auto-registered source: % (key=%)', p_source_name, v_source_key;
    END IF;

    -- -------------------------------------------------------------------------
    -- Step 4: Compute daily change from previous trading day's close
    -- -------------------------------------------------------------------------
    SELECT f.price_close
    INTO   v_prev_close
    FROM   warehouse.fact_oil_prices f
    JOIN   warehouse.dim_date        d ON d.date_key = f.date_key
    WHERE  f.commodity_key = v_commodity_key
      AND  d.full_date     < p_trade_date
    ORDER BY d.full_date DESC
    LIMIT 1;

    IF v_prev_close IS NOT NULL AND v_prev_close > 0 THEN
        v_daily_change     := p_close - v_prev_close;
        v_daily_change_pct := ROUND((v_daily_change / v_prev_close) * 100, 4);
    ELSE
        v_daily_change     := NULL;  -- First record for this commodity
        v_daily_change_pct := NULL;
    END IF;

    -- -------------------------------------------------------------------------
    -- Step 5: Upsert into fact table
    -- -------------------------------------------------------------------------
    INSERT INTO warehouse.fact_oil_prices (
        date_key, commodity_key, source_key,
        price_open, price_high, price_low, price_close, adj_close, volume,
        daily_change, daily_change_pct
    )
    VALUES (
        v_date_key, v_commodity_key, v_source_key,
        p_open, p_high, p_low, p_close, p_adj_close, p_volume,
        v_daily_change, v_daily_change_pct
    )
    ON CONFLICT (date_key, commodity_key, source_key) DO UPDATE SET
        price_open         = EXCLUDED.price_open,
        price_high         = EXCLUDED.price_high,
        price_low          = EXCLUDED.price_low,
        price_close        = EXCLUDED.price_close,
        adj_close          = EXCLUDED.adj_close,
        volume             = EXCLUDED.volume,
        daily_change       = EXCLUDED.daily_change,
        daily_change_pct   = EXCLUDED.daily_change_pct;

    RAISE NOTICE '[sp_upsert_oil_price] Upserted % on % (close=%, Δ=%)',
                 p_symbol, p_trade_date, p_close, v_daily_change;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION '[sp_upsert_oil_price] Failed for % on %: %  (SQLSTATE: %)',
                        p_symbol, p_trade_date, SQLERRM, SQLSTATE;
END;
$$;

COMMENT ON FUNCTION warehouse.sp_upsert_oil_price(VARCHAR,DATE,DECIMAL,DECIMAL,DECIMAL,DECIMAL,DECIMAL,BIGINT,VARCHAR) IS
'Single-row upsert for one oil price observation. Resolves or auto-creates dimension keys, calculates daily change from previous close, then INSERT...ON CONFLICT DO UPDATE into fact_oil_prices.';


-- =============================================================================
-- 3. warehouse.sp_process_staging
-- Orchestrates the full staging → warehouse promotion for all valid rows.
-- Calls sp_validate_staging_data() first, then sp_upsert_oil_price() per row.
-- =============================================================================
CREATE OR REPLACE FUNCTION warehouse.sp_process_staging()
RETURNS TABLE(
    processed   INT,
    skipped     INT,
    errors      INT
)
LANGUAGE plpgsql AS $$
DECLARE
    v_rec           RECORD;
    v_processed     INT := 0;
    v_skipped       INT := 0;
    v_errors        INT := 0;
    v_validation    RECORD;
BEGIN
    RAISE NOTICE '[sp_process_staging] Starting staging pipeline.';

    -- -------------------------------------------------------------------------
    -- Step 1: Run validation on any not-yet-validated rows
    -- -------------------------------------------------------------------------
    SELECT * INTO v_validation FROM staging.sp_validate_staging_data();
    RAISE NOTICE '[sp_process_staging] Validation done. Total=%, Valid=%, Invalid=%',
                 v_validation.total_records, v_validation.valid_records, v_validation.invalid_records;

    -- -------------------------------------------------------------------------
    -- Step 2: Promote valid, unprocessed rows to warehouse
    -- -------------------------------------------------------------------------
    FOR v_rec IN
        SELECT  staging_id,
                symbol,
                trade_date,
                price_open,
                price_high,
                price_low,
                price_close,
                adj_close,
                volume,
                source_name
        FROM    staging.stg_oil_prices
        WHERE   is_processed = FALSE
          AND   is_valid     = TRUE
        ORDER BY trade_date ASC, staging_id ASC  -- oldest first for correct daily_change
    LOOP
        BEGIN
            PERFORM warehouse.sp_upsert_oil_price(
                v_rec.symbol,
                v_rec.trade_date,
                v_rec.price_open,
                v_rec.price_high,
                v_rec.price_low,
                v_rec.price_close,
                v_rec.adj_close,
                v_rec.volume,
                v_rec.source_name
            );

            -- Mark as processed
            UPDATE staging.stg_oil_prices
            SET    is_processed = TRUE,
                   processed_at = CURRENT_TIMESTAMP
            WHERE  staging_id   = v_rec.staging_id;

            v_processed := v_processed + 1;

        EXCEPTION
            WHEN OTHERS THEN
                -- Log error but continue processing remaining rows
                RAISE WARNING '[sp_process_staging] Error on staging_id=%: %', v_rec.staging_id, SQLERRM;

                UPDATE staging.stg_oil_prices
                SET    is_processed      = TRUE,
                       processed_at      = CURRENT_TIMESTAMP,
                       is_valid          = FALSE,
                       validation_errors = COALESCE(validation_errors, '') || ' PROCESSING_ERROR: ' || SQLERRM
                WHERE  staging_id = v_rec.staging_id;

                v_errors := v_errors + 1;
        END;
    END LOOP;

    -- -------------------------------------------------------------------------
    -- Step 3: Count rows skipped (invalid and already-processed)
    -- -------------------------------------------------------------------------
    SELECT COUNT(*)
    INTO   v_skipped
    FROM   staging.stg_oil_prices
    WHERE  is_processed = FALSE
      AND  is_valid     = FALSE;

    -- Mark invalid rows as processed (they will not be retried automatically)
    UPDATE staging.stg_oil_prices
    SET    is_processed = TRUE,
           processed_at = CURRENT_TIMESTAMP
    WHERE  is_processed = FALSE
      AND  is_valid     = FALSE;

    RAISE NOTICE '[sp_process_staging] Complete. Promoted=%, Skipped(invalid)=%, Errors=%',
                 v_processed, v_skipped, v_errors;

    processed := v_processed;
    skipped   := v_skipped;
    errors    := v_errors;
    RETURN NEXT;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION '[sp_process_staging] Fatal error: %  (SQLSTATE: %)', SQLERRM, SQLSTATE;
END;
$$;

COMMENT ON FUNCTION warehouse.sp_process_staging() IS
'Full staging-to-warehouse pipeline. Validates unprocessed rows, then promotes valid ones via sp_upsert_oil_price(). Processes oldest dates first to ensure correct daily_change calculation. Continues on per-row errors, marking failed rows in-place.';


-- =============================================================================
-- 4. analytics.sp_calculate_metrics
-- Computes per-day technical indicators for a commodity over a date range.
-- Uses window functions for MA, volatility, and RSI calculations.
-- =============================================================================
CREATE OR REPLACE FUNCTION analytics.sp_calculate_metrics(
    p_commodity_key     INT,
    p_start_date        DATE DEFAULT NULL,
    p_end_date          DATE DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql AS $$
DECLARE
    v_start_date        DATE;
    v_end_date          DATE;
    v_lookback_start    DATE;  -- extended start to warm up window functions
    v_rows_upserted     INT;
BEGIN
    -- Default: last 365 days
    v_end_date   := COALESCE(p_end_date,   CURRENT_DATE);
    v_start_date := COALESCE(p_start_date, v_end_date - INTERVAL '365 days');

    -- Extend lookback by 90 days so 90-day MA is accurate from v_start_date
    v_lookback_start := v_start_date - INTERVAL '90 days';

    RAISE NOTICE '[sp_calculate_metrics] commodity_key=%, range % → %',
                 p_commodity_key, v_start_date, v_end_date;

    -- -------------------------------------------------------------------------
    -- Single CTE chain: gather prices → compute window metrics → RSI
    -- -------------------------------------------------------------------------
    WITH
    -- 1. Raw price series including warm-up buffer
    price_series AS (
        SELECT
            f.date_key,
            d.full_date,
            f.price_close,
            f.commodity_key
        FROM   warehouse.fact_oil_prices f
        JOIN   warehouse.dim_date        d ON d.date_key = f.date_key
        WHERE  f.commodity_key = p_commodity_key
          AND  d.full_date BETWEEN v_lookback_start AND v_end_date
        ORDER BY d.full_date
    ),

    -- 2. Compute moving averages and volatility using window functions
    with_mas AS (
        SELECT
            date_key,
            full_date,
            commodity_key,
            price_close,
            -- 7-day MA: minimum 7 rows required
            CASE WHEN COUNT(*) OVER w7  >= 7
                 THEN AVG(price_close) OVER w7  END   AS ma_7,
            -- 30-day MA: minimum 30 rows required
            CASE WHEN COUNT(*) OVER w30 >= 30
                 THEN AVG(price_close) OVER w30 END   AS ma_30,
            -- 90-day MA: minimum 90 rows required
            CASE WHEN COUNT(*) OVER w90 >= 90
                 THEN AVG(price_close) OVER w90 END   AS ma_90,
            -- 30-day rolling standard deviation (volatility)
            CASE WHEN COUNT(*) OVER w30 >= 30
                 THEN STDDEV_SAMP(price_close) OVER w30 END AS volatility_30d
        FROM  price_series
        WINDOW
            w7  AS (ORDER BY full_date ROWS BETWEEN  6 PRECEDING AND CURRENT ROW),
            w30 AS (ORDER BY full_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW),
            w90 AS (ORDER BY full_date ROWS BETWEEN 89 PRECEDING AND CURRENT ROW)
    ),

    -- 3. Compute daily change for RSI calculation
    with_changes AS (
        SELECT
            date_key,
            full_date,
            commodity_key,
            price_close,
            ma_7,
            ma_30,
            ma_90,
            volatility_30d,
            price_close - LAG(price_close) OVER (ORDER BY full_date) AS daily_change
        FROM with_mas
    ),

    -- 4. Separate gains and losses
    with_gains_losses AS (
        SELECT
            date_key,
            full_date,
            commodity_key,
            price_close,
            ma_7,
            ma_30,
            ma_90,
            volatility_30d,
            daily_change,
            GREATEST(daily_change,  0) AS gain,
            GREATEST(-daily_change, 0) AS loss
        FROM with_changes
    ),

    -- 5. Compute 14-period average gain and average loss (simple SMA-based RSI)
    with_rsi_components AS (
        SELECT
            date_key,
            full_date,
            commodity_key,
            price_close,
            ma_7,
            ma_30,
            ma_90,
            volatility_30d,
            AVG(gain) OVER w14 AS avg_gain_14,
            AVG(loss) OVER w14 AS avg_loss_14
        FROM with_gains_losses
        WINDOW w14 AS (ORDER BY full_date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW)
    ),

    -- 6. Compute final RSI and price_vs_ma30_pct, filter to target range
    final_metrics AS (
        SELECT
            date_key,
            commodity_key,
            ma_7,
            ma_30,
            ma_90,
            volatility_30d,
            -- RSI: 100 when all gains, 0 when all losses, NULL until 14 rows available
            CASE
                WHEN COUNT(*) OVER (ORDER BY full_date ROWS BETWEEN 13 PRECEDING AND CURRENT ROW) < 14
                    THEN NULL
                WHEN avg_loss_14 = 0
                    THEN 100.00
                ELSE ROUND(100 - (100.0 / (1 + avg_gain_14 / NULLIF(avg_loss_14, 0))), 2)
            END AS rsi_14,
            -- Price vs MA30 percentage
            CASE WHEN ma_30 IS NOT NULL AND ma_30 > 0
                 THEN ROUND(((price_close - ma_30) / ma_30) * 100, 4)
            END AS price_vs_ma30_pct
        FROM  with_rsi_components
        WHERE full_date BETWEEN v_start_date AND v_end_date
    )

    -- 7. Upsert into analytics.price_metrics
    INSERT INTO analytics.price_metrics (
        date_key, commodity_key,
        ma_7, ma_30, ma_90,
        volatility_30d, rsi_14, price_vs_ma30_pct,
        updated_at
    )
    SELECT
        date_key, commodity_key,
        ma_7, ma_30, ma_90,
        volatility_30d, rsi_14, price_vs_ma30_pct,
        CURRENT_TIMESTAMP
    FROM final_metrics
    ON CONFLICT (date_key, commodity_key) DO UPDATE SET
        ma_7              = EXCLUDED.ma_7,
        ma_30             = EXCLUDED.ma_30,
        ma_90             = EXCLUDED.ma_90,
        volatility_30d    = EXCLUDED.volatility_30d,
        rsi_14            = EXCLUDED.rsi_14,
        price_vs_ma30_pct = EXCLUDED.price_vs_ma30_pct,
        updated_at        = CURRENT_TIMESTAMP;

    GET DIAGNOSTICS v_rows_upserted = ROW_COUNT;
    RAISE NOTICE '[sp_calculate_metrics] Upserted % metric rows for commodity_key=%.',
                 v_rows_upserted, p_commodity_key;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION '[sp_calculate_metrics] Failed for commodity_key=%, range % → %: %  (SQLSTATE: %)',
                        p_commodity_key, v_start_date, v_end_date, SQLERRM, SQLSTATE;
END;
$$;

COMMENT ON FUNCTION analytics.sp_calculate_metrics(INT, DATE, DATE) IS
'Computes MA-7, MA-30, MA-90, 30-day rolling volatility, 14-day RSI, and price_vs_ma30_pct for a commodity over a date range. Includes a 90-day warm-up buffer before p_start_date for accurate window calculations. Upserts into analytics.price_metrics.';


-- =============================================================================
-- 5. analytics.sp_aggregate_monthly
-- Computes monthly aggregate statistics for all commodities in a given month.
-- Defaults to the current calendar month if no arguments provided.
-- =============================================================================
CREATE OR REPLACE FUNCTION analytics.sp_aggregate_monthly(
    p_year      INT  DEFAULT NULL,
    p_month     INT  DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql AS $$
DECLARE
    v_year          INT;
    v_month         INT;
    v_rows_upserted INT;
BEGIN
    v_year  := COALESCE(p_year,  EXTRACT(YEAR  FROM CURRENT_DATE)::INT);
    v_month := COALESCE(p_month, EXTRACT(MONTH FROM CURRENT_DATE)::INT);

    RAISE NOTICE '[sp_aggregate_monthly] Processing %-%',
                 v_year, LPAD(v_month::TEXT, 2, '0');

    INSERT INTO analytics.monthly_summary (
        commodity_key,
        year,
        month,
        avg_close,
        min_close,
        max_close,
        avg_volume,
        total_volume,
        volatility,
        trading_days,
        monthly_return_pct,
        updated_at
    )
    WITH monthly_prices AS (
        SELECT
            f.commodity_key,
            f.price_close,
            f.volume,
            d.full_date,
            -- First and last close in the month (for return calculation)
            FIRST_VALUE(f.price_close) OVER (
                PARTITION BY f.commodity_key
                ORDER BY d.full_date ASC
                ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
            ) AS first_close,
            LAST_VALUE(f.price_close) OVER (
                PARTITION BY f.commodity_key
                ORDER BY d.full_date ASC
                ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
            ) AS last_close
        FROM   warehouse.fact_oil_prices f
        JOIN   warehouse.dim_date        d ON d.date_key = f.date_key
        WHERE  d.year  = v_year
          AND  d.month = v_month
    )
    SELECT
        commodity_key,
        v_year::SMALLINT                                            AS year,
        v_month::SMALLINT                                           AS month,
        ROUND(AVG(price_close), 4)                                  AS avg_close,
        MIN(price_close)                                            AS min_close,
        MAX(price_close)                                            AS max_close,
        AVG(volume)::BIGINT                                         AS avg_volume,
        SUM(volume)                                                 AS total_volume,
        ROUND(STDDEV_SAMP(price_close)::DECIMAL, 4)                 AS volatility,
        COUNT(*)::SMALLINT                                          AS trading_days,
        ROUND(
            ((MAX(last_close) - MAX(first_close)) / NULLIF(MAX(first_close), 0)) * 100,
            4
        )                                                           AS monthly_return_pct,
        CURRENT_TIMESTAMP                                           AS updated_at
    FROM monthly_prices
    GROUP BY commodity_key
    ON CONFLICT (commodity_key, year, month) DO UPDATE SET
        avg_close          = EXCLUDED.avg_close,
        min_close          = EXCLUDED.min_close,
        max_close          = EXCLUDED.max_close,
        avg_volume         = EXCLUDED.avg_volume,
        total_volume       = EXCLUDED.total_volume,
        volatility         = EXCLUDED.volatility,
        trading_days       = EXCLUDED.trading_days,
        monthly_return_pct = EXCLUDED.monthly_return_pct,
        updated_at         = CURRENT_TIMESTAMP;

    GET DIAGNOSTICS v_rows_upserted = ROW_COUNT;
    RAISE NOTICE '[sp_aggregate_monthly] Upserted % commodity rows for %-%.', v_rows_upserted, v_year, v_month;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION '[sp_aggregate_monthly] Failed for %-% : %  (SQLSTATE: %)',
                        v_year, v_month, SQLERRM, SQLSTATE;
END;
$$;

COMMENT ON FUNCTION analytics.sp_aggregate_monthly(INT, INT) IS
'Aggregates monthly OHLCV statistics (avg, min, max, total volume, volatility, trading days, monthly return %) for all commodities in the specified year/month. Defaults to current month. Upserts into analytics.monthly_summary.';


-- =============================================================================
-- 6. warehouse.sp_manage_scd2
-- Handles a Slowly Changing Dimension Type 2 update on dim_commodity.
-- Expires the current row (set is_current=FALSE, valid_to=NOW()),
-- then inserts a new version with the updated field and version+1.
-- =============================================================================
CREATE OR REPLACE FUNCTION warehouse.sp_manage_scd2(
    p_commodity_id  VARCHAR(20),
    p_field_name    VARCHAR(100),
    p_new_value     VARCHAR(500)
)
RETURNS VOID
LANGUAGE plpgsql AS $$
DECLARE
    v_old_record        warehouse.dim_commodity%ROWTYPE;
    v_new_key           INTEGER;
    v_now               TIMESTAMP := CURRENT_TIMESTAMP;
BEGIN
    RAISE NOTICE '[sp_manage_scd2] Updating commodity_id=%, field=%, new_value=%',
                 p_commodity_id, p_field_name, p_new_value;

    -- -------------------------------------------------------------------------
    -- Step 1: Lock and fetch current version
    -- -------------------------------------------------------------------------
    SELECT *
    INTO   v_old_record
    FROM   warehouse.dim_commodity
    WHERE  commodity_id = p_commodity_id
      AND  is_current   = TRUE
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION '[sp_manage_scd2] No current record found for commodity_id=%', p_commodity_id;
    END IF;

    -- -------------------------------------------------------------------------
    -- Step 2: Expire current version
    -- -------------------------------------------------------------------------
    UPDATE warehouse.dim_commodity
    SET    is_current = FALSE,
           valid_to   = v_now,
           updated_at = v_now
    WHERE  commodity_key = v_old_record.commodity_key;

    -- -------------------------------------------------------------------------
    -- Step 3: Build new version — copy all fields, override changed one
    -- -------------------------------------------------------------------------
    INSERT INTO warehouse.dim_commodity (
        commodity_id,
        commodity_name,
        category,
        sub_category,
        currency,
        exchange,
        unit_of_measure,
        is_current,
        valid_from,
        valid_to,
        version,
        created_at,
        updated_at
    )
    VALUES (
        v_old_record.commodity_id,
        CASE WHEN p_field_name = 'commodity_name'  THEN p_new_value ELSE v_old_record.commodity_name  END,
        CASE WHEN p_field_name = 'category'         THEN p_new_value ELSE v_old_record.category         END,
        CASE WHEN p_field_name = 'sub_category'     THEN p_new_value ELSE v_old_record.sub_category     END,
        CASE WHEN p_field_name = 'currency'         THEN p_new_value ELSE v_old_record.currency         END,
        CASE WHEN p_field_name = 'exchange'         THEN p_new_value ELSE v_old_record.exchange         END,
        CASE WHEN p_field_name = 'unit_of_measure'  THEN p_new_value ELSE v_old_record.unit_of_measure  END,
        TRUE,           -- is_current
        v_now,          -- valid_from
        '9999-12-31 23:59:59'::TIMESTAMP,
        v_old_record.version + 1,
        v_old_record.created_at,   -- preserve original creation date
        v_now
    )
    RETURNING commodity_key INTO v_new_key;

    RAISE NOTICE '[sp_manage_scd2] Expired key=%, created new key=% (version=%)',
                 v_old_record.commodity_key, v_new_key, v_old_record.version + 1;

EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION '[sp_manage_scd2] Failed for commodity_id=%: %  (SQLSTATE: %)',
                        p_commodity_id, SQLERRM, SQLSTATE;
END;
$$;

COMMENT ON FUNCTION warehouse.sp_manage_scd2(VARCHAR, VARCHAR, VARCHAR) IS
'SCD Type 2 update for dim_commodity. Expires the current version (is_current=FALSE, valid_to=NOW()) and inserts a new version with the specified field changed, version incremented by 1. Preserves full audit history.';
