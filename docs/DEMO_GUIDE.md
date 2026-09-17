# SIH26056 — Real-Time Airfare Price Index for India
## Complete System Demonstration & Verification Guide

This guide provides step-by-step instructions for judges, evaluators, and engineers to run, inspect, and verify the entire SIH26056 application end-to-end.

---

### 1. Architectural Pipeline Overview

The system operates as a unified, deterministic end-to-end pipeline:

```
[DATA COLLECTION]
    Kumuda's Adapters (IGNAV / Synthetic Basket)
          │  RawFareRecord (canonical fare observations)
          ▼
[DATA QUALITY & NORMALIZATION]
    Hindu's Quality Pipeline (Fingerprinting, Component Validation, Outlier Detection)
          │  NormalizedFareObservation -> Engine FareObservation
          ▼
[STATISTICAL INDEX ENGINE]
    Samarth's Engine (Jevons Short Index, Route Aggregation, Weighting, Reproducibility Checksum)
          │  IndexResult, RouteIndex, WindowIndices
          ▼
[INTELLIGENCE & AI LAYER]
    Harshitha's Intelligence Engine (Isolation Forest, Pressure Index, Airfare Shock Detection)
          │  IntelligenceEvent, Shock Alerts, Anomaly Scores
          ▼
[BACKEND SERVICE & PERSISTENCE]
    Mohith's FastAPI & SQLite Layer (Database Ingestion, Historical Queries, Simulation, Validation)
          │  REST APIs (HTTP JSON)
          ▼
[NEXT.JS DASHBOARD]
    Nishanth's Responsive Web Dashboard (Live KPI Cards, Recharts, Horizon Heatmap, Simulator)
```

---

### 2. Environment Setup

From the repository root:

```bash
# 1. Activate Python virtual environment (Python 3.12 recommended)
source .venv/bin/activate

# 2. Install dependencies (if not already installed)
pip install -r requirements.txt

# 3. Verify environment variables
cp .env.example .env
```

---

### 3. Step 1: Run the End-to-End Pipeline CLI

Execute the complete pipeline runner to ingest data, cleanse observations, calculate national and route indices, evaluate intelligence shocks, and persist everything into the SQLite database:

```bash
PYTHONPATH="backend:statistical-engine/src:data-collection/src:data-quality/src:data-quality:data-collection:intelligence/src:." python run_pipeline.py
```

#### Expected CLI Output:
```
========================================
SIH26056 AIRFARE INDEX PIPELINE
========================================

Mode: SYNTHETIC

Observations collected: 90
Valid observations:     90
Rejected observations:  0

Routes processed:       6

T+1:  102.5
T+7:  102.5
T+15: 102.5
T+30: 102.5
T+45: 102.5

Intelligence events:    30

Calculation version:    CALC_2026-09-14_...
Checksum:               05423cebb6036667...

Database:               ./airfare_index.db

PIPELINE SUCCESS
========================================
```

---

### 4. Step 2: Verify Database Persistence

Confirm that all seven relational tables have been populated with live records:

```bash
python -c "
import sqlite3
conn = sqlite3.connect('airfare_index.db')
c = conn.cursor()
tables = ['routes', 'fare_observations', 'index_results', 'route_indices', 'quality_metrics', 'intelligence_events', 'simulation_results']
for t in tables:
    count = c.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
    print(f'{t:25s}: {count:5d} rows')
conn.close()
"
```

All tables will report active row counts (`routes: 6`, `fare_observations: >= 90`, `index_results: >= 5`, `route_indices: >= 30`, `quality_metrics: >= 1`, `intelligence_events: >= 30`, `simulation_results: >= 1`).

---

### 5. Step 3: Launch FastAPI Backend

Start the high-performance FastAPI server:

