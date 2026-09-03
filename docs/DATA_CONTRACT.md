# SIH26056 Shared Data Contract

**Status:** Proposed — Ready for Team Review
**Document Version:** 1.0.0-draft
**Scope:** Shared data interfaces connecting `data-collection`, `data-quality`, `statistical-engine`, `backend`, `intelligence`, and `database`.

---

## 1. Purpose

This document proposes the shared data contract based on the currently implemented statistical engine and available project documentation. Items marked "Requires team agreement" remain unresolved and are not yet authoritative. It outlines the data schemas, field types, validation rules, comparability dimensions, error statuses, and serialization conventions exchanged across the pipeline:

$$\text{Permitted Sources} \longrightarrow \text{Data Collection} \longrightarrow \text{Data Quality / Normalization} \longrightarrow \mathbf{Statistical\ Engine} \longrightarrow \text{Backend / API} \longrightarrow \text{Intelligence / Dashboard}$$

The contract establishes that:
1. The **Statistical Engine** receives clean, quality-controlled, comparable fare observations.
2. The **Backend & API** receive deterministic, structured, versioned index results and reproducibility metadata.
3. The **Intelligence Layer** receives clear contribution and index movement data without interfering with the statistical index calculation.

---

## 2. Contract Boundary

| Boundary Layer | Upstream Producer | Downstream Consumer | Exchange Object / Format | Contract Classification |
|---|---|---|---|---|
| **Collection $\to$ Quality** | `data-collection` (Kumuda) | `data-quality` (Hindu) | Raw Scraped Fare Events / Batches | Domain-specific collection feeds *(Requires team agreement on raw storage schema)* |
| **Quality $\to$ Statistics** | `data-quality` (Hindu) | `statistical-engine` (Samarth) | Cleaned `FareObservation` records | **Finalized by Statistical Engine Contract** (Section 3) |
| **Weights $\to$ Statistics** | `database` / Config | `statistical-engine` (Samarth) | Validated `WeightConfig` container | **Finalized by Statistical Engine Contract** (Section 6) |
| **Statistics $\to$ Backend** | `statistical-engine` (Samarth) | `backend` (Mohith) | `EngineCalculationOutput` | **Finalized by Statistical Engine Contract** (Section 8) |
| **Backend $\to$ Intelligence** | `backend` (Mohith) | `intelligence` (Harshitha) | Normalized Index & Contribution models | Derived from Engine Output (Section 8) |
| **Backend $\to$ Frontend** | `backend` (Mohith) | `frontend` (Nishanth) | REST / JSON API Responses | API design owned by Mohith *(Requires team agreement)* |

---

## 3. Fare Observation Contract

The statistical engine does **not** consume raw scraped records. Upstream normalization and quality filtering in `data-quality` must produce comparable observations conforming to the specification below.

### 3.1 Field Definitions

The table below defines every field supported and required by the statistical engine's [`FareObservation`](file:///Users/samarth07/Documents/Hackathon/sih26056-airfare-index/statistical-engine/src/statistical_engine/models/observation.py):

