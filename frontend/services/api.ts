import {
  IndexResult,
  IndexHistory,
  Route,
  RouteIndex,
  RouteContribution,
  QualityMetric,
  QualitySummary,
  IntelligenceEvent,
  SimulationRequest,
  SimulationResponse,
  BookingWindow,
  ValidationResult,
  LiveSourceStatus,
} from '@/types';
import { toNumber } from '@/lib/utils';

export function normalizeIndexResult(raw: any): IndexResult {
  if (!raw) return raw;
  return {
    ...raw,
    index: toNumber(raw.index),
    previous_index: toNumber(raw.previous_index),
    change_percent: toNumber(raw.change_percent),
  };
}

export function normalizeIndexHistory(raw: any): IndexHistory {
  if (!raw || !Array.isArray(raw.items)) return { items: [] };
  return {
    ...raw,
    items: raw.items.map(normalizeIndexResult),
  };
}

export function normalizeRouteIndex(raw: any): RouteIndex {
  if (!raw) return raw;
  return {
    ...raw,
    index: toNumber(raw.index),
    previous_index: toNumber(raw.previous_index),
    change_percent: toNumber(raw.change_percent),
    weight: toNumber(raw.weight),
    contribution: toNumber(raw.contribution),
    pressure_score: toNumber(raw.pressure_score) ?? undefined,
    source_coverage: toNumber(raw.source_coverage) ?? undefined,
    observation_count: toNumber(raw.observation_count) ?? undefined,
  };
}

export function normalizeQualityMetric(raw: any): QualityMetric {
  if (!raw) return raw;
  return {
    ...raw,
    observation_count: toNumber(raw.observation_count) ?? 0,
    route_coverage: toNumber(raw.route_coverage),
    source_coverage: toNumber(raw.source_coverage),
    freshness_minutes: toNumber(raw.freshness_minutes),
    missing_observations: toNumber(raw.missing_observations) ?? 0,
    invalid_observations: toNumber(raw.invalid_observations) ?? 0,
    anomalous_valid_observations: toNumber(raw.anomalous_valid_observations) ?? 0,
  };
}

export function normalizeIntelligenceEvent(raw: any): IntelligenceEvent {
  if (!raw) return raw;
  return {
    ...raw,
    anomaly_score: toNumber(raw.anomaly_score),
    pressure_score: toNumber(raw.pressure_score),
  };
}

export function normalizeSimulationResponse(raw: any): SimulationResponse {
  if (!raw) return raw;
  return {
    ...raw,
    current_index: toNumber(raw.current_index),
    shock_percent: toNumber(raw.shock_percent) ?? 0,
    projected_index: toNumber(raw.projected_index),
    impact_points: toNumber(raw.impact_points),
  };
}

export function normalizeRouteContribution(raw: any): RouteContribution {
  if (!raw) return raw;
  return {
    ...raw,
    weight: toNumber(raw.weight) ?? 0,
    route_index: toNumber(raw.route_index) ?? 100,
    level_contribution: toNumber(raw.level_contribution) ?? 0,
    point_contribution: toNumber(raw.point_contribution) ?? 0,
    percentage_share_of_change: toNumber(raw.percentage_share_of_change) ?? 0,
  };
}

export function normalizeValidationResult(raw: any): ValidationResult {
  if (!raw) return raw;
  return {
    ...raw,
    metrics: Array.isArray(raw.metrics)
      ? raw.metrics.map((m: any) => ({
          ...m,
          value: typeof m.value === 'number' ? toNumber(m.value) : m.value,
        }))
      : [],
    history: Array.isArray(raw.history)
      ? raw.history.map((h: any) => ({
          ...h,
          calculated_index: toNumber(h.calculated_index) ?? 100,
          reference_index: h.reference_index != null ? toNumber(h.reference_index) : null,
        }))
      : [],
    comparison: raw.comparison
      ? {
          ...raw.comparison,
          our_monthly_index: raw.comparison.our_monthly_index != null ? toNumber(raw.comparison.our_monthly_index) : null,
          mospi_monthly_index: raw.comparison.mospi_monthly_index != null ? toNumber(raw.comparison.mospi_monthly_index) : null,
          absolute_difference: raw.comparison.absolute_difference != null ? toNumber(raw.comparison.absolute_difference) : null,
          percentage_difference: raw.comparison.percentage_difference != null ? toNumber(raw.comparison.percentage_difference) : null,
          our_rebased_index: raw.comparison.our_rebased_index != null ? toNumber(raw.comparison.our_rebased_index) : null,
          mospi_rebased_index: raw.comparison.mospi_rebased_index != null ? toNumber(raw.comparison.mospi_rebased_index) : null,
        }
      : undefined,
    movement: raw.movement
      ? {
          ...raw.movement,
          our_mom_change: raw.movement.our_mom_change != null ? toNumber(raw.movement.our_mom_change) : null,
          mospi_mom_change: raw.movement.mospi_mom_change != null ? toNumber(raw.movement.mospi_mom_change) : null,
          absolute_difference: raw.movement.absolute_difference != null ? toNumber(raw.movement.absolute_difference) : null,
        }
      : undefined,
    correlation: raw.correlation
      ? {
          ...raw.correlation,
          value: raw.correlation.value != null ? toNumber(raw.correlation.value) : null,
        }
      : undefined,
    monthly_series: Array.isArray(raw.monthly_series)
      ? raw.monthly_series.map((m: any) => ({
          ...m,
          our_monthly_index: m.our_monthly_index != null ? toNumber(m.our_monthly_index) : null,
          mospi_cpi: m.mospi_cpi != null ? toNumber(m.mospi_cpi) : null,
          our_rebased: m.our_rebased != null ? toNumber(m.our_rebased) : null,
          mospi_rebased: m.mospi_rebased != null ? toNumber(m.mospi_rebased) : null,
        }))
      : [],
  };
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';

async function fetchWithTimeout(url: string, options: RequestInit = {}, timeoutMs = 4000): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    return response;
  } finally {
    clearTimeout(id);
  }
}

