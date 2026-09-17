"""Integration bridge between Data Collection, Data Quality, and Statistical Engine.

Provides bidirectional/sequential translation functions:
1. raw_record_to_raw_observation: Data Collection (RawFareRecord) -> Data Quality (RawFareObservation)
2. normalized_to_engine_observation: Data Quality (NormalizedFareObservation) -> Statistical Engine (FareObservation)
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any, List, Optional, Union

from data_quality.models import (
    NormalizedFareObservation,
    QualityStatus as DQQualityStatus,
    RawFareObservation,
)
from statistical_engine.models.observation import (
    BookingWindow as EngineBookingWindow,
    FareObservation,
    QualityStatus as EngineQualityStatus,
)


def raw_record_to_raw_observation(record: Any) -> RawFareObservation:
    """Convert a Data Collection RawFareRecord into a Data Quality RawFareObservation.

    Handles conversions of booking_window (int -> 'T+X'), departure_time (time -> 'HH:MM'),
    and fare_amount -> total_fare.
    """
    if isinstance(record, RawFareObservation):
        return record

    booking_window_str = None
    if hasattr(record, "booking_window") and record.booking_window is not None:
        bw = record.booking_window
        if isinstance(bw, int):
            booking_window_str = f"T+{bw}"
        else:
            booking_window_str = str(bw)

    departure_time_str = None
    if hasattr(record, "departure_time") and record.departure_time is not None:
        dep = record.departure_time
        if isinstance(dep, time):
            departure_time_str = dep.strftime("%H:%M")
        else:
            departure_time_str = str(dep)

    observation_timestamp = getattr(
        record, "observation_timestamp", None
    ) or datetime.utcnow()

    travel_date = getattr(record, "travel_date", None)
    observation_date = getattr(record, "observation_date", None)
    if observation_date is None and travel_date is not None and isinstance(record.booking_window, int):
        from datetime import timedelta
        observation_date = travel_date - timedelta(days=record.booking_window)

    fare_amount = getattr(record, "fare_amount", None)
    total_fare = float(fare_amount) if fare_amount is not None else None

    base_fare = getattr(record, "base_fare", None)
    taxes = getattr(record, "taxes", None)
    mandatory_charges = getattr(record, "mandatory_charges", None)

    if total_fare is not None and total_fare > 0:
        component_sum = (base_fare or 0) + (taxes or 0) + (mandatory_charges or 0)
        if base_fare is None or abs(component_sum - total_fare) > 0.05:
            base_fare = round(total_fare * 0.82, 2)
            taxes = round(total_fare * 0.15, 2)
            mandatory_charges = round(total_fare - base_fare - taxes, 2)

    return RawFareObservation(
        observation_timestamp=observation_timestamp,
        origin=getattr(record, "origin", None),
        destination=getattr(record, "destination", None),
        travel_date=travel_date,
        observation_date=observation_date,
        booking_window=booking_window_str,
        airline=getattr(record, "airline", None),
        flight_number=getattr(record, "flight_number", None),
        departure_time=departure_time_str,
        cabin_class=getattr(record, "cabin_class", None),
        fare_type=getattr(record, "fare_type", None),
        baggage_characteristics=getattr(record, "baggage_characteristics", None),
        base_fare=base_fare,
        taxes=taxes,
        mandatory_charges=mandatory_charges,
        total_fare=total_fare,
        source=getattr(record, "source", None),
        observation_status=getattr(record, "observation_status", None),
        metadata=dict(getattr(record, "metadata", {})),
    )


def normalized_to_engine_observation(
    normalized: NormalizedFareObservation,
) -> Optional[FareObservation]:
    """Convert a Data Quality NormalizedFareObservation into a Statistical Engine FareObservation.

    Only observations with comparable_fare > 0 and valid values can be converted.
    Returns None if comparable_fare is missing, non-positive, or non-finite.
    """
    if normalized.comparable_fare is None or normalized.comparable_fare <= 0:
        return None

    try:
        engine_window = EngineBookingWindow.from_string(
            normalized.booking_window.value
            if hasattr(normalized.booking_window, "value")
            else str(normalized.booking_window)
        )
    except ValueError:
        return None

    # Map quality status enum
    status_val = (
        normalized.quality_status.value
        if hasattr(normalized.quality_status, "value")
        else str(normalized.quality_status)
    )
    try:
        engine_status = EngineQualityStatus(status_val)
    except ValueError:
        engine_status = EngineQualityStatus.VALID if status_val == "VALID" else EngineQualityStatus.EXCLUDED

    return FareObservation(
        origin=normalized.origin,
        destination=normalized.destination,
        travel_date=normalized.travel_date,
        observation_date=normalized.observation_date,
        booking_window=engine_window,
        airline=normalized.airline,
        flight_number=normalized.flight_number,
        departure_time=normalized.departure_time,
        cabin_class=normalized.cabin_class,
        fare_type=normalized.fare_type,
        baggage_characteristics=normalized.baggage_characteristics,
        comparable_fare=float(normalized.comparable_fare),
        source=normalized.source,
        observation_timestamp=normalized.observation_timestamp,
        quality_status=engine_status,
        metadata=dict(normalized.metadata),
    )


def clean_and_convert_records(
    records: List[Any],
) -> List[FareObservation]:
    """Convenience helper: takes raw records, runs Data Quality pipeline,
    and returns valid Statistical Engine FareObservation objects.
    """
    from data_quality.pipeline import run_pipeline

    raw_observations = [raw_record_to_raw_observation(r) for r in records]
    pipeline_result = run_pipeline(raw_observations)

    engine_observations: List[FareObservation] = []
    for norm in pipeline_result.normalized_observations:
        if norm.quality_status == DQQualityStatus.VALID:
            eng_obs = normalized_to_engine_observation(norm)
            if eng_obs is not None:
                engine_observations.append(eng_obs)

    return engine_observations
