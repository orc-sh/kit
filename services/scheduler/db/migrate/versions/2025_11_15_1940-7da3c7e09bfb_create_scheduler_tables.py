"""create_scheduler_tables

Revision ID: 7da3c7e09bfb
Revises:
Create Date: 2025-11-15 19:40:33.153832

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "7da3c7e09bfb"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create projects table
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_projects_user_id", "projects", ["user_id"])

    # Create jobs table
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("project_id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("schedule", sa.String(50), nullable=False),
        sa.Column("type", sa.Integer(), nullable=False),
        sa.Column("timezone", sa.String(50), server_default="UTC"),
        sa.Column("enabled", sa.Boolean(), server_default="1"),
        sa.Column("last_run_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("next_run_at", sa.TIMESTAMP(), nullable=False),
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
    op.create_index("idx_jobs_project_id", "jobs", ["project_id"])
    op.create_index("idx_jobs_next_run_at", "jobs", ["next_run_at"])
    op.create_index("idx_jobs_enabled", "jobs", ["enabled"])

    # Create webhooks table
    op.create_table(
        "webhooks",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("job_id", sa.String(36), nullable=False),
        sa.Column("url", sa.String(1024), nullable=False),
        sa.Column(
            "method",
            sa.Enum("GET", "POST", "PUT", "PATCH", "DELETE", name="http_method_enum"),
            nullable=False,
            server_default="POST",
        ),
        sa.Column("headers", sa.JSON(), nullable=True),
        sa.Column("query_params", sa.JSON(), nullable=True),
        sa.Column("body_template", sa.Text(), nullable=True),
        sa.Column("content_type", sa.String(100), server_default="application/json"),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(),
            server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_webhooks_job_id", "webhooks", ["job_id"])

    # Create job_executions table
    op.create_table(
        "job_executions",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("job_id", sa.String(36), nullable=False),
        sa.Column("status", sa.Enum("pending", "success", "failure", name="execution_status_enum"), nullable=False),
        sa.Column("started_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("finished_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("response_code", sa.Integer(), nullable=True),
        sa.Column("response_body", mysql.MEDIUMTEXT(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_job_executions_job_id", "job_executions", ["job_id"])
    op.create_index("idx_job_executions_created_at", "job_executions", ["created_at"])

    # Create webhook_results table
    op.create_table(
        "webhook_results",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("webhook_id", sa.String(36), nullable=False),
        sa.Column("job_execution_id", sa.String(36), nullable=False),
        sa.Column("triggered_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.Column("request_url", sa.String(1024), nullable=False),
        sa.Column("request_method", sa.String(10), nullable=False),
        sa.Column("request_headers", sa.JSON(), nullable=True),
        sa.Column("request_body", mysql.LONGTEXT(), nullable=True),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("response_headers", sa.JSON(), nullable=True),
        sa.Column("response_body", mysql.LONGTEXT(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("is_success", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["webhook_id"], ["webhooks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_execution_id"], ["job_executions.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_webhook_results_webhook_id", "webhook_results", ["webhook_id"])
    op.create_index("idx_webhook_results_job_execution_id", "webhook_results", ["job_execution_id"])


def downgrade() -> None:
    # Drop tables in reverse order to respect foreign key constraints
    op.drop_index("idx_webhook_results_job_execution_id", "webhook_results")
    op.drop_index("idx_webhook_results_webhook_id", "webhook_results")
    op.drop_table("webhook_results")

    op.drop_index("idx_job_executions_created_at", "job_executions")
    op.drop_index("idx_job_executions_job_id", "job_executions")
    op.drop_table("job_executions")

    op.drop_index("idx_webhooks_job_id", "webhooks")
    op.drop_table("webhooks")

    op.drop_index("idx_jobs_enabled", "jobs")
    op.drop_index("idx_jobs_next_run_at", "jobs")
    op.drop_index("idx_jobs_project_id", "jobs")
    op.drop_table("jobs")

    op.drop_index("idx_projects_user_id", "projects")
    op.drop_table("projects")
