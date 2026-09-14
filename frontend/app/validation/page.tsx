'use client';

import React from 'react';
import { DataProvider } from '@/services/data-provider';
import { ValidationResult, DataProviderStatus } from '@/types';
import { ReferenceVsCalculatedChart } from '@/components/ui/ReferenceVsCalculatedChart';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { CheckCircle2, Shield, Info, AlertTriangle, GitCompare } from 'lucide-react';

export default function ValidationPage() {
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [status, setStatus] = React.useState<DataProviderStatus | undefined>();

  const [validation, setValidation] = React.useState<ValidationResult | null>(null);

  const loadData = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const statusRes = await DataProvider.getStatus();
      setStatus(statusRes);

      const res = await DataProvider.getValidationResult();
      setValidation(res.data);
    } catch (err: any) {
      setError(err.message || 'Failed to load validation back-test results');
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading) return <LoadingSkeleton />;
  if (error) return <ErrorState message={error} onRetry={loadData} />;

  const isDemo = status?.isDemo ?? true;
  const isConnected = validation?.is_reference_connected ?? false;

  return (
    <div className="space-y-6">
      {/* Non-Fabrication Rule Banner */}
      <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 flex items-start space-x-3 text-xs text-amber-900 dark:text-amber-300">
        <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
        <div>
          <h4 className="font-bold text-sm text-amber-950 dark:text-amber-200">
            Official Methodological Policy — Reference Data Non-Fabrication Rule
          </h4>
          <p className="mt-1 leading-relaxed text-amber-800 dark:text-amber-400">
            Per repository rules, official DGCA or MoSPI reference airfare datasets are strictly external inputs. Reference data is <strong>never fabricated</strong> to claim false accuracy. The chart below uses clearly labeled benchmark fixtures to demonstrate the 30-day backtesting system UI.
          </p>
        </div>
      </div>

      {/* Validation Metadata Bar */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm flex flex-wrap items-center justify-between gap-4 text-xs">
        <div className="flex flex-wrap items-center gap-4 text-slate-700 dark:text-slate-300">
          <div>Evaluation Period: <strong className="font-mono text-blue-600 dark:text-blue-400">{validation?.period}</strong></div>
          <div className="h-4 w-px bg-slate-200 dark:bg-slate-700 hidden sm:block"></div>
          <div>Reference Source: <strong className="font-mono">{validation?.reference_dataset}</strong></div>
        </div>
        <div className="flex items-center space-x-2">
          <StatusBadge status={isConnected ? 'CONNECTED' : 'NOT_CONNECTED'} />
        </div>
      </div>

      {/* Reference vs Calculated Line Chart */}
      <ReferenceVsCalculatedChart
        data={validation?.history || []}
        isConnected={isConnected}
        isDemo={isDemo}
      />

      {/* 30-Day Backtest Metrics Table */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              30-Day Backtest Statistical Metrics
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
              Samarth&apos;s Statistical Validation Suite (`statistical-engine/src/statistical_engine/validation`)
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border-collapse">
            <thead>
              <tr className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold border-b border-slate-200 dark:border-slate-700">
                <th className="p-3">Statistical Metric</th>
                <th className="p-3 font-mono">Calculated Value</th>
                <th className="p-3">Validation Status</th>
                <th className="p-3">Methodological Description</th>
              </tr>
            </thead>
            <tbody>
              {validation?.metrics.map((m) => (
                <tr key={m.metric} className="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/40">
                  <td className="p-3 font-bold text-slate-900 dark:text-slate-100 font-sans">
                    {m.metric}
                  </td>
                  <td className="p-3 font-mono font-extrabold text-blue-600 dark:text-blue-400 text-sm">
                    {m.value}
                  </td>
                  <td className="p-3">
                    <StatusBadge status={m.status} />
                  </td>
                  <td className="p-3 text-slate-600 dark:text-slate-400">
                    {m.description}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
