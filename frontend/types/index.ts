export type BookingWindow = 'T+1' | 'T+7' | 'T+15' | 'T+30' | 'T+45';

export interface IndexResult {
  index: number | null;
  previous_index?: number | null;
  change_percent?: number | null;
  timestamp: string;
  observation_date: string;
  booking_window: BookingWindow;
  status: string;
  methodology_version: string;
  basket_version: string;
  weight_version: string;
  calculation_version: string;
  observation_set_version: string;
  execution_checksum?: string | null;
}

export interface IndexHistory {
  items: IndexResult[];
}

export interface Route {
  route: string;
  origin: string;
  destination: string;
  active: boolean;
}

export interface RouteIndex {
  route: string;
  index: number | null;
  previous_index?: number | null;
  change_percent?: number | null;
  weight?: number | null;
  contribution?: number | null;
  timestamp: string;
  booking_window: BookingWindow;
  status: string;
  pressure_score?: number;
  anomaly_status?: string;
  source_coverage?: number;
  observation_count?: number;
}

export interface RouteContribution {
  route: string;
  weight: number;
  route_index: number;
  level_contribution: number;
  point_contribution: number;
  percentage_share_of_change: number;
}

export interface IntelligenceEvent {
  id: number;
  route?: string | null;
  event_type: 'AIRFARE_SHOCK' | 'ANOMALY' | 'PRESSURE_SPIKE' | 'PATTERN';
  anomaly_score?: number | null;
  pressure_score?: number | null;
  shock_status?: string | null;
  explanation?: string | null;
  affected_sources: string[];
  affected_routes: string[];
  model_version: string;
  event_timestamp: string;
}

export interface QualityMetric {
  id: number;
  metric_date: string;
  route?: string | null;
  source?: string | null;
  observation_count: number;
  route_coverage?: number | null;
  source_coverage?: number | null;
  freshness_minutes?: number | null;
  missing_observations: number;
  invalid_observations: number;
  anomalous_valid_observations: number;
  status: string;
  generated_at: string;
}

export interface SourceHealth {
  source: string;
  status: 'HEALTHY' | 'DEGRADED' | 'OFFLINE';
  last_collection: string;
  observation_count: number;
  coverage_percent: number;
}

export interface SimulationRequest {
  route: string;
  shock_percent: number;
  projected_index?: number | null;
  input_metadata?: Record<string, any>;
}

export interface SimulationResponse {
  current_index: number | null;
  route: string;
  shock_percent: number;
  projected_index: number | null;
  impact_points: number | null;
  simulation: boolean;
  status: string;
}

export interface ValidationMetric {
  metric: string;
  value: number | string;
  status: string;
  description: string;
}

export interface ValidationHistoryPoint {
  date: string;
  calculated_index: number;
  reference_index: number | null;
}

export interface ValidationResult {
  period: string;
  reference_dataset: string;
  methodology_version: string;
  observation_set_version: string;
  is_reference_connected: boolean;
  metrics: ValidationMetric[];
  history: ValidationHistoryPoint[];
}

export interface ConfidenceMetrics {
  overall_confidence: number;
  source_coverage: number;
  route_coverage: number;
  observation_volume: 'High' | 'Medium' | 'Low';
  freshness: 'Excellent' | 'Good' | 'Stale' | 'Outdated';
}

export interface DataProviderStatus {
  isDemo: boolean;
  isLive: boolean;
  lastChecked: string;
  error?: string;
}
