'use client';

import React from 'react';
import { DataProvider } from '@/services/data-provider';
import { ValidationResult, DataProviderStatus } from '@/types';
import { MoSPIComparisonChart } from '@/components/ui/MoSPIComparisonChart';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import {
  CheckCircle2,
  Shield,
  Info,
  AlertTriangle,
  GitCompare,
  Database,
  Calendar,
  Layers,
  ArrowRight,
  Radio,
} from 'lucide-react';
import { formatIndex, formatPercent } from '@/lib/utils';

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
  const mospiDetails = validation?.reference_dataset_details;
  const comparison = validation?.comparison;
  const movement = validation?.movement;
  const alignment = validation?.alignment;
  const correlation = validation?.correlation;

  return (
    <div className="space-y-6">
      {/* Synthetic / Demo Data Mode Banner */}
      {isDemo && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-3.5 px-4 flex items-center justify-between text-xs text-amber-800 dark:text-amber-300">
          <div className="flex items-center space-x-2">
            <Radio className="w-4 h-4 text-amber-500 animate-pulse shrink-0" />
            <span>
              <strong>Synthetic / Demo Execution Mode:</strong> Airfare observations are generated from controlled multi-route schedules. Reference MoSPI CPI is authentic government survey data.
            </span>
          </div>
          <span className="font-mono font-bold text-[10px] uppercase bg-amber-500/20 px-2 py-0.5 rounded border border-amber-500/40">
            SYNTHETIC OBSERVATIONS
          </span>
        </div>
      )}

      {/* Disconnected Reference State Notice */}
      {!isConnected && (
        <div className="bg-slate-100 dark:bg-slate-800/80 border border-slate-300 dark:border-slate-700 rounded-xl p-5 text-center space-y-2 text-xs text-slate-700 dark:text-slate-300">
          <div className="font-bold text-sm text-slate-900 dark:text-slate-100 flex items-center justify-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-500" />
            MoSPI Reference Dataset Offline / Disconnected
          </div>
          <p className="max-w-md mx-auto text-slate-500 dark:text-slate-400 text-[11px]">
            The official external MoSPI CPI Airfare series is currently not loaded. Live/demo calculated indices remain operational, but macro benchmark comparisons require database loading.
          </p>
        </div>
      )}

      {/* Official Status Banner */}
      <div
        className={`rounded-xl p-4 px-5 border flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all ${
          isConnected
            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-950 dark:text-emerald-200'
            : 'bg-amber-500/10 border-amber-500/30 text-amber-950 dark:text-amber-200'
        }`}
      >
        <div className="flex items-start sm:items-center space-x-3">
          {isConnected ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5 sm:mt-0" />
          ) : (
            <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5 sm:mt-0" />
          )}
          <div>
            <div className="flex items-center gap-2 font-bold text-sm">
              <span>Real MoSPI validation</span>
              <span
                className={`font-mono text-[11px] px-2 py-0.5 rounded font-bold uppercase ${
                  isConnected
                    ? 'bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 border border-emerald-500/40'
                    : 'bg-amber-500/20 text-amber-700 dark:text-amber-300 border border-amber-500/40'
                }`}
              >
                {isConnected ? '🟢 Connected' : '🟡 Not connected'}
              </span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
              {isConnected
                ? 'Official e-Sankhyiki Consumer Price Index (Airfare, Base 2024 = 100) imported from CPI_Airfare.xlsx.'
                : 'External benchmark reference dataset is currently not loaded in the reference database.'}
            </p>
          </div>
        </div>

        <div className="text-xs font-mono text-slate-500 dark:text-slate-400 self-start sm:self-auto">
          Dataset: <strong>{mospiDetails?.item_code || 'N/A'}</strong>
        </div>
      </div>

      {/* MoSPI Reference Metadata Cards */}
      {isConnected && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 text-xs">
          <div className="p-3.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
            <div className="text-slate-400 font-medium mb-1">Source / Dataset</div>
            <div className="font-bold text-slate-900 dark:text-slate-100 truncate font-mono">
              {mospiDetails?.source || mospiDetails?.name || 'N/A'}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Item: {mospiDetails?.item || 'Airfare'}</div>
          </div>

          <div className="p-3.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
            <div className="text-slate-400 font-medium mb-1">Base Year</div>
            <div className="font-extrabold text-blue-600 dark:text-blue-400 font-mono text-base">
              {mospiDetails?.base_year ? `${mospiDetails.base_year} = 100` : 'N/A'}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Series: Current</div>
          </div>

          <div className="p-3.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
            <div className="text-slate-400 font-medium mb-1">Scope / Sector</div>
            <div className="font-bold text-slate-900 dark:text-slate-100">
              {mospiDetails?.state || 'N/A'}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">{mospiDetails?.sector || 'Combined'}</div>
          </div>

          <div className="p-3.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
            <div className="text-slate-400 font-medium mb-1">Total Observations</div>
            <div className="font-extrabold text-emerald-600 dark:text-emerald-400 font-mono text-base">
              {mospiDetails?.records ?? '0'}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">
              {mospiDetails?.first_date && mospiDetails?.latest_date
                ? `${mospiDetails.first_date.slice(0, 7)} → ${mospiDetails.latest_date.slice(0, 7)}`
                : 'Monthly Series'}
            </div>
          </div>

          <div className="p-3.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
            <div className="text-slate-400 font-medium mb-1">Latest MoSPI CPI</div>
            <div className="font-extrabold text-purple-600 dark:text-purple-400 font-mono text-base">
              {formatIndex(mospiDetails?.latest_cpi)}
            </div>
            <div className="text-[10px] text-slate-500 mt-1">Airfare Index</div>
          </div>
        </div>
      )}

      {/* Dual Series Comparison Chart: Our System vs MoSPI */}
      <MoSPIComparisonChart
        data={validation?.monthly_series || []}
        isConnected={isConnected}
        referenceMonth={comparison?.reference_month}
      />

      {/* Statistical Alignment & Rebased Comparison Table */}
      {isConnected && comparison && (
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <GitCompare className="w-4 h-4 text-blue-600" />
                Monthly Level & Movement Comparison ({comparison.reference_month})
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                Arithmetic mean of daily headline index ($T+15$) aligned with official MoSPI calendar month
              </p>
            </div>
            <div className="text-xs font-mono text-slate-500">
              Aligned Months: <strong className="text-blue-600">{alignment?.overlapping_months || 1}</strong>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            {/* Raw Level Divergence */}
            <div className="p-4 bg-slate-50 dark:bg-slate-800/40 rounded-lg border border-slate-200 dark:border-slate-800 space-y-2">
              <div className="font-bold text-slate-700 dark:text-slate-300">Raw Level Comparison</div>
              <div className="flex justify-between items-center text-slate-600 dark:text-slate-400">
                <span>Our Monthly Index:</span>
                <span className="font-mono font-bold text-blue-600">{formatIndex(comparison.our_monthly_index)}</span>
              </div>
              <div className="flex justify-between items-center text-slate-600 dark:text-slate-400">
                <span>MoSPI CPI Level:</span>
                <span className="font-mono font-bold text-emerald-600">{formatIndex(comparison.mospi_monthly_index)}</span>
              </div>
              <div className="flex justify-between items-center text-slate-600 dark:text-slate-400 border-t border-slate-200 dark:border-slate-700 pt-1">
                <span>Absolute Level Difference:</span>
                <span className="font-mono font-bold text-amber-600">{comparison.absolute_difference?.toFixed(2)} pts</span>
              </div>
            </div>

            {/* Rebased Comparison */}
            <div className="p-4 bg-slate-50 dark:bg-slate-800/40 rounded-lg border border-slate-200 dark:border-slate-800 space-y-2">
              <div className="font-bold text-slate-700 dark:text-slate-300">Rebased Index Comparison</div>
              <div className="flex justify-between items-center text-slate-600 dark:text-slate-400">
                <span>Rebasing Anchor:</span>
                <span className="font-mono font-bold">{comparison.reference_month} = 100.0</span>
              </div>
              <div className="flex justify-between items-center text-slate-600 dark:text-slate-400">
                <span>Normalized Project:</span>
                <span className="font-mono font-bold text-blue-600">100.00</span>
              </div>
              <div className="flex justify-between items-center text-slate-600 dark:text-slate-400 border-t border-slate-200 dark:border-slate-700 pt-1">
                <span>Normalized MoSPI:</span>
                <span className="font-mono font-bold text-emerald-600">100.00</span>
              </div>
            </div>

            {/* Correlation & Movement */}
            <div className="p-4 bg-slate-50 dark:bg-slate-800/40 rounded-lg border border-slate-200 dark:border-slate-800 space-y-2">
              <div className="font-bold text-slate-700 dark:text-slate-300">Statistical Co-Movement</div>
              <div className="flex justify-between items-center text-slate-600 dark:text-slate-400">
                <span>Pearson Correlation (r):</span>
                <span className="font-mono font-bold">
                  {correlation?.value != null ? correlation.value.toFixed(4) : 'N/A'}
                </span>
              </div>
              <div className="flex justify-between items-center text-slate-600 dark:text-slate-400">
                <span>Statistical Status:</span>
                <span className="font-mono font-bold text-amber-500">
                  {correlation?.status === 'INSUFFICIENT_OVERLAP'
                    ? 'INSUFFICIENT OVERLAP (< 3 Months)'
                    : correlation?.status || 'CONNECTED'}
                </span>
              </div>
              <div className="text-[10px] text-slate-400 pt-1">
                MoSPI publishes monthly with a 1-month reporting lag; correlation requires $\ge 3$ aligned months.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 30-Day Backtest Metrics Table */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              Statistical Validation Metrics Suite
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
              Evaluated against database records adhering strictly to Non-Fabrication Rules
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
                <tr
                  key={m.metric}
                  className="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/40"
                >
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
