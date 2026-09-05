from datetime import date

from intelligence.cross_source.confirmer import CrossSourceConfirmer
from intelligence.models.result import IntelligenceStatus


def make_observation(
    source,
    fare,
    observation_date=date(2026, 8, 30),
):
    return {
        "origin": "DEL",
        "destination": "BOM",
        "booking_window": "T+7",
        "observation_date": observation_date,
        "source": source,
        "comparable_fare": fare,
    }


def test_cross_source_confirms_upward_movement():
    confirmer = CrossSourceConfirmer()

    previous = [
        make_observation("INDIGO", 5000),
        make_observation("AIR INDIA", 5000),
        make_observation("MAKEMYTRIP", 5000),
    ]

    current = [
        make_observation("INDIGO", 5400),
        make_observation("AIR INDIA", 5350),
        make_observation("MAKEMYTRIP", 5500),
    ]

    results = confirmer.confirm(current, previous)

    assert len(results) == 1

    result = results[0]

    assert result.route == "DEL-BOM"
    assert result.booking_window == "T+7"
    assert result.source_count == 3
    assert result.direction == "UPWARD"
    assert result.confirmed is True
    assert result.strength == "STRONG"
    assert result.status == IntelligenceStatus.SUCCESS


def test_cross_source_confirms_downward_movement():
    confirmer = CrossSourceConfirmer()

    previous = [
        make_observation("INDIGO", 6000),
        make_observation("AIR INDIA", 6000),
        make_observation("YATRA", 6000),
    ]

    current = [
        make_observation("INDIGO", 5400),
        make_observation("AIR INDIA", 5500),
        make_observation("YATRA", 5300),
    ]

    results = confirmer.confirm(current, previous)

    result = results[0]

    assert result.direction == "DOWNWARD"
    assert result.confirmed is True
    assert result.source_count == 3


def test_cross_source_does_not_confirm_with_one_source():
    confirmer = CrossSourceConfirmer()

    previous = [
        make_observation("INDIGO", 5000),
    ]

    current = [
        make_observation("INDIGO", 5500),
    ]

    results = confirmer.confirm(current, previous)

    assert len(results) == 1

    result = results[0]

    assert result.confirmed is False
    assert result.strength == "INSUFFICIENT"
    assert result.status == IntelligenceStatus.INSUFFICIENT_DATA


def test_cross_source_detects_mixed_direction():
    confirmer = CrossSourceConfirmer()

    previous = [
        make_observation("INDIGO", 5000),
        make_observation("AIR INDIA", 5000),
        make_observation("YATRA", 5000),
        make_observation("CLEARTRIP", 5000),
    ]

    current = [
        make_observation("INDIGO", 5500),
        make_observation("AIR INDIA", 5400),
        make_observation("YATRA", 5500),
        make_observation("CLEARTRIP", 4900),
    ]

    results = confirmer.confirm(current, previous)

    result = results[0]

    assert result.source_count == 4
    assert result.direction == "UPWARD"
    assert result.agreement_ratio == 0.75
    assert result.confirmed is True
    assert result.strength == "STRONG"


def test_cross_source_ignores_invalid_fares():
    confirmer = CrossSourceConfirmer()

    previous = [
        make_observation("INDIGO", 5000),
        make_observation("AIR INDIA", 5000),
        make_observation("YATRA", 5000),
    ]

    current = [
        make_observation("INDIGO", 5500),
        make_observation("AIR INDIA", None),
        make_observation("YATRA", 5400),
    ]

    results = confirmer.confirm(current, previous)

    result = results[0]

    assert result.source_count == 2
    assert result.confirmed is True
    assert result.direction == "UPWARD"


def test_cross_source_returns_empty_when_no_matching_previous_data():
    confirmer = CrossSourceConfirmer()

    current = [
        make_observation("INDIGO", 5500),
        make_observation("AIR INDIA", 5600),
    ]

    previous = []

    results = confirmer.confirm(current, previous)

    assert results == []


def test_cross_source_to_dict():
    confirmer = CrossSourceConfirmer()

    previous = [
        make_observation("INDIGO", 5000),
        make_observation("AIR INDIA", 5000),
    ]

    current = [
        make_observation("INDIGO", 5500),
        make_observation("AIR INDIA", 5400),
    ]

    result = confirmer.confirm(current, previous)[0]

    data = result.to_dict()

    assert data["route"] == "DEL-BOM"
    assert data["booking_window"] == "T+7"
    assert data["source_count"] == 2
    assert data["confirmed"] is True
    assert "agreement_ratio" in data