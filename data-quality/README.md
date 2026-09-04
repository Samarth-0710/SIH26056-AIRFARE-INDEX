# Data Quality

**Owner:** Hindu

The Data Quality module prepares airfare observations for the Statistical
Index Engine.

## Responsibilities

- Validate raw airfare observations
- Normalize route, source, text and fare values
- Calculate comparable fares from base fare, taxes and mandatory charges
- Assign the supported booking windows:
  - T+1
  - T+7
  - T+15
  - T+30
  - T+45
- Generate deterministic fare fingerprints
- Detect exact duplicate observations
- Detect comparable-fare outliers using the IQR method
- Calculate data-quality and coverage metrics
- Produce normalized and quality-controlled observations
- Preserve rejected observations for traceability

## Pipeline

Raw Fare Observation
        |
        v
Validation
        |
        v
Fare Normalization
        |
        v
Booking Window Assignment
        |
        v
Fare Fingerprinting
        |
        v
Duplicate Detection
        |
        v
Outlier Detection
        |
        v
Normalized + Quality-Controlled Observation