| Field Name | Type | Required | Format / Valid Values | Validation Rule | Purpose in Pipeline | Fingerprint? | Contract Category |
|---|---|:---:|---|---|---|:---:|---|
| `origin` | `str` | Yes | 3-letter IATA code (e.g. `"DEL"`) | Non-empty; auto-uppercased; `origin != destination` | Route grouping, basket identification | **Yes** | Documented Project Requirement |
| `destination` | `str` | Yes | 3-letter IATA code (e.g. `"BOM"`) | Non-empty; auto-uppercased; `destination != origin` | Route grouping, basket identification | **Yes** | Documented Project Requirement |
| `travel_date` | `datetime.date` | Yes | ISO-8601 Calendar Date (`YYYY-MM-DD`) | Valid date; `travel_date >= observation_date` | Departure date tracking; temporal sorting | Optional* | Documented Project Requirement |
| `observation_date` | `datetime.date` | Yes | ISO-8601 Calendar Date (`YYYY-MM-DD`) | Valid date | Period separation ($t$ vs $t-1$) | No | Documented Project Requirement |
| `booking_window` | `BookingWindow` | Yes | `"T+1"`, `"T+7"`, `"T+15"`, `"T+30"`, `"T+45"` | Must match one of the 5 documented booking windows | Advance-purchase window segregation | **Yes** | Documented Project Requirement |
| `airline` | `str` | Yes | Airline IATA/ICAO or brand (e.g. `"6E"`, `"AI"`) | Non-empty string; auto-uppercased | Constant-quality flight matching | **Yes** | Documented Project Requirement |
| `flight_number` | `str` | Yes | Flight number (e.g. `"6E-201"`, `"AI-301"`) | Non-empty string; auto-uppercased | Constant-quality flight matching | **Yes** | Documented Project Requirement |
| `departure_time` | `str` | Yes | Scheduled departure time (`"08:00"` or ISO time) | Non-empty string; standardized representation | Constant-quality departure slot matching | **Yes** | Documented Project Requirement |
| `cabin_class` | `str` | Yes | Standardized cabin (`"ECONOMY"`, `"BUSINESS"`) | Non-empty string; auto-uppercased | Constant-quality cabin matching | **Yes** | Documented Project Requirement |
| `fare_type` | `str` | Yes | Standardized fare brand (`"SAVER"`, `"FLEXI"`) | Non-empty string; auto-uppercased | Constant-quality condition matching | **Yes** | Documented Project Requirement |
| `baggage_characteristics` | `str` | Yes | Standardized allowance (`"15KG"`, `"CABIN_ONLY"`) | Non-empty string; auto-uppercased | Constant-quality amenity matching | **Yes** | Documented Project Requirement |
| `comparable_fare` | `float` | Yes | Positive finite decimal (INR) | Strictly positive ($> 0.0$); finite; no `NaN`/`Inf` | Numerator/denominator for price relative $R_i$ | No | Documented Project Requirement |
| `source` | `str` | Yes | Example source identifier (e.g. `"SOURCE_A"`, `"SOURCE_B"`) | Non-empty string | Audit trail & provenance tracking | No | Documented Project Requirement |
| `observation_timestamp` | `datetime.datetime` | Yes | ISO-8601 datetime | Valid datetime (canonical timezone representation requires team agreement) | Provenance & crawl time verification | No | Documented Project Requirement |
| `quality_status` | `QualityStatus` | No | `"VALID"`, `"SUSPECT"`, `"EXCLUDED"`, `"OUTLIER"` | Defaults to `QualityStatus.VALID` if omitted | Upstream quality filtering | No | Statistical Engine Implementation Requirement |
| `metadata` | `dict` | No | Key-value dictionary | Defaults to `{}` | Passthrough storage for integration extensions | No | Integration Convention |

*\*Note on `travel_date`: In standard advance-window tracking, the booking window (e.g. $T+7$) represents the constant-quality product. The engine also supports strict same-departure pairing via the `include_travel_date` flag.*

---

### 3.2 Booking Windows

The project methodology strictly requires separate index series for the following 5 advance purchase windows:
- **`T+1`**: 1-day advance booking (last-minute demand window)
- **`T+7`**: 7-day advance booking (1-week advance window)
- **`T+15`**: 15-day advance booking (2-week advance window)
- **`T+30`**: 30-day advance booking (1-month advance window)
- **`T+45`**: 45-day advance booking (early booking window)

#### Integration Conventions:
1. **Separation Rule:** The statistical engine strictly computes separate indices for each booking window. **Under no circumstances should observations from different booking windows be mixed into a single elementary index.**
2. **Lead Time Mapping:**
   - If upstream collection stores integer lead days ($\text{days} = \text{travel\_date} - \text{observation\_date}$), `data-quality` must map them to documented windows:
     $$1 \to \text{"T+1"}, \quad 7 \to \text{"T+7"}, \quad 15 \to \text{"T+15"}, \quad 30 \to \text{"T+30"}, \quad 45 \to \text{"T+45"}$$
   - Observations with lead days outside these exact values (e.g. 10 days) cannot be arbitrarily assigned to a booking window without project approval (*Requires team agreement*).

