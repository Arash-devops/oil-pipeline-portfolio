'use client';

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from 'recharts';
import { useApiData } from '@/hooks/useApiData';
import { samplePriceHistory, type PriceRecord } from '@/data/sample-api-data';
import LiveIndicator from './LiveIndicator';

const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

const formatDate = (s: unknown): string => {
  if (!s || typeof s !== 'string') return '';
  const parts = s.split('-');
  if (parts.length < 3) return String(s);
  const m = parseInt(parts[1], 10) - 1;
  const day = parseInt(parts[2], 10);
  if (isNaN(m) || isNaN(day) || m < 0 || m > 11) return '';
  return `${MONTHS[m]} ${day}`;
};

const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: { value: number }[]; label?: string }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-[#0d1117] border border-white/10 rounded-xl px-3 py-2 text-xs font-mono-custom shadow-xl">
      <p className="text-slate-400 mb-1">{label}</p>
      <p style={{ color: '#38bdf8' }}>${payload[0]?.value?.toFixed(2)}</p>
    </div>
  );
};

export default function PriceHistoryChart() {
  const { data, loading, isLive } = useApiData<PriceRecord>(
    '/prices/history?commodity=CL%3DF&limit=90',
    samplePriceHistory,
  );

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-display font-bold text-slate-100 text-lg">WTI Price History</h3>
          <p className="text-xs text-slate-500 font-mono-custom mt-0.5">90-day close price · CL=F</p>
        </div>
        <LiveIndicator isLive={isLive} loading={loading} />
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="w-6 h-6 border-2 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin" />
        </div>
      ) : (
        <div className="flex-1 min-h-[220px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data ?? []} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="wtiGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#38bdf8" stopOpacity={0.25} />
                  <stop offset="100%" stopColor="#38bdf8" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="rgba(255,255,255,0.04)" strokeDasharray="3 3" />
              <XAxis
                dataKey="trade_date"
                tickFormatter={formatDate}
                tick={{ fill: '#475569', fontSize: 10, fontFamily: 'var(--font-jetbrains)' }}
                tickLine={false}
                axisLine={false}
                interval={14}
              />
              <YAxis
                domain={['auto', 'auto']}
                tick={{ fill: '#475569', fontSize: 10, fontFamily: 'var(--font-jetbrains)' }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v: number) => `$${v}`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="price_close"
                stroke="#38bdf8"
                strokeWidth={2}
                fill="url(#wtiGrad)"
                dot={false}
                activeDot={{ r: 4, fill: '#38bdf8', strokeWidth: 0 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
