'use client';

import React from 'react';
import { Database } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  message?: string;
}

export function EmptyState({
  title = 'No Data Available',
  message = 'No data available for the selected period or filters.',
}: EmptyStateProps) {
  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-8 text-center space-y-3 max-w-md mx-auto my-6">
      <div className="w-10 h-10 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-400 flex items-center justify-center mx-auto">
        <Database className="w-5 h-5" />
      </div>
      <div>
        <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200">{title}</h4>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{message}</p>
      </div>
    </div>
  );
}
