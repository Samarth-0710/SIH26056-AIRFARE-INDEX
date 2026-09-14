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
} from '@/types';

const TODAY = new Date().toISOString().split('T')[0];
const TIMESTAMP = new Date().toISOString();

export const DEMO_NATIONAL_INDEX: IndexResult = {
  index: 112.6,
  previous_index: 110.0,
  change_percent: 2.36,
  timestamp: TIMESTAMP,
  observation_date: TODAY,
  booking_window: 'T+15',
  status: 'SUCCESS',
  methodology_version: 'JEVONS_SHORT_INDEX_v1.0',
  basket_version: 'BASKET_IND_TOP20_v1.0',
  weight_version: 'DGCA_PAX_WEIGHTS_2024_v1.0',
  calculation_version: '1.0.0',
  observation_set_version: 'OBS_20260908_01',
  execution_checksum: 'a8f4c91d8e72b35041a998c0b2d61184f',
};

export const DEMO_ROUTES: Route[] = [
  { route: 'DEL-BOM', origin: 'DEL', destination: 'BOM', active: true },
  { route: 'DEL-BLR', origin: 'DEL', destination: 'BLR', active: true },
  { route: 'BOM-BLR', origin: 'BOM', destination: 'BLR', active: true },
  { route: 'MAA-DEL', origin: 'MAA', destination: 'DEL', active: true },
  { route: 'CCU-DEL', origin: 'CCU', destination: 'DEL', active: true },
  { route: 'DEL-HYD', origin: 'DEL', destination: 'HYD', active: true },
  { route: 'BOM-GOI', origin: 'BOM', destination: 'GOI', active: true },
  { route: 'BLR-HYD', origin: 'BLR', destination: 'HYD', active: true },
];

export const DEMO_ROUTE_CONTRIBUTIONS: RouteContribution[] = [
  {
    route: 'DEL-BOM',
    weight: 0.28,
    route_index: 118.4,
    level_contribution: 33.15,
    point_contribution: 1.34,
    percentage_share_of_change: 56.78,
  },
  {
    route: 'DEL-BLR',
    weight: 0.22,
    route_index: 114.2,
    level_contribution: 25.12,
    point_contribution: 0.64,
    percentage_share_of_change: 27.12,
  },
  {
    route: 'MAA-DEL',
    weight: 0.16,
    route_index: 115.0,
    level_contribution: 18.40,
    point_contribution: 0.51,
    percentage_share_of_change: 21.61,
  },
  {
    route: 'CCU-DEL',
    weight: 0.16,
    route_index: 108.7,
    level_contribution: 17.39,
    point_contribution: 0.14,
    percentage_share_of_change: 5.93,
  },
  {
    route: 'BOM-BLR',
    weight: 0.18,
    route_index: 109.1,
    level_contribution: 19.64,
    point_contribution: -0.27,
    percentage_share_of_change: -11.44,
  },
];

export const DEMO_ROUTE_INDICES: Record<string, RouteIndex> = {
  'DEL-BOM': {
    route: 'DEL-BOM',
    index: 118.4,
    previous_index: 113.6,
    change_percent: 4.23,
    weight: 0.28,
    contribution: 1.34,
    timestamp: TIMESTAMP,
    booking_window: 'T+15',
    status: 'SUCCESS',
    pressure_score: 82,
    anomaly_status: 'AIRFARE_SHOCK',
    source_coverage: 0.98,
    observation_count: 1420,
  },
  'DEL-BLR': {
    route: 'DEL-BLR',
    index: 114.2,
    previous_index: 111.3,
    change_percent: 2.61,
    weight: 0.22,
    contribution: 0.64,
    timestamp: TIMESTAMP,
    booking_window: 'T+15',
    status: 'SUCCESS',
    pressure_score: 71,
    anomaly_status: 'NORMAL',
    source_coverage: 0.96,
    observation_count: 1180,
  },
  'MAA-DEL': {
    route: 'MAA-DEL',
    index: 115.0,
    previous_index: 111.8,
    change_percent: 2.86,
    weight: 0.16,
    contribution: 0.51,
    timestamp: TIMESTAMP,
    booking_window: 'T+15',
    status: 'SUCCESS',
    pressure_score: 64,
    anomaly_status: 'SUSPECT_SPIKE',
    source_coverage: 0.94,
    observation_count: 950,
  },
  'CCU-DEL': {
    route: 'CCU-DEL',
    index: 108.7,
    previous_index: 107.8,
    change_percent: 0.84,
    weight: 0.16,
    contribution: 0.14,
    timestamp: TIMESTAMP,
    booking_window: 'T+15',
    status: 'SUCCESS',
    pressure_score: 48,
    anomaly_status: 'NORMAL',
    source_coverage: 0.92,
    observation_count: 890,
  },
  'BOM-BLR': {
    route: 'BOM-BLR',
    index: 109.1,
    previous_index: 110.6,
    change_percent: -1.36,
    weight: 0.18,
    contribution: -0.27,
    timestamp: TIMESTAMP,
    booking_window: 'T+15',
    status: 'SUCCESS',
    pressure_score: 35,
    anomaly_status: 'NORMAL',
    source_coverage: 0.95,
    observation_count: 1040,
  },
};

