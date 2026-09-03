# SIH26056 Architecture

## System Flow

Source Adapters
→ Unified Fare Events
→ Fare Fingerprinting
→ Normalized Fare Records
→ Quality-Checked Observations
→ Index Basket
→ Statistical Index Engine
→ Intelligence Layer
→ API / Dashboard

## Ownership

- Data collection: Kumuda
- Data quality & normalization: Hindu
- Statistical index & validation: Samarth
- Intelligence: Harshitha
- Backend/API/database integration: Mohith
- Frontend/dashboard: Nishanth

## Contract Principle

Modules exchange structured, versioned data. Exact field names and API contracts must be finalized against the team's actual implementation before integration code is written.
