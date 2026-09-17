from typing import Any, List, Optional, Union
from pydantic import Field
from .common import APIModel


class ValidationMetricOut(APIModel):
    metric: str
    value: Union[float, int, str]
    status: str
    description: str


class ValidationHistoryPointOut(APIModel):
    date: str
    calculated_index: float
    reference_index: Optional[float] = None


class MoSPIReferenceDetailsOut(APIModel):
    name: str = "MoSPI e-Sankhyiki CPI Airfare"
    source: str = "MoSPI e-Sankhyiki"
    item: str = "Airfare"
    item_code: str = "07.3.3.1.2.01"
    base_year: int = 2024
    series: str = "Current"
    frequency: str = "MONTHLY"
    state: str = "All India"
    sector: str = "Combined"
    connected: bool = False
    records: int = 0
    first_date: Optional[str] = None
    latest_date: Optional[str] = None
    latest_cpi: Optional[float] = None


class AlignmentOut(APIModel):
    overlapping_months: int = 0
    status: str = "NOT_CONNECTED"
    aligned_months: List[str] = Field(default_factory=list)


class ComparisonOut(APIModel):
    reference_month: Optional[str] = None
    our_monthly_index: Optional[float] = None
    mospi_monthly_index: Optional[float] = None
    absolute_difference: Optional[float] = None
    percentage_difference: Optional[float] = None
    rebasing_method: str = "Rebased to common base 100.0 at reference month"
    our_rebased_index: Optional[float] = None
    mospi_rebased_index: Optional[float] = None


class MovementOut(APIModel):
    our_mom_change: Optional[float] = None
    mospi_mom_change: Optional[float] = None
    absolute_difference: Optional[float] = None


class CorrelationOut(APIModel):
    value: Optional[float] = None
    status: str = "NOT_CONNECTED"
    minimum_required_months: int = 3
    description: str = "Pearson correlation coefficient between aligned monthly index series"


class MonthlySeriesPointOut(APIModel):
    month: str
    our_monthly_index: Optional[float] = None
    mospi_cpi: Optional[float] = None
    our_rebased: Optional[float] = None
    mospi_rebased: Optional[float] = None
    status: str = "UNALIGNED"


class ValidationResultOut(APIModel):
    period: str
    reference_dataset: str
    methodology_version: str
    observation_set_version: str
    is_reference_connected: bool
    metrics: List[ValidationMetricOut]
    history: List[ValidationHistoryPointOut]

    # Detailed MoSPI Reference Integration
    reference_dataset_details: Optional[MoSPIReferenceDetailsOut] = None
    alignment: Optional[AlignmentOut] = None
    comparison: Optional[ComparisonOut] = None
    movement: Optional[MovementOut] = None
    correlation: Optional[CorrelationOut] = None
    monthly_series: List[MonthlySeriesPointOut] = Field(default_factory=list)
