'use client';

import React from 'react';
import { DataProvider } from '@/services/data-provider';
import {
  IndexResult,
  IndexHistory,
  RouteContribution,
  IntelligenceEvent,
  QualityMetric,
  ConfidenceMetrics,
  DataProviderStatus,
  BookingWindow,
} from '@/types';
import { KpiCard } from '@/components/ui/KpiCard';
import { TrendChart } from '@/components/ui/TrendChart';
import { ContributionChart } from '@/components/ui/ContributionChart';
import { ConfidenceMeter } from '@/components/ui/ConfidenceMeter';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import {
  Activity,
  Layers,
  AlertTriangle,
  ShieldCheck,
  CalendarClock,
  ArrowRight,
  TrendingUp,
  Radio,
  CheckCircle2,
} from 'lucide-react';
import Link from 'next/link';
import { formatIndex, formatPercent, cn } from '@/lib/utils';

export default function DashboardPage() {
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [status, setStatus] = React.useState<DataProviderStatus | undefined>();

  const [nationalIndex, setNationalIndex] = React.useState<IndexResult | null>(null);
  const [history, setHistory] = React.useState<IndexHistory | null>(null);
  const [contributions, setContributions] = React.useState<RouteContribution[]>([]);
  const [snapshots, setSnapshots] = React.useState<Record<BookingWindow, IndexResult> | null>(null);
  const [events, setEvents] = React.useState<IntelligenceEvent[]>([]);
  const [quality, setQuality] = React.useState<QualityMetric[]>([]);
  const [confidence, setConfidence] = React.useState<ConfidenceMetrics | undefined>();
  const [isMoSPIConnected, setIsMoSPIConnected] = React.useState<boolean>(false);

  const loadData = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const statusRes = await DataProvider.getStatus();
      setStatus(statusRes);

      const [
        indexRes,
        histRes,
        contribRes,
        snapRes,
        eventRes,
        qualRes,
        confRes,
        valRes,
      ] = await Promise.all([
        DataProvider.getCurrentIndex(),
        DataProvider.getIndexHistory(90),
        DataProvider.getRouteContributions(),
        DataProvider.getBookingWindowSnapshots(),
        DataProvider.getIntelligenceEvents(false),
        DataProvider.getQualityMetrics(),
        DataProvider.getConfidenceMetrics(),
        typeof DataProvider.getValidationResult === 'function'
          ? DataProvider.getValidationResult().catch(() => ({ data: { is_reference_connected: false } }))
          : Promise.resolve({ data: { is_reference_connected: false } }),
      ]);

      setNationalIndex(indexRes.data);
      setHistory(histRes.data);
      setContributions(contribRes.data);
      setSnapshots(snapRes.data);
      setEvents(eventRes.data);
      setQuality(qualRes.data);
      setConfidence(confRes.data);
      setIsMoSPIConnected(Boolean((valRes as any)?.data?.is_reference_connected));
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard data');
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
  const activeShock = events.find((e) => e.event_type === 'AIRFARE_SHOCK');

  const isLiveConnected = Boolean(!isDemo && status?.liveSource?.is_connected);
  const liveSourceStatus = status?.liveSource?.status || 'NOT_CONFIGURED';
  const liveSourceMessage = status?.liveSource?.message || 'Live API credentials unconfigured; fallback active';
  const isLiveDegraded = Boolean(!isDemo && (liveSourceStatus === 'DEGRADED' || liveSourceStatus === 'ERROR'));

  return (
    <div className="space-y-6">
      {/* Top Banner / Disclaimer */}
      {isDemo && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-3.5 px-4 flex items-center justify-between text-xs text-amber-800 dark:text-amber-300">
          <div className="flex items-center space-x-2">
            <Radio className="w-4 h-4 text-amber-500 animate-pulse shrink-0" />
            <span>
              <strong>Demo Data Active:</strong> Backend API is currently offline or unreachable. Displaying mathematically consistent demo index fixtures.
            </span>
          </div>
          <span className="font-mono font-bold text-[10px] uppercase bg-amber-500/20 px-2 py-0.5 rounded border border-amber-500/40">
            DEMO MODE
          </span>
        </div>
      )}

      {/* System Integrity & Reference Connection Status Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
        <div className="p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl flex items-center justify-between shadow-sm">
          <div className="flex items-center space-x-2.5">
            {isMoSPIConnected ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />
            )}
            <div>
              <div className="font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                <span>Real MoSPI validation</span>
                <Link href="/validation" className="text-[11px] text-blue-600 hover:underline">
                  (Details &rarr;)
                </Link>
              </div>
              <div className="text-[11px] text-slate-500">
                {isMoSPIConnected
                  ? 'Official CPI Airfare Series (07.3.3.1.2.01, Base 2024 = 100)'
                  : 'External MoSPI benchmark dataset not loaded'}
              </div>
            </div>
          </div>
          <span
            className={`font-mono text-[11px] font-bold px-2 py-0.5 rounded uppercase ${
              isMoSPIConnected
                ? 'bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 border border-emerald-500/40'
                : 'bg-amber-500/20 text-amber-700 dark:text-amber-300 border border-amber-500/40'
            }`}
          >
            {isMoSPIConnected ? '🟢 Connected' : '🟡 Not connected'}
          </span>
        </div>

        <div className="p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl flex items-center justify-between shadow-sm">
          <div className="flex items-center space-x-2.5">
            {isLiveConnected ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
            ) : isLiveDegraded ? (
              <AlertTriangle className="w-4 h-4 text-rose-500 shrink-0" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />
            )}
            <div>
              <div className="font-bold text-slate-900 dark:text-slate-100">Real live airfare data</div>
              <div className="text-[11px] text-slate-500">
                {isLiveConnected
                  ? (status?.liveSource?.message || 'Live Ignav airfare data is available.')
                  : liveSourceMessage}
              </div>
            </div>
          </div>
          <span
            className={cn(
              'font-mono text-[11px] font-bold px-2 py-0.5 rounded uppercase border',
              isLiveConnected
                ? 'bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 border-emerald-500/40'
                : isLiveDegraded
                ? 'bg-rose-500/20 text-rose-700 dark:text-rose-300 border-rose-500/40'
                : 'bg-amber-500/20 text-amber-700 dark:text-amber-300 border-amber-500/40'
            )}
          >
            {isLiveConnected
              ? '🟢 Connected'
              : isLiveDegraded
              ? '🔴 Degraded'
              : '🟡 Not demonstrated'}
          </span>
        </div>
      </div>

      {/* Main KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="National Airfare Price Index"
          value={nationalIndex?.index}
          previousValue={nationalIndex?.previous_index}
          changePercent={nationalIndex?.change_percent}
          isDemo={isDemo}
          confidence={confidence?.overall_confidence}
          statusText={nationalIndex?.status || 'SUCCESS'}
          badge="BASE 100.0"
          icon={Activity}
          subtitle={`Window: ${nationalIndex?.booking_window || 'T+15'}`}
        />

        <KpiCard
          title="Observation Coverage"
          value={confidence?.route_coverage}
          unit="%"
          isDemo={isDemo}
          statusText="FULL BASKET"
          badge="TOP 20"
          icon={Layers}
          subtitle="Top domestic corridors monitored"
        />

        <KpiCard
          title="Top Inflating Corridor"
          value={contributions[0]?.route_index}
          changePercent={contributions[0]?.point_contribution ?? 0}
          isDemo={isDemo}
          statusText={contributions[0]?.route || 'N/A'}
          badge="CORRIDOR"
          icon={TrendingUp}
          subtitle={contributions[0]?.weight != null ? `Weight: ${(contributions[0].weight * 100).toFixed(1)}%` : 'Corridor weight pending'}
        />

        <KpiCard
          title="Intelligence Shock Status"
          value={activeShock ? 1 : 0}
          unit={activeShock ? 'ACTIVE SHOCK' : 'NORMAL'}
          isDemo={isDemo}
          statusText={activeShock?.shock_status || 'NORMAL'}
          badge="AI SHOCK"
          icon={AlertTriangle}
          subtitle={activeShock ? `${activeShock.route} fare acceleration` : 'No active market shocks'}
        />
      </div>

      {/* Historical Trend Chart & Route Contributions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <TrendChart
            data={history?.items || []}
            isDemo={isDemo}
            title="National Airfare Price Index Trajectory"
            subtitle="Official Jevons short-index daily aggregate ($T+15$ advance window)"
          />
        </div>
        <div className="lg:col-span-1">
          <ContributionChart
            data={contributions}
            isDemo={isDemo}
            title="Route Contributions"
          />
        </div>
      </div>

      {/* Booking Window Snapshot Row */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <CalendarClock className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              Booking Window Snapshot ($T+1$ to $T+45$)
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
              Elementary indices evaluated separately across advance purchase horizons
            </p>
          </div>
          <Link
            href="/booking-windows"
            className="text-xs font-bold text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
          >
            Full Horizon Analysis <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {(['T+1', 'T+7', 'T+15', 'T+30', 'T+45'] as BookingWindow[]).map((w) => {
            const snap = snapshots ? snapshots[w] : null;
            const change = snap?.change_percent ?? 0;
            return (
              <div
                key={w}
                className="p-3.5 bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-200/80 dark:border-slate-800 flex flex-col justify-between"
              >
                <div className="flex items-center justify-between text-xs text-slate-500 font-semibold mb-1">
                  <span>{w}</span>
                  <span className="text-[10px] text-slate-400">
                    {w === 'T+1' ? '1-Day' : w === 'T+7' ? '7-Day' : w === 'T+15' ? '15-Day' : w === 'T+30' ? '30-Day' : '45-Day'}
                  </span>
                </div>
                <div className="text-2xl font-extrabold font-mono text-slate-900 dark:text-slate-100">
                  {formatIndex(snap?.index)}
                </div>
                <div className={`text-xs font-mono font-bold mt-1 ${change >= 0 ? 'text-rose-600 dark:text-rose-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
                  {formatPercent(change)}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Intelligence & Data Quality Summary Dual Panel */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Intelligence Alert Card */}
        <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3 border-b border-slate-100 dark:border-slate-800 pb-2">
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-amber-500" />
                Intelligence & Airfare Shock Alerts
              </h3>
              <Link href="/intelligence" className="text-xs font-bold text-blue-600 hover:underline">
                View All Events
              </Link>
            </div>

            {activeShock ? (
              <div className="p-3.5 bg-rose-500/10 border border-rose-500/30 rounded-lg space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-rose-700 dark:text-rose-400 font-mono">
                    POTENTIAL AIRFARE SHOCK DETECTED
                  </span>
                  <StatusBadge status={activeShock.shock_status || 'SHOCK'} />
                </div>
                <div className="text-slate-700 dark:text-slate-300 font-medium">
                  <strong>Corridor:</strong> {activeShock.route}
                </div>
                <p className="text-slate-600 dark:text-slate-400 text-[11px] leading-relaxed">
                  {activeShock.explanation}
                </p>
                <div className="flex items-center space-x-4 text-[10px] font-mono text-slate-500 pt-1">
                  <span>Sources: {activeShock.affected_sources.length}</span>
                  <span>Routes: {activeShock.affected_routes.length}</span>
                </div>
              </div>
            ) : (
              <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-xs text-emerald-800 dark:text-emerald-300 font-medium">
                No active airfare shocks detected across domestic corridors.
              </div>
            )}
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 text-[11px] text-slate-400">
            Powered by Harshitha's Intelligence Layer (Isolation Forest & Cross-Source Accelerator)
          </div>
        </div>

        {/* Confidence & Reliability Card */}
        <ConfidenceMeter metrics={confidence} />
      </div>

      {/* Metadata Provenance Bar */}
      <div className="bg-slate-900 text-slate-300 p-4 rounded-xl text-xs font-mono flex flex-wrap items-center justify-between gap-3 border border-slate-800">
        <div className="flex flex-wrap items-center gap-4">
          <span>Methodology: <strong className="text-blue-400">{nationalIndex?.methodology_version || 'JEVONS_SHORT_INDEX_v1.0'}</strong></span>
          <span>Basket: <strong className="text-slate-100">{nationalIndex?.basket_version || 'BASKET_v1.0'}</strong></span>
          <span>Weights: <strong className="text-slate-100">{nationalIndex?.weight_version || 'DGCA_PAX_2024'}</strong></span>
        </div>
        <div className="text-[11px] text-slate-400">
          Execution Checksum: {nationalIndex?.execution_checksum?.substring(0, 12) || 'a8f4c91d8e72'}...
        </div>
      </div>
    </div>
  );
}
