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
    const start = new Date('2024-10-01');
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

// 18 months of monthly summaries for WTI
export const sampleMonthlySummary: ApiEnvelope<MonthlySummaryRecord> = {
  status: 'success',
  data: [
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2023, month: 7,  trading_days: 21, avg_close: 77.2, min_close: 71.3, max_close: 83.4, stddev_close: 3.1, total_volume: 4200000, monthly_return_pct:  3.8 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2023, month: 8,  trading_days: 23, avg_close: 81.5, min_close: 77.8, max_close: 88.2, stddev_close: 2.9, total_volume: 4800000, monthly_return_pct:  5.6 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2023, month: 9,  trading_days: 20, avg_close: 89.4, min_close: 83.1, max_close: 95.0, stddev_close: 3.4, total_volume: 5100000, monthly_return_pct:  9.7 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2023, month: 10, trading_days: 22, avg_close: 84.6, min_close: 79.2, max_close: 91.3, stddev_close: 3.8, total_volume: 4900000, monthly_return_pct: -5.3 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2023, month: 11, trading_days: 21, avg_close: 77.8, min_close: 72.4, max_close: 83.1, stddev_close: 2.7, total_volume: 4300000, monthly_return_pct: -8.0 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2023, month: 12, trading_days: 20, avg_close: 71.3, min_close: 66.8, max_close: 76.9, stddev_close: 2.5, total_volume: 3900000, monthly_return_pct: -8.4 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2024, month: 1,  trading_days: 23, avg_close: 72.9, min_close: 69.5, max_close: 78.2, stddev_close: 2.1, total_volume: 4100000, monthly_return_pct:  2.2 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2024, month: 2,  trading_days: 21, avg_close: 76.1, min_close: 72.3, max_close: 80.6, stddev_close: 2.3, total_volume: 4400000, monthly_return_pct:  4.4 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2024, month: 3,  trading_days: 20, avg_close: 80.7, min_close: 76.5, max_close: 87.1, stddev_close: 3.1, total_volume: 4700000, monthly_return_pct:  6.0 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2024, month: 4,  trading_days: 22, avg_close: 83.4, min_close: 79.8, max_close: 87.9, stddev_close: 2.4, total_volume: 4600000, monthly_return_pct:  3.3 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2024, month: 5,  trading_days: 23, avg_close: 78.9, min_close: 74.2, max_close: 84.3, stddev_close: 2.9, total_volume: 4500000, monthly_return_pct: -5.4 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2024, month: 6,  trading_days: 20, avg_close: 80.2, min_close: 76.7, max_close: 84.8, stddev_close: 2.2, total_volume: 4200000, monthly_return_pct:  1.6 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2024, month: 7,  trading_days: 23, avg_close: 81.6, min_close: 77.1, max_close: 85.9, stddev_close: 2.6, total_volume: 4400000, monthly_return_pct:  1.7 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2024, month: 8,  trading_days: 22, avg_close: 76.3, min_close: 71.7, max_close: 81.2, stddev_close: 2.8, total_volume: 4100000, monthly_return_pct: -6.5 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2024, month: 9,  trading_days: 21, avg_close: 69.8, min_close: 65.4, max_close: 74.3, stddev_close: 2.5, total_volume: 3800000, monthly_return_pct: -8.5 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2024, month: 10, trading_days: 23, avg_close: 71.2, min_close: 66.9, max_close: 76.5, stddev_close: 2.7, total_volume: 4000000, monthly_return_pct:  2.0 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2024, month: 11, trading_days: 21, avg_close: 68.4, min_close: 63.8, max_close: 73.1, stddev_close: 2.6, total_volume: 3700000, monthly_return_pct: -3.9 },
    { commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2024, month: 12, trading_days: 22, avg_close: 70.1, min_close: 66.2, max_close: 74.8, stddev_close: 2.3, total_volume: 3900000, monthly_return_pct:  2.5 },
  ],
  meta: { count: 18, source: 'sample', query_time_ms: 7 },
};

// 90 days of WTI vs Brent spread
export const sampleComparison: ApiEnvelope<CommodityComparisonRecord> = {
  status: 'success',
  data: (() => {
    const rows: CommodityComparisonRecord[] = [];
    const start = new Date('2024-10-01');
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
