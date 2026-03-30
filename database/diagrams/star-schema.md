# Oil Price Data Warehouse — Star Schema

## Entity Relationship Diagram (Mermaid)

```mermaid
erDiagram
    DIM_DATE {
        int     date_key        PK
        date    full_date       UK
        smallint day_of_week
        varchar  day_name
        smallint day_of_month
        smallint day_of_year
        smallint week_of_year
        smallint month
        varchar  month_name
        smallint quarter
        smallint year
        boolean  is_weekend
        boolean  is_trading_day
        smallint fiscal_quarter
        smallint fiscal_year
    }

    DIM_COMMODITY {
        serial   commodity_key  PK
        varchar  commodity_id
        varchar  commodity_name
        varchar  category
        varchar  sub_category
        char     currency
        varchar  exchange
        varchar  unit_of_measure
        boolean  is_current
        timestamp valid_from
        timestamp valid_to
        int      version
    }

    DIM_SOURCE {
        serial   source_key     PK
        varchar  source_name    UK
        varchar  source_type
        varchar  api_endpoint
        decimal  reliability_score
        boolean  is_active
    }

    FACT_OIL_PRICES {
        bigserial price_key     PK
        int       date_key      FK
        int       commodity_key FK
        int       source_key    FK
        decimal   price_open
        decimal   price_high
        decimal   price_low
        decimal   price_close
        decimal   adj_close
        bigint    volume
        decimal   daily_change
        decimal   daily_change_pct
    }

    ANALYTICS_MONTHLY_SUMMARY {
        bigserial summary_key   PK
        int       commodity_key FK
        smallint  year
        smallint  month
        decimal   avg_close
        decimal   min_close
        decimal   max_close
        bigint    avg_volume
        bigint    total_volume
        decimal   volatility
        smallint  trading_days
        decimal   monthly_return_pct
    }

    ANALYTICS_PRICE_METRICS {
        bigserial metric_key    PK
        int       date_key      FK
        int       commodity_key FK
        decimal   ma_7
        decimal   ma_30
        decimal   ma_90
        decimal   volatility_30d
        decimal   rsi_14
        decimal   price_vs_ma30_pct
    }

    STAGING_OIL_PRICES {
        bigserial staging_id    PK
        varchar   symbol
        date      trade_date
        decimal   price_close
        decimal   price_open
        decimal   price_high
        decimal   price_low
        bigint    volume
        varchar   source_name
        boolean   is_processed
        boolean   is_valid
        text      validation_errors
    }

    FACT_OIL_PRICES       }|--|| DIM_DATE            : "date_key"
    FACT_OIL_PRICES       }|--|| DIM_COMMODITY        : "commodity_key"
    FACT_OIL_PRICES       }|--|| DIM_SOURCE           : "source_key"
    ANALYTICS_MONTHLY_SUMMARY }|--|| DIM_COMMODITY    : "commodity_key"
    ANALYTICS_PRICE_METRICS   }|--|| DIM_DATE         : "date_key"
    ANALYTICS_PRICE_METRICS   }|--|| DIM_COMMODITY    : "commodity_key"
```

---

## ASCII Star Schema Overview

```
                         ┌─────────────────────┐
                         │    DIM_DATE          │
                         │  (date_key PK)       │
                         │  full_date           │
                         │  year, month, day    │
                         │  is_trading_day      │
                         └──────────┬──────────┘
                                    │ FK: date_key
                                    │
┌──────────────────┐     ┌──────────▼──────────┐     ┌──────────────────────┐
│  DIM_COMMODITY   │     │  FACT_OIL_PRICES     │     │    DIM_SOURCE        │
│  (commodity_key) ├────▶│  price_key  (PK)     │◀────┤  (source_key PK)     │
│  commodity_id    │     │  date_key   (FK)     │     │  source_name         │
│  commodity_name  │     │  commodity_key (FK)  │     │  source_type         │
│  category        │     │  source_key (FK)     │     │  reliability_score   │
│  SCD Type 2      │     │  price_open          │     └──────────────────────┘
│  is_current      │     │  price_high          │
└──────────────────┘     │  price_low           │
                         │  price_close  ◀──────┼─── PRIMARY MEASURE
                         │  volume              │
                         │  daily_change        │
                         │  daily_change_pct    │
                         └──────────┬───────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
         ┌──────────▼───────────┐   ┌───────────────▼──────────┐
         │ ANALYTICS_MONTHLY    │   │  ANALYTICS_PRICE_METRICS  │
         │ _SUMMARY             │   │                           │
         │ (commodity,year,mon) │   │  (date_key, commodity)    │
         │ avg_close            │   │  ma_7, ma_30, ma_90       │
         │ volatility           │   │  volatility_30d           │
         │ monthly_return_pct   │   │  rsi_14                   │
         └──────────────────────┘   └───────────────────────────┘

STAGING (separate schema — no FKs by design):
         ┌──────────────────────────────────────┐
         │  STAGING.STG_OIL_PRICES              │
         │  symbol (raw), trade_date (raw)      │
         │  is_valid, validation_errors         │
         │  is_processed, processed_at          │
         │         │                            │
         │         └──▶ sp_process_staging() ──▶│──▶ FACT_OIL_PRICES
         └──────────────────────────────────────┘
```

---

## Data Flow

```
External Source (Yahoo Finance API / Manual)
        │
        ▼
staging.stg_oil_prices          ← raw, no FK constraints
        │
        ├──▶ staging.sp_validate_staging_data()
        │           └── marks is_valid / validation_errors
        │
        └──▶ warehouse.sp_process_staging()
                    ├── calls sp_upsert_oil_price() per row
                    └── resolves/creates dim keys on the fly
                                │
                                ▼
                warehouse.fact_oil_prices   ← clean, conformed
                                │
                                ├──▶ analytics.sp_calculate_metrics()
                                │           └── analytics.price_metrics (MA, RSI, σ)
                                │
                                └──▶ analytics.sp_aggregate_monthly()
                                            └── analytics.monthly_summary
```
