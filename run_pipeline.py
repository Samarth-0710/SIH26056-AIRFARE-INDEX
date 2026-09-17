#!/usr/bin/env python3
"""CLI runner for executing the SIH26056 Airfare Price Index pipeline.

Usage:
    python run_pipeline.py [--live] [--date YYYY-MM-DD] [--shock PERCENT]
"""

import argparse
import os
import sys
from datetime import date

# Ensure source directories are in PYTHONPATH
sys.path.insert(0, os.path.abspath("backend"))
sys.path.insert(0, os.path.abspath("data-collection/src"))
sys.path.insert(0, os.path.abspath("data-quality"))
sys.path.insert(0, os.path.abspath("data-quality/src"))
sys.path.insert(0, os.path.abspath("statistical-engine/src"))
sys.path.insert(0, os.path.abspath("intelligence/src"))

from app.db.database import Base, SessionLocal, engine
from app.services.pipeline_service import run_pipeline


def main():
    parser = argparse.ArgumentParser(description="SIH26056 Airfare Price Index Pipeline Runner")
    parser.add_argument("--days", type=int, default=30, help="Number of historical days to simulate (default: 30)")
    parser.add_argument("--date", type=str, default=None, help="Target observation date (YYYY-MM-DD)")
    parser.add_argument("--live", action="store_true", help="Use live external data sources if configured")
    parser.add_argument("--shock", type=float, default=2.5, help="Simulated price movement percentage")
    args = parser.parse_args()

    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    target_d = date.fromisoformat(args.date) if args.date else date.today()
    print(f"==================================================")
    print(f"Executing SIH26056 Airfare Price Index Pipeline")
    print(f"Observation Date: {target_d}")
    print(f"Historical Days:  {args.days}")
    print(f"Mode: {'LIVE' if args.live else 'DEMO/SYNTHETIC'}")
    print(f"==================================================")

    db = SessionLocal()
    try:
        result = run_pipeline(
            db=db,
            target_date=target_d,
            use_live_source=args.live,
            price_movement_pct=args.shock,
            days=args.days,
            clean=True,
        )
        indices = result.get("national_indices", {})
        db_path = str(engine.url).replace("sqlite:///", "")

        print("\n========================================")
        print("SIH26056 AIRFARE INDEX PIPELINE")
        print("========================================")
        print(f"Mode: {result['mode']}")
        print(f"Historical days: {result.get('historical_days', args.days)}")
        print(f"Observations collected: {result['observations_stored']}")
        print(f"Valid observations:     {result.get('valid_observations', result['observations_stored'])}")
        print(f"Rejected observations:  {result.get('rejected_observations', 0)}")
        print(f"Routes processed:       {result.get('routes_processed', 6)}")
        print(f"National Index T+1:  {indices.get('T+1', 'N/A')}")
        print(f"National Index T+7:  {indices.get('T+7', 'N/A')}")
        print(f"National Index T+15: {indices.get('T+15', 'N/A')}")
        print(f"National Index T+30: {indices.get('T+30', 'N/A')}")
        print(f"National Index T+45: {indices.get('T+45', 'N/A')}")
        print(f"Intelligence events:    {result['intelligence_events_stored']}")
        print(f"MoSPI reference records:{result.get('mospi_reference_records', 0)}")
        print(f"Calculation version:    {result['calculation_version']}")
        print(f"Checksum:               {result['execution_checksum']}")
        print(f"Database:               {db_path}")
        print("PIPELINE SUCCESS")
        print("========================================")
    except Exception as err:
        print(f"\n[ERROR] Pipeline failed: {err}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
