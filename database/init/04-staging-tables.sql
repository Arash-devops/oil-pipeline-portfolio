-- =============================================================================
-- 04-staging-tables.sql
-- Staging / landing zone tables.
-- Raw data arrives here. Validation runs in-place, then sp_process_staging()
-- promotes valid records to warehouse.fact_oil_prices.
-- =============================================================================

CREATE TABLE staging.stg_oil_prices (
    staging_id          BIGSERIAL       NOT NULL,
    symbol              VARCHAR(20),
    trade_date          DATE,
    price_open          DECIMAL(12,4),
    price_high          DECIMAL(12,4),
    price_low           DECIMAL(12,4),
    price_close         DECIMAL(12,4),
    adj_close           DECIMAL(12,4),
    volume              BIGINT,
    source_name         VARCHAR(100),
    loaded_at           TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_processed        BOOLEAN         NOT NULL DEFAULT FALSE,
    is_valid            BOOLEAN,                -- NULL = not yet validated
    validation_errors   TEXT,                   -- pipe-separated list of failures
    processed_at        TIMESTAMP,

    CONSTRAINT pk_stg_oil_prices PRIMARY KEY (staging_id)
);

COMMENT ON TABLE  staging.stg_oil_prices IS 'Raw landing table. No FK constraints intentionally — bad data is expected here. Validation occurs via sp_validate_staging_data().';
COMMENT ON COLUMN staging.stg_oil_prices.staging_id        IS 'Auto-incremented surrogate key for the staging row.';
COMMENT ON COLUMN staging.stg_oil_prices.symbol            IS 'Commodity ticker as received from the source. May be dirty / unmapped.';
COMMENT ON COLUMN staging.stg_oil_prices.trade_date        IS 'Trading date as received. May be NULL or future-dated (caught by validation).';
COMMENT ON COLUMN staging.stg_oil_prices.is_processed      IS 'TRUE once the row has been promoted to warehouse (regardless of validity).';
COMMENT ON COLUMN staging.stg_oil_prices.is_valid          IS 'NULL = not yet validated. TRUE = passed all checks. FALSE = failed one or more checks.';
COMMENT ON COLUMN staging.stg_oil_prices.validation_errors IS 'Semicolon-separated descriptions of validation failures. NULL when valid.';
COMMENT ON COLUMN staging.stg_oil_prices.processed_at      IS 'Timestamp when sp_process_staging() handled this row.';
