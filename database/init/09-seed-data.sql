-- =============================================================================
-- 09-seed-data.sql
-- Seed reference data:
--   1. warehouse.dim_date     → 2020-01-01 to 2035-12-31 via generate_series()
--   2. warehouse.dim_commodity → 4 energy futures
--   3. warehouse.dim_source    → 2 data sources
-- =============================================================================

DO $$ BEGIN RAISE NOTICE 'Seeding warehouse.dim_date (2020-01-01 to 2035-12-31)...'; END $$;

-- ---------------------------------------------------------------------------
-- 1. Populate warehouse.dim_date
-- ---------------------------------------------------------------------------
INSERT INTO warehouse.dim_date (
    date_key,
    full_date,
    day_of_week,
    day_name,
    day_of_month,
    day_of_year,
    week_of_year,
    month,
    month_name,
    quarter,
    year,
    is_weekend,
    is_trading_day,
    fiscal_quarter,
    fiscal_year
)
SELECT
    TO_CHAR(d, 'YYYYMMDD')::INTEGER                     AS date_key,
    d                                                   AS full_date,
    EXTRACT(ISODOW  FROM d)::SMALLINT                   AS day_of_week,    -- 1=Mon … 7=Sun (ISO)
    TRIM(TO_CHAR(d, 'Day'))                             AS day_name,
    EXTRACT(DAY     FROM d)::SMALLINT                   AS day_of_month,
    EXTRACT(DOY     FROM d)::SMALLINT                   AS day_of_year,
    EXTRACT(WEEK    FROM d)::SMALLINT                   AS week_of_year,
    EXTRACT(MONTH   FROM d)::SMALLINT                   AS month,
    TRIM(TO_CHAR(d, 'Month'))                           AS month_name,
    EXTRACT(QUARTER FROM d)::SMALLINT                   AS quarter,
    EXTRACT(YEAR    FROM d)::SMALLINT                   AS year,
    EXTRACT(ISODOW  FROM d) IN (6, 7)                   AS is_weekend,
    EXTRACT(ISODOW  FROM d) NOT IN (6, 7)               AS is_trading_day, -- weekdays only; public holidays not filtered
    EXTRACT(QUARTER FROM d)::SMALLINT                   AS fiscal_quarter, -- calendar = fiscal here; adjust if needed
    EXTRACT(YEAR    FROM d)::SMALLINT                   AS fiscal_year
FROM generate_series(
    '2020-01-01'::DATE,
    '2035-12-31'::DATE,
    '1 day'::INTERVAL
) AS d
ON CONFLICT (date_key) DO NOTHING;

DO $$ BEGIN RAISE NOTICE 'dim_date: % rows inserted.', (SELECT COUNT(*) FROM warehouse.dim_date); END $$;


-- ---------------------------------------------------------------------------
-- 2. Populate warehouse.dim_commodity
-- Four major energy futures traded on NYMEX / ICE
-- ---------------------------------------------------------------------------
INSERT INTO warehouse.dim_commodity
    (commodity_id, commodity_name, category, sub_category, currency, exchange, unit_of_measure)
VALUES
    ('CL=F', 'WTI Crude Oil',       'Energy', 'Crude Oil',        'USD', 'NYMEX', 'barrel'),
    ('BZ=F', 'Brent Crude Oil',     'Energy', 'Crude Oil',        'USD', 'ICE',   'barrel'),
    ('NG=F', 'Natural Gas',         'Energy', 'Natural Gas',      'USD', 'NYMEX', 'MMBtu'),
    ('HO=F', 'Heating Oil (ULSD)',  'Energy', 'Refined Products', 'USD', 'NYMEX', 'gallon')
ON CONFLICT DO NOTHING;

DO $$ BEGIN RAISE NOTICE 'dim_commodity: % rows total.', (SELECT COUNT(*) FROM warehouse.dim_commodity); END $$;


-- ---------------------------------------------------------------------------
-- 3. Populate warehouse.dim_source
-- ---------------------------------------------------------------------------
INSERT INTO warehouse.dim_source
    (source_name, source_type, api_endpoint, reliability_score, is_active)
VALUES
    ('Yahoo Finance', 'API',    'https://query1.finance.yahoo.com/v8/finance/chart/', 0.85, TRUE),
    ('Manual Entry',  'Manual', NULL,                                                  1.00, TRUE)
ON CONFLICT (source_name) DO NOTHING;

DO $$ BEGIN RAISE NOTICE 'dim_source: % rows total.', (SELECT COUNT(*) FROM warehouse.dim_source); END $$;
