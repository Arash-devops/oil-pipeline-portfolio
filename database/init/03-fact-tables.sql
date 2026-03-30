-- =============================================================================
-- 03-fact-tables.sql
-- Fact table: warehouse.fact_oil_prices
-- Central table of the star schema. Each row = one daily OHLCV observation
-- for one commodity from one source.
-- =============================================================================

CREATE TABLE warehouse.fact_oil_prices (
    price_key           BIGSERIAL       NOT NULL,
    date_key            INTEGER         NOT NULL,
    commodity_key       INTEGER         NOT NULL,
    source_key          INTEGER         NOT NULL,
    price_open          DECIMAL(12,4),
    price_high          DECIMAL(12,4),
    price_low           DECIMAL(12,4),
    price_close         DECIMAL(12,4)   NOT NULL,
    adj_close           DECIMAL(12,4),
    volume              BIGINT,
    daily_change        DECIMAL(12,4),  -- price_close - previous_day_close
    daily_change_pct    DECIMAL(8,4),   -- daily_change / previous_close * 100
    created_at          TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_fact_oil_prices
        PRIMARY KEY (price_key),

    CONSTRAINT uq_fact_oil_prices_natural
        UNIQUE (date_key, commodity_key, source_key),

    CONSTRAINT fk_fact_date
        FOREIGN KEY (date_key)
        REFERENCES warehouse.dim_date(date_key)
        ON DELETE RESTRICT,

    CONSTRAINT fk_fact_commodity
        FOREIGN KEY (commodity_key)
        REFERENCES warehouse.dim_commodity(commodity_key)
        ON DELETE RESTRICT,

    CONSTRAINT fk_fact_source
        FOREIGN KEY (source_key)
        REFERENCES warehouse.dim_source(source_key)
        ON DELETE RESTRICT,

    CONSTRAINT chk_fact_price_close_positive
        CHECK (price_close > 0),

    CONSTRAINT chk_fact_price_high_gte_low
        CHECK (price_high IS NULL OR price_low IS NULL OR price_high >= price_low),

    CONSTRAINT chk_fact_price_open_positive
        CHECK (price_open IS NULL OR price_open > 0),

    CONSTRAINT chk_fact_volume_non_negative
        CHECK (volume IS NULL OR volume >= 0)
);

COMMENT ON TABLE  warehouse.fact_oil_prices IS 'Central fact table. One row per trading day per commodity per data source. Grain: daily OHLCV.';
COMMENT ON COLUMN warehouse.fact_oil_prices.price_key         IS 'Surrogate key. BIGSERIAL for high-volume inserts.';
COMMENT ON COLUMN warehouse.fact_oil_prices.date_key          IS 'FK to dim_date. YYYYMMDD integer format.';
COMMENT ON COLUMN warehouse.fact_oil_prices.commodity_key     IS 'FK to dim_commodity. Points to current version unless historical re-processing.';
COMMENT ON COLUMN warehouse.fact_oil_prices.source_key        IS 'FK to dim_source. Allows multi-source price comparison.';
COMMENT ON COLUMN warehouse.fact_oil_prices.price_open        IS 'Opening price for the trading session.';
COMMENT ON COLUMN warehouse.fact_oil_prices.price_high        IS 'Intraday high.';
COMMENT ON COLUMN warehouse.fact_oil_prices.price_low         IS 'Intraday low.';
COMMENT ON COLUMN warehouse.fact_oil_prices.price_close       IS 'Official closing price. NOT NULL — primary measure of record.';
COMMENT ON COLUMN warehouse.fact_oil_prices.adj_close         IS 'Adjusted close accounting for splits/dividends. For commodities this is typically same as close.';
COMMENT ON COLUMN warehouse.fact_oil_prices.volume            IS 'Number of contracts traded (futures). NULL if not available.';
COMMENT ON COLUMN warehouse.fact_oil_prices.daily_change      IS 'Absolute change: price_close minus previous trading day close. NULL for first record.';
COMMENT ON COLUMN warehouse.fact_oil_prices.daily_change_pct  IS 'Percentage change from previous close. NULL for first record.';
