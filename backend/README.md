# SIH26056 Airfare Price Index API

This FastAPI service persists and exposes normalized fare observations plus official, versioned outputs from the statistical engine. It does **not** calculate, replace, or forecast the official Airfare Price Index.

## Setup

Create a virtual environment, install `pip install -r requirements.txt`, copy `.env.example` to `.env`, and set a PostgreSQL `DATABASE_URL`. Apply `database/migrations/001_initial_schema.sql` from the repository root with `psql "$DATABASE_URL" -f database/migrations/001_initial_schema.sql`.

Run from `backend/` with `uvicorn app.main:app --reload`. Swagger is at `/docs`; system endpoints are `/` and `/health`.

## API

Public versioned endpoints are `GET /api/v1/index/current`, `GET /api/v1/index/history`, `GET /api/v1/routes`, `GET /api/v1/routes/{route}/index`, `GET /api/v1/booking-windows`, `GET /api/v1/booking-windows/{booking_window}/index`, `GET /api/v1/quality`, `GET /api/v1/intelligence`, `GET /api/v1/intelligence/shocks`, and `POST /api/v1/simulation`.

Integration ingestion endpoints are under `/api/v1/ingestion/` for normalized observations, official index results (with route results), quality metrics, and intelligence events. Add authentication/authorization before exposing ingestion endpoints outside a trusted pipeline.

Index-result ingestion requires the engine's observation-set, basket, weight, methodology, calculation versions and checksum. Calculations are immutable by `(observation_date, booking_window, calculation_version)`. API reads return `404` when an official result is not yet stored; no synthetic official values are seeded.

The simulation endpoint requires a `projected_index` produced by an approved policy-simulation component and labels every stored response `simulation: true`; it cannot overwrite official results or invent a projection.

## Testing

From `backend/`, run `pytest`. Tests use an isolated in-memory SQLite database only; deployment remains PostgreSQL-first.

## Team contracts

Data Quality supplies the normalized observation contract in `docs/DATA_CONTRACT.md`. Statistical Engine supplies versioned official results and route contributions. Intelligence supplies events with model version and timestamps. Booking windows remain separate: `T+1`, `T+7`, `T+15`, `T+30`, `T+45`.
