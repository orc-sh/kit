"""
Load test run model for storing individual load test execution instances.
"""

from sqlalchemy import TIMESTAMP, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class LoadTestRun(Base):
    __tablename__ = "load_test_runs"

    id = Column(String(36), primary_key=True)
    load_test_configuration_id = Column(
        String(36), ForeignKey("load_test_configurations.id", ondelete="CASCADE"), nullable=False
    )

    # Test status
    status = Column(String(50), nullable=False, default="pending")  # pending, running, completed, failed, cancelled

    # Timestamps
    started_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    configuration = relationship("LoadTestConfiguration", back_populates="runs")
    reports = relationship("LoadTestReport", back_populates="run", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_load_test_runs_config_id", "load_test_configuration_id"),
        Index("idx_load_test_runs_status", "status"),
        Index("idx_load_test_runs_created_at", "created_at"),
    )
