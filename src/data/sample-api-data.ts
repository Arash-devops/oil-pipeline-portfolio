// Sample data matching the exact FastAPI response envelope: { status, data, meta }
// Used as fallback when the live API is unreachable (static site deployment).

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

// 90 days of WTI price history
export const samplePriceHistory: ApiEnvelope<PriceRecord> = {
  status: 'success',
  data: (() => {
    const rows: PriceRecord[] = [];
    const start = new Date('2025-12-01');
    let price = 74.2;
    for (let i = 0; i < 90; i++) {
      const d = new Date(start);
      d.setDate(start.getDate() + i);
      const day = d.getDay();
      if (day === 0 || day === 6) continue;
      const change = (Math.random() - 0.48) * 2.4;
      price = Math.max(60, Math.min(95, price + change));
      const open = price + (Math.random() - 0.5) * 1.2;
      const hi = Math.max(open, price) + Math.random() * 1.5;
      const lo = Math.min(open, price) - Math.random() * 1.5;
      rows.push({
        commodity_id: 'CL=F',
        trade_date: d.toISOString().slice(0, 10),
        price_open: +open.toFixed(2),
        price_high: +hi.toFixed(2),
        price_low: +lo.toFixed(2),
        price_close: +price.toFixed(2),
        volume: Math.floor(200000 + Math.random() * 300000),
      });
    }
    return rows;
  })(),
  meta: { count: 63, source: 'sample', query_time_ms: 4 },
};

// 18 months of monthly summaries for WTI (Aug 2024 – Feb 2026)
export const sampleMonthlySummary: ApiEnvelope<MonthlySummaryRecord> = {
  status: 'success',
  data: [
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2024, month: 8,  trading_days: 22, avg_close: 76.3, min_close: 71.7, max_close: 81.2, stddev_close: 2.8, total_volume: 4100000, monthly_return_pct: -6.5 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2024, month: 9,  trading_days: 21, avg_close: 69.8, min_close: 65.4, max_close: 74.3, stddev_close: 2.5, total_volume: 3800000, monthly_return_pct: -8.5 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2024, month: 10, trading_days: 23, avg_close: 71.2, min_close: 66.9, max_close: 76.5, stddev_close: 2.7, total_volume: 4000000, monthly_return_pct:  2.0 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2024, month: 11, trading_days: 21, avg_close: 68.4, min_close: 63.8, max_close: 73.1, stddev_close: 2.6, total_volume: 3700000, monthly_return_pct: -3.9 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2024, month: 12, trading_days: 22, avg_close: 70.1, min_close: 66.2, max_close: 74.8, stddev_close: 2.3, total_volume: 3900000, monthly_return_pct:  2.5 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2025, month: 1,  trading_days: 23, avg_close: 73.4, min_close: 69.1, max_close: 78.6, stddev_close: 2.6, total_volume: 4200000, monthly_return_pct:  4.7 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2025, month: 2,  trading_days: 20, avg_close: 70.8, min_close: 66.3, max_close: 75.4, stddev_close: 2.4, total_volume: 3900000, monthly_return_pct: -3.5 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2025, month: 3,  trading_days: 21, avg_close: 68.2, min_close: 63.9, max_close: 72.8, stddev_close: 2.5, total_volume: 3700000, monthly_return_pct: -3.7 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2025, month: 4,  trading_days: 22, avg_close: 63.5, min_close: 58.4, max_close: 68.9, stddev_close: 3.1, total_volume: 3500000, monthly_return_pct: -6.9 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2025, month: 5,  trading_days: 22, avg_close: 61.8, min_close: 57.2, max_close: 66.4, stddev_close: 2.7, total_volume: 3400000, monthly_return_pct: -2.7 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2025, month: 6,  trading_days: 21, avg_close: 65.3, min_close: 61.0, max_close: 70.1, stddev_close: 2.5, total_volume: 3600000, monthly_return_pct:  5.7 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2025, month: 7,  trading_days: 23, avg_close: 67.9, min_close: 63.5, max_close: 72.6, stddev_close: 2.6, total_volume: 3800000, monthly_return_pct:  4.0 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2025, month: 8,  trading_days: 21, avg_close: 71.2, min_close: 66.8, max_close: 76.3, stddev_close: 2.8, total_volume: 4000000, monthly_return_pct:  4.9 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2025, month: 9,  trading_days: 22, avg_close: 69.4, min_close: 64.9, max_close: 74.2, stddev_close: 2.6, total_volume: 3900000, monthly_return_pct: -2.5 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2025, month: 10, trading_days: 23, avg_close: 66.7, min_close: 62.1, max_close: 71.5, stddev_close: 2.7, total_volume: 3700000, monthly_return_pct: -3.9 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2025, month: 11, trading_days: 20, avg_close: 68.9, min_close: 64.3, max_close: 73.8, stddev_close: 2.5, total_volume: 3800000, monthly_return_pct:  3.3 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2025, month: 12, trading_days: 22, avg_close: 71.6, min_close: 67.2, max_close: 76.4, stddev_close: 2.7, total_volume: 4100000, monthly_return_pct:  3.9 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2026, month: 1,  trading_days: 22, avg_close: 74.3, min_close: 69.8, max_close: 79.1, stddev_close: 2.6, total_volume: 4300000, monthly_return_pct:  3.8 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2026, month: 2,  trading_days: 20, avg_close: 72.1, min_close: 68.0, max_close: 76.5, stddev_close: 2.3, total_volume: 4000000, monthly_return_pct: -3.0 },
  ],
  meta: { count: 19, source: 'sample', query_time_ms: 7 },
};

