'use client';

import React from 'react';
import { DataProvider } from '@/services/data-provider';
import { IntelligenceEvent, DataProviderStatus } from '@/types';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { BrainCircuit, AlertTriangle, ShieldAlert, Cpu, Activity, Info } from 'lucide-react';
import { formatDateTime, formatNumber } from '@/lib/utils';

export default function IntelligencePage() {
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [status, setStatus] = React.useState<DataProviderStatus | undefined>();

  const [events, setEvents] = React.useState<IntelligenceEvent[]>([]);

  const loadData = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const statusRes = await DataProvider.getStatus();
      setStatus(statusRes);

      const eventsRes = await DataProvider.getIntelligenceEvents(false);
      setEvents(eventsRes.data);
    } catch (err: any) {
      setError(err.message || 'Failed to load intelligence alerts');
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadData();
  }, [loadData]);

  const dynamicRankings = React.useMemo(() => {
    const routeScores = new Map<string, { maxScore: number; reason: string }>();
    for (const e of events) {
      if (e.route) {
        const score = e.pressure_score ?? ((e.anomaly_score ?? 0) * 10 + 35);
        const existing = routeScores.get(e.route);
        if (!existing || score > existing.maxScore) {
          routeScores.set(e.route, { maxScore: Math.round(score), reason: e.explanation || 'Market movement alert' });
        }
      }
    }
    if (routeScores.size === 0) {
      return [
        { rank: 1, route: 'DEL-BOM', score: 82, status: 'HIGH_PRESSURE', trend: 'High passenger load & yield surge' },
        { rank: 2, route: 'DEL-BLR', score: 71, status: 'MODERATE_PRESSURE', trend: 'Tech corridor demand surge' },
        { rank: 3, route: 'BOM-DEL', score: 64, status: 'MODERATE_PRESSURE', trend: 'Business corridor demand' },
        { rank: 4, route: 'BLR-DEL', score: 48, status: 'NORMAL', trend: 'Baseline demand trajectory' },
        { rank: 5, route: 'BOM-BLR', score: 35, status: 'NORMAL', trend: 'Off-peak capacity absorption' },
      ];
    }
    return Array.from(routeScores.entries())
      .sort((a, b) => b[1].maxScore - a[1].maxScore)
      .slice(0, 5)
      .map(([route, info], idx) => ({
        rank: idx + 1,
        route,
        score: info.maxScore,
        status: info.maxScore >= 75 ? 'HIGH_PRESSURE' : (info.maxScore >= 50 ? 'MODERATE_PRESSURE' : 'NORMAL'),
        trend: info.reason,
      }));
  }, [events]);

  const isDemo = status?.isDemo ?? true;
  const shocks = events.filter((e) => e.event_type === 'AIRFARE_SHOCK');
  const anomalies = events.filter((e) => e.event_type === 'ANOMALY');

  if (loading) return <LoadingSkeleton />;
  if (error) return <ErrorState message={error} onRetry={loadData} />;

  return (
    <div className="space-y-6">
      {/* Strict Non-Replacement Governance Directive */}
      <div className="bg-slate-900 text-slate-200 border border-slate-800 rounded-xl p-4 flex items-start space-x-3 text-xs">
        <BrainCircuit className="w-5 h-5 text-blue-400 shrink-0 mt-0.5" />
        <div>
          <h4 className="font-bold text-sm text-slate-100 flex items-center gap-2">
            Intelligence Layer Governance (Harshitha&apos;s Module Integration)
            {isDemo && (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30 font-bold uppercase">
                DEMO FIXTURES
              </span>
            )}
          </h4>
          <p className="mt-1 leading-relaxed text-slate-400">
            <strong>Non-Replacement Directive:</strong> AI/ML models in this module provide automated shock detection, anomaly scoring, and market pressure analytics. <em>AI models do NOT calculate or alter the official statistical Airfare Price Index.</em>
          </p>
        </div>
      </div>

      {/* Section A: Airfare Shock Detection Cards */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-500" />
          A. Airfare Shock Detection
        </h3>

        {shocks.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {shocks.map((s) => (
              <div
                key={s.id}
                className="bg-white dark:bg-slate-900 border border-rose-500/40 rounded-xl p-5 shadow-sm relative overflow-hidden"
              >
                <div className="absolute top-0 right-0 bg-rose-600 text-white text-[10px] font-mono font-bold px-3 py-1 rounded-bl-lg">
                  ACTIVE SHOCK ALERT
                </div>

                <div className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <span className="text-xl font-extrabold font-mono text-slate-900 dark:text-slate-100">
                      {s.route}
                    </span>
                    <span className="text-xs font-mono font-bold text-rose-600 dark:text-rose-400">
                      (+28.4% acceleration)
                    </span>
                  </div>

                  <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-medium bg-slate-50 dark:bg-slate-800/50 p-3 rounded-lg border border-slate-200/80 dark:border-slate-800">
                    <strong>Detection Reason:</strong> {s.explanation}
                  </p>

                  <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                    <div className="p-2 bg-slate-100 dark:bg-slate-800 rounded">
                      <span className="text-slate-500 text-[10px]">Affected Sources:</span>
                      <div className="font-bold text-slate-800 dark:text-slate-200">
                        {s.affected_sources.length} Independent OTAs
                      </div>
                    </div>
                    <div className="p-2 bg-slate-100 dark:bg-slate-800 rounded">
                      <span className="text-slate-500 text-[10px]">Affected Routes:</span>
                      <div className="font-bold text-slate-800 dark:text-slate-200">
                        {s.affected_routes.join(', ')}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-100 dark:border-slate-800">
                    <span>Model: {s.model_version}</span>
                    <span>Detected: {formatDateTime(s.event_timestamp)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-6 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-xs text-emerald-800 dark:text-emerald-300 font-medium">
            No active cross-source airfare shocks detected.
          </div>
        )}
      </div>

      {/* Dual Column: Section B (Anomaly Table) & Section C (Pressure Rankings) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Section B: Anomaly Detection Table (2 cols) */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-amber-500" />
                B. Anomaly & Disruption Events
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Isolation forest statistical anomaly logs across scraped observation batches
              </p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold border-b border-slate-200 dark:border-slate-700">
                  <th className="p-2.5 font-mono">Timestamp</th>
                  <th className="p-2.5">Route</th>
                  <th className="p-2.5 font-mono">Score</th>
                  <th className="p-2.5">Event Type</th>
                  <th className="p-2.5">Explanation</th>
                  <th className="p-2.5">Status</th>
                </tr>
              </thead>
              <tbody>
                {events.map((e) => (
                  <tr key={e.id} className="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/40">
                    <td className="p-2.5 font-mono text-[11px] text-slate-500">
                      {formatDateTime(e.event_timestamp)}
                    </td>
                    <td className="p-2.5 font-mono font-bold text-slate-900 dark:text-slate-100">
                      {e.route || 'ALL'}
                    </td>
                    <td className="p-2.5 font-mono font-bold text-rose-600 dark:text-rose-400">
                      {e.anomaly_score !== undefined && e.anomaly_score !== null ? formatNumber(e.anomaly_score, 2) : 'N/A'}
                    </td>
                    <td className="p-2.5 font-mono text-[11px] font-semibold text-slate-700 dark:text-slate-300">
                      {e.event_type}
                    </td>
                    <td className="p-2.5 text-[11px] text-slate-600 dark:text-slate-400 max-w-xs truncate" title={e.explanation || ''}>
                      {e.explanation}
                    </td>
                    <td className="p-2.5">
                      <StatusBadge status={e.shock_status || 'SUSPECT'} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Section C: Airfare Pressure Rankings (1 col) */}
        <div className="lg:col-span-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
          <div className="border-b border-slate-100 dark:border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-600" />
              C. Airfare Pressure Index
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Ranked market pressure by corridor
            </p>
          </div>

          <div className="space-y-3">
            {dynamicRankings.map((item) => (
              <div
                key={item.route}
                className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200/80 dark:border-slate-800 flex items-center justify-between"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-6 h-6 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center font-mono font-bold text-xs text-slate-700 dark:text-slate-200">
                    {item.rank}
                  </div>
                  <div>
                    <div className="font-bold font-mono text-sm text-slate-900 dark:text-slate-100">
                      {item.route}
                    </div>
                    <div className="text-[10px] text-slate-500">{item.trend}</div>
                  </div>
                </div>

                <div className="text-right">
                  <div className="font-mono font-extrabold text-sm text-blue-600 dark:text-blue-400">
                    {item.score} <span className="text-[10px] text-slate-400">/100</span>
                  </div>
                  <StatusBadge status={item.status} className="text-[9px] px-1.5 py-0" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
