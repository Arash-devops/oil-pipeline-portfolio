'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { fadeUp, viewportOptions } from '@/lib/animations';

type Endpoint = {
  method: 'GET';
  path: string;
  backend: 'PostgreSQL' | 'DuckDB';
  description: string;
  params: { name: string; type: string; description: string; example: string }[];
  sampleResponse: object;
};

const endpoints: Endpoint[] = [
  {
    method: 'GET',
    path: '/api/v1/prices/latest',
    backend: 'PostgreSQL',
    description: 'Latest price per commodity, or N most recent for one',
    params: [
      { name: 'commodity', type: 'string?', description: 'CL=F | BZ=F | NG=F | HO=F', example: 'CL=F' },
      { name: 'limit', type: 'int (1–50)', description: 'Number of rows to return', example: '5' },
    ],
    sampleResponse: {
      status: 'success',
      data: [{ commodity_id: 'CL=F', trade_date: '2024-12-31', price_close: 71.34, volume: 284500 }],
      meta: { count: 1, source: 'postgresql', query_time_ms: 8 },
    },
  },
  {
    method: 'GET',
    path: '/api/v1/prices/history',
    backend: 'PostgreSQL',
    description: 'Historical OHLCV with date range and pagination',
    params: [
      { name: 'commodity', type: 'string', description: 'Required: CL=F | BZ=F | NG=F | HO=F', example: 'BZ=F' },
      { name: 'start_date', type: 'date?', description: 'ISO 8601 start date', example: '2024-01-01' },
      { name: 'end_date', type: 'date?', description: 'ISO 8601 end date', example: '2024-03-31' },
      { name: 'limit', type: 'int (max 1000)', description: 'Page size', example: '100' },
      { name: 'offset', type: 'int', description: 'Pagination offset', example: '0' },
    ],
    sampleResponse: {
      status: 'success',
      data: [{ commodity_id: 'BZ=F', trade_date: '2024-01-02', price_open: 77.1, price_high: 78.5, price_low: 76.8, price_close: 78.2, volume: 195000 }],
      meta: { count: 63, source: 'postgresql', query_time_ms: 12 },
    },
  },
  {
    method: 'GET',
    path: '/api/v1/analytics/monthly-summary',
    backend: 'DuckDB',
    description: 'Monthly avg/min/max/stddev/volume per commodity from Gold Parquet',
    params: [
      { name: 'commodity', type: 'string?', description: 'Filter by symbol', example: 'CL=F' },
      { name: 'year', type: 'int?', description: 'Filter by year', example: '2024' },
      { name: 'limit', type: 'int (max 500)', description: 'Number of rows', example: '12' },
    ],
    sampleResponse: {
      status: 'success',
      data: [{ commodity_id: 'CL=F', commodity_name: 'WTI Crude Oil', year: 2024, month: 1, trading_days: 23, avg_close: 72.9, monthly_return_pct: 2.2 }],
      meta: { count: 12, source: 'duckdb', query_time_ms: 5 },
    },
  },
  {
    method: 'GET',
    path: '/api/v1/analytics/price-metrics',
    backend: 'DuckDB',
    description: 'Rolling 7/30/90-day MAs, 20-day volatility, Bollinger bands',
    params: [
      { name: 'commodity', type: 'string', description: 'Required: CL=F | BZ=F | NG=F | HO=F', example: 'CL=F' },
      { name: 'start_date', type: 'date?', description: 'Start of window', example: '2024-10-01' },
      { name: 'end_date', type: 'date?', description: 'End of window', example: '2024-12-31' },
      { name: 'limit', type: 'int', description: 'Page size', example: '90' },
    ],
    sampleResponse: {
      status: 'success',
      data: [{ commodity_id: 'CL=F', date: '2024-12-31', close: 71.34, ma_7: 70.8, ma_30: 71.2, ma_90: 74.1, bollinger_upper: 76.3, bollinger_lower: 66.1 }],
      meta: { count: 63, source: 'duckdb', query_time_ms: 6 },
    },
  },
  {
    method: 'GET',
    path: '/api/v1/analytics/commodity-comparison',
    backend: 'DuckDB',
    description: 'Daily WTI vs Brent spread and price ratio',
    params: [
      { name: 'start_date', type: 'date?', description: 'Start of window', example: '2024-10-01' },
      { name: 'end_date', type: 'date?', description: 'End of window', example: '2024-12-31' },
      { name: 'limit', type: 'int', description: 'Page size', example: '90' },
    ],
    sampleResponse: {
      status: 'success',
      data: [{ date: '2024-12-31', wti_close: 71.34, brent_close: 74.82, spread: -3.48, ratio: 0.9535 }],
      meta: { count: 63, source: 'duckdb', query_time_ms: 5 },
    },
  },
];