---

### 3.3 Quality Status

The `quality_status` field communicates the verification result from `data-quality` (Hindu) to `statistical-engine`:

- **`VALID`**: Observation passed all sanity, range, and format checks. Included in pairing and index calculations.
- **`SUSPECT`**: Observation triggered a soft quality warning (e.g. unusual price fluctuation). Excluded from calculations by default; included only if explicitly enabled (`allow_suspect = True`).
- **`EXCLUDED`**: Observation failed quality checks (e.g. invalid fare components, cancelled flight, test scrape). **Always excluded** from index calculations.
- **`OUTLIER`**: Observation identified as an extreme statistical anomaly by upstream cleansing. Handled according to upstream configuration; treated as `EXCLUDED` if marked as such.

> [!IMPORTANT]
> `data-quality` must resolve raw scraping flags and assign one of these four standardized enum strings before passing data to `statistical-engine`.

---

### 3.4 Comparable Fare

`comparable_fare` is the standardized fare value supplied by the data-quality layer for statistical comparison.

The statistical engine requires the value to be:
- numeric
- finite
- strictly greater than zero ($\text{comparable\_fare} > 0.0$)

Values $\le 0.0$, `NaN`, or `Infinity` are rejected with validation errors.

The exact treatment of base fare, taxes, mandatory charges, optional ancillaries, convenience fees, and other fare components is a data-quality methodology decision and requires team agreement.

---

## 4. Comparability Contract

To prevent comparing dissimilar services, the statistical engine constructs a deterministic constant-quality fingerprint hash:

$$\text{Fingerprint} = \text{SHA256}(\text{route} \mid \text{booking\_window} \mid \text{airline} \mid \text{flight\_number} \mid \text{departure\_time} \mid \text{cabin\_class} \mid \text{fare\_type} \mid \text{baggage\_characteristics})$$

### Comparability Rules:
1. **Identical Service Bundle:** Two observations across time periods $t-1$ and $t$ are considered comparable if and only if their fingerprints match exactly.
2. **Elementary Price Relative:**
   $$R_i = \frac{P_{i,t}}{P_{i,t-1}}$$
   where $P_{i,t}$ and $P_{i,t-1}$ share the identical fingerprint $i$.
3. **Statistical-Engine Implementation Convention:** Upstream modules must ensure that fields like `departure_time` (e.g. `"08:00"` vs `"08:00:00"`) and `cabin_class` (`"ECONOMY"` vs `"Economy"`) are consistently normalized to prevent artificial fingerprint mismatches.

---

## 5. Data Quality Boundary

To ensure high architectural cohesion, responsibilities are partitioned cleanly:

| Responsibility | Upstream Data Quality (`data-quality`) | Statistical Engine Defensive Handling (`statistical-engine`) |
|---|---|---|
| **Zero / Negative Fares** | Must filter out or flag as `EXCLUDED` | Strictly rejects with `ValueError` on model initialization |
| **Route Identifiers** | Data-quality should validate/normalize route identifiers | Validates expected 3-letter uppercase route-code format and `origin != destination` |
| **Inconsistent Dates** | Must discard records where travel precedes observation | Rejects with `ValueError` if `travel_date < observation_date` |
| **Duplicate Fares in Batch** | **Primary responsibility:** Deduplicate multiple scrapes of the same flight in the same period | **Defensive fallback:** Logs diagnostic warning and deterministically selects lowest fare |
| **Outlier Detection** | Identifies scraping spikes / non-standard promotional flash errors | Discards any record marked `EXCLUDED` |

---

## 6. Weight Configuration Contract

Route indices are aggregated into national composite indices using reference weights.

### 6.1 WeightConfig Specification

