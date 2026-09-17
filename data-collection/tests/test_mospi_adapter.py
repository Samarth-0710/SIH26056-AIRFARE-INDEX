from datetime import date
from pathlib import Path
import pandas as pd
import pytest

from data_collection.mospi_adapter import MoSPIReferenceAdapter, MoSPIReferenceRecord

def _find_reference_excel() -> Path:
    candidates = [
        Path("data/reference/CPI_Airfare.xlsx"),
        Path(__file__).resolve().parents[2] / "data" / "reference" / "CPI_Airfare.xlsx",
        Path("../data/reference/CPI_Airfare.xlsx"),
    ]
    for p in candidates:
        if p.exists():
            return p.resolve()
    return candidates[0]


REFERENCE_EXCEL_PATH = _find_reference_excel()


def test_mospi_adapter_loads_exact_20_records():
    assert REFERENCE_EXCEL_PATH.exists(), f"Reference file missing at {REFERENCE_EXCEL_PATH}"
    adapter = MoSPIReferenceAdapter(REFERENCE_EXCEL_PATH)
    records = adapter.load()

    assert len(records) == 20
    assert all(isinstance(r, MoSPIReferenceRecord) for r in records)


def test_mospi_adapter_date_range_and_values():
    adapter = MoSPIReferenceAdapter(REFERENCE_EXCEL_PATH)
    records = adapter.load()

    first = records[0]
    latest = records[-1]

    assert first.reference_date == date(2025, 1, 1)
    assert first.year == 2025
    assert first.month_name == "January"
    assert first.index_value == pytest.approx(115.05, abs=1e-2)

    assert latest.reference_date == date(2026, 8, 1)
    assert latest.year == 2026
    assert latest.month_name == "August"
    assert latest.index_value == pytest.approx(135.49, abs=1e-2)


def test_mospi_adapter_metadata_and_filters():
    adapter = MoSPIReferenceAdapter(REFERENCE_EXCEL_PATH)
    records = adapter.load()

    for r in records:
        assert r.item_code == "07.3.3.1.2.01"
        assert r.item == "Airfare"
        assert r.state == "All India"
        assert r.sector == "Combined"
        assert r.base_year == 2024
        assert r.frequency == "MONTHLY"
        assert r.source == "MoSPI e-Sankhyiki"
        assert r.index_value > 0


def test_mospi_adapter_chronological_order():
    adapter = MoSPIReferenceAdapter(REFERENCE_EXCEL_PATH)
    records = adapter.load()

    dates = [r.reference_date for r in records]
    assert dates == sorted(dates)
    assert len(dates) == len(set(dates)), "Duplicate reference dates found"


def test_mospi_adapter_to_dataframe():
    adapter = MoSPIReferenceAdapter(REFERENCE_EXCEL_PATH)
    df = adapter.to_dataframe()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 20
    assert "reference_date" in df.columns
    assert "index_value" in df.columns
    assert "item_code" in df.columns


def test_mospi_adapter_file_not_found():
    adapter = MoSPIReferenceAdapter("non_existent_file.xlsx")
    with pytest.raises(FileNotFoundError):
        adapter.load()


def test_mospi_adapter_missing_columns(tmp_path):
    invalid_excel = tmp_path / "invalid.xlsx"
    pd.DataFrame({"colA": [1, 2], "colB": [3, 4]}).to_excel(invalid_excel, sheet_name="CPI Data", index=False)

    adapter = MoSPIReferenceAdapter(invalid_excel)
    with pytest.raises(ValueError, match="missing expected columns"):
        adapter.load()
