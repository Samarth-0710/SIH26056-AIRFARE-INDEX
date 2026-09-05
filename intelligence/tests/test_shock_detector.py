from intelligence.shocks.detector import (
    ShockDetector,
    ShockSeverity,
    ShockStage,
)


def test_no_comparable_data():
    detector = ShockDetector()

    result = detector.detect(
        {"DEL-BOM": None},
        {"DEL-BOM": 100.0},
    )

    assert result["detected"] is False
    assert result["severity"] == ShockSeverity.NONE
    assert result["stage"] == ShockStage.NORMAL


def test_single_route_large_movement_is_not_broad_shock():
    detector = ShockDetector()

    result = detector.detect(
        {"DEL-BOM": 125.0},
        {"DEL-BOM": 100.0},
    )

    assert result["maximum_movement"] == 25.0
    assert result["severity"] == ShockSeverity.HIGH

    # A single route does not satisfy the broad-shock condition.
    assert result["detected"] is False


def test_acceleration_stage():
    detector = ShockDetector(
        acceleration_threshold=2.0,
    )

    result = detector.detect(
        {"DEL-BOM": 110.0},
        {"DEL-BOM": 105.0},
        previous_movements={
            "DEL-BOM": 2.0,
        },
    )

    assert result["acceleration_detected"] is True
    assert "DEL-BOM" in result["acceleration_routes"]
    assert result["stage"] == ShockStage.ACCELERATION


def test_multiple_routes_stage():
    detector = ShockDetector(
        minimum_affected_routes=2,
        minimum_affected_route_ratio=0.5,
    )

    result = detector.detect(
        {
            "DEL-BOM": 110.0,
            "DEL-BLR": 112.0,
            "BOM-BLR": 101.0,
            "DEL-CCU": 100.0,
        },
        {
            "DEL-BOM": 100.0,
            "DEL-BLR": 100.0,
            "BOM-BLR": 100.0,
            "DEL-CCU": 100.0,
        },
    )

    assert result["affected_route_count"] == 2
    assert result["affected_route_ratio"] == 0.5
    assert result["stage"] == ShockStage.MULTIPLE_ROUTES


def test_cross_source_confirmation_stage():
    detector = ShockDetector()

    result = detector.detect(
        {
            "DEL-BOM": 110.0,
            "DEL-BLR": 112.0,
        },
        {
            "DEL-BOM": 100.0,
            "DEL-BLR": 100.0,
        },
        cross_source_confirmations=[
            {
                "route": "DEL-BOM",
                "confirmed": True,
                "agreement_ratio": 1.0,
            },
            {
                "route": "DEL-BLR",
                "confirmed": True,
                "agreement_ratio": 0.75,
            },
        ],
    )

    assert result["cross_source_confirmed"] is True
    assert set(
        result["cross_source_confirmed_routes"]
    ) == {"DEL-BOM", "DEL-BLR"}

    assert (
        result["stage"]
        == ShockStage.CROSS_SOURCE_CONFIRMATION
    )


def test_potential_airfare_shock_requires_multiple_signals():
    detector = ShockDetector(
        minimum_affected_routes=2,
        minimum_affected_route_ratio=0.5,
        acceleration_threshold=2.0,
    )

    result = detector.detect(
        {
            "DEL-BOM": 115.0,
            "DEL-BLR": 112.0,
            "BOM-BLR": 101.0,
            "DEL-CCU": 100.0,
        },
        {
            "DEL-BOM": 100.0,
            "DEL-BLR": 100.0,
            "BOM-BLR": 100.0,
            "DEL-CCU": 100.0,
        },
        previous_movements={
            "DEL-BOM": 5.0,
            "DEL-BLR": 3.0,
        },
        cross_source_confirmations=[
            {
                "route": "DEL-BOM",
                "confirmed": True,
                "agreement_ratio": 1.0,
            },
            {
                "route": "DEL-BLR",
                "confirmed": True,
                "agreement_ratio": 0.75,
            },
        ],
        coverage_ratio=1.0,
        freshness_hours=2.0,
    )

    assert result["detected"] is True
    assert (
        result["stage"]
        == ShockStage.POTENTIAL_AIRFARE_SHOCK
    )


def test_historical_baseline_support():
    detector = ShockDetector()

    result = detector.detect(
        {"DEL-BOM": 110.0},
        {"DEL-BOM": 100.0},
        historical_baseline={
            "DEL-BOM": 100.0,
        },
    )

    assert result["historical_support_routes"] == [
        "DEL-BOM"
    ]


def test_coverage_and_freshness_are_reported():
    detector = ShockDetector()

    result = detector.detect(
        {
            "DEL-BOM": 110.0,
            "DEL-BLR": 110.0,
        },
        {
            "DEL-BOM": 100.0,
            "DEL-BLR": 100.0,
        },
        coverage_ratio=0.75,
        freshness_hours=6.0,
    )

    assert result["coverage_ratio"] == 0.75
    assert result["coverage_ok"] is True
    assert result["freshness_hours"] == 6.0
    assert result["freshness_ok"] is True


def test_data_quality_is_not_overridden():
    detector = ShockDetector()

    result = detector.detect(
        {
            "DEL-BOM": 110.0,
            "DEL-BLR": 110.0,
        },
        {
            "DEL-BOM": 100.0,
            "DEL-BLR": 100.0,
        },
        data_quality={
            "DEL-BOM": "VALID",
            "DEL-BLR": "OUTLIER",
        },
    )

    assert result["quality_ratio"] == 0.5

    # The intelligence layer records the quality information.
    # It does not silently convert or delete the observation.
    assert result["movements"][1]["quality_status"] == "OUTLIER"


def test_downward_movement():
    detector = ShockDetector()

    result = detector.detect(
        {"DEL-BOM": 80.0},
        {"DEL-BOM": 100.0},
    )

    assert result["average_movement"] == -20.0
    assert result["maximum_movement"] == 20.0
    assert result["detected"] is False
    assert result["severity"] == ShockSeverity.HIGH


def test_invalid_configuration():
    try:
        ShockDetector(
            low_threshold=10.0,
            medium_threshold=5.0,
        )
        assert False
    except ValueError:
        assert True