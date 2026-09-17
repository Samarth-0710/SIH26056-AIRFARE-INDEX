'use client';

import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import { MonthlySeriesPoint } from '@/types';
import { formatIndex, formatNumber } from '@/lib/utils';
import { CheckCircle2, AlertCircle } from 'lucide-react';

interface MoSPIComparisonChartProps {
  data: MonthlySeriesPoint[];
  isConnected?: boolean;
  referenceMonth?: string | null;
}

export function MoSPIComparisonChart({
  data,
  isConnected = false,
  referenceMonth = '2026-08',
}: MoSPIComparisonChartProps) {
  const [viewMode, setViewMode] = React.useState<'raw' | 'rebased'>('raw');

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            Airfare Index — Our System vs MoSPI
            {isConnected ? (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 font-bold uppercase flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" />
                OFFICIAL REFERENCE CONNECTED
              </span>
            ) : (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/30 font-bold uppercase flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                REFERENCE NOT CONNECTED
              </span>
            )}
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
            Comparative analysis between project aggregated monthly index and official MoSPI CPI Airfare (Combined, All India, Base 2024 = 100)
          </p>
        </div>

        {/* View Mode Toggle */}
        <div className="flex items-center space-x-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-lg text-xs font-semibold self-start sm:self-auto">
          <button
            type="button"
            onClick={() => setViewMode('raw')}
            className={`px-3 py-1 rounded-md transition-all ${
              viewMode === 'raw'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-sm'
                : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            Raw Index Levels
          </button>
          <button
            type="button"
            onClick={() => setViewMode('rebased')}
            className={`px-3 py-1 rounded-md transition-all ${
              viewMode === 'rebased'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-sm'
                : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200'
            }`}
          >
            Rebased ({referenceMonth || 'Common'} = 100)
          </button>
        </div>
      </div>

      <div className="h-72 w-full">
        {data && data.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 10, right: 15, left: -15, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" opacity={0.6} />
              <XAxis
                dataKey="month"
                tick={{ fontSize: 11, fill: '#64748b' }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 11, fill: '#64748b', fontFamily: 'monospace' }}
                axisLine={false}
                tickLine={false}
                domain={['auto', 'auto']}
              />
              <Tooltip content={<MoSPITooltip viewMode={viewMode} />} />
              <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '12px' }} />
              <Line
                name="Our Index"
                type="monotone"
                dataKey={viewMode === 'raw' ? 'our_monthly_index' : 'our_rebased'}
                stroke="#2563eb"
                strokeWidth={2.5}
                dot={{ r: 4, fill: '#2563eb' }}
                activeDot={{ r: 6 }}
                connectNulls={false}
              />
              <Line
                name="MoSPI Airfare CPI Reference"
                type="monotone"
                dataKey={viewMode === 'raw' ? 'mospi_cpi' : 'mospi_rebased'}
                stroke="#059669"
                strokeWidth={2}
                strokeDasharray="4 4"
                dot={{ r: 3, fill: '#059669' }}
                activeDot={{ r: 6 }}
                connectNulls={false}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex items-center justify-center text-xs text-slate-400">
            No monthly comparison data available.
          </div>
        )}
      </div>

      <div className="text-[11px] text-slate-400 dark:text-slate-500 pt-2 border-t border-slate-100 dark:border-slate-800 flex flex-wrap items-center justify-between gap-2">
        <span>MoSPI e-Sankhyiki Source: Consumer Price Index (Airfare, Item Code: 07.3.3.1.2.01, Base 2024 = 100)</span>
        <span>Aggregation: Arithmetic mean of daily headline national index within each calendar month</span>
      </div>
    </div>
  );
}

function MoSPITooltip({ active, payload, label, viewMode }: any) {
  if (active && payload && payload.length) {
    const ourVal = payload.find((p: any) => p.name === 'Our Index')?.value;
    const mospiVal = payload.find((p: any) => p.name === 'MoSPI Airfare CPI Reference')?.value;
    const diff =
      ourVal !== undefined && ourVal !== null && mospiVal !== undefined && mospiVal !== null
        ? formatNumber(ourVal - mospiVal, 2)
        : null;

    return (
      <div className="bg-slate-900 text-white p-3 rounded-lg shadow-xl border border-slate-800 text-xs font-mono space-y-1.5">
        <div className="text-slate-400 text-[11px] border-b border-slate-800 pb-1 font-sans font-bold">
          Month: {label}
        </div>
        <div className="flex items-center justify-between gap-6 text-blue-400 font-bold">
          <span>Our Index:</span>
          <span>{ourVal != null ? formatIndex(ourVal) : 'N/A (Outside Window)'}</span>
        </div>
        <div className="flex items-center justify-between gap-6 text-emerald-400 font-bold">
          <span>MoSPI Reference:</span>
          <span>{mospiVal != null ? formatIndex(mospiVal) : 'N/A'}</span>
        </div>
        {diff !== null && (
          <div className="flex items-center justify-between gap-6 text-slate-300 text-[11px] pt-1 border-t border-slate-800">
            <span>Divergence:</span>
            <span className={Number(diff) >= 0 ? 'text-amber-400 font-bold' : 'text-cyan-400 font-bold'}>
              {Number(diff) > 0 ? `+${diff}` : diff} pts
            </span>
          </div>
        )}
      </div>
    );
  }
  return null;
}