export const DEMO_BOOKING_WINDOW_SNAPSHOTS: Record<BookingWindow, IndexResult> = {
  'T+1': {
    index: 124.8,
    previous_index: 117.5,
    change_percent: 6.21,
    timestamp: TIMESTAMP,
    observation_date: TODAY,
    booking_window: 'T+1',
    status: 'SUCCESS',
    methodology_version: 'JEVONS_SHORT_INDEX_v1.0',
    basket_version: 'BASKET_IND_TOP20_v1.0',
    weight_version: 'DGCA_PAX_WEIGHTS_2024_v1.0',
    calculation_version: '1.0.0',
    observation_set_version: 'OBS_20260908_01',
  },
  'T+7': {
    index: 116.3,
    previous_index: 112.0,
    change_percent: 3.84,
    timestamp: TIMESTAMP,
    observation_date: TODAY,
    booking_window: 'T+7',
    status: 'SUCCESS',
    methodology_version: 'JEVONS_SHORT_INDEX_v1.0',
    basket_version: 'BASKET_IND_TOP20_v1.0',
    weight_version: 'DGCA_PAX_WEIGHTS_2024_v1.0',
    calculation_version: '1.0.0',
    observation_set_version: 'OBS_20260908_01',
  },
  'T+15': {
    index: 112.6,
    previous_index: 110.0,
    change_percent: 2.36,
    timestamp: TIMESTAMP,
    observation_date: TODAY,
    booking_window: 'T+15',
    status: 'SUCCESS',
    methodology_version: 'JEVONS_SHORT_INDEX_v1.0',
    basket_version: 'BASKET_IND_TOP20_v1.0',
    weight_version: 'DGCA_PAX_WEIGHTS_2024_v1.0',
    calculation_version: '1.0.0',
    observation_set_version: 'OBS_20260908_01',
  },
  'T+30': {
    index: 107.1,
    previous_index: 106.1,
    change_percent: 0.94,
    timestamp: TIMESTAMP,
    observation_date: TODAY,
    booking_window: 'T+30',
    status: 'SUCCESS',
    methodology_version: 'JEVONS_SHORT_INDEX_v1.0',
    basket_version: 'BASKET_IND_TOP20_v1.0',
    weight_version: 'DGCA_PAX_WEIGHTS_2024_v1.0',
    calculation_version: '1.0.0',
    observation_set_version: 'OBS_20260908_01',
  },
  'T+45': {
    index: 103.4,
    previous_index: 103.8,
    change_percent: -0.38,
    timestamp: TIMESTAMP,
    observation_date: TODAY,
    booking_window: 'T+45',
    status: 'SUCCESS',
    methodology_version: 'JEVONS_SHORT_INDEX_v1.0',
    basket_version: 'BASKET_IND_TOP20_v1.0',
    weight_version: 'DGCA_PAX_WEIGHTS_2024_v1.0',
    calculation_version: '1.0.0',
    observation_set_version: 'OBS_20260908_01',
  },
};

export const DEMO_HEATMAP_DATA = [
  { route: 'DEL-BOM', 'T+1': 134.2, 'T+7': 122.5, 'T+15': 118.4, 'T+30': 111.0, 'T+45': 106.2 },
  { route: 'DEL-BLR', 'T+1': 126.8, 'T+7': 118.1, 'T+15': 114.2, 'T+30': 108.4, 'T+45': 104.1 },
  { route: 'MAA-DEL', 'T+1': 128.4, 'T+7': 119.3, 'T+15': 115.0, 'T+30': 107.9, 'T+45': 103.8 },
  { route: 'BOM-BLR', 'T+1': 118.5, 'T+7': 112.4, 'T+15': 109.1, 'T+30': 104.2, 'T+45': 101.5 },
  { route: 'CCU-DEL', 'T+1': 117.2, 'T+7': 111.0, 'T+15': 108.7, 'T+30': 103.8, 'T+45': 101.2 },
];