// 90 days of WTI vs Brent spread
export const sampleComparison: ApiEnvelope<CommodityComparisonRecord> = {
  status: 'success',
  data: (() => {
    const rows: CommodityComparisonRecord[] = [];
    const start = new Date('2025-12-01');
    let wti = 74.5;
    let brent = 78.1;
    for (let i = 0; i < 90; i++) {
      const d = new Date(start);
      d.setDate(start.getDate() + i);
      const day = d.getDay();
      if (day === 0 || day === 6) continue;
      wti = Math.max(60, Math.min(95, wti + (Math.random() - 0.48) * 2.2));
      brent = Math.max(65, Math.min(100, brent + (Math.random() - 0.48) * 2.1));
      const spread = +(wti - brent).toFixed(2);
      const ratio = +(wti / brent).toFixed(4);
      rows.push({
        date: d.toISOString().slice(0, 10),
        wti_close: +wti.toFixed(2),
        brent_close: +brent.toFixed(2),
        spread,
        ratio,
      });
    }
    return rows;
  })(),
  meta: { count: 63, source: 'sample', query_time_ms: 5 },
};

// 90 days of WTI price metrics with rolling MAs
export const samplePriceMetrics: ApiEnvelope<PriceMetricsRecord> = {
  status: 'success',
  data: (() => {
    const history = samplePriceHistory.data;
    return history.map((row, i) => {
      const window7 = history.slice(Math.max(0, i - 6), i + 1).map((r) => r.price_close);
      const window30 = history.slice(Math.max(0, i - 29), i + 1).map((r) => r.price_close);
      const window90 = history.slice(0, i + 1).map((r) => r.price_close);
      const avg = (arr: number[]) => arr.reduce((a, b) => a + b, 0) / arr.length;
      const ma7 = +avg(window7).toFixed(2);
      const ma30 = +avg(window30).toFixed(2);
      const ma90 = +avg(window90).toFixed(2);
      const vol20 = history.slice(Math.max(0, i - 19), i + 1).map((r) => r.price_close);
      const meanVol = avg(vol20);
      const stddev = Math.sqrt(vol20.reduce((s, v) => s + (v - meanVol) ** 2, 0) / vol20.length);
      return {
        commodity_id: 'CL=F',
        date: row.trade_date,
        close: row.price_close,
        ma_7: ma7,
        ma_30: ma30,
        ma_90: ma90,
        volatility_20d: +stddev.toFixed(2),
        bollinger_upper: +(ma30 + 2 * stddev).toFixed(2),
        bollinger_lower: +(ma30 - 2 * stddev).toFixed(2),
      };
    });
  })(),
  meta: { count: 63, source: 'sample', query_time_ms: 6 },
};
