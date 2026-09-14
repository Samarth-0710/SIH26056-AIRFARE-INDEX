import {
  IndexResult,
  IndexHistory,
  Route,
  RouteIndex,
  QualityMetric,
  IntelligenceEvent,
  SimulationRequest,
  SimulationResponse,
  BookingWindow,
} from '@/types';

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

  async getCurrentIndex(bookingWindow?: BookingWindow): Promise<IndexResult> {
    const params = new URLSearchParams();
    if (bookingWindow) params.append('booking_window', bookingWindow);
    const url = `${API_BASE_URL}/index/current${params.toString() ? '?' + params.toString() : ''}`;
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return res.json();
  },

  async getIndexHistory(start?: string, end?: string, bookingWindow?: BookingWindow): Promise<IndexHistory> {
    const params = new URLSearchParams();
    if (start) params.append('start', start);
    if (end) params.append('end', end);
    if (bookingWindow) params.append('booking_window', bookingWindow);
    const url = `${API_BASE_URL}/index/history${params.toString() ? '?' + params.toString() : ''}`;
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return res.json();
  },

  async getRoutes(): Promise<Route[]> {
    const url = `${API_BASE_URL}/routes`;
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return res.json();
  },

  async getRouteIndex(route: string, bookingWindow?: BookingWindow): Promise<RouteIndex> {
    const params = new URLSearchParams();
    if (bookingWindow) params.append('booking_window', bookingWindow);
    const url = `${API_BASE_URL}/routes/${encodeURIComponent(route)}/index${params.toString() ? '?' + params.toString() : ''}`;
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return res.json();
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
    return res.json();
  },

  async getQualityMetrics(route?: string, source?: string): Promise<QualityMetric[]> {
    const params = new URLSearchParams();
    if (route) params.append('route', route);
    if (source) params.append('source', source);
    const url = `${API_BASE_URL}/quality${params.toString() ? '?' + params.toString() : ''}`;
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return res.json();
  },

  async getIntelligenceEvents(shocksOnly = false): Promise<IntelligenceEvent[]> {
    const url = `${API_BASE_URL}/intelligence${shocksOnly ? '/shocks' : ''}`;
    const res = await fetchWithTimeout(url);
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return res.json();
  },

  async postSimulation(payload: SimulationRequest): Promise<SimulationResponse> {
    const url = `${API_BASE_URL}/simulation`;
    const res = await fetchWithTimeout(url, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return res.json();
  },
};
