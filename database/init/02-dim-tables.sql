-- =============================================================================
-- 02-dim-tables.sql
-- Dimension tables for the oil price star schema
-- Dimensions: dim_date, dim_commodity, dim_source
-- =============================================================================

-- ---------------------------------------------------------------------------
-- warehouse.dim_date
-- Date dimension pre-populated via 09-seed-data.sql.
-- Surrogate key uses YYYYMMDD integer format for fast range filtering.
-- ---------------------------------------------------------------------------
CREATE TABLE warehouse.dim_date (
    date_key        INTEGER     NOT NULL,
    full_date       DATE        NOT NULL,
    day_of_week     SMALLINT    NOT NULL,   -- 1=Monday … 7=Sunday (ISO)
    day_name        VARCHAR(10) NOT NULL,
    day_of_month    SMALLINT    NOT NULL,
    day_of_year     SMALLINT    NOT NULL,
    week_of_year    SMALLINT    NOT NULL,
    month           SMALLINT    NOT NULL,
    month_name      VARCHAR(10) NOT NULL,
    quarter         SMALLINT    NOT NULL,
    year            SMALLINT    NOT NULL,
    is_weekend      BOOLEAN     NOT NULL DEFAULT FALSE,
    is_trading_day  BOOLEAN     NOT NULL DEFAULT TRUE,  -- FALSE on weekends/holidays
    fiscal_quarter  SMALLINT    NOT NULL,
    fiscal_year     SMALLINT    NOT NULL,

    CONSTRAINT pk_dim_date PRIMARY KEY (date_key),
    CONSTRAINT uq_dim_date_full_date UNIQUE (full_date),

    CONSTRAINT chk_dim_date_day_of_week  CHECK (day_of_week  BETWEEN 1 AND 7),
    CONSTRAINT chk_dim_date_month        CHECK (month        BETWEEN 1 AND 12),
    CONSTRAINT chk_dim_date_quarter      CHECK (quarter      BETWEEN 1 AND 4),
    CONSTRAINT chk_dim_date_fiscal_qtr   CHECK (fiscal_quarter BETWEEN 1 AND 4)
);

COMMENT ON TABLE  warehouse.dim_date IS 'Date dimension. Covers 2020-01-01 to 2035-12-31. Surrogate key is YYYYMMDD integer.';
COMMENT ON COLUMN warehouse.dim_date.date_key       IS 'Surrogate key in YYYYMMDD format (e.g. 20240115). Enables efficient date range queries.';
COMMENT ON COLUMN warehouse.dim_date.full_date      IS 'Calendar date. Natural key.';
COMMENT ON COLUMN warehouse.dim_date.day_of_week    IS 'ISO day of week: 1=Monday, 7=Sunday.';
COMMENT ON COLUMN warehouse.dim_date.is_weekend     IS 'TRUE for Saturday and Sunday.';
COMMENT ON COLUMN warehouse.dim_date.is_trading_day IS 'TRUE for weekdays. Set to FALSE manually for public holidays.';
COMMENT ON COLUMN warehouse.dim_date.fiscal_quarter IS 'Fiscal quarter. Assumes fiscal year starts January (aligns with calendar year). Adjust if needed.';
COMMENT ON COLUMN warehouse.dim_date.fiscal_year    IS 'Fiscal year. Same as calendar year here. Override for non-calendar fiscal years.';


