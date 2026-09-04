-- SIH26056 initial PostgreSQL schema. Apply once to an empty target database.
-- It is additive and must not be replaced with destructive table recreation.
CREATE TABLE IF NOT EXISTS routes (
  id SERIAL PRIMARY KEY, code VARCHAR(7) NOT NULL UNIQUE, origin VARCHAR(3) NOT NULL,
  destination VARCHAR(3) NOT NULL, active BOOLEAN NOT NULL DEFAULT TRUE,
  CHECK (code ~ '^[A-Z]{3}-[A-Z]{3}$'), CHECK (origin <> destination)
);
CREATE TABLE IF NOT EXISTS fare_observations (
  id BIGSERIAL PRIMARY KEY, route_id INTEGER NOT NULL REFERENCES routes(id), observation_timestamp TIMESTAMPTZ NOT NULL,
  observation_date DATE NOT NULL, travel_date DATE NOT NULL, booking_window VARCHAR(4) NOT NULL,
  airline VARCHAR(20) NOT NULL, flight_number VARCHAR(30) NOT NULL, departure_time VARCHAR(20) NOT NULL,
  cabin_class VARCHAR(30) NOT NULL, fare_type VARCHAR(50) NOT NULL, baggage_characteristics VARCHAR(100) NOT NULL,
  base_fare NUMERIC(12,2), taxes NUMERIC(12,2), mandatory_charges NUMERIC(12,2), comparable_fare NUMERIC(12,2) NOT NULL CHECK (comparable_fare > 0),
  source VARCHAR(80) NOT NULL, fingerprint VARCHAR(128) NOT NULL, quality_status VARCHAR(12) NOT NULL, metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  CONSTRAINT uq_observation_identity UNIQUE (fingerprint, observation_timestamp, source),
  CHECK (booking_window IN ('T+1','T+7','T+15','T+30','T+45'))
);
CREATE TABLE IF NOT EXISTS index_results (
  id BIGSERIAL PRIMARY KEY, observation_date DATE NOT NULL, booking_window VARCHAR(4) NOT NULL,
  index_value NUMERIC(12,4), status VARCHAR(30) NOT NULL, observation_set_version VARCHAR(100) NOT NULL,
  basket_version VARCHAR(100) NOT NULL, weight_version VARCHAR(100) NOT NULL, methodology_version VARCHAR(100) NOT NULL,
  calculation_version VARCHAR(100) NOT NULL, execution_checksum VARCHAR(128), calculation_timestamp TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT uq_index_calculation UNIQUE (observation_date, booking_window, calculation_version),
  CHECK (booking_window IN ('T+1','T+7','T+15','T+30','T+45'))
);
CREATE TABLE IF NOT EXISTS route_indices (
  id BIGSERIAL PRIMARY KEY, index_result_id BIGINT NOT NULL REFERENCES index_results(id), route_id INTEGER NOT NULL REFERENCES routes(id),
  index_value NUMERIC(12,4), status VARCHAR(30) NOT NULL, weight NUMERIC(12,8), contribution NUMERIC(12,4),
  CHECK (weight IS NULL OR (weight >= 0 AND weight <= 1))
);
CREATE TABLE IF NOT EXISTS quality_metrics (
  id BIGSERIAL PRIMARY KEY, metric_date DATE NOT NULL, route_id INTEGER REFERENCES routes(id), source VARCHAR(80),
  observation_count INTEGER NOT NULL CHECK (observation_count >= 0), route_coverage NUMERIC(6,4), source_coverage NUMERIC(6,4), freshness_minutes INTEGER,
  missing_observations INTEGER NOT NULL DEFAULT 0, invalid_observations INTEGER NOT NULL DEFAULT 0, anomalous_valid_observations INTEGER NOT NULL DEFAULT 0,
  status VARCHAR(30) NOT NULL, generated_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS intelligence_events (
  id BIGSERIAL PRIMARY KEY, route_id INTEGER REFERENCES routes(id), event_type VARCHAR(30) NOT NULL, anomaly_score NUMERIC(8,4),
  pressure_score NUMERIC(8,4), shock_status VARCHAR(30), explanation TEXT, affected_sources JSONB NOT NULL DEFAULT '[]'::jsonb,
  affected_routes JSONB NOT NULL DEFAULT '[]'::jsonb, model_version VARCHAR(100) NOT NULL, event_timestamp TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS simulation_results (
  id BIGSERIAL PRIMARY KEY, route_id INTEGER NOT NULL REFERENCES routes(id), shock_percent NUMERIC(8,4) NOT NULL,
  current_index NUMERIC(12,4), projected_index NUMERIC(12,4), impact_points NUMERIC(12,4), status VARCHAR(30) NOT NULL,
  input_metadata JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_index_latest ON index_results (booking_window, observation_date DESC, calculation_timestamp DESC);
CREATE INDEX IF NOT EXISTS ix_route_indices_lookup ON route_indices (route_id, index_result_id);
CREATE INDEX IF NOT EXISTS ix_observations_lookup ON fare_observations (route_id, booking_window, observation_date);
