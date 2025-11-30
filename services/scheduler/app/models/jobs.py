from sqlalchemy import TIMESTAMP, Boolean, Column, ForeignKey, Index, Integer, String
from sqlalchemy.sql import func

from .base import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True)
    account_id = Column(String(36), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    schedule = Column(String(50), nullable=False)  # cron string
    type = Column(Integer, nullable=False)
    timezone = Column(String(50), server_default="UTC")
    enabled = Column(Boolean, server_default="1")
    last_run_at = Column(TIMESTAMP, nullable=True)
    next_run_at = Column(TIMESTAMP, nullable=False)  # precomputed cron
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    __table_args__ = (
        Index("idx_jobs_account_id", "account_id"),
        Index("idx_jobs_next_run_at", "next_run_at"),
        Index("idx_jobs_enabled", "enabled"),
    )
