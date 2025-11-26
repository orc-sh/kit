"""make_webhook_job_id_nullable

Revision ID: 5016f2dc7749
Revises: c19e2ecf8012
Create Date: 2025-11-26 10:34:51.588009

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5016f2dc7749"
down_revision: Union[str, None] = "c19e2ecf8012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make job_id nullable in webhooks table to support load tests
    # The foreign key constraint will remain but will allow NULL values
    op.alter_column("webhooks", "job_id", existing_type=sa.String(length=36), nullable=True)


def downgrade() -> None:
    # Revert job_id to NOT NULL
    # Note: This will fail if there are any NULL values in the column
    op.alter_column("webhooks", "job_id", existing_type=sa.String(length=36), nullable=False)
