'use client';

import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({
  title = 'Backend API Unavailable',
  message = 'The statistical service API is unreachable or returned an error. Click below to retry or view demo fixtures.',
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="bg-amber-500/5 dark:bg-amber-950/20 border border-amber-500/30 rounded-xl p-8 text-center space-y-4 max-w-xl mx-auto my-8">
      <div className="w-12 h-12 rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-400 flex items-center justify-center mx-auto">
        <AlertTriangle className="w-6 h-6" />
      </div>
      <div>
        <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">{title}</h3>
        <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 max-w-md mx-auto">{message}</p>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center px-4 py-2 bg-amber-600 text-white rounded-lg text-xs font-semibold hover:bg-amber-700 transition-colors shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5 mr-1.5" /> Retry Connection
        </button>
      )}
    </div>
  );
}
