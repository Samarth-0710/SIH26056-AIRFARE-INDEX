from abc import ABC, abstractmethod
from datetime import date
from enum import Enum
from typing import List

from .models import RawFareRecord


class SourceStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    DEGRADED = "DEGRADED"


class SourceAdapter(ABC):
    """
    Interface for airfare data sources.

    Each permitted airline/OTA source should implement this
    interface and return raw fare records.
    """

    @abstractmethod
    def collect(
        self,
        origin: str,
        destination: str,
        travel_date: date,
    ) -> List[RawFareRecord]:
        """
        Collect raw fare records for a route and travel date.

        Implementations should preserve the information received
        from the source. Normalization and quality checks happen
        downstream.
        """
        raise NotImplementedError

    def get_status(self) -> SourceStatus:
        """Return operational status of this source."""
        return SourceStatus.AVAILABLE