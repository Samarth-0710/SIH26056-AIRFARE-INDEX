'use client';

import React from 'react';
import { DataProvider } from '@/services/data-provider';
import { Route, SimulationResponse, DataProviderStatus } from '@/types';
import { KpiCard } from '@/components/ui/KpiCard';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { Sliders, AlertCircle, ArrowRight, RefreshCw, Calculator, Activity, Plane } from 'lucide-react';
import { formatIndex, formatPercent, formatNumber } from '@/lib/utils';

export default function SimulatorPage() {
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [status, setStatus] = React.useState<DataProviderStatus | undefined>();

  const [routes, setRoutes] = React.useState<Route[]>([]);
  const [selectedRoute, setSelectedRoute] = React.useState<string>('DEL-BOM');
  const [shockPercent, setShockPercent] = React.useState<number>(15);
  const [simulating, setSimulating] = React.useState<boolean>(false);

  const [simulationResult, setSimulationResult] = React.useState<SimulationResponse | null>(null);

  const loadInitialData = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const statusRes = await DataProvider.getStatus();
      setStatus(statusRes);

      const routesRes = await DataProvider.getRoutes();
      setRoutes(routesRes.data);

      // Run initial default simulation (+15% on DEL-BOM)
      const simRes = await DataProvider.postSimulation({
        route: 'DEL-BOM',
        shock_percent: 15,
      });
      setSimulationResult(simRes.data);
    } catch (err: any) {
      setError(err.message || 'Failed to initialize simulator');
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

  const handleRunSimulation = async (e: React.FormEvent) => {
    e.preventDefault();
    setSimulating(true);
    try {
      const res = await DataProvider.postSimulation({
        route: selectedRoute,
        shock_percent: shockPercent,
      });
      setSimulationResult(res.data);
    } catch (err: any) {
      alert(`Simulation failed: ${err.message}`);
    } finally {
      setSimulating(false);
    }
  };

  if (loading) return <LoadingSkeleton />;
  if (error) return <ErrorState message={error} onRetry={loadInitialData} />;

  const isDemo = status?.isDemo ?? true;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Simulation Policy Header */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-blue-600/10 text-blue-600 dark:text-blue-400 flex items-center justify-center">
              <Sliders className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                WHAT-IF AIRFARE POLICY SIMULATOR
                {isDemo && (
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/30 font-bold uppercase">
                    DEMO DATA
                  </span>
                )}
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                Hypothetical route shock impact modeling on national airfare price index aggregate
              </p>
            </div>
          </div>

          <span className="text-xs font-mono font-bold text-amber-700 dark:text-amber-400 bg-amber-500/10 px-3 py-1 rounded-full border border-amber-500/30 hidden sm:inline-block">
            SIMULATION — NOT OFFICIAL INDEX
          </span>
        </div>
      </div>

      {/* Main Interactive Controls & Results Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Controls Column (1 col) */}
        <div className="lg:col-span-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-5">
          <div className="border-b border-slate-100 dark:border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider flex items-center gap-2">
              <Calculator className="w-4 h-4 text-blue-600" />
              Scenario Parameters
            </h3>
            <p className="text-xs text-slate-500">Configure hypothetical corridor shock</p>
          </div>

          <form onSubmit={handleRunSimulation} className="space-y-4 text-xs font-medium">
            {/* Route Selector */}
            <div>
              <label className="block text-slate-700 dark:text-slate-300 font-semibold mb-1.5">
                Target Domestic Corridor (r):
              </label>
              <select
                value={selectedRoute}
                onChange={(e) => setSelectedRoute(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg font-mono font-bold text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {routes.map((r) => (
                  <option key={r.route} value={r.route}>
                    {r.route} ({r.origin} → {r.destination})
                  </option>
                ))}
              </select>
            </div>

            {/* Shock Percentage Input & Slider */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-slate-700 dark:text-slate-300 font-semibold">
                  Hypothetical Fare Shock (Delta P_r):
                </label>
                <span className="font-mono font-bold text-sm text-blue-600 dark:text-blue-400">
                  {shockPercent > 0 ? `+${shockPercent}%` : `${shockPercent}%`}
                </span>
              </div>
              <input
                type="range"
                min="-50"
                max="100"
                step="5"
                value={shockPercent}
                onChange={(e) => setShockPercent(Number(e.target.value))}
                className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
              />
              <div className="flex justify-between text-[10px] text-slate-400 font-mono mt-1">
                <span>-50%</span>
                <span>0%</span>
                <span>+50%</span>
                <span>+100%</span>
              </div>
            </div>

            {/* Quick Preset Buttons */}
            <div>
              <label className="block text-slate-500 text-[11px] mb-1.5">Quick Scenario Presets:</label>
              <div className="grid grid-cols-3 gap-1.5 font-mono">
                {[-10, 15, 25].map((val) => (
                  <button
                    key={val}
                    type="button"
                    onClick={() => setShockPercent(val)}
                    className={`py-1 rounded border text-[11px] font-bold transition-all ${
                      shockPercent === val
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-300 dark:border-slate-700 hover:bg-slate-200'
                    }`}
                  >
                    {val > 0 ? `+${val}%` : `${val}%`}
                  </button>
                ))}
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={simulating}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-lg transition-colors shadow-md shadow-blue-500/20 flex items-center justify-center gap-2"
            >
              {simulating ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" /> Simulating...
                </>
              ) : (
                <>
                  Execute Simulation <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </div>

        {/* Results Column (2 cols) */}
        <div className="lg:col-span-2 space-y-4">
          {/* Result Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <KpiCard
              title="Baseline Index"
              value={simulationResult?.current_index ?? 112.6}
              badge="CURRENT"
              icon={Activity}
              subtitle="Official un-shocked level"
            />

            <KpiCard
              title="Projected Index"
              value={simulationResult?.projected_index ?? 115.0}
              changePercent={
                simulationResult && simulationResult.current_index && simulationResult.projected_index
                  ? ((simulationResult.projected_index - simulationResult.current_index) / simulationResult.current_index) * 100
                  : 2.1
              }
              badge="PROJECTED"
              icon={Sliders}
              subtitle="National composite level"
            />

            <KpiCard
              title="Aggregate Impact"
              value={simulationResult?.impact_points ?? 2.4}
              unit="pts"
              badge="DELTA"
              icon={Calculator}
              subtitle={`Impact of ${selectedRoute} shock`}
            />
          </div>

          {/* Scenario Details Box */}
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider border-b border-slate-100 dark:border-slate-800 pb-2">
              Simulation Scenario Summary
            </h3>

            <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg space-y-2 text-xs font-mono">
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Target Corridor:</span>
                <span className="font-bold text-slate-900 dark:text-slate-100">{simulationResult?.route}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Hypothetical Shock:</span>
                <span className="font-bold text-rose-600 dark:text-rose-400">
                  {simulationResult?.shock_percent ? `${simulationResult.shock_percent > 0 ? '+' : ''}${simulationResult.shock_percent}%` : '+15%'}
                </span>
              </div>
              <div className="flex items-center justify-between border-t border-slate-200 dark:border-slate-700 pt-2">
                <span className="text-slate-500">National Index Impact:</span>
                <span className="font-bold text-blue-600 dark:text-blue-400">
                  +{formatNumber(simulationResult?.impact_points, 2)} Index Points
                </span>
              </div>
            </div>

            {/* Simulation Disclaimer Alert */}
            <div className="flex items-start space-x-2 text-[11px] text-amber-800 dark:text-amber-300 bg-amber-500/10 p-3 rounded-lg border border-amber-500/30">
              <AlertCircle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
              <span>
                <strong>Official Disclaimer:</strong> This scenario applies a hypothetical route-level fare shock using the configured representative basket and weights. It does <em>not</em> modify or recalculate the official Airfare Price Index database records.
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
