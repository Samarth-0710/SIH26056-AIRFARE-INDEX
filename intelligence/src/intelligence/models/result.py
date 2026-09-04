from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class IntelligenceStatus(str, Enum):
    SUCCESS = "SUCCESS"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    FAILED = "FAILED"


class AnomalySeverity(str, Enum):
    NORMAL = "NORMAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass(frozen=True)
class AnomalyResult:
    """
    Result produced by the intelligence layer for an index observation.

    The intelligence layer supports the statistical engine.
    It does not replace or modify the official statistical index.
    """

    route: str
    booking_window: str

    current_index: Optional[float]
    previous_index: Optional[float]

    point_change: Optional[float]
    percentage_change: Optional[float]

    anomaly_score: Optional[float]
    severity: AnomalySeverity

    detected: bool

    reason: Optional[str] = None

    status: IntelligenceStatus = IntelligenceStatus.SUCCESS
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "route": self.route,
            "booking_window": self.booking_window,
            "current_index": self.current_index,
            "previous_index": self.previous_index,
            "point_change": self.point_change,
            "percentage_change": self.percentage_change,
            "anomaly_score": self.anomaly_score,
            "severity": self.severity.value,
            "detected": self.detected,
            "reason": self.reason,
            "status": self.status.value,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class IntelligenceOutput:
    """
    Top-level output of the Intelligence layer.

    This object is intended to be consumed later by the backend/API.
    """

    observation_date: str

    anomalies: List[AnomalyResult] = field(default_factory=list)

    status: IntelligenceStatus = IntelligenceStatus.SUCCESS

    warnings: List[str] = field(default_factory=list)

    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "observation_date": self.observation_date,
            "anomalies": [
                anomaly.to_dict()
                for anomaly in self.anomalies
            ],
            "status": self.status.value,
            "warnings": list(self.warnings),
            "metadata": dict(self.metadata),
        }