'use client';

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
} from 'recharts';
import { useApiData } from '@/hooks/useApiData';
import { sampleComparison, type CommodityComparisonRecord } from '@/data/sample-api-data';
import LiveIndicator from './LiveIndicator';

const formatDate = (s: string) => {
  const d = new Date(s);
  return `${d.toLocaleString('default', { month: 'short' })} ${d.getDate()}`;
};

const CustomTooltip = ({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: { value: number }[];
  label?: string;
}) => {
  if (!active || !payload?.length) return null;
  const spread = payload[0]?.value ?? 0;
  return (
    <div className="bg-[#0d1117] border border-white/10 rounded-xl px-3 py-2 text-xs font-mono-custom shadow-xl">
      <p className="text-slate-400 mb-1">{label}</p>
      <p style={{ color: spread >= 0 ? '#fbbf24' : '#fb7185' }}>
        Spread: {spread >= 0 ? '+' : ''}${spread.toFixed(2)}
      </p>
    </div>
  );
};

export default function SpreadChart() {
  const { data, loading, isLive } = useApiData<CommodityComparisonRecord>(
    '/analytics/commodity-comparison?limit=90',
    sampleComparison,
  );

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-display font-bold text-slate-100 text-lg">WTI–Brent Spread</h3>
          <p className="text-xs text-slate-500 font-mono-custom mt-0.5">Daily price differential (USD/bbl)</p>
        </div>
        <LiveIndicator isLive={isLive} loading={loading} />
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="w-6 h-6 border-2 border-amber-400/30 border-t-amber-400 rounded-full animate-spin" />
        </div>
      ) : (
        <div className="flex-1 min-h-[220px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data ?? []} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="spreadGradPos" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#fbbf24" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#fbbf24" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="spreadGradNeg" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#fb7185" stopOpacity={0} />
                  <stop offset="100%" stopColor="#fb7185" stopOpacity={0.3} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="rgba(255,255,255,0.04)" strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={formatDate}
                tick={{ fill: '#475569', fontSize: 10, fontFamily: 'var(--font-jetbrains)' }}
                tickLine={false}
                axisLine={false}
                interval={14}
              />
              <YAxis
                tick={{ fill: '#475569', fontSize: 10, fontFamily: 'var(--font-jetbrains)' }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v: number) => `$${v}`}
              />
              <ReferenceLine y={0} stroke="rgba(255,255,255,0.12)" strokeDasharray="4 4" />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="spread"
                stroke="#fbbf24"
                strokeWidth={2}
                fill="url(#spreadGradPos)"
                dot={false}
                activeDot={{ r: 4, fill: '#fbbf24', strokeWidth: 0 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
