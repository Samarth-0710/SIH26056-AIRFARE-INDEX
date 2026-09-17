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
import { ValidationHistoryPoint } from '@/types';
import { formatDate, formatIndex, formatNumber } from '@/lib/utils';
import { AlertCircle } from 'lucide-react';

interface ReferenceVsCalculatedChartProps {
  data: ValidationHistoryPoint[];
  isConnected?: boolean;
  isDemo?: boolean;
}

export function ReferenceVsCalculatedChart({
  data,
  isConnected = false,
  isDemo = false,
}: ReferenceVsCalculatedChartProps) {
  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 gap-2">
        <div>
          <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            Reference Benchmark vs Calculated Airfare Index
            {isDemo && (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 font-bold uppercase">
                DEMO FIXTURE
              </span>
            )}
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
            30-day continuous back-test evaluation against DGCA / MoSPI reference series
          </p>
        </div>

        {/* Reference Data Connection Status */}
        <div
          className={`flex items-center space-x-1.5 text-xs font-mono font-semibold px-3 py-1 rounded-full border self-start sm:self-auto ${
            isConnected
              ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30'
              : 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/30'
          }`}
        >
          <AlertCircle className="w-3.5 h-3.5" />
          <span>{isConnected ? 'LIVE REFERENCE CONNECTED' : 'REFERENCE DATA NOT CONNECTED'}</span>
        </div>
      </div>

      <div className="h-72 w-full">
        {data && data.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" opacity={0.6} />
              <XAxis
                dataKey="date"
                tickFormatter={(val) => formatDate(val).split(',')[0]}
                tick={{ fontSize: 11, fill: '#64748b' }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis tick={{ fontSize: 11, fill: '#64748b', fontFamily: 'monospace' }} axisLine={false} tickLine={false} domain={['auto', 'auto']} />
              <Tooltip content={<ValidationTooltip />} />
              <Legend verticalAlign="top" height={36} wrapperStyle={{ fontSize: '12px' }} />
              <Line
                name="Calculated Index (SIH26056 Engine)"
                type="monotone"
                dataKey="calculated_index"
                stroke="#2563eb"
                strokeWidth={2.5}
                dot={false}
                activeDot={{ r: 5 }}
              />
              <Line
                name="Reference Benchmark (DGCA/MoSPI)"
                type="monotone"
                dataKey="reference_index"
                stroke="#059669"
                strokeWidth={2}
                strokeDasharray="4 4"
                dot={false}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex items-center justify-center text-xs text-slate-400">
            No validation back-test history available.
          </div>
        )}
      </div>
    </div>
  );
}

function ValidationTooltip({ active, payload, label }: any) {
  if (active && payload && payload.length) {
    const calc = payload.find((p: any) => p.dataKey === 'calculated_index')?.value;
    const ref = payload.find((p: any) => p.dataKey === 'reference_index')?.value;
    const diff = calc !== undefined && calc !== null && ref !== undefined && ref !== null ? formatNumber(calc - ref, 2) : 'N/A';
    return (
      <div className="bg-slate-900 text-white p-3 rounded-lg shadow-xl border border-slate-800 text-xs font-mono space-y-1">
        <div className="text-slate-400 text-[11px] border-b border-slate-800 pb-1">{formatDate(label)}</div>
        <div className="flex items-center justify-between gap-4 text-blue-400 font-bold">
          <span>Calculated:</span>
          <span>{formatIndex(calc)}</span>
        </div>
        <div className="flex items-center justify-between gap-4 text-emerald-400 font-bold">
          <span>Reference:</span>
          <span>{formatIndex(ref)}</span>
        </div>
        <div className="flex items-center justify-between gap-4 text-slate-300 text-[11px] pt-1">
          <span>Divergence (MAE):</span>
          <span>{diff} pts</span>
        </div>
      </div>
    );
  }
  return null;
}