The statistical engine accepts route weights via the [`WeightConfig`](file:///Users/samarth07/Documents/Hackathon/sih26056-airfare-index/statistical-engine/src/statistical_engine/models/weights.py) container:

| Field Name | Type | Required | Description |
|---|---|:---:|---|
| `version` | `str` | Yes | Version identifier for the supplied weight set |
| `source` | `str` | Yes | Provenance/source identifier for the supplied weight set |
| `weights` | `Dict[str, float]` | Yes | Route-to-weight mapping supplied by the approved/reference methodology |
| `effective_from` | `Optional[datetime.date]` | No | Calendar date from which these weights take effect |
| `description` | `str` | No | Informational description of the weight set |
| `is_official` | `bool` | No | Boolean indicating whether the supplied weight set is designated as official/reference data by the project (defaults to `False`) |

### 6.2 Weight Validation Rules
1. **Non-Negativity:** Every individual route weight must be non-negative ($w_i \ge 0.0$).
2. **Normalization:** The sum of weights must equal $1.0$ within a tolerance of $10^{-4}$ (or $100.0$, which is automatically converted to decimal).
3. **Strict Zero Fabrication Rule:** Official route weights must **never** be invented or hardcoded. Any synthetic example used in tests must be explicitly marked with `source = "DEMO_FIXTURE"` and `is_official = False`.

---

## 7. Statistical Engine Input

When invoking the engine for a period transition ($t-1 \to t$), downstream orchestration in `backend` (Mohith) provides:

```python
output: EngineCalculationOutput = engine.calculate_daily_indices(
    current_observations=current_clean_observations,    # List[FareObservation] for date t
    previous_observations=previous_clean_observations,  # List[FareObservation] for date t-1
    observation_date=date(2024, 4, 8),                  # Date t
    previous_observation_date=date(2024, 4, 7),         # Date t-1
    weight_config=active_weight_config,                 # WeightConfig
    observation_set_version="OBS_20240408_01",          # Provenance tag
    basket_version="BASKET_v1.0",                       # Route basket tag
    target_booking_windows=[                            # Optional window subset
        BookingWindow.T_1,
        BookingWindow.T_7,
        BookingWindow.T_15,
        BookingWindow.T_30,
        BookingWindow.T_45,
    ],
    previous_route_indices=previous_indices_dict,       # Optional for point contribution tracking
    allow_partial_coverage=False,                       # Defaults to False (strict basket coverage)
)
```

---

## 8. Statistical Engine Output

The engine produces structured, strongly-typed results via [`EngineCalculationOutput`](file:///Users/samarth07/Documents/Hackathon/sih26056-airfare-index/statistical-engine/src/statistical_engine/models/index_result.py):

### 8.1 Calculation Status
- **`SUCCESS`**: Calculation completed successfully with full basket coverage.
- **`INSUFFICIENT_DATA`**: Fewer valid observations than required, or required routes missing under strict coverage. National index is set to `None`.
- **`PARTIAL_COVERAGE`**: Returned **only** when `allow_partial_coverage = True` is explicitly enabled and sub-basket re-normalization occurred.
- **`FAILED`**: Calculation could not be completed due to an execution or configuration failure.

### 8.2 Route Results (`Dict[str, RouteIndexResult]`)
Keyed by normalized route string (e.g. `"DEL-BOM"`):
- `route`: Route identifier.
- `status`: Status for route calculation (`SUCCESS` or `INSUFFICIENT_DATA`).
- `warnings`: Diagnostic messages.
- `window_indices`: Mapping of `BookingWindow` $\to$ `ElementaryIndexResult`:
  - `index_value`: Elementary Jevons index level (float, base 100.0).
  - `geometric_mean_relative`: Unscaled geometric mean $\left(\prod R_i\right)^{1/n}$.
  - `num_matched_pairs`: Count of valid matched comparable observation pairs.
  - `num_current_observations`: Total valid current observations in this slice.
  - `num_previous_observations`: Total valid previous observations in this slice.

### 8.3 National Results (`Dict[BookingWindow, NationalIndexResult]`)
Keyed by `BookingWindow`:
- `booking_window`: Evaluated window (e.g. `BookingWindow.T_7`).
- `national_index`: Composite national airfare index:
  $$I_t^{\text{national}} = \sum_{r \in \text{Routes}} w_r \cdot I_{r,t}$$
- `coverage_ratio`: Sum of configured weights for routes actually observed ($0.0$ to $1.0$).
- `weight_version`: Version string of the active `WeightConfig`.
- `status`: Status of the national calculation.
- `route_indices`: Mapping of route code to route index level.
- `route_contributions`: Mapping of route code to `RouteContribution`.

### 8.4 Contributions (`Dict[str, RouteContribution]`)
Per-route decomposition for each booking window:
- `weight`: Route weight $w_r$.
- `route_index`: Route index value $I_{r,t}$.
- `level_contribution`: Route contribution to national index level ($w_r \cdot I_{r,t}$).
- `point_contribution`: Route contribution to aggregate index change ($w_r \cdot (I_{r,t} - I_{r,t-1})$), where $\sum_r C_r^{\text{point}} = \Delta I_t^{\text{national}}$.
- `percentage_share_of_change`: Share of total index movement attributable to route $\left(\frac{C_r^{\text{point}}}{\Delta I_t} \times 100\%\right)$.

### 8.5 Reproducibility Metadata
Stored in `output.reproducibility`:
- `observation_set_version`: Version tag of the raw/clean observation set.
- `basket_version`: Version tag of the route basket definition.
- `weight_version`: Version identifier of route weights.
- `methodology_version`: String constant (e.g. `"JEVONS_SHORT_INDEX_v1.0"`).
- `calculation_timestamp`: UTC timestamp of execution.
- `execution_checksum`: Deterministic SHA-256 hash computed over inputs, versions, and outputs.

---

## 9. Validation / Back-Test Contract

The engine includes a reusable 30-day validation framework against external reference data.

### 9.1 Validation Metrics
Evaluated over aligned daily index series vs external benchmark series:

| Metric | Formula / Definition | Output Status When Undefined | Project Status |
|---|---|---|:---:|
| **Pearson Correlation ($r$)** | Linear co-movement between calculated index and reference series | Returns `UNDEFINED_VARIANCE` with `value = None` if either series is constant | Documented Requirement |
| **Spearman Correlation ($\rho$)** | Rank correlation assessing monotonic relationship | Returns `UNDEFINED_VARIANCE` with `value = None` if either series is constant | Statistical Engine Addition |
| **Mean Absolute Error (MAE)** | $\frac{1}{n} \sum \|I_t - R_t\|$ (in index points) | Returns `INSUFFICIENT_DATA` if $n = 0$ | Documented Requirement |
| **Root Mean Squared Error (RMSE)** | $\sqrt{\frac{1}{n} \sum (I_t - R_t)^2}$ (penalizes large divergences) | Returns `INSUFFICIENT_DATA` if $n = 0$ | Documented Requirement |
| **Directional Accuracy** | Proportion of days where $\operatorname{sgn}(\Delta I_t) == \operatorname{sgn}(\Delta R_t)$ | Range $[0.0, 1.0]$; requires at least 2 consecutive days | Documented Requirement |
| **Coverage** | $\frac{\text{valid days evaluated}}{\text{expected calendar days in window}}$ | Range $[0.0, 1.0]$ | Documented Requirement |
| **Stability** | Sample standard deviation of daily first differences $\sigma(\Delta I_t)$ | Requires at least 3 points | Documented Requirement |

### 9.2 Zero Fabrication Rule for Reference Data
Reference benchmark data is strictly an **external input** to the `BacktestRunner`. Official DGCA or MoSPI reference series must never be fabricated. Synthetic series generated for testing are strictly marked `is_official_reference = False`.

---

## 10. Serialization / Integration Notes

The statistical engine is completely decoupled from databases and web frameworks:

1. **JSON Serialization:**
   - Every output model implements a `.to_dict()` method returning native Python primitives (`int`, `float`, `str`, `dict`, `list`).
   - Standard serialization via `json.dumps(output.to_dict())` works with zero custom encoders.
2. **Database Deserialization:**
   - `FareObservation.from_dict(row)` automatically converts ISO date strings (`"YYYY-MM-DD"`) and ISO timestamps into `datetime.date` and `datetime.datetime` objects.
   - `BookingWindow.from_string(str_val)` handles string-to-enum conversion cleanly.
3. **Purity:** Core calculations are stateless pure functions. No threading, caching, or background processes are initiated by the engine.

---

## 11. Open Decisions / Requires Team Agreement

The following items are unresolved across the shared repository and require formal team agreement:

1. **Lead Time Handling for Non-Documented Advance Days:**
   - *Issue:* Scrapers may gather fares for lead days other than 1, 7, 15, 30, and 45 (e.g. 3, 10, 21 days).
   - *Status:* Requires team agreement between Kumuda (`data-collection`), Hindu (`data-quality`), and Samarth (`statistical-engine`) on whether non-standard lead days should be discarded, bucketed into the nearest window, or tracked separately.
2. **Fare Component Normalization Policy:**
   - *Issue:* Different booking portals display fares differently (e.g. base fare only vs base fare + taxes vs total payable with convenience fees).
   - *Status:* Requires team agreement on Hindu's exact normalization formula for deriving `comparable_fare`.
3. **Database Schema & Table Names for Versioned Weights:**
   - *Issue:* The shared database schema (`database/`) must persist `WeightConfig` records with audit provenance.
   - *Status:* Requires team agreement with Mohith (`backend`).
4. **Upstream Quality Score Mapping:**
   - *Issue:* `data-quality` may produce numerical confidence scores (e.g. 0.0 to 1.0) rather than categorical flags.
   - *Status:* Requires team agreement on score thresholds mapping to `QualityStatus` (`VALID`, `SUSPECT`, `EXCLUDED`).
5. **Partial Basket Aggregation Policy:**
   - *Issue:* The statistical engine defaults to strict basket coverage (`allow_partial_coverage = False`). If live scraping experiences temporary route outages, the team must decide whether the API should return `INSUFFICIENT_DATA` (authoritative) or opt into re-normalized weights (`allow_partial_coverage = True`).
   - *Status:* Requires team agreement for production deployment.

---

## 12. Module Ownership Boundary

Per `TEAM.md` and repository architecture:

```
[Kumuda]          Data Collection   : Raw source scraping, provider adapters, fetch timestamps
       ↓
[Hindu]           Data Quality      : Cleansing, normalization, fare components, quality flags, deduplication
       ↓
[Samarth]         Statistical Engine: Authoritative Jevons elementary index, route & national aggregation,
                                      contributions, reproducibility metadata, 30-day back-test
       ↓
[Mohith]          Backend & API     : Pipeline orchestration, database persistence, FastAPI endpoints, auth
       ↓
[Nishanth]        Frontend          : UI dashboard, route trends, index visualization, user controls
       │
[Harshitha]       Intelligence      : Anomaly detection, shock analysis, intelligence drivers
                                      (consumes statistical engine output; does NOT compute index)
```

Shared ownership areas:
- `docs/`: Shared methodology and contracts.
- `database/`: Shared relational schema (PostgreSQL / SQLite).
- `tests/`: End-to-end integration tests.

---

## 13. Methodology Integrity

> [!CAUTION]
> **Strict Non-Replacement Principle:**
> 1. For the SIH26056 system implementation, the **Statistical Engine** is the authoritative calculator of the project's Airfare Price Index.
> 2. **AI/ML models must NOT compute, predict, or replace the documented statistical index calculation.**
> 3. AI/ML functions in the intelligence layer (`intelligence/` — Harshitha) are strictly analytical and explanatory (e.g. detecting fare anomalies, explaining inflation drivers, clustering fare movements).
> 4. Official weights and reference data must **never** be fabricated.
