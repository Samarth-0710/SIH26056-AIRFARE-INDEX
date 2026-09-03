"""Weight configuration and models for route-level aggregation.

Adheres strictly to the project rule:
- Do NOT invent official weights.
- Distinguish reference/demo weights from configured weights.
- Enforce strict validation and normalization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
import math
from typing import Any, Dict, List, Optional


class WeightSource(str, Enum):
    """Source classification for route weights."""
    REFERENCE_DGCA_PUBLISHED = "REFERENCE_DGCA_PUBLISHED"
    HISTORICAL_PASSENGER_TRAFFIC = "HISTORICAL_PASSENGER_TRAFFIC"
    USER_CONFIGURED = "USER_CONFIGURED"
    DEMO_FIXTURE = "DEMO_FIXTURE"


@dataclass(frozen=True)
class RouteWeight:
    """Weight assigned to a specific route segment."""
    route: str
    weight: float

    def __post_init__(self) -> None:
        if not self.route or "-" not in self.route:
            raise ValueError(f"Invalid route format: '{self.route}'. Expected 'ORIGIN-DEST'")
        if not isinstance(self.weight, (int, float)):
            raise ValueError(f"Weight must be numeric, got {type(self.weight)}")
        w = float(self.weight)
        if math.isnan(w) or math.isinf(w):
            raise ValueError(f"Weight for route {self.route} cannot be NaN or Infinite")
        if w < 0.0:
            raise ValueError(f"Weight for route {self.route} cannot be negative ({w})")
        object.__setattr__(self, "route", self.route.strip().upper())
        object.__setattr__(self, "weight", w)


@dataclass(frozen=True)
class WeightConfig:
    """Configurable route weights container for aggregation.
    
    Attributes:
        version: Unique identifier for this weight configuration (e.g., 'W_2024_Q1')
        source: Provenance of the weights (WeightSource or string)
        weights: Mapping from normalized route string (e.g., 'DEL-BOM') to non-negative weight
        effective_from: Optional date from which these weights take effect
        description: Informational description of how weights were derived
        is_official: Flag indicating whether these weights are officially gazetted/DGCA sanctioned.
                     Defaults to False to prevent inventing official weights.
    """
    version: str
    source: str
    weights: Dict[str, float]
    effective_from: Optional[date] = None
    description: str = ""
    is_official: bool = False

    def __post_init__(self) -> None:
        if not self.version or not self.version.strip():
            raise ValueError("WeightConfig must have a non-empty version identifier")
        if not self.source or not self.source.strip():
            raise ValueError("WeightConfig must have a non-empty source identifier")
        if not self.weights:
            raise ValueError("WeightConfig must contain at least one route weight")

        cleaned_weights: Dict[str, float] = {}
        for route, w in self.weights.items():
            rw = RouteWeight(route=route, weight=w)
            cleaned_weights[rw.route] = rw.weight

        total_weight = sum(cleaned_weights.values())
        if total_weight <= 0.0:
            raise ValueError("Total sum of route weights must be strictly positive (> 0)")

        # Normalization check: if close to 1.0 (within 1e-5), normalize cleanly
        # If sum is close to 100.0 (percentage format), convert to decimal
        if abs(total_weight - 100.0) < 1e-3:
            cleaned_weights = {r: w / 100.0 for r, w in cleaned_weights.items()}
            total_weight = sum(cleaned_weights.values())

        if abs(total_weight - 1.0) > 1e-4:
            raise ValueError(
                f"Route weights must sum to 1.0 (or 100%). Current sum is {total_weight:.6f}. "
                f"Normalize the weights before initializing WeightConfig."
            )

        # Enforce exact sum = 1.0 by minor scaling if floating-point drift occurred
        if total_weight != 1.0:
            cleaned_weights = {r: w / total_weight for r, w in cleaned_weights.items()}

        object.__setattr__(self, "weights", cleaned_weights)

    @property
    def routes(self) -> List[str]:
        """List of routes covered by this weight configuration."""
        return sorted(list(self.weights.keys()))

    def get_weight(self, route: str) -> float:
        """Retrieve weight for a route, or 0.0 if not present."""
        return self.weights.get(route.strip().upper(), 0.0)

    @classmethod
    def from_raw_weights(
        cls,
        raw_weights: Dict[str, float],
        version: str,
        source: str = WeightSource.USER_CONFIGURED.value,
        auto_normalize: bool = True,
        effective_from: Optional[date] = None,
        description: str = "",
        is_official: bool = False,
    ) -> WeightConfig:
        """Factory method allowing raw unnormalized weights with explicit normalization."""
        if not raw_weights:
            raise ValueError("Cannot construct WeightConfig from empty weights mapping")

        total = sum(float(w) for w in raw_weights.values())
        if total <= 0.0:
            raise ValueError(f"Total weight sum must be positive, got {total}")

        if auto_normalize:
            normalized = {
                r.strip().upper(): float(w) / total for r, w in raw_weights.items()
            }
        else:
            normalized = {
                r.strip().upper(): float(w) for r, w in raw_weights.items()
            }

        return cls(
            version=version,
            source=source,
            weights=normalized,
            effective_from=effective_from,
            description=description,
            is_official=is_official,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize weight configuration."""
        return {
            "version": self.version,
            "source": self.source,
            "weights": self.weights,
            "effective_from": self.effective_from.isoformat() if self.effective_from else None,
            "description": self.description,
            "is_official": self.is_official,
        }


def get_demo_reference_weights() -> WeightConfig:
    """Returns clearly marked DEMO weights for testing and examples.
    
    CRITICAL: This is an illustrative demonstration fixture based on top Indian domestic trunk routes.
    It is NOT an official gazetted DGCA weight set.
    """
    demo_dict = {
        "DEL-BOM": 0.25,
        "BOM-DEL": 0.25,
        "DEL-BLR": 0.15,
        "BLR-DEL": 0.15,
        "BOM-BLR": 0.10,
        "BLR-BOM": 0.10,
    }
    return WeightConfig(
        version="DEMO_FIXTURE_TOP_ROUTES_V1",
        source=WeightSource.DEMO_FIXTURE.value,
        weights=demo_dict,
        description="Demo fixture representing top Indian trunk routes for tests and examples ONLY. Not official.",
        is_official=False,
    )
