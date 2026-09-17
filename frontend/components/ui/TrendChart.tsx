'use client';

import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from 'recharts';
import { IndexResult } from '@/types';
import { formatDate, formatIndex, formatPercent } from '@/lib/utils';

interface TrendChartProps {
  data: IndexResult[];
  title?: string;
  subtitle?: string;
  isDemo?: boolean;
}

export function TrendChart({
  data,
  title = 'National Airfare Price Index History',
  subtitle = 'Official Jevons short-index daily trajectory (Base = 100.0)',
  isDemo = false,
}: TrendChartProps) {
  const [range, setRange] = React.useState<7 | 30 | 90>(30);

  const filteredData = React.useMemo(() => {
    if (!data || data.length === 0) return [];
    return data.slice(-range);
  }, [data, range]);

  const minIndex = React.useMemo(() => {
    if (filteredData.length === 0) return 90;
    const vals = filteredData.map((d) => d.index ?? 100);
    return Math.floor(Math.min(...vals) - 2);
  }, [filteredData]);

  const maxIndex = React.useMemo(() => {
    if (filteredData.length === 0) return 120;
    const vals = filteredData.map((d) => d.index ?? 100);
    return Math.ceil(Math.max(...vals) + 2);
  }, [filteredData]);

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
      {/* Chart Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-3">
        <div>
          <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            {title}
            {isDemo && (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 font-bold uppercase">
                DEMO DATA
              </span>
            )}
          </h3>
          {subtitle && <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">{subtitle}</p>}
        </div>

        {/* Date Range Selector */}
        <div className="flex items-center space-x-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-lg self-start sm:self-auto text-xs font-semibold">
          {([7, 30, 90] as const).map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={`px-3 py-1 rounded-md transition-all font-mono ${
                range === r
                  ? 'bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 shadow-sm'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              {r}D
            </button>
          ))}
        </div>
      </div>

      {/* Recharts Area Container */}
      <div className="h-72 w-full">
        {filteredData.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={filteredData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="indexGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2563eb" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#2563eb" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" opacity={0.6} />
              <XAxis
                dataKey="observation_date"
                tickFormatter={(val) => formatDate(val).split(',')[0]}
                tick={{ fontSize: 11, fill: '#64748b' }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                domain={[minIndex, maxIndex]}
                tick={{ fontSize: 11, fill: '#64748b', fontFamily: 'monospace' }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine y={100} stroke="#94a3b8" strokeDasharray="4 4" label={{ value: 'Base (100.0)', position: 'insideBottomLeft', fill: '#94a3b8', fontSize: 10 }} />
              <Area
                type="monotone"
                dataKey="index"
                stroke="#2563eb"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#indexGradient)"
                activeDot={{ r: 6, stroke: '#1d4ed8', strokeWidth: 2, fill: '#ffffff' }}
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex items-center justify-center text-xs text-slate-400">
            No historical index data available for this range.
          </div>
        )}
      </div>
    </div>
  );
}

function CustomTooltip({ active, payload, label }: any) {
  if (active && payload && payload.length) {
    const data: IndexResult = payload[0].payload;
    const change = data.change_percent ?? 0;
    return (
      <div className="bg-slate-900 text-white p-3 rounded-lg shadow-xl border border-slate-800 text-xs font-mono space-y-1">
        <div className="text-slate-400 text-[11px] border-b border-slate-800 pb-1">{formatDate(label)}</div>
        <div className="flex items-center justify-between gap-4 font-bold text-sm text-blue-400">
          <span>Index:</span>
          <span>{formatIndex(data.index)}</span>
        </div>
        {data.change_percent !== undefined && data.change_percent !== null && (
          <div className={`flex items-center justify-between gap-4 font-semibold ${change >= 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
            <span>Daily Change:</span>
            <span>{formatPercent(change)}</span>
          </div>
        )}
        <div className="text-[10px] text-slate-500 pt-1">
          Window: {data.booking_window} | {data.methodology_version}
        </div>
      </div>
    );
  }
  return null;
}