```bash
PYTHONPATH="backend:statistical-engine/src:data-collection/src:data-quality/src:data-quality:data-collection:intelligence/src:." \
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Key Endpoints to Inspect:
- **System Health**: `http://localhost:8000/health`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **National Current Index**: `GET http://localhost:8000/api/v1/index/current?booking_window=T%2B15`
- **Index History**: `GET http://localhost:8000/api/v1/index/history`
- **Corridor Contributions**: `GET http://localhost:8000/api/v1/routes/contributions`
- **Booking Windows Matrix**: `GET http://localhost:8000/api/v1/booking-windows/matrix`
- **Data Quality Summary**: `GET http://localhost:8000/api/v1/quality/summary`
- **Intelligence Shocks**: `GET http://localhost:8000/api/v1/intelligence/shocks`
- **Validation Evaluation**: `GET http://localhost:8000/api/v1/validation`
- **Trigger Pipeline Run**: `POST http://localhost:8000/api/v1/pipeline/run`

---

### 6. Step 4: Launch Next.js Dashboard

In a separate terminal tab:

```bash
cd frontend
npm install
npm run dev
```

Navigate to `http://localhost:3000`.

---

### 7. Step 5: Dashboard Feature Inspection

1. **Executive Dashboard (`/dashboard`)**:
   - **National Index KPI**: Shows current index, previous index, and day-over-day change percentage calculated by the Jevons short-index formula.
   - **Top Inflating Corridor**: Shows the corridor with the highest index change and its exact percentage contribution to the national basket.
   - **Booking Window Snapshot**: Displays separate current index readings across $T+1, T+7, T+15, T+30, T+45$.
   - **Methodological Metadata Bar**: Displays the calculation version, basket version, weight version, and SHA-256 execution checksum.

2. **Booking Windows Page (`/booking-windows`)**:
   - **Separation Principle Banner**: Explains why booking windows represent distinct constant-quality commodities and are never combined into a single elementary index.
   - **Advance Purchase Horizon Comparison**: Overlaid historical index trajectories for each advance window.
   - **Route $\times$ Horizon Heatmap**: Interactive corridor-by-window matrix showing relative price escalation across lead times.

3. **Data Quality Audit (`/data-quality`)**:
   - **Observation Filtering Funnel**: Displays real counts of total observations, valid cleansed records, suspect records, and excluded outliers.
   - **Freshness Metric**: Reports latency between collection and index calculation.
   - **Source Health Table**: Live monitoring table of permitted adapters (IGNAV, Synthetic Basket) with status, timestamp, observation volume, and coverage ratio.

4. **Corridors / Routes (`/routes`)**:
   - **Corridor Index Grid**: Detailed breakdown of index levels for major Indian corridors (DEL-BOM, DEL-BLR, BOM-BLR, etc.).
   - **Weight Share & Pressure**: Displays DGCA passenger volume weights and corridor pricing pressure scores.

5. **AI/ML Intelligence (`/intelligence`)**:
   - **Airfare Shock Detector**: Alerts triggered by rapid non-linear price escalations across multiple sources.
   - **Anomaly Score & Pressure Gauge**: Real-time evaluation from Harshitha's machine learning models.

6. **What-If Policy Simulator (`/simulator`)**:
   - **Interactive Shock Injection**: Select a corridor (e.g., DEL-BOM) and specify a hypothetical fare shock percentage (e.g., $+15\%$).
   - **Impact Projection**: Calculates the exact point contribution and projected national index using the official formula: $\Delta I = I_{\text{base}} \times w_r \times \Delta P_r$.

7. **Statistical Validation (`/validation`)**:
   - **Non-Fabrication Policy**: Honestly flags `NOT_CONNECTED` when external DGCA/MoSPI benchmark data is not live streamed, clearly labeling benchmark demonstration fixtures.
   - **30-Day Backtest Metrics Table**: Displays Pearson correlation ($r$), Spearman rank correlation ($\rho$), Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), and Directional Accuracy.

---

### 8. Step 6: Automated Test Verification

Run all test suites across the repository to verify that all mathematical, data quality, intelligence, and backend assertions hold:

#### Python Pytest Suite (295/295 Tests Passing)
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

#### Frontend Jest Tests (23/23 Tests Passing)
```bash
cd frontend && npm test
```

#### Next.js Production Build Verification
```bash
cd frontend && npm run build
```
Builds all 12 routes with 0 TypeScript errors and optimized production bundles.
