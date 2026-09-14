'use client';

import React from 'react';
import { ArrowUpRight, ArrowDownRight, Minus, Info } from 'lucide-react';
import { cn, formatIndex, formatPercent } from '@/lib/utils';

interface KpiCardProps {
  title: string;
  value: number | null | undefined;
  previousValue?: number | null;
  changePercent?: number | null;
  unit?: string;
  subtitle?: string;
  statusText?: string;
  isDemo?: boolean;
  confidence?: number;
  icon?: React.ElementType;
  className?: string;
  badge?: string;
}

export function KpiCard({
  title,
  value,
  previousValue,
  changePercent,
  unit = '',
  subtitle,
  statusText,
  isDemo = false,
  confidence,
  icon: Icon,
  className,
  badge,
}: KpiCardProps) {
  const isPositive = (changePercent || 0) > 0;
  const isNegative = (changePercent || 0) < 0;

  return (
    <div
      className={cn(
        'bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm hover:border-slate-300 dark:hover:border-slate-700 transition-all flex flex-col justify-between relative overflow-hidden',
        className
      )}
    >
      {/* Demo watermark if applicable */}
      {isDemo && (
        <div className="absolute top-2 right-2 text-[9px] font-mono uppercase font-bold text-amber-600 dark:text-amber-400 bg-amber-500/10 border border-amber-500/20 px-1.5 py-0.5 rounded">
          DEMO DATA
        </div>
      )}

      {/* Header */}
      <div>
        <div className="flex items-center justify-between mb-1 pr-16">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 flex items-center gap-1.5">
            {Icon && <Icon className="w-3.5 h-3.5 text-slate-400" />}
            {title}
          </span>
          {badge && (
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 font-semibold border border-blue-200 dark:border-blue-800">
              {badge}
            </span>
          )}
        </div>

        {/* Value + Change Badge */}
        <div className="flex items-baseline space-x-3 mt-2">
          <div className="text-3xl font-extrabold font-mono text-slate-900 dark:text-slate-100 tracking-tight">
            {formatIndex(value)}
            {unit && <span className="text-sm font-sans font-normal text-slate-500 ml-1">{unit}</span>}
          </div>

          {changePercent !== undefined && changePercent !== null && (
            <div
              className={cn(
                'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold font-mono border',
                isPositive
                  ? 'bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-500/20' // Airfare inflation is red/rose
                  : isNegative
                  ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/20' // Airfare drop is emerald
                  : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400 border-slate-300'
              )}
            >
              {isPositive ? (
                <ArrowUpRight className="w-3.5 h-3.5 mr-0.5 stroke-[2.5]" />
              ) : isNegative ? (
                <ArrowDownRight className="w-3.5 h-3.5 mr-0.5 stroke-[2.5]" />
              ) : (
                <Minus className="w-3.5 h-3.5 mr-0.5 stroke-[2.5]" />
              )}
              {formatPercent(changePercent)}
            </div>
          )}
        </div>
      </div>

      {/* Footer Meta */}
      <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 font-medium">
        <div>
          {subtitle && <span>{subtitle}</span>}
          {!subtitle && previousValue !== undefined && (
            <span>Prev: <span className="font-mono font-semibold">{formatIndex(previousValue)}</span></span>
          )}
        </div>

        {confidence !== undefined && (
          <div className="flex items-center space-x-1">
            <span className="text-[11px] text-slate-400">Confidence:</span>
            <span className="font-mono font-bold text-slate-700 dark:text-slate-300">{confidence}%</span>
          </div>
        )}

        {statusText && (
          <span className="font-mono text-[11px] font-semibold text-slate-600 dark:text-slate-400 uppercase">
            {statusText}
          </span>
        )}
      </div>
    </div>
  );
}
