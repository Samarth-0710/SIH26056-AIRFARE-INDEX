'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const s = status.toUpperCase();

  let colorClasses = 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-slate-300 dark:border-slate-700';

  if (['SUCCESS', 'OPTIMAL', 'VALID', 'HEALTHY', 'PASS'].includes(s)) {
    colorClasses = 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/30';
  } else if (['SUSPECT', 'WARNING', 'DEGRADED', 'MONITORING', 'SUSPECT_SPIKE', 'WARNING_FRESHNESS'].includes(s)) {
    colorClasses = 'bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-500/30';
  } else if (['EXCLUDED', 'OUTLIER', 'AIRFARE_SHOCK', 'ACTIVE_SHOCK', 'OFFLINE', 'FAIL'].includes(s)) {
    colorClasses = 'bg-rose-500/10 text-rose-700 dark:text-rose-400 border-rose-500/30';
  }

  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold border uppercase tracking-wider',
        colorClasses,
        className
      )}
    >
      {status}
    </span>
  );
}