export const apiService = {
  async checkHealth(): Promise<boolean> {
    try {
      const res = await fetchWithTimeout(`${API_BASE_URL.replace('/api/v1', '')}/health`, {}, 2000);
      return res.ok;
    } catch {
      return false;
    }
  },

  async getCurrentIndex(bookingWindow: BookingWindow = 'T+15'): Promise<IndexResult> {
    const params = new URLSearchParams();
    if (bookingWindow) params.append('booking_window', bookingWindow);
    const url = `${API_BASE_URL}/index/current${params.toString() ? '?' + params.toString() : ''}`;
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    const data = await res.json();
    return normalizeIndexResult(data);
  },

  async getIndexHistory(start?: string, end?: string, bookingWindow: BookingWindow = 'T+15'): Promise<IndexHistory> {
    const params = new URLSearchParams();
    if (start) params.append('start', start);
    if (end) params.append('end', end);
    if (bookingWindow) params.append('booking_window', bookingWindow);
    const url = `${API_BASE_URL}/index/history${params.toString() ? '?' + params.toString() : ''}`;
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    const data = await res.json();
    return normalizeIndexHistory(data);
  },

  async getRoutes(): Promise<Route[]> {
    const url = `${API_BASE_URL}/routes`;
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return res.json();
  },

  async getRouteIndex(route: string, bookingWindow: BookingWindow = 'T+15'): Promise<RouteIndex> {
    const params = new URLSearchParams();
    if (bookingWindow) params.append('booking_window', bookingWindow);
    const url = `${API_BASE_URL}/routes/${encodeURIComponent(route)}/index${params.toString() ? '?' + params.toString() : ''}`;
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    const data = await res.json();
    return normalizeRouteIndex(data);
  },

  async getBookingWindows(): Promise<string[]> {
    const url = `${API_BASE_URL}/booking-windows`;
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return res.json();
  },

  async getWindowIndex(bookingWindow: BookingWindow): Promise<IndexHistory> {
    const url = `${API_BASE_URL}/booking-windows/${encodeURIComponent(bookingWindow)}/index`;
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    const data = await res.json();
    return normalizeIndexHistory(data);
  },

  async getQualityMetrics(route?: string, source?: string): Promise<QualityMetric[]> {
    const params = new URLSearchParams();
    if (route) params.append('route', route);
    if (source) params.append('source', source);
    const url = `${API_BASE_URL}/quality${params.toString() ? '?' + params.toString() : ''}`;
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    const data = await res.json();
    return Array.isArray(data) ? data.map(normalizeQualityMetric) : [];
  },

  async getIntelligenceEvents(shocksOnly = false): Promise<IntelligenceEvent[]> {
    const url = `${API_BASE_URL}/intelligence${shocksOnly ? '/shocks' : ''}`;
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    const data = await res.json();
    return Array.isArray(data) ? data.map(normalizeIntelligenceEvent) : [];
  },

  async postSimulation(payload: SimulationRequest): Promise<SimulationResponse> {
    const url = `${API_BASE_URL}/simulation`;
    const res = await fetchWithTimeout(url, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    const data = await res.json();
    return normalizeSimulationResponse(data);
  },

  async getRouteContributions(): Promise<RouteContribution[]> {
    const url = `${API_BASE_URL}/routes/contributions`;
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    const data = await res.json();
    return Array.isArray(data) ? data.map(normalizeRouteContribution) : [];
  },

  async getBookingWindowsMatrix(): Promise<any[]> {
    const url = `${API_BASE_URL}/booking-windows/matrix`;
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return res.json();
  },

  async getQualitySummary(): Promise<QualitySummary> {
    const url = `${API_BASE_URL}/quality/summary`;
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    const data = await res.json();
    return {
      ...data,
      total_observations: toNumber(data.total_observations) ?? 0,
      valid_observations: toNumber(data.valid_observations) ?? 0,
      suspect_observations: toNumber(data.suspect_observations) ?? 0,
      excluded_observations: toNumber(data.excluded_observations) ?? 0,
      outlier_count: toNumber(data.outlier_count) ?? 0,
      route_coverage: toNumber(data.route_coverage) ?? 1.0,
      source_coverage: toNumber(data.source_coverage) ?? 1.0,
      freshness_minutes: toNumber(data.freshness_minutes) ?? 0,
      source_health: Array.isArray(data.source_health)
        ? data.source_health.map((s: any) => ({
            ...s,
            observation_count: toNumber(s.observation_count) ?? 0,
            coverage_percent: toNumber(s.coverage_percent) ?? 0,
          }))
        : [],
    };
  },

  async getValidationResult(): Promise<ValidationResult> {
    const url = `${API_BASE_URL}/validation`;
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    const data = await res.json();
    return normalizeValidationResult(data);
  },

  async getLiveSourceStatus(): Promise<LiveSourceStatus> {
    const url = `${API_BASE_URL}/pipeline/live-status`;
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return await res.json();
  },
};
