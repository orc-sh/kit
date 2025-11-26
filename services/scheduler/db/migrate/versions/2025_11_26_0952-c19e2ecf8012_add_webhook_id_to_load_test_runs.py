"""add_webhook_id_to_load_test_runs

Revision ID: c19e2ecf8012
Revises: 330ae1de6799
Create Date: 2025-11-26 09:52:23.221166

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c19e2ecf8012"
down_revision: Union[str, None] = "330ae1de6799"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if webhook_id column already exists
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col["name"] for col in inspector.get_columns("load_test_runs")]

    # Add webhook_id column if it doesn't exist
    if "webhook_id" not in columns:
        op.add_column("load_test_runs", sa.Column("webhook_id", sa.String(length=36), nullable=True))

    # Check if foreign key already exists
    foreign_keys = [fk["name"] for fk in inspector.get_foreign_keys("load_test_runs")]
    if "fk_load_test_runs_webhook_id" not in foreign_keys:
        op.create_foreign_key(
            "fk_load_test_runs_webhook_id", "load_test_runs", "webhooks", ["webhook_id"], ["id"], ondelete="CASCADE"
        )

    # Check if index already exists
    indexes = [idx["name"] for idx in inspector.get_indexes("load_test_runs")]
    if "idx_load_test_runs_webhook_id" not in indexes:
        op.create_index("idx_load_test_runs_webhook_id", "load_test_runs", ["webhook_id"], unique=False)

    # Make old columns nullable for backward compatibility
    # MySQL requires existing type to be specified
    op.alter_column("load_test_runs", "target_url", existing_type=sa.String(length=2048), nullable=True)
    op.alter_column("load_test_runs", "oas_spec", existing_type=sa.Text(), nullable=True)
    op.alter_column("load_test_runs", "oas_url", existing_type=sa.String(length=2048), nullable=True)
    op.alter_column("load_test_runs", "test_type", existing_type=sa.String(length=50), nullable=True)
    op.alter_column("load_test_runs", "endpoint_path", existing_type=sa.String(length=512), nullable=True)
    op.alter_column("load_test_runs", "endpoint_method", existing_type=sa.String(length=10), nullable=True)


def downgrade() -> None:
    # Remove index
    op.drop_index("idx_load_test_runs_webhook_id", table_name="load_test_runs")

    # Remove foreign key constraint
    op.drop_constraint("fk_load_test_runs_webhook_id", "load_test_runs", type_="foreignkey")

    # Remove webhook_id column
    op.drop_column("load_test_runs", "webhook_id")

    # Restore old columns to not nullable (if they were originally required)
    op.alter_column("load_test_runs", "target_url", existing_type=sa.String(length=2048), nullable=False)
    op.alter_column("load_test_runs", "test_type", existing_type=sa.String(length=50), nullable=False)