export function generateDemoHistory(days = 90, baseIndex = 100): IndexResult[] {
  const items: IndexResult[] = [];
  const now = new Date();
  
  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i);
    const dateStr = d.toISOString().split('T')[0];
    
    // Realistic trend with seasonal oscillation and upward drift
    const trend = (days - i) * 0.12;
    const sinWave = Math.sin((days - i) / 5) * 1.8;
    const noise = Math.sin((days - i) * 1.3) * 0.7;
    const indexVal = parseFloat((baseIndex + trend + sinWave + noise).toFixed(1));
    const prevVal = i < days - 1 ? items[items.length - 1].index! : indexVal - 0.2;
    const change = parseFloat((((indexVal - prevVal) / prevVal) * 100).toFixed(2));

    items.push({
      index: indexVal,
      previous_index: prevVal,
      change_percent: change,
      timestamp: d.toISOString(),
      observation_date: dateStr,
      booking_window: 'T+15',
      status: 'SUCCESS',
      methodology_version: 'JEVONS_SHORT_INDEX_v1.0',
      basket_version: 'BASKET_IND_TOP20_v1.0',
      weight_version: 'DGCA_PAX_WEIGHTS_2024_v1.0',
      calculation_version: '1.0.0',
      observation_set_version: `OBS_${dateStr.replace(/-/g, '')}_01`,
    });
  }
  return items;
}

export const DEMO_INTELLIGENCE_EVENTS: IntelligenceEvent[] = [
  {
    id: 101,
    route: 'DEL-BOM',
    event_type: 'AIRFARE_SHOCK',
    anomaly_score: 0.94,
    pressure_score: 82,
    shock_status: 'ACTIVE_SHOCK',
    explanation: 'Rapid acceleration (+28.4% relative fare spike) confirmed across 3 independent booking platforms during peak departure windows.',
    affected_sources: ['OTA_ALPHA', 'META_SEARCH', 'DIRECT_API'],
    affected_routes: ['DEL-BOM', 'BOM-DEL', 'DEL-PNQ'],
    model_version: 'SHOCK_DETECTOR_v2.1',
    event_timestamp: new Date(Date.now() - 3600000 * 2).toISOString(),
  },
  {
    id: 102,
    route: 'MAA-DEL',
    event_type: 'ANOMALY',
    anomaly_score: 0.81,
    pressure_score: 64,
    shock_status: 'SUSPECT',
    explanation: 'Unusual fare dispersion across morning departure slots ($T+7$ window), exceeding 3.2 standard deviations above historical mean.',
    affected_sources: ['OTA_ALPHA', 'META_SEARCH'],
    affected_routes: ['MAA-DEL'],
    model_version: 'ANOMALY_ISO_FOREST_v1.4',
    event_timestamp: new Date(Date.now() - 3600000 * 6).toISOString(),
  },
  {
    id: 103,
    route: 'DEL-BLR',
    event_type: 'PRESSURE_SPIKE',
    anomaly_score: 0.65,
    pressure_score: 71,
    shock_status: 'MONITORING',
    explanation: 'Sustained upward price trend driven by high business-cabin load factors ahead of holiday weekend.',
    affected_sources: ['DIRECT_API', 'META_SEARCH'],
    affected_routes: ['DEL-BLR', 'BLR-DEL'],
    model_version: 'PRESSURE_RANKER_v1.0',
    event_timestamp: new Date(Date.now() - 3600000 * 12).toISOString(),
  },
  {
    id: 104,
    route: 'BOM-BLR',
    event_type: 'PATTERN',
    anomaly_score: 0.32,
    pressure_score: 35,
    shock_status: 'NORMAL',
    explanation: 'Expected weekend promotional discount cycle matching historical seasonality models.',
    affected_sources: ['OTA_ALPHA', 'OTA_BETA'],
    affected_routes: ['BOM-BLR'],
    model_version: 'SEASONAL_PATTERN_v1.0',
    event_timestamp: new Date(Date.now() - 3600000 * 24).toISOString(),
  },
];

export const DEMO_QUALITY_METRICS: QualityMetric[] = [
  {
    id: 1,
    metric_date: TODAY,
    route: 'DEL-BOM',
    source: 'OTA_ALPHA',
    observation_count: 18450,
    route_coverage: 0.98,
    source_coverage: 0.97,
    freshness_minutes: 8,
    missing_observations: 120,
    invalid_observations: 45,
    anomalous_valid_observations: 12,
    status: 'OPTIMAL',
    generated_at: TIMESTAMP,
  },
  {
    id: 2,
    metric_date: TODAY,
    route: 'DEL-BLR',
    source: 'OTA_BETA',
    observation_count: 14200,
    route_coverage: 0.96,
    source_coverage: 0.95,
    freshness_minutes: 14,
    missing_observations: 210,
    invalid_observations: 68,
    anomalous_valid_observations: 19,
    status: 'OPTIMAL',
    generated_at: TIMESTAMP,
  },
  {
    id: 3,
    metric_date: TODAY,
    route: 'MAA-DEL',
    source: 'META_SEARCH',
    observation_count: 11800,
    route_coverage: 0.94,
    source_coverage: 0.92,
    freshness_minutes: 25,
    missing_observations: 340,
    invalid_observations: 102,
    anomalous_valid_observations: 28,
    status: 'WARNING_FRESHNESS',
    generated_at: TIMESTAMP,
  },
];

