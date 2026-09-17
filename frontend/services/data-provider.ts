import { apiService } from './api';
import {
  DEMO_NATIONAL_INDEX,
  DEMO_ROUTES,
  DEMO_ROUTE_CONTRIBUTIONS,
  DEMO_ROUTE_INDICES,
  DEMO_BOOKING_WINDOW_SNAPSHOTS,
  DEMO_HEATMAP_DATA,
  DEMO_INTELLIGENCE_EVENTS,
  DEMO_QUALITY_METRICS,
  DEMO_SOURCE_HEALTH,
  DEMO_VALIDATION_RESULT,
  DEMO_CONFIDENCE_METRICS,
  generateDemoHistory,
  simulatePolicyShock,
} from './demo-data';
import {
  IndexResult,
  IndexHistory,
  Route,
  RouteIndex,
  RouteContribution,
  IntelligenceEvent,
  QualityMetric,
  QualitySummary,
  SourceHealth,
  ValidationResult,
  SimulationRequest,
  SimulationResponse,
  ConfidenceMetrics,
  BookingWindow,
  DataProviderStatus,
  LiveSourceStatus,
} from '@/types';

export class DataProvider {
  private static statusCache: DataProviderStatus | null = null;
  private static lastCheckTime = 0;
  private static statusListeners: Array<(status: DataProviderStatus) => void> = [];

  static subscribeStatus(listener: (status: DataProviderStatus) => void): () => void {
    this.statusListeners.push(listener);
    if (this.statusCache) {
      listener(this.statusCache);
    }
    return () => {
      this.statusListeners = this.statusListeners.filter((l) => l !== listener);
    };
  }

  private static notifyStatusListeners(status: DataProviderStatus) {
    for (const listener of this.statusListeners) {
      try {
        listener(status);
      } catch (err) {
        console.error('Error in status listener', err);
      }
    }
  }

  static async getStatus(forceRefresh = false): Promise<DataProviderStatus> {
    const now = Date.now();
    // Cache live status for 15 seconds to avoid spamming /health and /live-status
    if (!forceRefresh && this.statusCache !== null && now - this.lastCheckTime < 15000) {
      return this.statusCache;
    }

    const isHealthy = await apiService.checkHealth();
    let liveSource: LiveSourceStatus = {
      source: 'IGNAV',
      is_configured: false,
      is_connected: false,
      status: 'NOT_CONFIGURED',
      message: 'Live API credentials unconfigured; fallback active',
    };

    if (isHealthy) {
      try {
        liveSource = await apiService.getLiveSourceStatus();
      } catch (err: any) {
        liveSource = {
          source: 'IGNAV',
          is_configured: false,
          is_connected: false,
          status: 'DEGRADED',
          message: 'Failed to reach live source status endpoint; fallback active',
        };
      }
    }

    const statusResult: DataProviderStatus = {
      isDemo: !isHealthy,
      isLive: isHealthy,
      lastChecked: new Date(now).toLocaleTimeString(),
      liveSource,
    };

    this.statusCache = statusResult;
    this.lastCheckTime = now;
    this.notifyStatusListeners(statusResult);

    return statusResult;
  }

  static async getCurrentIndex(bookingWindow?: BookingWindow): Promise<{ data: IndexResult; status: DataProviderStatus }> {
    const status = await this.getStatus();
    if (status.isLive) {
      try {
        const data = await apiService.getCurrentIndex(bookingWindow);
        return { data, status };
      } catch (err: any) {
        console.warn('API fetch failed for getCurrentIndex, falling back to Demo Data:', err.message);
      }
    }
    const data = bookingWindow ? (DEMO_BOOKING_WINDOW_SNAPSHOTS[bookingWindow] || DEMO_NATIONAL_INDEX) : DEMO_NATIONAL_INDEX;
    return { data, status: { ...status, isDemo: true, isLive: false } };
  }

  static async getIndexHistory(days = 30, bookingWindow?: BookingWindow): Promise<{ data: IndexHistory; status: DataProviderStatus }> {
    const status = await this.getStatus();
    if (status.isLive) {
      try {
        const data = await apiService.getIndexHistory(undefined, undefined, bookingWindow);
        if (data && data.items && data.items.length > 0) {
          return { data, status };
        }
      } catch (err: any) {
        console.warn('API fetch failed for getIndexHistory, falling back to Demo Data:', err.message);
      }
    }
    const items = generateDemoHistory(days, 100);
    return { data: { items }, status: { ...status, isDemo: true, isLive: false } };
  }

