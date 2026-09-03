"""Comparable observation identification and matching for the statistical engine.

Implements fare fingerprinting to strictly pair identical flight/fare characteristics
between period t and period t-1.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Dict, List, Optional, Set, Tuple

from statistical_engine.models.observation import BookingWindow, FareObservation, QualityStatus


def generate_fare_fingerprint(
    obs: FareObservation,
    include_travel_date: bool = False,
) -> str:
    """Generate a deterministic fingerprint hash representing comparable fare dimensions.
    
    Dimensions included:
    - route (origin-destination)
    - booking_window
    - airline
    - flight_number
    - departure_time
    - cabin_class
    - fare_type
    - baggage_characteristics
    
    Note on travel_date:
    In standard price index construction across time periods (e.g. daily index for booking window T+7),
    observation at date t observes a flight departing at t+7, while observation at date t-1 observed a flight
    departing at (t-1)+7. They represent the identical constant-quality service (same flight, same advance window,
    same time slot, same cabin, same fare conditions) tracked across time.
    If include_travel_date is True, the fingerprint strictly matches the exact same travel departure date.
    """
    components = [
        obs.route,
        obs.booking_window.value,
        obs.airline,
        obs.flight_number,
        obs.departure_time,
        obs.cabin_class,
        obs.fare_type,
        obs.baggage_characteristics,
    ]
    if include_travel_date:
        components.append(obs.travel_date.isoformat())

    raw_key = "|".join(components)
    digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]
    return f"{obs.route}_{obs.booking_window.value}_{digest}"


@dataclass(frozen=True)
class MatchedObservationPair:
    """A pair of comparable observations for the same constant-quality service between t and t-1."""
    fingerprint: str
    current_observation: FareObservation
    previous_observation: FareObservation

    @property
    def route(self) -> str:
        return self.current_observation.route

    @property
    def booking_window(self) -> BookingWindow:
        return self.current_observation.booking_window

    @property
    def price_relative(self) -> float:
        return self.current_observation.comparable_fare / self.previous_observation.comparable_fare


@dataclass(frozen=True)
class PairingResult:
    """Result of matching current and previous observations."""
    matched_pairs: List[MatchedObservationPair]
    unmatched_current_count: int
    unmatched_previous_count: int
    duplicate_fingerprints: List[str]
    warnings: List[str]


def match_comparable_pairs(
    current_observations: List[FareObservation],
    previous_observations: List[FareObservation],
    include_travel_date: bool = False,
    allow_suspect: bool = False,
) -> PairingResult:
    """Match current (t) observations with previous (t-1) observations by comparable fingerprint.
    
    Filters:
    - Excludes invalid, zero, negative or excluded quality observations.
    - Deterministically detects and handles duplicate fingerprints within the same period.
    """
    warnings: List[str] = []

    # 1. Filter valid observations
    valid_current: List[FareObservation] = []
    for obs in current_observations:
        if obs.comparable_fare <= 0:
            warnings.append(f"Excluded current observation with non-positive fare: {obs.comparable_fare}")
            continue
        if obs.quality_status == QualityStatus.EXCLUDED or (
            obs.quality_status == QualityStatus.SUSPECT and not allow_suspect
        ):
            continue
        valid_current.append(obs)

    valid_previous: List[FareObservation] = []
    for obs in previous_observations:
        if obs.comparable_fare <= 0:
            warnings.append(f"Excluded previous observation with non-positive fare: {obs.comparable_fare}")
            continue
        if obs.quality_status == QualityStatus.EXCLUDED or (
            obs.quality_status == QualityStatus.SUSPECT and not allow_suspect
        ):
            continue
        valid_previous.append(obs)

    # 2. Index previous observations by fingerprint with duplicate detection
    prev_by_fp: Dict[str, FareObservation] = {}
    prev_duplicates: Set[str] = set()

    for obs in valid_previous:
        fp = generate_fare_fingerprint(obs, include_travel_date=include_travel_date)
        if fp in prev_by_fp:
            prev_duplicates.add(fp)
            warnings.append(f"Duplicate fingerprint in previous observations: {fp}. Keeping earliest/lowest.")
            # Deterministic resolution: choose lowest fare or keep existing
            if obs.comparable_fare < prev_by_fp[fp].comparable_fare:
                prev_by_fp[fp] = obs
        else:
            prev_by_fp[fp] = obs

    # 3. Match current observations
    curr_by_fp: Dict[str, FareObservation] = {}
    curr_duplicates: Set[str] = set()

    for obs in valid_current:
        fp = generate_fare_fingerprint(obs, include_travel_date=include_travel_date)
        if fp in curr_by_fp:
            curr_duplicates.add(fp)
            warnings.append(f"Duplicate fingerprint in current observations: {fp}. Keeping earliest/lowest.")
            if obs.comparable_fare < curr_by_fp[fp].comparable_fare:
                curr_by_fp[fp] = obs
        else:
            curr_by_fp[fp] = obs

    # 4. Form matched pairs deterministically sorted by fingerprint
    matched_pairs: List[MatchedObservationPair] = []
    matched_fps = set(curr_by_fp.keys()).intersection(set(prev_by_fp.keys()))

    for fp in sorted(list(matched_fps)):
        pair = MatchedObservationPair(
            fingerprint=fp,
            current_observation=curr_by_fp[fp],
            previous_observation=prev_by_fp[fp],
        )
        matched_pairs.append(pair)

    unmatched_curr = len(curr_by_fp) - len(matched_pairs)
    unmatched_prev = len(prev_by_fp) - len(matched_pairs)
    all_dupes = sorted(list(prev_duplicates.union(curr_duplicates)))

    return PairingResult(
        matched_pairs=matched_pairs,
        unmatched_current_count=unmatched_curr,
        unmatched_previous_count=unmatched_prev,
        duplicate_fingerprints=all_dupes,
        warnings=warnings,
    )
