'use client';

import React from 'react';
import { BookingWindow } from '@/types';
import { cn, formatIndex } from '@/lib/utils';

interface HeatmapRow {
  route: string;
  'T+1': number;
  'T+7': number;
  'T+15': number;
  'T+30': number;
  'T+45': number;
  [key: string]: any;
}

interface HeatmapChartProps {
  data: HeatmapRow[];
  title?: string;
  isDemo?: boolean;
}

const BOOKING_WINDOWS: BookingWindow[] = ['T+1', 'T+7', 'T+15', 'T+30', 'T+45'];

export function HeatmapChart({
  data,
  title = 'Route × Booking Window Pressure Matrix',
  isDemo = false,
}: HeatmapChartProps) {
  const getCellColor = (val: number) => {
    if (val >= 130) return 'bg-rose-900/90 text-rose-100 font-extrabold border-rose-700';
    if (val >= 120) return 'bg-rose-600/80 text-white font-bold border-rose-500';
    if (val >= 115) return 'bg-amber-500/80 text-slate-950 font-bold border-amber-400';
    if (val >= 108) return 'bg-blue-500/30 text-blue-900 dark:text-blue-100 font-semibold border-blue-400/40';
    if (val >= 100) return 'bg-emerald-500/20 text-emerald-900 dark:text-emerald-200 font-semibold border-emerald-500/30';
    return 'bg-emerald-600/40 text-emerald-950 dark:text-emerald-100 font-bold border-emerald-600/50';
  };

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
            Elementary Jevons price relatives across advance purchase windows (Base = 100.0)
          </p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs font-mono text-center border-collapse">
          <thead>
            <tr className="bg-slate-100 dark:bg-slate-800/80 text-slate-700 dark:text-slate-300">
              <th className="p-3 text-left font-sans font-bold border border-slate-200 dark:border-slate-700">Corridor</th>
              {BOOKING_WINDOWS.map((w) => (
                <th key={w} className="p-3 font-bold border border-slate-200 dark:border-slate-700">
                  <div>{w}</div>
                  <div className="text-[9px] font-normal text-slate-500 dark:text-slate-400">
                    {w === 'T+1' ? '1 Day' : w === 'T+7' ? '7 Days' : w === 'T+15' ? '15 Days' : w === 'T+30' ? '30 Days' : '45 Days'}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr key={row.route} className="hover:bg-slate-50 dark:hover:bg-slate-800/30 transition-colors">
                <td className="p-3 text-left font-sans font-bold text-slate-900 dark:text-slate-100 border border-slate-200 dark:border-slate-800">
                  {row.route}
                </td>
                {BOOKING_WINDOWS.map((w) => {
                  const val = row[w] ?? 100;
                  return (
                    <td
                      key={w}
                      className={cn(
                        'p-3 border transition-all',
                        getCellColor(val)
                      )}
                    >
                      <div className="text-sm tracking-tight">{formatIndex(val)}</div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-end space-x-3 text-[11px] text-slate-500 font-medium">
        <span>Fare Pressure:</span>
        <div className="flex items-center space-x-1.5 font-mono">
          <span className="w-3 h-3 rounded bg-emerald-500/30 border border-emerald-500/50 inline-block"></span>
          <span>Baseline (&lt;108)</span>
          <span className="w-3 h-3 rounded bg-amber-500/80 border border-amber-400 inline-block ml-2"></span>
          <span>Moderate (115-120)</span>
          <span className="w-3 h-3 rounded bg-rose-600/80 border border-rose-500 inline-block ml-2"></span>
          <span>High Spike (&gt;120)</span>
        </div>
      </div>
    </div>
  );
}
