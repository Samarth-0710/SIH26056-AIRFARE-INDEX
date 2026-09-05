from typing import Any, Dict, List, Optional


class ShockSeverity:
    """
    Severity levels for detected airfare shocks.
    """

    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ShockStage:
    """
    Progression stages used to explain the evidence behind
    a potential airfare shock.

    These are analytical stages, not official MoSPI/CPI classifications.
    """

    NORMAL = "NORMAL"
    ACCELERATION = "ACCELERATION"
    MULTIPLE_ROUTES = "MULTIPLE_ROUTES"
    CROSS_SOURCE_CONFIRMATION = "CROSS_SOURCE_CONFIRMATION"
    POTENTIAL_AIRFARE_SHOCK = "POTENTIAL_AIRFARE_SHOCK"


class ShockDetector:
    """
    Detects potential airfare shocks from route-level movements.

    This is a supporting intelligence component.
    It does not calculate, replace, or modify the statistical index.

    The detector combines:
        - route-level percentage movement
        - acceleration
        - number of affected routes
        - cross-source confirmation
        - route coverage
        - historical baseline
        - freshness
        - data-quality information

    Thresholds and scoring parameters are implementation choices.
    They are not official MoSPI/CPI thresholds.
    """

    def __init__(
        self,
        low_threshold: float = 5.0,
        medium_threshold: float = 10.0,
        high_threshold: float = 20.0,
        minimum_affected_routes: int = 2,
        minimum_affected_route_ratio: float = 0.5,
        acceleration_threshold: float = 2.0,
        historical_deviation_threshold: float = 5.0,
        minimum_coverage_ratio: float = 0.5,
        maximum_freshness_hours: Optional[float] = 48.0,
    ):
        if low_threshold < 0:
            raise ValueError("low_threshold must be non-negative")

        if medium_threshold < low_threshold:
            raise ValueError(
                "medium_threshold must be >= low_threshold"
            )

        if high_threshold < medium_threshold:
            raise ValueError(
                "high_threshold must be >= medium_threshold"
            )

        if minimum_affected_routes < 1:
            raise ValueError(
                "minimum_affected_routes must be at least 1"
            )

        if not 0 <= minimum_affected_route_ratio <= 1:
            raise ValueError(
                "minimum_affected_route_ratio must be between 0 and 1"
            )

        if acceleration_threshold < 0:
            raise ValueError(
                "acceleration_threshold must be non-negative"
            )

        if historical_deviation_threshold < 0:
            raise ValueError(
                "historical_deviation_threshold must be non-negative"
            )

        if not 0 <= minimum_coverage_ratio <= 1:
            raise ValueError(
                "minimum_coverage_ratio must be between 0 and 1"
            )

        if maximum_freshness_hours is not None:
            if maximum_freshness_hours < 0:
                raise ValueError(
                    "maximum_freshness_hours must be non-negative"
                )

        self.low_threshold = low_threshold
        self.medium_threshold = medium_threshold
        self.high_threshold = high_threshold
        self.minimum_affected_routes = minimum_affected_routes
        self.minimum_affected_route_ratio = (
            minimum_affected_route_ratio
        )
        self.acceleration_threshold = acceleration_threshold
        self.historical_deviation_threshold = (
            historical_deviation_threshold
        )
        self.minimum_coverage_ratio = minimum_coverage_ratio
        self.maximum_freshness_hours = maximum_freshness_hours

    def detect(
        self,
        route_indices: Dict[str, Optional[float]],
        previous_route_indices: Dict[str, Optional[float]],
        *,
        previous_movements: Optional[
            Dict[str, Optional[float]]
        ] = None,
        cross_source_confirmations: Optional[
            List[Dict[str, Any]]
        ] = None,
        coverage_ratio: Optional[float] = None,
        historical_baseline: Optional[
            Dict[str, float]
        ] = None,
        freshness_hours: Optional[float] = None,
        data_quality: Optional[
            Dict[str, Any]
        ] = None,
    ) -> Dict:
        """
        Detect a potential shock from route-level index movements.

        Parameters
        ----------
        route_indices:
            Current route index values.

        previous_route_indices:
            Previous observation's route index values.

        previous_movements:
            Previous route-level percentage movements.

            Used to determine acceleration:

                current movement - previous movement

            The caller must provide chronologically valid information.

        cross_source_confirmations:
            Optional cross-source confirmation results.

            Each result may contain:
                route
                confirmed
                agreement_ratio
                strength

        coverage_ratio:
            Proportion of required route observations available.

        historical_baseline:
            Optional mapping of route -> historical reference index.

            This is used only as an analytical baseline.

        freshness_hours:
            Age of the underlying observations relative to the
            evaluation timestamp.

        data_quality:
            Optional quality information supplied by the upstream
            Data Quality component.

            Supported values include:
                valid
                suspect
                excluded
                outlier

            The detector does not override Data Quality classification.

        Returns
        -------
        Dict
            Explainable shock-analysis result.

        Notes
        -----
        The progression is:

            NORMAL
                ↓
            ACCELERATION
                ↓
            MULTIPLE_ROUTES
                ↓
            CROSS_SOURCE_CONFIRMATION
                ↓
            POTENTIAL_AIRFARE_SHOCK

        Not every stage must be present for a result to be returned.
        The returned stage represents the strongest evidence reached.
        """

        movements = self._calculate_movements(
            route_indices,
            previous_route_indices,
        )

        if not movements:
            return self._insufficient_result()

        self._add_acceleration(
            movements,
            previous_movements,
        )

        self._add_historical_deviation(
            movements,
            historical_baseline,
        )

        self._add_quality_flags(
            movements,
            data_quality,
        )

        affected_routes = [
            movement["route"]
            for movement in movements
            if movement["absolute_change"]
            >= self.low_threshold
        ]

        affected_route_count = len(affected_routes)
        comparable_route_count = len(movements)

        affected_route_ratio = (
            affected_route_count / comparable_route_count
            if comparable_route_count
            else 0.0
        )

        acceleration_routes = [
            movement["route"]
            for movement in movements
            if movement["acceleration"] is not None
            and abs(movement["acceleration"])
            >= self.acceleration_threshold
        ]

        confirmed_routes = self._confirmed_routes(
            cross_source_confirmations
        )

        valid_quality_count = sum(
            1
            for movement in movements
            if movement["quality_status"]
            not in {"EXCLUDED", "OUTLIER"}
        )

        quality_ratio = (
            valid_quality_count / comparable_route_count
            if comparable_route_count
            else 0.0
        )

        average_movement = (
            sum(
                movement["percentage_change"]
                for movement in movements
            )
            / comparable_route_count
        )

        maximum_movement_record = max(
            movements,
            key=lambda movement: movement["absolute_change"],
        )

        maximum_absolute_movement = (
            maximum_movement_record["absolute_change"]
        )

        historical_routes = [
            movement
            for movement in movements
            if movement["historical_deviation"] is not None
        ]

        historical_support = [
            movement["route"]
            for movement in historical_routes
            if movement["historical_deviation_absolute"]
            >= self.historical_deviation_threshold
        ]

        coverage_ok = (
            coverage_ratio is None
            or coverage_ratio >= self.minimum_coverage_ratio
        )

        freshness_ok = (
            freshness_hours is None
            or self.maximum_freshness_hours is None
            or freshness_hours <= self.maximum_freshness_hours
        )

        quality_ok = quality_ratio > 0

        acceleration_detected = bool(acceleration_routes)

        multiple_routes_detected = (
            affected_route_count
            >= self.minimum_affected_routes
            and affected_route_ratio
            >= self.minimum_affected_route_ratio
        )

        cross_source_detected = bool(
            set(confirmed_routes).intersection(affected_routes)
        )

        magnitude_detected = (
            maximum_absolute_movement >= self.low_threshold
        )

        strong_magnitude = (
            maximum_absolute_movement >= self.high_threshold
        )

        # Determine progression stage.

        stage = ShockStage.NORMAL

        if acceleration_detected:
            stage = ShockStage.ACCELERATION

        if multiple_routes_detected:
            stage = ShockStage.MULTIPLE_ROUTES

        if cross_source_detected:
            stage = ShockStage.CROSS_SOURCE_CONFIRMATION

        # A potential shock requires all of the following:
        #   1. meaningful movement
        #   2. multiple affected routes
        #   3. cross-source confirmation
        #   4. explicit coverage information
        #   5. explicit freshness information
        #   6. usable data quality
        #
        # Missing coverage/freshness information must not be silently
        # interpreted as evidence that the data is sufficient.

        potential_shock = (
            magnitude_detected
            and multiple_routes_detected
            and cross_source_detected
            and coverage_ratio is not None
            and freshness_hours is not None
            and coverage_ok
            and freshness_ok
            and quality_ok
        )

        if potential_shock:
            stage = ShockStage.POTENTIAL_AIRFARE_SHOCK

        severity = self._classify_severity(
            maximum_absolute_movement
        )

        # A single-route movement remains an anomaly/supporting signal,
        # but is not automatically classified as a broad airfare shock.
        detected = potential_shock

        if not detected and magnitude_detected:
            severity = self._supporting_severity(
                severity
            )

        direction = self._overall_direction(
            average_movement
        )

        reason = self._build_reason(
            direction=direction,
            stage=stage,
            maximum_movement=maximum_absolute_movement,
            affected_route_count=affected_route_count,
            comparable_route_count=comparable_route_count,
            acceleration_route_count=len(acceleration_routes),
            confirmed_route_count=len(
                set(confirmed_routes).intersection(
                    affected_routes
                )
            ),
            coverage_ratio=coverage_ratio,
            freshness_hours=freshness_hours,
            quality_ratio=quality_ratio,
            historical_support_count=len(historical_support),
        )

        return {
            "detected": detected,
            "severity": severity,
            "stage": stage,
            "average_movement": average_movement,
            "maximum_movement": maximum_absolute_movement,
            "maximum_movement_route": (
                maximum_movement_record["route"]
            ),
            "affected_routes": affected_routes,
            "affected_route_count": affected_route_count,
            "affected_route_ratio": affected_route_ratio,
            "comparable_route_count": comparable_route_count,
            "acceleration_detected": acceleration_detected,
            "acceleration_routes": acceleration_routes,
            "cross_source_confirmed": cross_source_detected,
            "cross_source_confirmed_routes": list(
                set(confirmed_routes).intersection(
                    affected_routes
                )
            ),
            "historical_support_routes": historical_support,
            "coverage_ratio": coverage_ratio,
            "coverage_ok": coverage_ok,
            "freshness_hours": freshness_hours,
            "freshness_ok": freshness_ok,
            "quality_ratio": quality_ratio,
            "quality_ok": quality_ok,
            "movements": movements,
            "reason": reason,
        }

    def _calculate_movements(
        self,
        route_indices: Dict[str, Optional[float]],
        previous_route_indices: Dict[str, Optional[float]],
    ) -> List[Dict]:
        movements: List[Dict] = []

        for route, current_index in route_indices.items():
            previous_index = previous_route_indices.get(route)

            if current_index is None or previous_index is None:
                continue

            try:
                current = float(current_index)
                previous = float(previous_index)
            except (TypeError, ValueError):
                continue

            if current <= 0 or previous <= 0:
                continue

            percentage_change = (
                (current - previous)
                / previous
            ) * 100.0

            movements.append(
                {
                    "route": route,
                    "current_index": current,
                    "previous_index": previous,
                    "percentage_change": percentage_change,
                    "absolute_change": abs(percentage_change),
                    "acceleration": None,
                    "historical_deviation": None,
                    "historical_deviation_absolute": None,
                    "quality_status": "VALID",
                }
            )

        return movements

    def _add_acceleration(
        self,
        movements: List[Dict],
        previous_movements: Optional[
            Dict[str, Optional[float]]
        ],
    ) -> None:
        if previous_movements is None:
            return

        for movement in movements:
            previous_change = previous_movements.get(
                movement["route"]
            )

            if previous_change is None:
                continue

            try:
                previous_change = float(previous_change)
            except (TypeError, ValueError):
                continue

            movement["acceleration"] = (
                movement["percentage_change"]
                - previous_change
            )

    def _add_historical_deviation(
        self,
        movements: List[Dict],
        historical_baseline: Optional[
            Dict[str, float]
        ],
    ) -> None:
        if historical_baseline is None:
            return

        for movement in movements:
            baseline = historical_baseline.get(
                movement["route"]
            )

            if baseline is None:
                continue

            try:
                baseline = float(baseline)
            except (TypeError, ValueError):
                continue

            if baseline <= 0:
                continue

            deviation = (
                (
                    movement["current_index"]
                    - baseline
                )
                / baseline
            ) * 100.0

            movement["historical_deviation"] = deviation
            movement["historical_deviation_absolute"] = (
                abs(deviation)
            )

    def _add_quality_flags(
        self,
        movements: List[Dict],
        data_quality: Optional[
            Dict[str, Any]
        ],
    ) -> None:
        if data_quality is None:
            return

        for movement in movements:
            route = movement["route"]

            quality = data_quality.get(route)

            if quality is None:
                continue

            if isinstance(quality, dict):
                quality = quality.get(
                    "status",
                    "VALID",
                )

            movement["quality_status"] = str(
                quality
            ).upper()

    @staticmethod
    def _confirmed_routes(
        confirmations: Optional[
            List[Dict[str, Any]]
        ],
    ) -> List[str]:
        if not confirmations:
            return []

        routes: List[str] = []

        for confirmation in confirmations:
            if not isinstance(confirmation, dict):
                continue

            if not confirmation.get("confirmed", False):
                continue

            route = confirmation.get("route")

            if route:
                routes.append(str(route))

        return routes

    @staticmethod
    def _overall_direction(
        average_movement: float,
    ) -> str:
        if average_movement > 0:
            return "upward"

        if average_movement < 0:
            return "downward"

        return "stable"

    def _classify_severity(
        self,
        movement: float,
    ) -> str:
        if movement >= self.high_threshold:
            return ShockSeverity.HIGH

        if movement >= self.medium_threshold:
            return ShockSeverity.MEDIUM

        if movement >= self.low_threshold:
            return ShockSeverity.LOW

        return ShockSeverity.NONE

    @staticmethod
    def _supporting_severity(
        severity: str,
    ) -> str:
        """
        Preserve magnitude information without claiming that a
        single-route event is a broad shock.
        """

        return severity

    @staticmethod
    def _insufficient_result() -> Dict:
        return {
            "detected": False,
            "severity": ShockSeverity.NONE,
            "stage": ShockStage.NORMAL,
            "average_movement": None,
            "maximum_movement": None,
            "maximum_movement_route": None,
            "affected_routes": [],
            "affected_route_count": 0,
            "affected_route_ratio": 0.0,
            "comparable_route_count": 0,
            "acceleration_detected": False,
            "acceleration_routes": [],
            "cross_source_confirmed": False,
            "cross_source_confirmed_routes": [],
            "historical_support_routes": [],
            "coverage_ratio": None,
            "coverage_ok": False,
            "freshness_hours": None,
            "freshness_ok": False,
            "quality_ratio": 0.0,
            "quality_ok": False,
            "movements": [],
            "reason": (
                "Insufficient comparable route-level data "
                "for shock detection."
            ),
        }

    def _build_reason(
        self,
        *,
        direction: str,
        stage: str,
        maximum_movement: float,
        affected_route_count: int,
        comparable_route_count: int,
        acceleration_route_count: int,
        confirmed_route_count: int,
        coverage_ratio: Optional[float],
        freshness_hours: Optional[float],
        quality_ratio: float,
        historical_support_count: int,
    ) -> str:
        parts = [
            f"Overall movement was {direction}.",
            (
                f"Maximum route movement was "
                f"{maximum_movement:.2f}%."
            ),
            (
                f"{affected_route_count} of "
                f"{comparable_route_count} comparable routes "
                f"met the movement threshold."
            ),
        ]

        if acceleration_route_count:
            parts.append(
                f"Acceleration was observed on "
                f"{acceleration_route_count} route(s)."
            )

        if confirmed_route_count:
            parts.append(
                f"Cross-source confirmation was available "
                f"for {confirmed_route_count} affected route(s)."
            )

        if historical_support_count:
            parts.append(
                f"{historical_support_count} route(s) also "
                f"deviated materially from the supplied "
                f"historical baseline."
            )

        if coverage_ratio is not None:
            parts.append(
                f"Coverage ratio was {coverage_ratio:.2f}."
            )

        if freshness_hours is not None:
            parts.append(
                f"Observation freshness was "
                f"{freshness_hours:.2f} hour(s)."
            )

        parts.append(
            f"Usable data-quality ratio was "
            f"{quality_ratio:.2f}."
        )

        parts.append(
            f"Evidence stage: {stage}."
        )

        if stage != ShockStage.POTENTIAL_AIRFARE_SHOCK:
            parts.append(
                "The evidence is treated as a supporting "
                "intelligence signal rather than an official "
                "airfare-shock classification."
            )

        return " ".join(parts)