  static async getRoutes(): Promise<{ data: Route[]; status: DataProviderStatus }> {
    const status = await this.getStatus();
    if (status.isLive) {
      try {
        const data = await apiService.getRoutes();
        if (data && data.length > 0) return { data, status };
      } catch (err: any) {
        console.warn('API fetch failed for getRoutes, falling back to Demo Data:', err.message);
      }
    }
    return { data: DEMO_ROUTES, status: { ...status, isDemo: true, isLive: false } };
  }

  static async getRouteIndices(bookingWindow?: BookingWindow): Promise<{ data: Record<string, RouteIndex>; status: DataProviderStatus }> {
    const status = await this.getStatus();
    if (status.isLive) {
      try {
        const routes = await apiService.getRoutes();
        const results: Record<string, RouteIndex> = {};
        for (const r of routes) {
          try {
            const idx = await apiService.getRouteIndex(r.route, bookingWindow);
            results[r.route] = idx;
          } catch {
            results[r.route] = DEMO_ROUTE_INDICES[r.route] || {
              route: r.route,
              index: 100.0,
              timestamp: new Date().toISOString(),
              booking_window: bookingWindow || 'T+15',
              status: 'DEMO',
            };
          }
        }
        if (Object.keys(results).length > 0) return { data: results, status };
      } catch (err: any) {
        console.warn('API fetch failed for getRouteIndices, falling back to Demo Data:', err.message);
      }
    }
    return { data: DEMO_ROUTE_INDICES, status: { ...status, isDemo: true, isLive: false } };
  }

  static async getRouteContributions(): Promise<{ data: RouteContribution[]; status: DataProviderStatus }> {
    const status = await this.getStatus();
    if (status.isLive) {
      try {
        const data = await apiService.getRouteContributions();
        if (data && data.length > 0) return { data, status };
      } catch (err: any) {
        console.warn('API fetch failed for getRouteContributions, falling back to Demo Data:', err.message);
      }
    }
    return { data: DEMO_ROUTE_CONTRIBUTIONS, status: { ...status, isDemo: true, isLive: false } };
  }

  static async getBookingWindowSnapshots(): Promise<{ data: Record<BookingWindow, IndexResult>; status: DataProviderStatus }> {
    const status = await this.getStatus();
    if (status.isLive) {
      try {
        const windows: BookingWindow[] = ['T+1', 'T+7', 'T+15', 'T+30', 'T+45'];
        const results: Partial<Record<BookingWindow, IndexResult>> = {};
        for (const w of windows) {
          const res = await apiService.getCurrentIndex(w);
          results[w] = res;
        }
        return { data: results as Record<BookingWindow, IndexResult>, status };
      } catch (err: any) {
        console.warn('API fetch failed for booking windows, falling back to Demo Data:', err.message);
      }
    }
    return { data: DEMO_BOOKING_WINDOW_SNAPSHOTS, status: { ...status, isDemo: true, isLive: false } };
  }

  static async getHeatmapData(): Promise<{ data: any[]; status: DataProviderStatus }> {
    const status = await this.getStatus();
    if (status.isLive) {
      try {
        const data = await apiService.getBookingWindowsMatrix();
        if (data && data.length > 0) return { data, status };
      } catch (err: any) {
        console.warn('API fetch failed for getHeatmapData, falling back to Demo Data:', err.message);
      }
    }
    return { data: DEMO_HEATMAP_DATA, status: { ...status, isDemo: true, isLive: false } };
  }

