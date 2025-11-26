"""add_notifications_table

Revision ID: add_notifications_table
Revises: ae5fd0efc627
Create Date: 2025-11-26 12:23:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_notifications_table"
down_revision: Union[str, None] = "ae5fd0efc627"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create notifications table
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("project_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column(
            "type",
            sa.Enum("email", "slack", "discord", "webhook", name="notification_type"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("enabled", sa.String(10), nullable=False, server_default="true"),
        sa.Column("config", sa.Text(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_notifications_project_id", "notifications", ["project_id"])
    op.create_index("idx_notifications_user_id", "notifications", ["user_id"])
    op.create_index("idx_notifications_type", "notifications", ["type"])


def downgrade() -> None:
    op.drop_index("idx_notifications_type", table_name="notifications")
    op.drop_index("idx_notifications_user_id", table_name="notifications")
    op.drop_index("idx_notifications_project_id", table_name="notifications")
    op.drop_table("notifications")
    # Drop the enum type
    op.execute("DROP TYPE IF EXISTS notification_type")
