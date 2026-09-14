'use client';

import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  CartesianGrid,
  ReferenceLine,
} from 'recharts';
import { RouteContribution } from '@/types';

interface ContributionChartProps {
  data: RouteContribution[];
  title?: string;
  isDemo?: boolean;
}

export function ContributionChart({
  data,
  title = 'Route Contributions to Index Movement',
  isDemo = false,
}: ContributionChartProps) {
  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            {title}
            {isDemo && (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 font-bold uppercase">
                DEMO DATA
              </span>
            )}
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
            {'Point contributions (w_r * (I_{r,t} - I_{r,t-1})) driving the national aggregate'}
          </p>
        </div>
      </div>

      <div className="h-64 w-full">
        {data && data.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} layout="vertical" margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" opacity={0.6} />
              <XAxis type="number" tick={{ fontSize: 11, fill: '#64748b', fontFamily: 'monospace' }} axisLine={false} tickLine={false} />
              <YAxis dataKey="route" type="category" tick={{ fontSize: 11, fill: '#64748b', fontWeight: 600 }} axisLine={false} tickLine={false} width={70} />
              <Tooltip content={<ContributionTooltip />} />
              <ReferenceLine x={0} stroke="#94a3b8" />
              <Bar dataKey="point_contribution" radius={[0, 4, 4, 0]}>
                {data.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={entry.point_contribution >= 0 ? '#e11d48' : '#059669'} // Red for positive airfare push, Emerald for drop
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex items-center justify-center text-xs text-slate-400">
            No route contribution data available.
          </div>
        )}
      </div>
    </div>
  );
}

function ContributionTooltip({ active, payload }: any) {
  if (active && payload && payload.length) {
    const item: RouteContribution = payload[0].payload;
    const isPos = item.point_contribution >= 0;
    return (
      <div className="bg-slate-900 text-white p-3 rounded-lg shadow-xl border border-slate-800 text-xs font-mono space-y-1">
        <div className="font-bold text-sm text-slate-100 border-b border-slate-800 pb-1">{item.route} Corridor</div>
        <div className="flex items-center justify-between gap-4">
          <span className="text-slate-400">Route Index:</span>
          <span className="font-bold text-blue-400">{item.route_index.toFixed(1)}</span>
        </div>
        <div className="flex items-center justify-between gap-4">
          <span className="text-slate-400">Weight ($w_r$):</span>
          <span>{(item.weight * 100).toFixed(1)}%</span>
        </div>
        <div className={`flex items-center justify-between gap-4 font-bold ${isPos ? 'text-rose-400' : 'text-emerald-400'}`}>
          <span>Point Impact:</span>
          <span>{isPos ? `+${item.point_contribution.toFixed(2)} pts` : `${item.point_contribution.toFixed(2)} pts`}</span>
        </div>
        <div className="flex items-center justify-between gap-4 text-slate-400 text-[11px] pt-1">
          <span>Share of Change:</span>
          <span>{item.percentage_share_of_change.toFixed(1)}%</span>
        </div>
      </div>
    );
  }
  return null;
}
