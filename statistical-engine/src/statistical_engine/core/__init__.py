"""Core mathematical and comparability package exports for statistical_engine."""

from statistical_engine.core.comparability import (
    MatchedObservationPair,
    PairingResult,
    generate_fare_fingerprint,
    match_comparable_pairs,
)
from statistical_engine.core.price_relatives import (
    calculate_price_relative,
    extract_price_relatives,
)
from statistical_engine.core.jevons import (
    JevonsResult,
    calculate_jevons_index,
)
from statistical_engine.core.elementary import (
    calculate_elementary_index_for_slice,
)

__all__ = [
    "MatchedObservationPair",
    "PairingResult",
    "generate_fare_fingerprint",
    "match_comparable_pairs",
    "calculate_price_relative",
    "extract_price_relatives",
    "JevonsResult",
    "calculate_jevons_index",
    "calculate_elementary_index_for_slice",
]
