"""Jevons geometric mean elementary index calculation.

The elementary index formula documented by the project:
    E_t = ( product(i=1..n) [P_i,t / P_i,t-1] )^(1/n) * 100

where:
    P_i,t     = current comparable fare
    P_i,t-1   = previous comparable fare
    n         = number of valid comparable observations

Implemented with numerical stability via log-sum:
    ln(GM) = (1/n) * sum(ln(R_i))
    GM     = exp(ln(GM))
    E_t    = GM * 100.0
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import List, Optional, Sequence

from statistical_engine.models.index_result import CalculationStatus


@dataclass(frozen=True)
class JevonsResult:
    """Mathematical result of Jevons elementary calculation."""
    index_value: Optional[float]
    geometric_mean: Optional[float]
    valid_pairs_count: int
    status: CalculationStatus
    error_message: str = ""


def calculate_jevons_index(
    price_relatives: Sequence[float],
    base_value: float = 100.0,
) -> JevonsResult:
    """Calculate Jevons elementary index from a sequence of price relatives.
    
    Args:
        price_relatives: Sequence of valid price relatives (P_i,t / P_i,t-1).
                         Must be strictly positive floats.
        base_value: Index base level (default: 100.0).
        
    Returns:
        JevonsResult containing index value, geometric mean, sample count, and status.
    """
    if not price_relatives:
        return JevonsResult(
            index_value=None,
            geometric_mean=None,
            valid_pairs_count=0,
            status=CalculationStatus.INSUFFICIENT_DATA,
            error_message="No price relatives provided for Jevons calculation",
        )

    valid_relatives: List[float] = []
    for r in price_relatives:
        if not isinstance(r, (int, float)):
            continue
        rf = float(r)
        if math.isnan(rf) or math.isinf(rf) or rf <= 0.0:
            continue
        valid_relatives.append(rf)

    n = len(valid_relatives)
    if n == 0:
        return JevonsResult(
            index_value=None,
            geometric_mean=None,
            valid_pairs_count=0,
            status=CalculationStatus.INSUFFICIENT_DATA,
            error_message="Zero valid strictly positive price relatives found",
        )

    # Numerically stable geometric mean using sum of natural logarithms
    sum_log = sum(math.log(r) for r in valid_relatives)
    mean_log = sum_log / n
    geometric_mean = math.exp(mean_log)

    index_value = geometric_mean * base_value

    return JevonsResult(
        index_value=index_value,
        geometric_mean=geometric_mean,
        valid_pairs_count=n,
        status=CalculationStatus.SUCCESS,
    )
