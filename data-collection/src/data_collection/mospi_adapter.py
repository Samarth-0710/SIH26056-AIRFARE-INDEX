"""MoSPI Reference Data Adapter for official e-Sankhyiki Consumer Price Index (Airfare).

This module handles the loading, programmatic filtering, validation, and serialization
of the official monthly MoSPI CPI Airfare reference dataset.

IMPORTANT:
- This is a SEPARATE validation/reference dataset.
- It is NOT raw airfare data and is NEVER passed into the Statistical Engine or fare_observations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd


MONTH_MAP = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


@dataclass(frozen=True)
class MoSPIReferenceRecord:
    """Represents a validated monthly observation from the official MoSPI CPI dataset."""
    reference_date: date
    year: int
    month_name: str
    index_value: float
    item_code: str
    item: str
    base_year: int
    series: str
    state: str
    sector: str
    source: str = "MoSPI e-Sankhyiki"
    frequency: str = "MONTHLY"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["reference_date"] = self.reference_date.isoformat()
        return d


def _find_default_dataset_path() -> Path:
    candidates = [
        Path("data/reference/CPI_Airfare.xlsx"),
        Path(__file__).resolve().parents[3] / "data" / "reference" / "CPI_Airfare.xlsx",
        Path("../data/reference/CPI_Airfare.xlsx"),
        Path("../../data/reference/CPI_Airfare.xlsx"),
    ]
    for p in candidates:
        if p.exists():
            return p.resolve()
    return candidates[0]


class MoSPIReferenceAdapter:
    """Adapter for importing and filtering the official MoSPI CPI Airfare Excel dataset."""

    DEFAULT_DATASET_PATH = _find_default_dataset_path()
    SHEET_NAME = "CPI Data"

    REQUIRED_COLUMNS = [
        "base_year",
        "series",
        "year",
        "month",
        "state",
        "sector",
        "division",
        "group",
        "class",
        "sub_class",
        "item",
        "code",
        "index",
        "inflation",
        "imputation",
    ]

    # Exact filter criteria per official MoSPI national domestic airfare specification
    FILTER_BASE_YEAR = 2024
    FILTER_SERIES = "Current"
    FILTER_STATE = "All India"
    FILTER_SECTOR = "Combined"
    FILTER_DIVISION = "Transport"
    FILTER_GROUP = "Passenger transport services"
    FILTER_CLASS = "Passenger transport by air"
    FILTER_SUB_CLASS = "Passenger transport by air, domestic"
    FILTER_ITEM = "Airfare"
    FILTER_CODE = "07.3.3.1.2.01"

    def __init__(self, dataset_path: Optional[str | Path] = None):
        if dataset_path:
            p = Path(dataset_path)
            if not p.exists():
                alt = Path(__file__).resolve().parents[3] / dataset_path
                if alt.exists():
                    p = alt.resolve()
            self.dataset_path = p
        else:
            self.dataset_path = _find_default_dataset_path()

    def get_status(self) -> str:
        """Check if dataset file exists and is accessible."""
        return "AVAILABLE" if self.dataset_path.exists() else "UNAVAILABLE"

    def load_raw(self) -> pd.DataFrame:
        """Load the raw Excel worksheet and validate column presence."""
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"MoSPI dataset file not found at: {self.dataset_path}")

        df = pd.read_excel(self.dataset_path, sheet_name=self.SHEET_NAME)

        missing = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(f"MoSPI dataset is missing expected columns: {missing}")

        return df

    def get_national_series(self) -> List[MoSPIReferenceRecord]:
        """Programmatically filter, validate, and return the official All India Combined airfare series.

        Returns:
            List of chronologically sorted MoSPIReferenceRecord objects.
        """
        df = self.load_raw()

        # Exact multi-column filtering
        mask = (
            (df["base_year"] == self.FILTER_BASE_YEAR)
            & (df["series"].astype(str).str.strip() == self.FILTER_SERIES)
            & (df["state"].astype(str).str.strip() == self.FILTER_STATE)
            & (df["sector"].astype(str).str.strip() == self.FILTER_SECTOR)
            & (df["division"].astype(str).str.strip() == self.FILTER_DIVISION)
            & (df["group"].astype(str).str.strip() == self.FILTER_GROUP)
            & (df["class"].astype(str).str.strip() == self.FILTER_CLASS)
            & (df["sub_class"].astype(str).str.strip() == self.FILTER_SUB_CLASS)
            & (df["item"].astype(str).str.strip() == self.FILTER_ITEM)
            & (df["code"].astype(str).str.strip() == self.FILTER_CODE)
        )

        filtered = df[mask].copy()

        if filtered.empty:
            raise ValueError("No records matched the exact MoSPI All India Combined airfare criteria.")

        records: List[MoSPIReferenceRecord] = []
        seen_dates = set()

        for _, row in filtered.iterrows():
            year_val = int(row["year"])
            month_str = str(row["month"]).strip().lower()

            if month_str not in MONTH_MAP:
                raise ValueError(f"Unrecognized month format '{row['month']}' in MoSPI dataset.")

            month_num = MONTH_MAP[month_str]
            ref_date = date(year_val, month_num, 1)

            if ref_date in seen_dates:
                raise ValueError(f"Duplicate monthly observation detected for {ref_date}")
            seen_dates.add(ref_date)

            try:
                idx_val = float(row["index"])
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid non-numeric CPI index value '{row['index']}' on {ref_date}") from e

            if idx_val <= 0:
                raise ValueError(f"MoSPI CPI index must be strictly positive (> 0), got {idx_val} on {ref_date}")

            records.append(
                MoSPIReferenceRecord(
                    reference_date=ref_date,
                    year=year_val,
                    month_name=str(row["month"]).strip(),
                    index_value=round(idx_val, 4),
                    item_code=self.FILTER_CODE,
                    item=self.FILTER_ITEM,
                    base_year=self.FILTER_BASE_YEAR,
                    series=self.FILTER_SERIES,
                    state=self.FILTER_STATE,
                    sector=self.FILTER_SECTOR,
                    source="MoSPI e-Sankhyiki",
                    frequency="MONTHLY",
                )
            )

        # Sort chronologically by reference date
        records.sort(key=lambda r: r.reference_date)
        return records

    def load(self) -> List[MoSPIReferenceRecord]:
        """Convenience alias for get_national_series()."""
        return self.get_national_series()

    def to_dataframe(self) -> pd.DataFrame:
        """Return the validated national domestic series as a pandas DataFrame."""
        records = self.get_national_series()
        return pd.DataFrame([r.to_dict() for r in records])
