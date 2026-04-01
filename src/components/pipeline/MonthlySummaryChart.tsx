'use client';

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from 'recharts';
import { useApiData } from '@/hooks/useApiData';
import { sampleMonthlySummary, type MonthlySummaryRecord } from '@/data/sample-api-data';
import LiveIndicator from './LiveIndicator';

const MONTH_SHORT = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

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
  const val = payload[0]?.value ?? 0;
  return (
    <div className="bg-[#0d1117] border border-white/10 rounded-xl px-3 py-2 text-xs font-mono-custom shadow-xl">
      <p className="text-slate-400 mb-1">{label}</p>
      <p style={{ color: val >= 0 ? '#34d399' : '#fb7185' }}>
        {val >= 0 ? '+' : ''}{val.toFixed(1)}%
      </p>
    </div>
  );
};

export default function MonthlySummaryChart() {
  const { data, loading, isLive } = useApiData<MonthlySummaryRecord>(
    '/analytics/monthly-summary?commodity=CL%3DF',
    sampleMonthlySummary,
  );

  const chartData = (data ?? []).map((r) => ({
    label: `${MONTH_SHORT[(r.month ?? 1) - 1]} ${String(r.year).slice(2)}`,
    return: r.monthly_return_pct,
  }));

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-display font-bold text-slate-100 text-lg">Monthly Returns</h3>
          <p className="text-xs text-slate-500 font-mono-custom mt-0.5">WTI monthly return % · CL=F</p>
        </div>
        <LiveIndicator isLive={isLive} loading={loading} />
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="w-6 h-6 border-2 border-green-400/30 border-t-green-400 rounded-full animate-spin" />
        </div>
      ) : (
        <div className="flex-1 min-h-[220px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 4, right: 4, left: -20, bottom: 44 }}>
              <CartesianGrid stroke="rgba(255,255,255,0.04)" strokeDasharray="3 3" />
              <XAxis
                dataKey="label"
                tick={{ fill: '#475569', fontSize: 9, fontFamily: 'var(--font-jetbrains)', textAnchor: 'end' }}
                tickLine={false}
                axisLine={false}
                interval={0}
                angle={-35}
                dx={-2}
                dy={4}
                tickFormatter={(value: string, index: number) => (index % 4 === 0 ? value : '')}
              />
              <YAxis
                tick={{ fill: '#475569', fontSize: 10, fontFamily: 'var(--font-jetbrains)' }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v: number) => `${v}%`}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
              <Bar dataKey="return" radius={[3, 3, 0, 0]}>
                {chartData.map((entry, i) => (
                  <Cell
                    key={i}
                    fill={entry.return >= 0 ? '#34d399' : '#fb7185'}
                    fillOpacity={0.8}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
