import {
  normalizeIndexResult,
  normalizeIndexHistory,
  normalizeRouteIndex,
  normalizeQualityMetric,
  normalizeIntelligenceEvent,
  normalizeSimulationResponse,
} from '@/services/api';

describe('API Response Normalizers', () => {
  it('normalizes string-encoded decimals in IndexResult to numbers', () => {
    const raw = {
      index: '102.5000',
      previous_index: '100.0000',
      change_percent: '2.5000',
      timestamp: '2026-09-14T12:00:00Z',
      observation_date: '2026-09-14',
      booking_window: 'T+15',
      status: 'SUCCESS',
      methodology_version: 'v1',
      basket_version: 'v1',
      weight_version: 'v1',
      calculation_version: 'v1',
      observation_set_version: 'v1',
    };

    const normalized = normalizeIndexResult(raw);
    expect(normalized.index).toBe(102.5);
    expect(typeof normalized.index).toBe('number');
    expect(normalized.previous_index).toBe(100.0);
    expect(normalized.change_percent).toBe(2.5);
  });

  it('handles null or missing numeric fields in IndexResult', () => {
    const raw = {
      index: null,
      previous_index: null,
      change_percent: null,
      timestamp: '2026-09-14T12:00:00Z',
      observation_date: '2026-09-14',
      booking_window: 'T+15',
      status: 'UNAVAILABLE',
    };

    const normalized = normalizeIndexResult(raw);
    expect(normalized.index).toBeNull();
    expect(normalized.previous_index).toBeNull();
    expect(normalized.change_percent).toBeNull();
  });

  it('normalizes items in IndexHistory', () => {
    const raw = {
      items: [
        { index: '101.5000', previous_index: null, change_percent: null },
        { index: '102.5000', previous_index: '101.5000', change_percent: '0.9852' },
      ],
    };

    const normalized = normalizeIndexHistory(raw);
    expect(normalized.items.length).toBe(2);
    expect(normalized.items[0].index).toBe(101.5);
    expect(normalized.items[1].index).toBe(102.5);
    expect(normalized.items[1].change_percent).toBeCloseTo(0.9852, 4);
  });

  it('normalizes string-encoded decimals in RouteIndex', () => {
    const raw = {
      route: 'DEL-BOM',
      index: '102.5000',
      previous_index: '100.0000',
      change_percent: '2.5000',
      weight: '0.25000000',
      contribution: '25.6250',
      pressure_score: '50.0',
      source_coverage: '1.0000',
      observation_count: '90',
      timestamp: '2026-09-14T12:00:00Z',
      booking_window: 'T+15',
      status: 'SUCCESS',
    };

    const normalized = normalizeRouteIndex(raw);
    expect(normalized.index).toBe(102.5);
    expect(normalized.weight).toBe(0.25);
    expect(normalized.contribution).toBe(25.625);
    expect(normalized.pressure_score).toBe(50);
    expect(normalized.source_coverage).toBe(1.0);
    expect(normalized.observation_count).toBe(90);
  });

  it('normalizes string-encoded decimals in QualityMetric', () => {
    const raw = {
      id: 1,
      metric_date: '2026-09-14',
      observation_count: '90',
      route_coverage: '1.0000',
      source_coverage: '0.9500',
      freshness_minutes: '5',
      missing_observations: '0',
      invalid_observations: '0',
      anomalous_valid_observations: '0',
      status: 'COMPLETE',
      generated_at: '2026-09-14T12:00:00Z',
    };

    const normalized = normalizeQualityMetric(raw);
    expect(normalized.route_coverage).toBe(1.0);
    expect(normalized.source_coverage).toBe(0.95);
    expect(normalized.observation_count).toBe(90);
    expect(normalized.freshness_minutes).toBe(5);
  });

  it('normalizes string-encoded decimals in IntelligenceEvent', () => {
    const raw = {
      id: 1,
      event_type: 'ANOMALY',
      anomaly_score: '0.8500',
      pressure_score: '0.5000',
      model_version: 'v1',
      event_timestamp: '2026-09-14T12:00:00Z',
      affected_sources: [],
      affected_routes: [],
    };

    const normalized = normalizeIntelligenceEvent(raw);
    expect(normalized.anomaly_score).toBe(0.85);
    expect(normalized.pressure_score).toBe(0.5);
  });

  it('normalizes string-encoded decimals in SimulationResponse', () => {
    const raw = {
      current_index: '102.5000',
      route: 'DEL-BOM',
      shock_percent: '15.0000',
      projected_index: '106.3438',
      impact_points: '3.8438',
      simulation: true,
      status: 'SIMULATED',
    };

    const normalized = normalizeSimulationResponse(raw);
    expect(normalized.current_index).toBe(102.5);
    expect(normalized.shock_percent).toBe(15.0);
    expect(normalized.projected_index).toBe(106.3438);
    expect(normalized.impact_points).toBe(3.8438);
  });
});
