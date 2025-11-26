"""
Load test report model for storing aggregated results/metrics for each run.
"""

from sqlalchemy import TIMESTAMP, Column, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class LoadTestReport(Base):
    __tablename__ = "load_test_reports"

    id = Column(String(36), primary_key=True)
    load_test_run_id = Column(String(36), ForeignKey("load_test_runs.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=True)  # Optional report name

    # Results summary
    total_requests = Column(Integer, nullable=False, default=0)
    successful_requests = Column(Integer, nullable=False, default=0)
    failed_requests = Column(Integer, nullable=False, default=0)
    avg_response_time_ms = Column(Integer, nullable=True)
    min_response_time_ms = Column(Integer, nullable=True)
    max_response_time_ms = Column(Integer, nullable=True)
    p95_response_time_ms = Column(Integer, nullable=True)
    p99_response_time_ms = Column(Integer, nullable=True)

    # Additional metadata
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    run = relationship("LoadTestRun", back_populates="reports")
    results = relationship("LoadTestResult", back_populates="report", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_load_test_reports_run_id", "load_test_run_id"),
        Index("idx_load_test_reports_created_at", "created_at"),
    )
