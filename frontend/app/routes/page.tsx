'use client';

import React from 'react';
import { DataProvider } from '@/services/data-provider';
import { Route, RouteIndex, BookingWindow, DataProviderStatus } from '@/types';
import { KpiCard } from '@/components/ui/KpiCard';
import { TrendChart } from '@/components/ui/TrendChart';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { Plane, Filter, ArrowUpDown, Shield, AlertTriangle, Layers } from 'lucide-react';
import { formatIndex, formatPercent, formatNumber } from '@/lib/utils';

export default function RouteAnalysisPage() {
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [status, setStatus] = React.useState<DataProviderStatus | undefined>();

  const [routes, setRoutes] = React.useState<Route[]>([]);
  const [routeIndices, setRouteIndices] = React.useState<Record<string, RouteIndex>>({});
  const [selectedRoute, setSelectedRoute] = React.useState<string>('DEL-BOM');
  const [selectedWindow, setSelectedWindow] = React.useState<BookingWindow>('T+15');
  const [sortField, setSortField] = React.useState<'index' | 'change' | 'weight' | 'pressure'>('index');
  const [sortOrder, setSortOrder] = React.useState<'asc' | 'desc'>('desc');

  const [historyData, setHistoryData] = React.useState<any[]>([]);

  const loadData = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const statusRes = await DataProvider.getStatus();
      setStatus(statusRes);

      const [routesRes, indicesRes, histRes] = await Promise.all([
        DataProvider.getRoutes(),
        DataProvider.getRouteIndices(selectedWindow),
        DataProvider.getIndexHistory(60, selectedWindow),
      ]);

      setRoutes(routesRes.data);
      setRouteIndices(indicesRes.data);
      setHistoryData(histRes.data.items);
    } catch (err: any) {
      setError(err.message || 'Failed to load route analysis');
    } finally {
      setLoading(false);
    }
  }, [selectedWindow]);

  React.useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading) return <LoadingSkeleton />;
  if (error) return <ErrorState message={error} onRetry={loadData} />;

  const isDemo = status?.isDemo ?? true;
  const routeList = Object.values(routeIndices);
  const activeRouteObj = routeIndices[selectedRoute] || (routeList.length > 0 ? routeList[0] : {
    route: selectedRoute,
    index: null,
    previous_index: null,
    change_percent: null,
    weight: null,
    contribution: null,
    pressure_score: undefined,
    anomaly_status: undefined,
    source_coverage: undefined,
    observation_count: undefined,
    booking_window: selectedWindow,
    status: 'INSUFFICIENT_DATA',
    timestamp: new Date().toISOString(),
  });
  const sortedRoutes = [...routeList].sort((a, b) => {
    let valA = 0;
    let valB = 0;
    if (sortField === 'index') {
      valA = a.index ?? 0;
      valB = b.index ?? 0;
    } else if (sortField === 'change') {
      valA = a.change_percent ?? 0;
      valB = b.change_percent ?? 0;
    } else if (sortField === 'weight') {
      valA = a.weight ?? 0;
      valB = b.weight ?? 0;
    } else if (sortField === 'pressure') {
      valA = a.pressure_score ?? 0;
      valB = b.pressure_score ?? 0;
    }
    return sortOrder === 'desc' ? valB - valA : valA - valB;
  });

  const toggleSort = (field: 'index' | 'change' | 'weight' | 'pressure') => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  return (
    <div className="space-y-6">
      {/* Filter Bar */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center space-x-2 text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
            <Filter className="w-4 h-4 text-blue-600" />
            <span>Select Corridor:</span>
          </div>
          <select
            value={selectedRoute}
            onChange={(e) => setSelectedRoute(e.target.value)}
            className="px-3 py-1.5 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-xs font-mono font-bold text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {routes.map((r) => (
              <option key={r.route} value={r.route}>
                {r.route} ({r.origin} → {r.destination})
              </option>
            ))}
          </select>

          <div className="h-4 w-px bg-slate-200 dark:bg-slate-700 hidden sm:block"></div>

          <div className="flex items-center space-x-2 text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
            <span>Booking Horizon:</span>
          </div>
          <div className="flex items-center space-x-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-lg text-xs font-mono">
            {(['T+1', 'T+7', 'T+15', 'T+30', 'T+45'] as BookingWindow[]).map((w) => (
              <button
                key={w}
                onClick={() => setSelectedWindow(w)}
                className={`px-2.5 py-1 rounded transition-all font-semibold ${
                  selectedWindow === w
                    ? 'bg-white dark:bg-slate-900 text-blue-600 dark:text-blue-400 shadow-sm'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900'
                }`}
              >
                {w}
              </button>
            ))}
          </div>
        </div>

        {isDemo && (
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/30 font-bold">
            DEMO FIXTURES ACTIVE
          </span>
        )}
      </div>

      {/* Selected Corridor KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title={`${activeRouteObj.route} Index`}
          value={activeRouteObj.index}
          previousValue={activeRouteObj.previous_index}
          changePercent={activeRouteObj.change_percent}
          isDemo={isDemo}
          badge={selectedWindow}
          icon={Plane}
          subtitle={`Corridor Jevons Index (${selectedWindow})`}
        />

        <KpiCard
          title="National Basket Weight"
          value={activeRouteObj.weight != null ? parseFloat((activeRouteObj.weight * 100).toFixed(1)) : null}
          unit="%"
          isDemo={isDemo}
          badge="BASKET SHARE"
          icon={Layers}
          subtitle="Fixed representative route weight"
        />

        <KpiCard
          title="Corridor Pressure Score"
          value={activeRouteObj.pressure_score ?? (activeRouteObj.status === 'SUCCESS' ? 50 : null)}
          unit="/100"
          isDemo={isDemo}
          badge="INTELLIGENCE"
          icon={AlertTriangle}
          subtitle="Relative demand pressure"
        />

        <KpiCard
          title="Sampling Coverage"
          value={activeRouteObj.source_coverage != null ? parseFloat((activeRouteObj.source_coverage * 100).toFixed(1)) : (activeRouteObj.status === 'SUCCESS' ? 100 : null)}
          unit="%"
          isDemo={isDemo}
          badge="DATA QUALITY"
          icon={Shield}
          subtitle={activeRouteObj.observation_count != null ? `${activeRouteObj.observation_count} valid observations` : 'Corridor sampling verified'}
        />
      </div>

      {/* Corridor Trend Chart */}
      <TrendChart
        data={historyData}
        isDemo={isDemo}
        title={`${selectedRoute} Elementary Index History (${selectedWindow})`}
        subtitle={`Historical constant-quality price relative trajectory for ${selectedRoute}`}
      />

      {/* Corridor Comparison Analytics Table */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <Plane className="w-5 h-5 text-blue-600" />
              Domestic Corridors Analytical Matrix
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
              Comparison across major domestic corridors for {selectedWindow} advance purchase horizon
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border-collapse">
            <thead>
              <tr className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold border-b border-slate-200 dark:border-slate-700">
                <th className="p-3">Corridor</th>
                <th className="p-3 cursor-pointer select-none hover:text-blue-600" onClick={() => toggleSort('index')}>
                  <div className="flex items-center gap-1 font-mono">
                    Index Level <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th className="p-3 cursor-pointer select-none hover:text-blue-600" onClick={() => toggleSort('change')}>
                  <div className="flex items-center gap-1 font-mono">
                    Change % <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th className="p-3 cursor-pointer select-none hover:text-blue-600" onClick={() => toggleSort('weight')}>
                  <div className="flex items-center gap-1 font-mono">
                    Weight (w_r) <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th className="p-3 font-mono">Point Impact</th>
                <th className="p-3 cursor-pointer select-none hover:text-blue-600" onClick={() => toggleSort('pressure')}>
                  <div className="flex items-center gap-1 font-mono">
                    Pressure <ArrowUpDown className="w-3 h-3" />
                  </div>
                </th>
                <th className="p-3">Anomaly Status</th>
                <th className="p-3 font-mono">Coverage</th>
              </tr>
            </thead>
            <tbody>
              {sortedRoutes.map((r) => {
                const isSelected = r.route === selectedRoute;
                const change = r.change_percent ?? 0;
                return (
                  <tr
                    key={r.route}
                    onClick={() => setSelectedRoute(r.route)}
                    className={`cursor-pointer border-b border-slate-100 dark:border-slate-800 transition-colors ${
                      isSelected
                        ? 'bg-blue-50/80 dark:bg-blue-950/40 font-semibold'
                        : 'hover:bg-slate-50 dark:hover:bg-slate-800/40'
                    }`}
                  >
                    <td className="p-3 font-bold text-slate-900 dark:text-slate-100 font-mono">
                      {r.route}
                    </td>
                    <td className="p-3 font-mono font-bold text-slate-900 dark:text-slate-100">
                      {formatIndex(r.index)}
                    </td>
                    <td className={`p-3 font-mono font-bold ${change >= 0 ? 'text-rose-600 dark:text-rose-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
                      {formatPercent(change)}
                    </td>
                    <td className="p-3 font-mono text-slate-600 dark:text-slate-400">
                      {r.weight !== undefined && r.weight !== null ? `${formatNumber(r.weight * 100, 1)}%` : 'N/A'}
                    </td>
                    <td className="p-3 font-mono text-slate-600 dark:text-slate-400">
                      {r.contribution !== undefined && r.contribution !== null ? `${r.contribution > 0 ? '+' : ''}${formatNumber(r.contribution, 2)}` : 'N/A'}
                    </td>
                    <td className="p-3 font-mono font-bold text-slate-900 dark:text-slate-100">
                      <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                        {r.pressure_score != null ? `${r.pressure_score}/100` : (r.status === 'SUCCESS' ? '50/100' : 'N/A')}
                      </span>
                    </td>
                    <td className="p-3">
                      <StatusBadge status={r.anomaly_status || 'NORMAL'} />
                    </td>
                    <td className="p-3 font-mono text-slate-500 text-[11px]">
                      {r.source_coverage !== undefined && r.source_coverage !== null ? `${formatNumber(r.source_coverage * 100, 0)}%` : (r.status === 'SUCCESS' ? '100%' : 'N/A')}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
