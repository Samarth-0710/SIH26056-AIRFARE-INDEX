"""Persistence models. These store upstream outputs and never calculate official indices."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class Route(Base):
    __tablename__ = "routes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(7), unique=True, index=True)
    origin: Mapped[str] = mapped_column(String(3))
    destination: Mapped[str] = mapped_column(String(3))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class FareObservation(Base):
    __tablename__ = "fare_observations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id"), index=True)
    observation_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    observation_date: Mapped[date] = mapped_column(Date, index=True)
    travel_date: Mapped[date] = mapped_column(Date)
    booking_window: Mapped[str] = mapped_column(String(4), index=True)
    airline: Mapped[str] = mapped_column(String(20), index=True)
    flight_number: Mapped[str] = mapped_column(String(30))
    departure_time: Mapped[str] = mapped_column(String(20))
    cabin_class: Mapped[str] = mapped_column(String(30))
    fare_type: Mapped[str] = mapped_column(String(50))
    baggage_characteristics: Mapped[str] = mapped_column(String(100))
    base_fare: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    taxes: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    mandatory_charges: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    comparable_fare: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    source: Mapped[str] = mapped_column(String(80), index=True)
    fingerprint: Mapped[str] = mapped_column(String(128), index=True)
    quality_status: Mapped[str] = mapped_column(String(12), index=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    route: Mapped[Route] = relationship()
    __table_args__ = (UniqueConstraint("fingerprint", "observation_timestamp", "source", name="uq_observation_identity"),)


class IndexResult(Base):
    __tablename__ = "index_results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    observation_date: Mapped[date] = mapped_column(Date, index=True)
    booking_window: Mapped[str] = mapped_column(String(4), index=True)
    index_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    status: Mapped[str] = mapped_column(String(30), index=True)
    observation_set_version: Mapped[str] = mapped_column(String(100))
    basket_version: Mapped[str] = mapped_column(String(100))
    weight_version: Mapped[str] = mapped_column(String(100))
    methodology_version: Mapped[str] = mapped_column(String(100))
    calculation_version: Mapped[str] = mapped_column(String(100))
    execution_checksum: Mapped[Optional[str]] = mapped_column(String(128))
    calculation_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    __table_args__ = (UniqueConstraint("observation_date", "booking_window", "calculation_version", name="uq_index_calculation"),)


class RouteIndex(Base):
    __tablename__ = "route_indices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    index_result_id: Mapped[int] = mapped_column(ForeignKey("index_results.id"), index=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id"), index=True)
    index_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    status: Mapped[str] = mapped_column(String(30))
    weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 8))
    contribution: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    route: Mapped[Route] = relationship()


class QualityMetric(Base):
    __tablename__ = "quality_metrics"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    metric_date: Mapped[date] = mapped_column(Date, index=True)
    route_id: Mapped[Optional[int]] = mapped_column(ForeignKey("routes.id"), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    observation_count: Mapped[int] = mapped_column(Integer)
    route_coverage: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4))
    source_coverage: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 4))
    freshness_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    missing_observations: Mapped[int] = mapped_column(Integer, default=0)
    invalid_observations: Mapped[int] = mapped_column(Integer, default=0)
    anomalous_valid_observations: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class IntelligenceEvent(Base):
    __tablename__ = "intelligence_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    route_id: Mapped[Optional[int]] = mapped_column(ForeignKey("routes.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(30), index=True)
    anomaly_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4))
    pressure_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 4))
    shock_status: Mapped[Optional[str]] = mapped_column(String(30))
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    affected_sources: Mapped[list] = mapped_column(JSON, default=list)
    affected_routes: Mapped[list] = mapped_column(JSON, default=list)
    model_version: Mapped[str] = mapped_column(String(100))
    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    route: Mapped[Optional[Route]] = relationship()


class SimulationResult(Base):
    __tablename__ = "simulation_results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id"))
    shock_percent: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    current_index: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    projected_index: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    impact_points: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4))
    status: Mapped[str] = mapped_column(String(30))
    input_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    route: Mapped[Route] = relationship()

Index("ix_route_index_unique_lookup", RouteIndex.index_result_id, RouteIndex.route_id)
