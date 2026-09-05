from pathlib import Path

import pandas as pd


class CPIReferenceDataAdapter:
    """
    Adapter for the official e-Sankhyiki CPI Airfare dataset.

    This dataset contains aggregate monthly CPI information
    for domestic airfare. It is used as reference/validation
    data and is NOT converted into RawFareRecord objects.
    """

    SOURCE_NAME = "eSankhyiki_CPI_Airfare"

    REQUIRED_COLUMNS = {
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
    }

    def __init__(self, dataset_path: str | Path):
        self.dataset_path = Path(dataset_path)

        if not self.dataset_path.exists():
            raise FileNotFoundError(
                f"Dataset not found: {self.dataset_path}"
            )

    def load(self) -> pd.DataFrame:
        """
        Load the e-Sankhyiki Excel dataset and validate
        its expected structure.
        """

        dataframe = pd.read_excel(
            self.dataset_path,
            sheet_name="CPI Data",
        )

        missing_columns = (
            self.REQUIRED_COLUMNS
            - set(dataframe.columns)
        )

        if missing_columns:
            raise ValueError(
                "Dataset is missing expected columns: "
                f"{sorted(missing_columns)}"
            )

        return dataframe

    def get_airfare_data(self) -> pd.DataFrame:
        """
        Return only the domestic airfare CPI observations.
        """

        dataframe = self.load()

        airfare_data = dataframe[
            dataframe["item"]
            .astype(str)
            .str.strip()
            .str.lower()
            == "airfare"
        ].copy()

        return airfare_data

    def get_latest_airfare(self) -> pd.DataFrame:
        """
        Return the latest available Airfare CPI observation.
        """

        airfare_data = self.get_airfare_data()

        if airfare_data.empty:
            return airfare_data

        airfare_data = airfare_data.sort_values(
            by=["year", "month"]
        )

        return airfare_data.tail(1)