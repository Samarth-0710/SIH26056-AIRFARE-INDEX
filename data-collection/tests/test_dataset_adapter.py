from pathlib import Path

from data_collection.dataset_adapter import (
    CPIReferenceDataAdapter,
)


def test_cpi_dataset_loads():

    dataset_path = Path(
        "dataset/cpi_1797.xlsx"
    )

    adapter = CPIReferenceDataAdapter(
        dataset_path
    )

    dataframe = adapter.load()

    assert not dataframe.empty


def test_airfare_data_exists():

    dataset_path = Path(
        "dataset/cpi_1797.xlsx"
    )

    adapter = CPIReferenceDataAdapter(
        dataset_path
    )

    airfare_data = adapter.get_airfare_data()

    assert not airfare_data.empty

    assert (
        airfare_data["item"]
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("airfare")
        .all()
    )


def test_latest_airfare_exists():

    dataset_path = Path(
        "dataset/cpi_1797.xlsx"
    )

    adapter = CPIReferenceDataAdapter(
        dataset_path
    )

    latest = adapter.get_latest_airfare()

    assert not latest.empty