const backendColor = { PostgreSQL: '#38bdf8', DuckDB: '#34d399' };

export default function ApiExplorer() {
  const [open, setOpen] = useState<string | null>(null);

  return (
    <section className="relative py-24 lg:py-32 bg-[#0a0e17]">
      <div className="section-divider absolute top-0 inset-x-0" />

      <div className="max-w-7xl mx-auto px-6 lg:px-8">
        <motion.div
          variants={fadeUp}
          initial="hidden"
          whileInView="visible"
          viewport={viewportOptions}
          className="text-center mb-16"
        >
          <p className="font-mono-custom text-xs text-cyan-400 tracking-[0.2em] uppercase mb-3">
            API Reference
          </p>
          <h2 className="font-display text-4xl lg:text-5xl font-bold text-slate-100 mb-4">
            REST Endpoints
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto leading-relaxed">
            5 data endpoints across dual backends. Click any endpoint to see parameters and a sample response.
          </p>
        </motion.div>

        <motion.div
          variants={fadeUp}
          initial="hidden"
          whileInView="visible"
          viewport={viewportOptions}
          className="flex flex-col gap-3"
        >
          {endpoints.map((ep) => {
            const isOpen = open === ep.path;
            const color = backendColor[ep.backend];
            return (
              <div
                key={ep.path}
                className="rounded-2xl border overflow-hidden transition-colors duration-200"
                style={{
                  borderColor: isOpen ? `${color}30` : 'rgba(255,255,255,0.05)',
                  backgroundColor: '#111827',
                }}
              >
                <button
                  className="w-full flex items-center gap-4 px-6 py-4 text-left group"
                  onClick={() => setOpen(isOpen ? null : ep.path)}
                >
                  {/* Method badge */}
                  <span className="flex-shrink-0 px-2 py-0.5 rounded-md text-xs font-mono-custom font-bold bg-cyan-400/10 text-cyan-400 border border-cyan-400/20">
                    {ep.method}
                  </span>

                  {/* Path */}
                  <span className="flex-1 text-sm font-mono-custom text-slate-200 group-hover:text-white transition-colors truncate">
                    {ep.path}
                  </span>

                  {/* Backend */}
                  <span
                    className="hidden sm:inline-flex px-2 py-0.5 rounded-full text-xs font-mono-custom border flex-shrink-0"
                    style={{ color, borderColor: `${color}30`, backgroundColor: `${color}10` }}
                  >
                    {ep.backend}
                  </span>

                  <motion.svg
                    animate={{ rotate: isOpen ? 180 : 0 }}
                    transition={{ duration: 0.2 }}
                    className="w-4 h-4 flex-shrink-0 text-slate-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </motion.svg>
                </button>

                <AnimatePresence>
                  {isOpen && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94] }}
                      className="overflow-hidden"
                    >
                      <div className="px-6 pb-6 pt-2 border-t border-white/5">
                        <p className="text-sm text-slate-400 mb-5">{ep.description}</p>

                        <div className="grid lg:grid-cols-2 gap-6">
                          {/* Parameters */}
                          <div>
                            <p className="text-xs font-mono-custom text-slate-500 uppercase tracking-wider mb-3">
                              Parameters
                            </p>
                            <div className="flex flex-col gap-2">
                              {ep.params.map((p) => (
                                <div
                                  key={p.name}
                                  className="flex items-start gap-3 p-3 rounded-xl bg-white/3 border border-white/5"
                                >
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 flex-wrap mb-0.5">
                                      <span className="text-xs font-mono-custom font-semibold text-slate-200">
                                        {p.name}
                                      </span>
                                      <span className="text-xs font-mono-custom text-slate-600">{p.type}</span>
                                    </div>
                                    <p className="text-xs text-slate-500">{p.description}</p>
                                  </div>
                                  <span className="text-xs font-mono-custom text-cyan-400/70 flex-shrink-0">
                                    e.g. {p.example}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Sample response */}
                          <div>
                            <p className="text-xs font-mono-custom text-slate-500 uppercase tracking-wider mb-3">
                              Sample Response
                            </p>
                            <pre className="text-xs font-mono-custom text-slate-300 bg-[#080c12] rounded-xl p-4 overflow-auto max-h-52 border border-white/5 leading-relaxed">
                              {JSON.stringify(ep.sampleResponse, null, 2)}
                            </pre>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })}
        </motion.div>
      </div>
    </section>
  );
}
