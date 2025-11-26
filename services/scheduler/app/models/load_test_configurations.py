"""
Load test configuration model for storing load test templates/configurations.
"""

from sqlalchemy import TIMESTAMP, Column, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class LoadTestConfiguration(Base):
    __tablename__ = "load_test_configurations"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    webhook_id = Column(String(36), ForeignKey("webhooks.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)

    # Load test parameters (configuration)
    concurrent_users = Column(Integer, nullable=False, default=10)
    duration_seconds = Column(Integer, nullable=False, default=60)
    requests_per_second = Column(Integer, nullable=True)  # Optional rate limiting

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # Relationships
    webhook = relationship("Webhook", foreign_keys=[webhook_id])
    runs = relationship("LoadTestRun", back_populates="configuration", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_load_test_configs_project_id", "project_id"),
        Index("idx_load_test_configs_webhook_id", "webhook_id"),
        Index("idx_load_test_configs_created_at", "created_at"),
    )