-- ---------------------------------------------------------------------------
-- warehouse.dim_commodity
-- SCD Type 2: tracks history of commodity attribute changes.
-- is_current = TRUE identifies the active record.
-- valid_from / valid_to form the effective date range.
-- ---------------------------------------------------------------------------
CREATE TABLE warehouse.dim_commodity (
    commodity_key   SERIAL          NOT NULL,
    commodity_id    VARCHAR(20)     NOT NULL,   -- ticker symbol, e.g. 'CL=F'
    commodity_name  VARCHAR(100)    NOT NULL DEFAULT 'Unknown',
    category        VARCHAR(50)     NOT NULL DEFAULT 'Energy',
    sub_category    VARCHAR(50),
    currency        CHAR(3)         NOT NULL DEFAULT 'USD',
    exchange        VARCHAR(50),
    unit_of_measure VARCHAR(20)     NOT NULL DEFAULT 'barrel',
    is_current      BOOLEAN         NOT NULL DEFAULT TRUE,
    valid_from      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_to        TIMESTAMP       NOT NULL DEFAULT '9999-12-31 23:59:59',
    version         INTEGER         NOT NULL DEFAULT 1,
    created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_dim_commodity PRIMARY KEY (commodity_key),
    CONSTRAINT chk_dim_commodity_currency CHECK (currency ~ '^[A-Z]{3}$'),
    CONSTRAINT chk_dim_commodity_version  CHECK (version >= 1),
    CONSTRAINT chk_dim_commodity_dates    CHECK (valid_from <= valid_to)
);

COMMENT ON TABLE  warehouse.dim_commodity IS 'Commodity dimension with SCD Type 2 support. Each change to commodity attributes creates a new row; previous row gets valid_to stamped and is_current set to FALSE.';
COMMENT ON COLUMN warehouse.dim_commodity.commodity_key   IS 'Surrogate key. Auto-incremented. Unique per version.';
COMMENT ON COLUMN warehouse.dim_commodity.commodity_id    IS 'Natural key: ticker symbol (e.g. CL=F for WTI crude on CME).';
COMMENT ON COLUMN warehouse.dim_commodity.is_current      IS 'TRUE for the active/current version of a commodity record.';
COMMENT ON COLUMN warehouse.dim_commodity.valid_from      IS 'Timestamp when this version became effective.';
COMMENT ON COLUMN warehouse.dim_commodity.valid_to        IS 'Timestamp when this version was superseded. 9999-12-31 means still current.';
COMMENT ON COLUMN warehouse.dim_commodity.version         IS 'Sequential version number per commodity_id. Starts at 1.';
COMMENT ON COLUMN warehouse.dim_commodity.sub_category    IS 'e.g. Fossil Fuels, Renewables.';
COMMENT ON COLUMN warehouse.dim_commodity.unit_of_measure IS 'e.g. barrel, MMBtu (million British thermal units for natural gas).';


-- ---------------------------------------------------------------------------
-- warehouse.dim_source
-- Tracks where price data was obtained from.
-- ---------------------------------------------------------------------------
CREATE TABLE warehouse.dim_source (
    source_key        SERIAL          NOT NULL,
    source_name       VARCHAR(100)    NOT NULL,
    source_type       VARCHAR(30)     NOT NULL DEFAULT 'API',  -- API | Manual | Scraper | File
    api_endpoint      VARCHAR(500),
    reliability_score DECIMAL(3,2)    NOT NULL DEFAULT 0.80,
    is_active         BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at        TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_dim_source PRIMARY KEY (source_key),
    CONSTRAINT uq_dim_source_name UNIQUE (source_name),
    CONSTRAINT chk_dim_source_type  CHECK (source_type IN ('API', 'Manual', 'Scraper', 'File', 'Stream')),
    CONSTRAINT chk_dim_source_score CHECK (reliability_score BETWEEN 0.00 AND 1.00)
);

COMMENT ON TABLE  warehouse.dim_source IS 'Data source dimension. Records where each price observation originated.';
COMMENT ON COLUMN warehouse.dim_source.source_key        IS 'Surrogate key.';
COMMENT ON COLUMN warehouse.dim_source.source_name       IS 'Human-readable source name, e.g. Yahoo Finance, Manual Entry.';
COMMENT ON COLUMN warehouse.dim_source.source_type       IS 'Ingestion method: API, Manual, Scraper, File, or Stream.';
COMMENT ON COLUMN warehouse.dim_source.api_endpoint      IS 'Base URL of the API endpoint if source_type = API.';
COMMENT ON COLUMN warehouse.dim_source.reliability_score IS 'Subjective reliability score 0.00–1.00. Used to weight conflicting prices.';
COMMENT ON COLUMN warehouse.dim_source.is_active         IS 'FALSE when a source is deprecated but historical records must be kept.';
