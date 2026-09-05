import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from data_collection.ignav_adapter import IgnavFareAdapter


def test_full_10_city_collection():
    adapter = IgnavFareAdapter()

    observation_date = date.today()

    records = adapter.collect_all(
        observation_date=observation_date
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