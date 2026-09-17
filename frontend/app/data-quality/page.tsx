'use client';

import React from 'react';
import { DataProvider } from '@/services/data-provider';
import { QualityMetric, QualitySummary, SourceHealth, DataProviderStatus } from '@/types';
import { KpiCard } from '@/components/ui/KpiCard';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { ShieldCheck, Database, Server, Clock, AlertTriangle, CheckCircle } from 'lucide-react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';

export default function DataQualityPage() {
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [status, setStatus] = React.useState<DataProviderStatus | undefined>();

  const [metrics, setMetrics] = React.useState<QualityMetric[]>([]);
  const [sourceHealth, setSourceHealth] = React.useState<SourceHealth[]>([]);
  const [summary, setSummary] = React.useState<QualitySummary | undefined>();

  const loadData = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const statusRes = await DataProvider.getStatus();
      setStatus(statusRes);

      const res = await DataProvider.getQualityMetrics();
      setMetrics(res.data);
      setSourceHealth(res.sourceHealth);
      setSummary(res.summary);
    } catch (err: any) {
      setError(err.message || 'Failed to load data quality metrics');
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

  const totalObs = summary?.total_observations ?? 0;
  const validObs = summary?.valid_observations ?? 0;
  const suspectObs = summary?.suspect_observations ?? 0;
  const excludedObs = (summary?.excluded_observations ?? 0) + (summary?.outlier_count ?? 0);
  const freshnessMins = summary?.freshness_minutes ?? 1;

  const validPct = totalObs > 0 ? ((validObs / totalObs) * 100).toFixed(1) : '0.0';
  const filteredPct = totalObs > 0 ? (((suspectObs + excludedObs) / totalObs) * 100).toFixed(1) : '0.0';

  const pieData = [
    { name: 'Valid Observations', value: validObs, color: '#059669' },
    { name: 'Suspect / Warnings', value: suspectObs, color: '#d97706' },
    { name: 'Excluded / Outliers', value: excludedObs, color: '#e11d48' },
  ];

  return (
    <div className="space-y-6">
      {/* Top Directive Banner */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              Data Quality & Normalization Audit
              {isDemo && (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/30 font-bold uppercase">
                  DEMO DATA
                </span>
              )}
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
              Hindu&apos;s Data Quality Module • Upstream fare normalization, deduplication &amp; invalid record filtering
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-xs font-mono font-semibold bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 px-3 py-1.5 rounded-full border border-emerald-500/30">
          <CheckCircle className="w-4 h-4" />
          <span>QUALITY AUDIT OPTIMAL</span>
        </div>
      </div>

      {/* Main Quality KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="Total Ingested Observations"
          value={totalObs}
          isDemo={isDemo}
          badge="DAILY VOLUME"
          icon={Database}
          subtitle="Total scraped raw fare events"
        />

        <KpiCard
          title="Valid Cleansed Observations"
          value={validObs}
          unit={`(${validPct}%)`}
          isDemo={isDemo}
          badge="PASSED"
          icon={CheckCircle}
          subtitle="Passed all fare component sanity checks"
        />

        <KpiCard
          title="Suspect & Outlier Records"
          value={suspectObs + excludedObs}
          unit={`(${filteredPct}%)`}
          isDemo={isDemo}
          badge="FILTERED"
          icon={AlertTriangle}
          subtitle="Excluded from statistical index calculation"
        />

        <KpiCard
          title="Crawl Data Freshness"
          value={freshnessMins}
          unit="mins ago"
          isDemo={isDemo}
          badge="REAL-TIME"
          icon={Clock}
          subtitle="Average scrape-to-engine latency"
        />
      </div>

      {/* Quality Breakdown & Source Health Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Observation Quality Breakdown Chart */}
        <div className="lg:col-span-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
          <div className="border-b border-slate-100 dark:border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider">
              Observation Filtering Breakdown
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
              Distribution of incoming raw scrape records
            </p>
          </div>

          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: any) => `${Number(value).toLocaleString()} records`} />
                <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: '11px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Source Health Table (2 cols) */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider flex items-center gap-2">
                <Server className="w-4 h-4 text-blue-600" />
                Permitted Data Source Health &amp; Ingestion Audit
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                Live monitoring of Kumuda&apos;s data collection adapters
              </p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold border-b border-slate-200 dark:border-slate-700">
                  <th className="p-3">Data Provider Source</th>
                  <th className="p-3">Status</th>
                  <th className="p-3 font-mono">Last Collection</th>
                  <th className="p-3 font-mono">Observations</th>
                  <th className="p-3 font-mono">Coverage %</th>
                </tr>
              </thead>
              <tbody>
                {sourceHealth.map((s) => (
                  <tr key={s.source} className="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/40">
                    <td className="p-3 font-bold text-slate-900 dark:text-slate-100 font-sans">
                      {s.source}
                    </td>
                    <td className="p-3">
                      <StatusBadge status={s.status} />
                    </td>
                    <td className="p-3 font-mono text-slate-600 dark:text-slate-400">
                      {s.last_collection}
                    </td>
                    <td className="p-3 font-mono font-bold text-slate-900 dark:text-slate-100">
                      {s.observation_count.toLocaleString()}
                    </td>
                    <td className="p-3 font-mono font-bold text-blue-600 dark:text-blue-400">
                      {s.coverage_percent.toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
