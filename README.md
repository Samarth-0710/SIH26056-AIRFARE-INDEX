# SIH26056 — Real-Time Airfare Price Index for India

Team repository for Smart India Hackathon Problem Statement SIH26056.

## Team Ownership

| Area | Owner | Responsibility |
|---|---|---|
| `frontend/` | Nishanth | Frontend, dashboard & UX |
| `backend/` | Mohith | Backend, API & database integration |
| `data-collection/` | Kumuda | Data collection & source adapters |
| `data-quality/` | Hindu | Data quality & fare normalization |
| `statistical-engine/` | Samarth | Statistical index engine & validation |
| `intelligence/` | Harshitha | AI/ML intelligence layer |
| `database/` | Team | Shared database/schema |
| `tests/` | Team | Cross-module/integration tests |
| `docs/` | Team | Documentation and methodology |

## End-to-End Flow

Permitted Sources
→ Data Collection
→ Data Quality / Normalization
→ Comparable Observations
→ Statistical Index Engine
→ Intelligence Layer
→ Backend/API
→ Dashboard

## Statistical Principle

Statistics calculates the official Airfare Price Index.

AI/ML does not calculate or replace the official index. It supports the surrounding intelligence layer.

Core pipeline:

Clean Comparable Fares
→ Price Relatives
→ Jevons / Short Index
→ Route & Lead-Time Indices
→ Reference/Prescribed Weighted Aggregation
→ National Airfare Price Index
→ Contribution Analysis
→ Validation

## Booking Windows

- T+1
- T+7
- T+15
- T+30
- T+45

## Validation

The project includes a 30-day back-test against the appropriate DGCA/reference airfare data.

Metrics include:

- Correlation
- MAE
- RMSE
- Directional Accuracy
- Coverage
- Stability

Do not fabricate reference data or official results.

## Repository Rules

1. Do not invent official route weights.
2. Keep methodology and weights configurable.
3. Do not calculate the index directly from raw scraped fares.
4. Preserve data provenance and version information.
5. Do not replace statistical calculation with ML prediction.
6. Do not rewrite another teammate's module unnecessarily.
7. Discuss shared-contract changes before merging.

## Branches

Recommended branches:

- `feature/frontend`
- `feature/backend`
- `feature/data-collection`
- `feature/data-quality`
- `feature/statistical-engine`
- `feature/intelligence`
- `feature/database`
- `feature/tests`

Use pull requests into `main`.

## Status

Initial repository scaffold.
