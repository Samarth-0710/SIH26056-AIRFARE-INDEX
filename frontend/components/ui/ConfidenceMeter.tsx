'use client';

import React from 'react';
import { ShieldCheck, Info, CheckCircle, Database, Server, RefreshCw } from 'lucide-react';
import { ConfidenceMetrics } from '@/types';
import { cn } from '@/lib/utils';

interface ConfidenceMeterProps {
  metrics?: ConfidenceMetrics;
  className?: string;
}

export function ConfidenceMeter({ metrics, className }: ConfidenceMeterProps) {
  const overall = metrics?.overall_confidence ?? 94;
  const sourceCoverage = metrics?.source_coverage ?? 96;
  const routeCoverage = metrics?.route_coverage ?? 98;
  const volume = metrics?.observation_volume ?? 'High';
  const freshness = metrics?.freshness ?? 'Excellent';

  return (
    <div className={cn('bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm', className)}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider">
            Measurement Reliability & Confidence
          </h3>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-xs font-semibold text-slate-500">Overall Reliability:</span>
          <span className="text-lg font-mono font-extrabold text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/60 px-2.5 py-0.5 rounded border border-blue-200 dark:border-blue-800">
            {overall}%
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-100 dark:bg-slate-800 h-2.5 rounded-full overflow-hidden mb-5">
        <div
          className="bg-gradient-to-r from-blue-600 to-emerald-500 h-full rounded-full transition-all duration-500"
          style={{ width: `${overall}%` }}
        />
      </div>

      {/* Supporting Indicators Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs mb-4">
        <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200/80 dark:border-slate-800">
          <div className="text-slate-500 dark:text-slate-400 font-medium mb-1 flex items-center gap-1">
            <Server className="w-3.5 h-3.5 text-slate-400" /> Source Coverage
          </div>
          <div className="font-mono font-bold text-slate-900 dark:text-slate-100 text-sm">{sourceCoverage}%</div>
        </div>

        <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200/80 dark:border-slate-800">
          <div className="text-slate-500 dark:text-slate-400 font-medium mb-1 flex items-center gap-1">
            <Database className="w-3.5 h-3.5 text-slate-400" /> Route Coverage
          </div>
          <div className="font-mono font-bold text-slate-900 dark:text-slate-100 text-sm">{routeCoverage}%</div>
        </div>

        <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200/80 dark:border-slate-800">
          <div className="text-slate-500 dark:text-slate-400 font-medium mb-1 flex items-center gap-1">
            <CheckCircle className="w-3.5 h-3.5 text-slate-400" /> Observation Vol.
          </div>
          <div className="font-mono font-bold text-emerald-600 dark:text-emerald-400 text-sm">{volume}</div>
        </div>

        <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200/80 dark:border-slate-800">
          <div className="text-slate-500 dark:text-slate-400 font-medium mb-1 flex items-center gap-1">
            <RefreshCw className="w-3.5 h-3.5 text-slate-400" /> Data Freshness
          </div>
          <div className="font-mono font-bold text-blue-600 dark:text-blue-400 text-sm">{freshness}</div>
        </div>
      </div>

      {/* Mandatory Statistical Clarification */}
      <div className="flex items-start space-x-2 text-[11px] text-slate-500 dark:text-slate-400 bg-blue-50/50 dark:bg-blue-950/20 p-2.5 rounded-md border border-blue-100 dark:border-blue-900/40">
        <Info className="w-4 h-4 text-blue-500 shrink-0 mt-0.5" />
        <span>
          <strong>Methodological Note:</strong> Confidence describes the statistical coverage, source sampling density, and data quality reliability of the current measurement. It is <em>not</em> ML prediction accuracy.
        </span>
      </div>
    </div>
  );
}
