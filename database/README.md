# SIH26056 about database mko


PostgreSQL assets for durable, versioned storage of normalized observations and upstream calculation outputs. The backend owns connection/session use; this folder owns deployable schema assets.

Apply `migrations/001_initial_schema.sql` to a new PostgreSQL database, then set `DATABASE_URL` in `backend/.env`. The migration is additive (`CREATE TABLE IF NOT EXISTS`) and never drops data.

Tables: `routes`, `fare_observations`, `index_results`, `route_indices`, `quality_metrics`, `intelligence_events`, and `simulation_results`.

No seed file is included: the repository must not portray synthetic fares, weights, or indices as official data. The ingestion API accepts clearly identified upstream outputs after migration.
