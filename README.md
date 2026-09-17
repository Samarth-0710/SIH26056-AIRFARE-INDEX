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

## Quick Start & Execution Guide

### 1. Environment Setup

```bash
# Create and activate Python virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install consolidated Python dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### 2. Run the Complete End-to-End Pipeline

Run the integrated pipeline to collect data, normalize, calculate indices, run intelligence, and persist results to the database:

```bash
# Run pipeline with synthetic/demo dataset (zero external credentials needed)
python run_pipeline.py

# Or run with simulated price shock
python run_pipeline.py --shock 5.0
```

### 3. Start Backend API Server

```bash
# Launch FastAPI backend on port 8000
PYTHONPATH=".:backend:data-collection/src:data-quality:data-quality/src:statistical-engine/src:intelligence/src" uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API documentation will be available at:
- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`
- Pipeline trigger: `POST http://localhost:8000/api/v1/pipeline/run`

### 4. Start Frontend Dashboard

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your browser. The dashboard automatically detects the live API server and displays real-time calculated indices. If the backend is offline, it seamlessly falls back to controlled demo fixtures with clear status badges.

### 5. Running the Test Suite

Run the full cross-module test suite (295 tests across all 7 boundaries):

```bash
PYTHONPATH="backend:statistical-engine/src:data-collection/src:data-quality/src:data-quality:data-collection:intelligence/src:." \
pytest --import-mode=importlib \
    tests \
    statistical-engine/tests \
    data-collection/tests \
    data-quality/tests \
    intelligence/tests \
    backend/tests
```

Frontend Jest tests (23 tests):

```bash
cd frontend && npm test
```

Frontend Production Build:

```bash
cd frontend && npm run build
```

### 6. Demonstration & Evaluation Guide

For a complete step-by-step walkthrough of the pipeline, API endpoints, and dashboard pages, see [docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md).
