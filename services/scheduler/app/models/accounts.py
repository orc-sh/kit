from sqlalchemy import TIMESTAMP, Column, Index, String
from sqlalchemy.sql import func

from .base import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    __table_args__ = (Index("idx_accounts_user_id", "user_id"),)
