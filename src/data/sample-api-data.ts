// Sample data sourced from the real API responses in the JSON files.
// Used as fallback when the live API is unreachable (static site deployment).

import rawHistory from './sample-history.json';
import rawMonthlySummary from './sample-monthly-summary.json';
import rawPriceMetrics from './sample-price-metrics.json';
import rawComparison from './sample-commodity-comparison.json';

export type ApiEnvelope<T> = {
  status: 'success';
  data: T[];
  meta: { count: number; source: string; query_time_ms: number };
};

export type PriceRecord = {
  commodity_id: string;
  trade_date: string;
  price_open: number;
  price_high: number;
  price_low: number;
  price_close: number;
  volume: number;
};

export type MonthlySummaryRecord = {
  commodity_id: string;
  commodity_name: string;
  year: number;
  month: number;
  trading_days: number;
  avg_close: number;
  min_close: number;
  max_close: number;
  stddev_close: number;
  total_volume: number;
  monthly_return_pct: number;
};

export type CommodityComparisonRecord = {
  date: string;
  wti_close: number;
  brent_close: number;
  spread: number;
  ratio: number;
};

export type PriceMetricsRecord = {
  commodity_id: string;
  date: string;
  close: number;
  ma_7: number;
  ma_30: number;
  ma_90: number;
  volatility_20d: number;
  bollinger_upper: number;
  bollinger_lower: number;
};

// ── Helpers ──────────────────────────────────────────────────────────────────

type RawHistoryRow = {
  commodity_id: string;
  trade_date: string;
  price_open: string | number;
  price_high: string | number;
  price_low: string | number;
  price_close: string | number;
  volume: number;
};

type RawMonthlyRow = {
  symbol: string;
  commodity_name: string;
  year: number;
  month: number;
  trading_days: number;
  avg_close: number;
  min_close: number;
  max_close: number;
  stddev_close: number;
  total_volume: string | number;
  monthly_return_pct: number;
};

type RawComparisonRow = {
  trade_date: string;
  wti_close: number;
  brent_close: number;
  spread: number;
  ratio: number;
};

type RawMetricsRow = {
  symbol: string;
  trade_date: string;
  close: number;
  ma7: number | null;
  ma30: number | null;
  ma90: number | null;
  volatility_20d: number | null;
  bollinger_upper: number | null;
  bollinger_lower: number | null;
};

// ── Transformed exports ───────────────────────────────────────────────────────

const historyRows = (rawHistory.data as unknown as RawHistoryRow[])
  .filter((r) => r.commodity_id === 'CL=F')
  .sort((a, b) => a.trade_date.localeCompare(b.trade_date))
  .slice(-90)
  .map((r): PriceRecord => ({
    commodity_id: r.commodity_id,
    trade_date: r.trade_date,
    price_open: parseFloat(String(r.price_open)),
    price_high: parseFloat(String(r.price_high)),
    price_low: parseFloat(String(r.price_low)),
    price_close: parseFloat(String(r.price_close)),
    volume: r.volume,
  }));

export const samplePriceHistory: ApiEnvelope<PriceRecord> = {
  status: 'success',
  data: historyRows,
  meta: { count: historyRows.length, source: 'sample', query_time_ms: 4 },
};

const monthlyRows = (rawMonthlySummary.data as unknown as RawMonthlyRow[])
  .filter((r) => r.symbol === 'CL=F')
  .map((r): MonthlySummaryRecord => ({
    commodity_id: r.symbol,
    commodity_name: r.commodity_name,
    year: r.year,
    month: r.month,
    trading_days: r.trading_days,
    avg_close: r.avg_close,
    min_close: r.min_close,
    max_close: r.max_close,
    stddev_close: r.stddev_close,
    total_volume: parseFloat(String(r.total_volume)),
    monthly_return_pct: r.monthly_return_pct,
  }));

export const sampleMonthlySummary: ApiEnvelope<MonthlySummaryRecord> = {
  status: 'success',
  data: monthlyRows,
  meta: { count: monthlyRows.length, source: 'sample', query_time_ms: 7 },
};

const comparisonRows = (rawComparison.data as unknown as RawComparisonRow[])
  .slice(-90)
  .map((r): CommodityComparisonRecord => ({
    date: r.trade_date,
    wti_close: r.wti_close,
    brent_close: r.brent_close,
    spread: r.spread,
    ratio: r.ratio,
  }));

export const sampleComparison: ApiEnvelope<CommodityComparisonRecord> = {
  status: 'success',
  data: comparisonRows,
  meta: { count: comparisonRows.length, source: 'sample', query_time_ms: 5 },
};

const metricsRows = (rawPriceMetrics.data as unknown as RawMetricsRow[])
  .filter((r) => r.symbol === 'CL=F' && r.volatility_20d !== null && r.bollinger_upper !== null && r.bollinger_lower !== null)
  .slice(-90)
  .map((r): PriceMetricsRecord => ({
    commodity_id: r.symbol,
    date: r.trade_date,
    close: r.close,
    ma_7: r.ma7 ?? r.close,
    ma_30: r.ma30 ?? r.close,
    ma_90: r.ma90 ?? r.close,
    volatility_20d: r.volatility_20d!,
    bollinger_upper: r.bollinger_upper!,
    bollinger_lower: r.bollinger_lower!,
  }));

export const samplePriceMetrics: ApiEnvelope<PriceMetricsRecord> = {
  status: 'success',
  data: metricsRows,
  meta: { count: metricsRows.length, source: 'sample', query_time_ms: 6 },
};
