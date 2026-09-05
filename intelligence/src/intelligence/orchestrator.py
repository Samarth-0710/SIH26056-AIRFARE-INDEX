from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from intelligence.anomaly.detector import AnomalyDetector
from intelligence.explainability.explainer import AnomalyExplainer
from intelligence.patterns.detector import PatternDetector
from intelligence.shocks.detector import ShockDetector
from intelligence.cross_source.confirmer import CrossSourceConfirmer
from intelligence.pressure.scorer import AirfarePressureScorer
from intelligence.confidence.scorer import ConfidenceSupportScorer
from intelligence.missing_data.supporter import MissingDataSupporter

from intelligence.models.result import (
    AnomalyResult,
    IntelligenceOutput,
    IntelligenceProvenance,
    IntelligenceStatus,
)


class IntelligenceOrchestrator:
    """
    Coordinates the supporting intelligence components.

    The Statistical Engine remains responsible for calculating
    the official airfare price index.

    This class only analyses statistical-engine results and,
    when supplied, normalized fare observations.

    Intelligence signals do not modify the official index.
    """

    def __init__(
        self,
        anomaly_detector: Optional[AnomalyDetector] = None,
        pattern_detector: Optional[PatternDetector] = None,
        shock_detector: Optional[ShockDetector] = None,
        explainer: Optional[AnomalyExplainer] = None,
        cross_source_confirmer: Optional[CrossSourceConfirmer] = None,
        pressure_scorer: Optional[AirfarePressureScorer] = None,
        confidence_scorer: Optional[ConfidenceSupportScorer] = None,
        missing_data_supporter: Optional[MissingDataSupporter] = None,
    ):
        self.anomaly_detector = (
            anomaly_detector or AnomalyDetector()
        )

        self.pattern_detector = (
            pattern_detector or PatternDetector()
        )

        self.shock_detector = (
            shock_detector or ShockDetector()
        )

        self.explainer = (
            explainer or AnomalyExplainer()
        )

        self.cross_source_confirmer = (
            cross_source_confirmer or CrossSourceConfirmer()
        )

        self.pressure_scorer = (
            pressure_scorer or AirfarePressureScorer()
        )

        self.confidence_scorer = (
            confidence_scorer or ConfidenceSupportScorer()
        )

        self.missing_data_supporter = (
            missing_data_supporter or MissingDataSupporter()
        )

    def analyze(
        self,
        observation_date: str,
        current_route_indices: Dict[str, float],
        previous_route_indices: Dict[str, float],
        historical_route_indices: Optional[
            Dict[str, List[float]]
        ] = None,
        booking_window: str = "T+7",
        current_observations: Optional[List[Any]] = None,
        previous_observations: Optional[List[Any]] = None,
        coverage_ratio: Optional[float] = None,
        missing_route_fares: Optional[
            Dict[str, List[float]]
        ] = None,
        previous_movements: Optional[
            Dict[str, Optional[float]]
        ] = None,
        historical_baseline: Optional[
            Dict[str, float]
        ] = None,
        freshness_hours: Optional[float] = None,
        data_quality: Optional[
            Dict[str, Any]
        ] = None,
    ) -> IntelligenceOutput:
        """
        Run the complete supporting intelligence pipeline.

        Existing route-index inputs remain compatible with the
        original orchestrator interface.

        Optional normalized fare observations enable:
        - cross-source confirmation
        - supporting missing-data estimation

        Additional optional inputs enable the enhanced shock detector:
        - previous route movements
        - historical route baselines
        - freshness
        - data-quality information
        - coverage

        The Intelligence layer does not modify or replace the
        Statistical Engine's official index.
        """

        anomalies: List[AnomalyResult] = []

        # ---------------------------------------------------------
        # 1. Route-level anomaly detection
        # ---------------------------------------------------------

        for route, current_index in current_route_indices.items():

            previous_index = previous_route_indices.get(route)

            result = self.anomaly_detector.detect(
                route=route,
                booking_window=booking_window,
                current_index=current_index,
                previous_index=previous_index,
            )

            if result.detected:
                explanation = self.explainer.explain(result)

                result = AnomalyResult(
                    route=result.route,
                    booking_window=result.booking_window,
                    current_index=result.current_index,
                    previous_index=result.previous_index,
                    point_change=result.point_change,
                    percentage_change=result.percentage_change,
                    anomaly_score=result.anomaly_score,
                    severity=result.severity,
                    detected=result.detected,
                    reason=explanation,
                    status=result.status,
                    warnings=result.warnings,
                )

            anomalies.append(result)

        # ---------------------------------------------------------
        # 2. Pattern detection
        # ---------------------------------------------------------

        pattern_results = {}

        if historical_route_indices:

            for route, index_values in historical_route_indices.items():

                pattern_results[route] = (
                    self.pattern_detector.detect(
                        route=route,
                        booking_window=booking_window,
                        index_values=index_values,
                    )
                )

        # ---------------------------------------------------------
        # 3. Cross-source confirmation
        # ---------------------------------------------------------

        cross_source_results = []

        if (
            current_observations is not None
            and previous_observations is not None
        ):
            cross_source_results = (
                self.cross_source_confirmer.confirm(
                    current_observations=current_observations,
                    previous_observations=previous_observations,
                )
            )

        # ---------------------------------------------------------
        # 4. Shock detection
        # ---------------------------------------------------------

        shock_result = self.shock_detector.detect(
            route_indices=current_route_indices,
            previous_route_indices=previous_route_indices,
            previous_movements=previous_movements,
            cross_source_confirmations=[
                result.to_dict()
                for result in cross_source_results
            ],
            coverage_ratio=coverage_ratio,
            historical_baseline=historical_baseline,
            freshness_hours=freshness_hours,
            data_quality=data_quality,
        )

        # ---------------------------------------------------------
        # 5. Airfare pressure score
        # ---------------------------------------------------------

        pressure_results = {}

        for anomaly in anomalies:

            agreement_ratio = None

            for confirmation in cross_source_results:
                if (
                    confirmation.route == anomaly.route
                    and confirmation.booking_window
                    == anomaly.booking_window
                ):
                    agreement_ratio = (
                        confirmation.agreement_ratio
                    )
                    break

            pressure_results[anomaly.route] = (
                self.pressure_scorer.calculate(
                    route=anomaly.route,
                    booking_window=booking_window,
                    percentage_change=anomaly.percentage_change,
                    anomaly_score=anomaly.anomaly_score,
                    cross_source_agreement=agreement_ratio,
                ).to_dict()
            )

        # ---------------------------------------------------------
        # 6. Confidence support
        # ---------------------------------------------------------

        confidence_results = {}

        for anomaly in anomalies:

            agreement_ratio = None

            for confirmation in cross_source_results:
                if (
                    confirmation.route == anomaly.route
                    and confirmation.booking_window
                    == anomaly.booking_window
                ):
                    agreement_ratio = (
                        confirmation.agreement_ratio
                    )
                    break

            route_data_quality = None

            if isinstance(data_quality, dict):
                candidate_quality = (
                    data_quality.get(anomaly.route)
                )

                if isinstance(candidate_quality, (int, float)):
                    route_data_quality = float(
                        candidate_quality
                    )

                elif isinstance(candidate_quality, dict):
                    for key in (
                        "quality_score",
                        "data_quality",
                        "score",
                    ):
                        value = candidate_quality.get(key)

                        if isinstance(value, (int, float)):
                            route_data_quality = float(value)
                            break

            observation_count = None

            if current_observations is not None:
                observation_count = len(
                    current_observations
                )

            confidence_results[anomaly.route] = (
                self.confidence_scorer.calculate(
                    route=anomaly.route,
                    booking_window=booking_window,
                    coverage_ratio=coverage_ratio,
                    cross_source_agreement=agreement_ratio,
                    anomaly_available=(
                        anomaly.percentage_change is not None
                    ),
                    observation_count=observation_count,
                    expected_observation_count=None,
                    data_quality=route_data_quality,
                    freshness_hours=freshness_hours,
                ).to_dict()
            )

        # ---------------------------------------------------------
        # 7. Missing-data support
        # ---------------------------------------------------------

        missing_data_results = {}

        if missing_route_fares:

            for route, fares in missing_route_fares.items():

                missing_data_results[route] = (
                    self.missing_data_supporter.estimate(
                        route=route,
                        booking_window=booking_window,
                        comparable_fares=fares,
                    ).to_dict()
                )

        # ---------------------------------------------------------
        # 8. Unified metadata
        # ---------------------------------------------------------

        metadata = {
            "booking_window": booking_window,

            "patterns": pattern_results,

            "shock": shock_result,

            "cross_source_confirmation": [
                result.to_dict()
                for result in cross_source_results
            ],

            "pressure_scores": pressure_results,

            "confidence_support": confidence_results,

            "missing_data_support": missing_data_results,
        }

        # ---------------------------------------------------------
        # 9. Intelligence provenance
        # ---------------------------------------------------------
        #
        # The current Intelligence implementation is primarily
        # deterministic/rule-based. Therefore no training dataset
        # is claimed.
        #
        # Reference dataset information will be populated only
        # when an actual versioned reference dataset is supplied.
        #
        # Component names are recorded for reproducibility without
        # inventing undocumented threshold/configuration values.
        # ---------------------------------------------------------

        generated_at = datetime.now(
            timezone.utc
        ).isoformat()

        provenance = IntelligenceProvenance(
            model_version="intelligence-rules-v1",
            feature_version="features-v1",
            training_dataset_version="NOT_APPLICABLE",
            reference_dataset_version="NOT_APPLICABLE",
            generated_at=generated_at,
            configuration={
                "anomaly_detector": (
                    type(self.anomaly_detector).__name__
                ),
                "pattern_detector": (
                    type(self.pattern_detector).__name__
                ),
                "shock_detector": (
                    type(self.shock_detector).__name__
                ),
                "cross_source_confirmer": (
                    type(
                        self.cross_source_confirmer
                    ).__name__
                ),
                "pressure_scorer": (
                    type(self.pressure_scorer).__name__
                ),
                "confidence_scorer": (
                    type(self.confidence_scorer).__name__
                ),
                "missing_data_supporter": (
                    type(
                        self.missing_data_supporter
                    ).__name__
                ),
            },
        )

        # ---------------------------------------------------------
        # 10. Construct unified Intelligence output
        # ---------------------------------------------------------

        return IntelligenceOutput(
            observation_date=observation_date,
            anomalies=anomalies,
            status=IntelligenceStatus.SUCCESS,
            warnings=[],
            metadata=metadata,
            provenance=provenance,
        )