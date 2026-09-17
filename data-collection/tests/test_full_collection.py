import os
import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

import pytest
from data_collection.ignav_adapter import IgnavFareAdapter


def test_full_10_city_collection():
    adapter = IgnavFareAdapter()
    if not adapter.api_key:
        with pytest.raises(ValueError, match="IGNAV_API_KEY is not configured"):
            adapter.search_route("BLR", "DEL", date.today())
        return

    observation_date = date.today()

    # Unless explicitly opted into a full 450-request live crawl (RUN_FULL_LIVE_CRAWL=1),
    # constrain test suite execution to a deterministic sample route to verify
    # collect_all() aggregation and serialization end-to-end quickly without 450 network waits.
    run_full = os.getenv("RUN_FULL_LIVE_CRAWL", "").lower() in ("1", "true", "yes")
    target_routes = None if run_full else [("BLR", "DEL")]

    records = adapter.collect_all(
        observation_date=observation_date,
        routes=target_routes,
    )

    print(
        f"\nTotal records collected: {len(records)}"
    )

    assert records

    output_file = Path(
        "full_collection_output.jsonl"
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:

        for record in records:
            file.write(
                json.dumps(
                    asdict(record),
                    default=str,
                )
                + "\n"
            )

    print(
        f"Saved records to: {output_file}"
    )