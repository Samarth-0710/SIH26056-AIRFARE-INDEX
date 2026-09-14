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
  SourceHealth,
  ValidationResult,
  SimulationRequest,
  SimulationResponse,
  ConfidenceMetrics,
  BookingWindow,
  DataProviderStatus,
} from '@/types';

export class DataProvider {
  private static isLiveCache: boolean | null = null;
  private static lastCheckTime = 0;

  static async getStatus(): Promise<DataProviderStatus> {
    const now = Date.now();
    // Cache live status for 15 seconds to avoid spamming /health
    if (this.isLiveCache !== null && now - this.lastCheckTime < 15000) {
      return {
        isDemo: !this.isLiveCache,
        isLive: this.isLiveCache,
        lastChecked: new Date(this.lastCheckTime).toLocaleTimeString(),
      };
    }

    const isHealthy = await apiService.checkHealth();
    this.isLiveCache = isHealthy;
    this.lastCheckTime = now;

    return {
      isDemo: !isHealthy,
      isLive: isHealthy,
      lastChecked: new Date(now).toLocaleTimeString(),
    };
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

  static async getRouteIndices(): Promise<{ data: Record<string, RouteIndex>; status: DataProviderStatus }> {
    const status = await this.getStatus();
    if (status.isLive) {
      try {
        const routes = await apiService.getRoutes();
        const results: Record<string, RouteIndex> = {};
        for (const r of routes) {
          try {
            const idx = await apiService.getRouteIndex(r.route);
            results[r.route] = idx;
          } catch {
            results[r.route] = DEMO_ROUTE_INDICES[r.route] || {
              route: r.route,
              index: 100.0,
              timestamp: new Date().toISOString(),
              booking_window: 'T+15',
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
    // Currently contributions are calculated inside engine / output in backend
    return { data: DEMO_ROUTE_CONTRIBUTIONS, status: { ...status, isDemo: !status.isLive } };
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
    return { data: DEMO_HEATMAP_DATA, status: { ...status, isDemo: !status.isLive } };
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

  static async getQualityMetrics(): Promise<{ data: QualityMetric[]; sourceHealth: SourceHealth[]; status: DataProviderStatus }> {
    const status = await this.getStatus();
    if (status.isLive) {
      try {
        const data = await apiService.getQualityMetrics();
        if (data && data.length > 0) {
          return { data, sourceHealth: DEMO_SOURCE_HEALTH, status };
        }
      } catch (err: any) {
        console.warn('API fetch failed for getQualityMetrics, falling back to Demo Data:', err.message);
      }
    }
    return { data: DEMO_QUALITY_METRICS, sourceHealth: DEMO_SOURCE_HEALTH, status: { ...status, isDemo: true, isLive: false } };
  }

  static async getValidationResult(): Promise<{ data: ValidationResult; status: DataProviderStatus }> {
    const status = await this.getStatus();
    return { data: DEMO_VALIDATION_RESULT, status: { ...status, isDemo: !status.isLive } };
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
