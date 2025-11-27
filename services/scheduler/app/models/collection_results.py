"""
Collection result model for storing individual request results from collections.
"""

from sqlalchemy import JSON, TIMESTAMP, Column, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class CollectionResult(Base):
    __tablename__ = "collection_results"

    id = Column(String(36), primary_key=True)
    collection_report_id = Column(String(36), ForeignKey("collection_reports.id", ondelete="CASCADE"), nullable=False)

    # Request details
    endpoint_path = Column(String(512), nullable=False)
    method = Column(String(10), nullable=False)
    request_headers = Column(JSON, nullable=True)
    request_body = Column(Text, nullable=True)

    # Response details
    response_status = Column(Integer, nullable=True)
    response_headers = Column(JSON, nullable=True)
    response_body = Column(Text, nullable=True)
    response_time_ms = Column(Integer, nullable=False)

    # Error information
    error_message = Column(Text, nullable=True)
    is_success = Column(Integer, nullable=False, default=1)  # 1 for success, 0 for failure

    # Timing
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    # Relationships
    report = relationship("CollectionReport", back_populates="results")

    __table_args__ = (
        Index("idx_collection_results_report_id", "collection_report_id"),
        Index("idx_collection_results_created_at", "created_at"),
        Index("idx_collection_results_is_success", "is_success"),
    )
