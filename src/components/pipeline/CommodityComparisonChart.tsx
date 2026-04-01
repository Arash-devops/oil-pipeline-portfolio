'use client';

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
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
  payload?: { name: string; value: number; color: string }[];
  label?: string;
}) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-[#0d1117] border border-white/10 rounded-xl px-3 py-2 text-xs font-mono-custom shadow-xl">
      <p className="text-slate-400 mb-2">{label}</p>
      {payload.map((p) => (
        <p key={p.name} style={{ color: p.color }}>
          {p.name}: ${p.value?.toFixed(2)}
        </p>
      ))}
    </div>
  );
};

export default function CommodityComparisonChart() {
  const { data, loading, isLive } = useApiData<CommodityComparisonRecord>(
    '/analytics/commodity-comparison?limit=90',
    sampleComparison,
  );

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-display font-bold text-slate-100 text-lg">WTI vs Brent</h3>
          <p className="text-xs text-slate-500 font-mono-custom mt-0.5">Daily close comparison</p>
        </div>
        <LiveIndicator isLive={isLive} loading={loading} />
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="w-6 h-6 border-2 border-indigo-400/30 border-t-indigo-400 rounded-full animate-spin" />
        </div>
      ) : (
        <div className="flex-1 min-h-[220px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data ?? []} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
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
                domain={['auto', 'auto']}
                tick={{ fill: '#475569', fontSize: 10, fontFamily: 'var(--font-jetbrains)' }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v: number) => `$${v}`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                formatter={(value: string) => (
                  <span style={{ color: '#94a3b8', fontSize: 11, fontFamily: 'var(--font-jetbrains)' }}>
                    {value}
                  </span>
                )}
              />
              <Line
                type="monotone"
                dataKey="wti_close"
                name="WTI"
                stroke="#38bdf8"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, fill: '#38bdf8', strokeWidth: 0 }}
              />
              <Line
                type="monotone"
                dataKey="brent_close"
                name="Brent"
                stroke="#818cf8"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, fill: '#818cf8', strokeWidth: 0 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