export const DEMO_SOURCE_HEALTH: SourceHealth[] = [
  { source: 'OTA_ALPHA (Permitted GDS/OTA)', status: 'HEALTHY', last_collection: '6 mins ago', observation_count: 24500, coverage_percent: 98.4 },
  { source: 'OTA_BETA (Permitted Aggregator)', status: 'HEALTHY', last_collection: '12 mins ago', observation_count: 19800, coverage_percent: 96.1 },
  { source: 'META_SEARCH (Direct Feed)', status: 'HEALTHY', last_collection: '18 mins ago', observation_count: 15400, coverage_percent: 94.2 },
  { source: 'DIRECT_AIRLINE_API (Brand Feed)', status: 'DEGRADED', last_collection: '45 mins ago', observation_count: 9200, coverage_percent: 88.6 },
];

export const DEMO_VALIDATION_RESULT: ValidationResult = {
  period: 'Last 30 Days (Aug 09 - Sep 08, 2026)',
  reference_dataset: 'DGCA Official Domestic Airfare Benchmark / MoSPI Survey Data (30-Day Backtest)',
  methodology_version: 'JEVONS_SHORT_INDEX_v1.0',
  observation_set_version: 'OBS_VALIDATION_SET_30D',
  is_reference_connected: false, // Labelled explicitly as fixture unless connected
  metrics: [
    { metric: 'Pearson Correlation (r)', value: '0.942', status: 'PASS', description: 'Strong linear co-movement with reference series (> 0.85 target)' },
    { metric: 'Spearman Rank Correlation (ρ)', value: '0.928', status: 'PASS', description: 'High monotonic order alignment across top domestic corridors' },
    { metric: 'Mean Absolute Error (MAE)', value: '1.42 pts', status: 'PASS', description: 'Average absolute divergence from benchmark index level' },
    { metric: 'Root Mean Squared Error (RMSE)', value: '1.88 pts', status: 'PASS', description: 'Low variance penalty for extreme index deviations' },
    { metric: 'Directional Accuracy', value: '91.2%', status: 'PASS', description: 'Day-over-day sign movement matching percentage' },
    { metric: 'Basket Coverage Ratio', value: '98.5%', status: 'PASS', description: 'Sum of matched corridor weights evaluated' },
    { metric: 'Index Stability (σ ΔI)', value: '0.74', status: 'PASS', description: 'Sample standard deviation of daily first differences' },
  ],
  history: Array.from({ length: 30 }).map((_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - (29 - i));
    const base = 104.0 + i * 0.28 + Math.sin(i / 3) * 1.2;
    return {
      date: d.toISOString().split('T')[0],
      calculated_index: parseFloat(base.toFixed(1)),
      reference_index: parseFloat((base + Math.sin(i / 2) * 0.6 - 0.2).toFixed(1)),
    };
  }),
};

export const DEMO_CONFIDENCE_METRICS: ConfidenceMetrics = {
  overall_confidence: 94,
  source_coverage: 96,
  route_coverage: 98,
  observation_volume: 'High',
  freshness: 'Excellent',
};

export function simulatePolicyShock(req: SimulationRequest): SimulationResponse {
  const currentVal = DEMO_NATIONAL_INDEX.index || 112.6;
  const routeObj = DEMO_ROUTE_INDICES[req.route] || { weight: 0.20, index: 110.0 };
  const routeWeight = routeObj.weight || 0.20;
  
  // Hypothetical impact: weight * route fare shock percentage
  const routeShockMultiplier = req.shock_percent / 100;
  const impactPoints = parseFloat((currentVal * routeWeight * routeShockMultiplier).toFixed(2));
  const projectedIndex = parseFloat((currentVal + impactPoints).toFixed(1));

  return {
    current_index: currentVal,
    route: req.route,
    shock_percent: req.shock_percent,
    projected_index: projectedIndex,
    impact_points: impactPoints,
    simulation: true,
    status: 'SUCCESS_HYPOTHETICAL',
  };
}