  static async getBookingWindowsComparisonHistory(): Promise<{ data: any[]; status: DataProviderStatus }> {
    const status = await this.getStatus();
    const windows: BookingWindow[] = ['T+1', 'T+7', 'T+15', 'T+30', 'T+45'];
    if (status.isLive) {
      try {
        const windowHistories = await Promise.all(
          windows.map((w) => apiService.getWindowIndex(w).catch(() => ({ items: [] })))
        );

        const dateMap = new Map<string, any>();
        windows.forEach((w, i) => {
          const hist = windowHistories[i];
          if (hist && Array.isArray(hist.items)) {
            for (const item of hist.items) {
              if (!dateMap.has(item.observation_date)) {
                dateMap.set(item.observation_date, { date: item.observation_date });
              }
              dateMap.get(item.observation_date)![w] = item.index;
            }
          }
        });

        const sorted = Array.from(dateMap.values()).sort((a, b) => a.date.localeCompare(b.date));
        if (sorted.length > 0) {
          return { data: sorted, status };
        }
      } catch (err: any) {
        console.warn('Failed to fetch multi-window comparison history, falling back:', err.message);
      }
    }

    // Mathematically aligned demo fallback
    const baseItems = generateDemoHistory(30, 100);
    const demoOverlay = baseItems.map((item) => {
      const val = item.index ?? 110;
      return {
        date: item.observation_date,
        'T+1': parseFloat((val * 1.108).toFixed(1)),
        'T+7': parseFloat((val * 1.033).toFixed(1)),
        'T+15': val,
        'T+30': parseFloat((val * 0.951).toFixed(1)),
        'T+45': parseFloat((val * 0.918).toFixed(1)),
      };
    });
    return { data: demoOverlay, status: { ...status, isDemo: true, isLive: false } };
  }

  static async getIntelligenceEvents(shocksOnly = false): Promise<{ data: IntelligenceEvent[]; status: DataProviderStatus }> {
    const status = await this.getStatus();
    if (status.isLive) {
      try {
        const data = await apiService.getIntelligenceEvents(shocksOnly);
        if (data && data.length > 0) return { data, status };
      } catch (err: any) {
        console.warn('API fetch failed for getIntelligenceEvents, falling back to Demo Data:', err.message);
      }
    }
    const filtered = shocksOnly ? DEMO_INTELLIGENCE_EVENTS.filter((e) => e.event_type === 'AIRFARE_SHOCK') : DEMO_INTELLIGENCE_EVENTS;
    return { data: filtered, status: { ...status, isDemo: true, isLive: false } };
  }

  static async getQualityMetrics(): Promise<{
    data: QualityMetric[];
    sourceHealth: SourceHealth[];
    summary?: QualitySummary;
    status: DataProviderStatus;
  }> {
    const status = await this.getStatus();
    if (status.isLive) {
      try {
        const [metrics, summary] = await Promise.all([
          apiService.getQualityMetrics(),
          apiService.getQualitySummary().catch(() => null),
        ]);
        const sourceHealth = summary?.source_health && summary.source_health.length > 0
          ? summary.source_health
          : DEMO_SOURCE_HEALTH;
        return {
          data: metrics.length > 0 ? metrics : DEMO_QUALITY_METRICS,
          sourceHealth,
          summary: summary || undefined,
          status,
        };
      } catch (err: any) {
        console.warn('API fetch failed for getQualityMetrics, falling back to Demo Data:', err.message);
      }
    }
    return {
      data: DEMO_QUALITY_METRICS,
      sourceHealth: DEMO_SOURCE_HEALTH,
      status: { ...status, isDemo: true, isLive: false },
    };
  }

  static async getValidationResult(): Promise<{ data: ValidationResult; status: DataProviderStatus }> {
    const status = await this.getStatus();
    if (status.isLive) {
      try {
        const data = await apiService.getValidationResult();
        return { data, status };
      } catch (err: any) {
        console.warn('API fetch failed for getValidationResult, falling back to Demo Data:', err.message);
      }
    }
    return { data: DEMO_VALIDATION_RESULT, status: { ...status, isDemo: true, isLive: false } };
  }

  static async getConfidenceMetrics(): Promise<{ data: ConfidenceMetrics; status: DataProviderStatus }> {
    const status = await this.getStatus();
    return { data: DEMO_CONFIDENCE_METRICS, status: { ...status, isDemo: !status.isLive } };
  }

  static async postSimulation(req: SimulationRequest): Promise<{ data: SimulationResponse; status: DataProviderStatus }> {
    const status = await this.getStatus();
    if (status.isLive) {
      try {
        const data = await apiService.postSimulation(req);
        return { data, status };
      } catch (err: any) {
        console.warn('API fetch failed for postSimulation, using simulation fallback:', err.message);
      }
    }
    const data = simulatePolicyShock(req);
    return { data, status: { ...status, isDemo: true, isLive: false } };
  }
}
