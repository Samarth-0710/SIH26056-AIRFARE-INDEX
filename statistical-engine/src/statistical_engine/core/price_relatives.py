"""Price relative calculation and validation.

Implements the elementary price relative:
    R_i = P_i,t / P_i,t-1
for comparable observations.
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

from statistical_engine.core.comparability import MatchedObservationPair
from statistical_engine.models.index_result import PriceRelative


def calculate_price_relative(
    current_fare: float,
    previous_fare: float,
    fingerprint: str = "",
    route: str = "",
    booking_window: Optional[any] = None,
) -> Optional[PriceRelative]:
    """Calculate single price relative P_i,t / P_i,t-1.
    
    Returns None if:
    - fares are <= 0
    - fares are NaN or Infinite
    """
    if not isinstance(current_fare, (int, float)) or not isinstance(previous_fare, (int, float)):
        return None

    c_fare = float(current_fare)
    p_fare = float(previous_fare)

    if math.isnan(c_fare) or math.isnan(p_fare) or math.isinf(c_fare) or math.isinf(p_fare):
        return None

    if c_fare <= 0.0 or p_fare <= 0.0:
        return None

    rel = c_fare / p_fare
    if math.isnan(rel) or math.isinf(rel) or rel <= 0.0:
        return None

    return PriceRelative(
        fingerprint=fingerprint,
        route=route,
        booking_window=booking_window,
        current_fare=c_fare,
        previous_fare=p_fare,
        relative=rel,
    )


def extract_price_relatives(
    matched_pairs: List[MatchedObservationPair],
) -> Tuple[List[PriceRelative], List[str]]:
    """Convert matched observation pairs to valid PriceRelative objects."""
    relatives: List[PriceRelative] = []
    warnings: List[str] = []

    for pair in matched_pairs:
        rel = calculate_price_relative(
            current_fare=pair.current_observation.comparable_fare,
            previous_fare=pair.previous_observation.comparable_fare,
            fingerprint=pair.fingerprint,
            route=pair.route,
            booking_window=pair.booking_window,
        )
        if rel is not None:
            relatives.append(rel)
        else:
            warnings.append(
                f"Invalid fare values for pair {pair.fingerprint}: "
                f"current={pair.current_observation.comparable_fare}, "
                f"previous={pair.previous_observation.comparable_fare}"
            )

    return relatives, warnings
