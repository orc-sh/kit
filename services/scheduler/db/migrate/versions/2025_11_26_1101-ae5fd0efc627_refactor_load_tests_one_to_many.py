"""refactor_load_tests_one_to_many

Revision ID: ae5fd0efc627
Revises: 5016f2dc7749
Create Date: 2025-11-26 11:01:15.648413

"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "ae5fd0efc627"
down_revision: Union[str, None] = "5016f2dc7749"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if tables already exist
    inspector = sa.inspect(op.get_bind())
    existing_tables = inspector.get_table_names()

    # Step 1: Create load_test_configurations table
    if "load_test_configurations" not in existing_tables:
        op.create_table(
            "load_test_configurations",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("project_id", sa.String(length=36), nullable=False),
            sa.Column("webhook_id", sa.String(length=36), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("concurrent_users", sa.Integer(), nullable=False, server_default="10"),
            sa.Column("duration_seconds", sa.Integer(), nullable=False, server_default="60"),
            sa.Column("requests_per_second", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.Column(
                "updated_at",
                sa.TIMESTAMP(),
                server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
                nullable=True,
            ),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["webhook_id"], ["webhooks.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("idx_load_test_configs_project_id", "load_test_configurations", ["project_id"], unique=False)
        op.create_index("idx_load_test_configs_webhook_id", "load_test_configurations", ["webhook_id"], unique=False)
        op.create_index("idx_load_test_configs_created_at", "load_test_configurations", ["created_at"], unique=False)

    # Step 2: Create load_test_reports table
    if "load_test_reports" not in existing_tables:
        op.create_table(
            "load_test_reports",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("load_test_run_id", sa.String(length=36), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=True),
            sa.Column("total_requests", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("successful_requests", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("failed_requests", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("avg_response_time_ms", sa.Integer(), nullable=True),
            sa.Column("min_response_time_ms", sa.Integer(), nullable=True),
            sa.Column("max_response_time_ms", sa.Integer(), nullable=True),
            sa.Column("p95_response_time_ms", sa.Integer(), nullable=True),
            sa.Column("p99_response_time_ms", sa.Integer(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.Column(
                "updated_at",
                sa.TIMESTAMP(),
                server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
                nullable=True,
            ),
            sa.ForeignKeyConstraint(["load_test_run_id"], ["load_test_runs.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("idx_load_test_reports_run_id", "load_test_reports", ["load_test_run_id"], unique=False)
        op.create_index("idx_load_test_reports_created_at", "load_test_reports", ["created_at"], unique=False)

    # Step 3: Migrate data - Create configurations from existing runs
    # For each unique combination of project_id, webhook_id, concurrent_users, duration_seconds, requests_per_second
    # Create a configuration and map runs to it
    connection = op.get_bind()

    # Get all unique configurations
    result = connection.execute(
        text(
            """
        SELECT DISTINCT
            project_id,
            webhook_id,
            name,
            concurrent_users,
            duration_seconds,
            requests_per_second,
            MIN(created_at) as first_created_at
        FROM load_test_runs
        WHERE webhook_id IS NOT NULL
        GROUP BY project_id, webhook_id, name, concurrent_users,
                 duration_seconds, requests_per_second
    """
        )
    )

    # Maps (project_id, webhook_id, name, concurrent_users, duration_seconds,
    # requests_per_second) -> config_id
    config_map = {}

    for row in result:
        config_id = str(uuid.uuid4())
        config_map[(row[0], row[1], row[2], row[3], row[4], row[5])] = config_id

        # Insert configuration
        connection.execute(
            text(
                """
            INSERT INTO load_test_configurations
            (id, project_id, webhook_id, name, concurrent_users, duration_seconds,
             requests_per_second, created_at)
            VALUES (:id, :project_id, :webhook_id, :name, :concurrent_users,
                    :duration_seconds, :requests_per_second, :created_at)
        """
            ),
            {
                "id": config_id,
                "project_id": row[0],
                "webhook_id": row[1],
                "name": row[2],
                "concurrent_users": row[3],
                "duration_seconds": row[4],
                "requests_per_second": row[5],
                "created_at": row[6],
            },
        )

    # Step 4: Add load_test_configuration_id column to load_test_runs
    # (temporarily nullable)
    existing_columns = [col["name"] for col in inspector.get_columns("load_test_runs")]
    if "load_test_configuration_id" not in existing_columns:
        op.add_column("load_test_runs", sa.Column("load_test_configuration_id", sa.String(length=36), nullable=True))

    # Step 5: Update load_test_runs to reference configurations
    for key, config_id in config_map.items():
        project_id, webhook_id, name, concurrent_users, duration_seconds, requests_per_second = key
        connection.execute(
            text(
                """
            UPDATE load_test_runs
            SET load_test_configuration_id = :config_id
            WHERE project_id = :project_id
            AND webhook_id = :webhook_id
            AND name = :name
            AND concurrent_users = :concurrent_users
            AND duration_seconds = :duration_seconds
            AND (requests_per_second = :requests_per_second OR
                 (requests_per_second IS NULL AND :requests_per_second IS NULL))
        """
            ),
            {
                "config_id": config_id,
                "project_id": project_id,
                "webhook_id": webhook_id,
                "name": name,
                "concurrent_users": concurrent_users,
                "duration_seconds": duration_seconds,
                "requests_per_second": requests_per_second,
            },
        )

    # Step 6: Create reports for each run that has metrics
    runs_result = connection.execute(
        text(
            """
        SELECT id, total_requests, successful_requests, failed_requests,
               avg_response_time_ms, min_response_time_ms, max_response_time_ms,
               p95_response_time_ms, p99_response_time_ms
        FROM load_test_runs
        WHERE total_requests IS NOT NULL OR avg_response_time_ms IS NOT NULL
    """
        )
    )

    for run_row in runs_result:
        report_id = str(uuid.uuid4())
        connection.execute(
            text(
                """
            INSERT INTO load_test_reports
            (id, load_test_run_id, total_requests, successful_requests, failed_requests,
             avg_response_time_ms, min_response_time_ms, max_response_time_ms,
             p95_response_time_ms, p99_response_time_ms, created_at)
            VALUES (:id, :run_id, :total_requests, :successful_requests, :failed_requests,
                    :avg_response_time_ms, :min_response_time_ms, :max_response_time_ms,
                    :p95_response_time_ms, :p99_response_time_ms, NOW())
        """
            ),
            {
                "id": report_id,
                "run_id": run_row[0],
                "total_requests": run_row[1] or 0,
                "successful_requests": run_row[2] or 0,
                "failed_requests": run_row[3] or 0,
                "avg_response_time_ms": run_row[4],
                "min_response_time_ms": run_row[5],
                "max_response_time_ms": run_row[6],
                "p95_response_time_ms": run_row[7],
                "p99_response_time_ms": run_row[8],
            },
        )

    # Step 7: Add load_test_report_id to load_test_results (temporarily nullable)
    existing_result_columns = [col["name"] for col in inspector.get_columns("load_test_results")]
    if "load_test_report_id" not in existing_result_columns:
        op.add_column("load_test_results", sa.Column("load_test_report_id", sa.String(length=36), nullable=True))

    # Step 8: Update load_test_results to reference reports
    # For each result, find the report for its run
    results_result = connection.execute(
        text(
            """
        SELECT ltr.id, ltr.load_test_run_id, ltr2.id as report_id
        FROM load_test_results ltr
        LEFT JOIN load_test_reports ltr2 ON ltr.load_test_run_id = ltr2.load_test_run_id
    """
        )
    )

    for result_row in results_result:
        if result_row[2]:  # If report exists
            connection.execute(
                text(
                    """
                UPDATE load_test_results
                SET load_test_report_id = :report_id
                WHERE id = :result_id
            """
                ),
                {"report_id": result_row[2], "result_id": result_row[0]},
            )

    # Step 9: Make load_test_configuration_id NOT NULL and add foreign key
    # First check if column exists and is nullable
    existing_run_columns = {col["name"]: col for col in inspector.get_columns("load_test_runs")}
    if "load_test_configuration_id" in existing_run_columns and existing_run_columns["load_test_configuration_id"].get(
        "nullable", True
    ):
        op.alter_column(
            "load_test_runs", "load_test_configuration_id", existing_type=sa.String(length=36), nullable=False
        )
    op.create_foreign_key(
        "fk_load_test_runs_config_id",
        "load_test_runs",
        "load_test_configurations",
        ["load_test_configuration_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("idx_load_test_runs_config_id", "load_test_runs", ["load_test_configuration_id"], unique=False)

    # Step 10: Make load_test_report_id NOT NULL and add foreign key
    # (for results that have reports)
    # Note: Some results might not have reports if the run didn't complete,
    # so we'll keep it nullable
    op.create_foreign_key(
        "fk_load_test_results_report_id",
        "load_test_results",
        "load_test_reports",
        ["load_test_report_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("idx_load_test_results_report_id", "load_test_results", ["load_test_report_id"], unique=False)

    # Step 11: Drop old foreign keys and indexes first (before dropping columns)
    # Get actual constraint names from database
    inspector = sa.inspect(op.get_bind())
    fks = inspector.get_foreign_keys("load_test_runs")
    for fk in fks:
        if "project_id" in fk["constrained_columns"]:
            op.drop_constraint(fk["name"], "load_test_runs", type_="foreignkey")
        elif "webhook_id" in fk["constrained_columns"]:
            op.drop_constraint(fk["name"], "load_test_runs", type_="foreignkey")

    # Drop indexes
    try:
        op.drop_index("idx_load_test_runs_project_id", "load_test_runs")
    except Exception:
        pass
    try:
        op.drop_index("idx_load_test_runs_webhook_id", "load_test_runs")
    except Exception:
        pass

    # Drop old index from load_test_results
    fks_results = inspector.get_foreign_keys("load_test_results")
    for fk in fks_results:
        if "load_test_run_id" in fk["constrained_columns"]:
            op.drop_constraint(fk["name"], "load_test_results", type_="foreignkey")
    try:
        op.drop_index("idx_load_test_results_run_id", "load_test_results")
    except Exception:
        pass

    # Step 12: Drop old columns from load_test_runs
    op.drop_column("load_test_runs", "project_id")
    op.drop_column("load_test_runs", "webhook_id")
    op.drop_column("load_test_runs", "name")
    op.drop_column("load_test_runs", "concurrent_users")
    op.drop_column("load_test_runs", "duration_seconds")
    op.drop_column("load_test_runs", "requests_per_second")
    op.drop_column("load_test_runs", "total_requests")
    op.drop_column("load_test_runs", "successful_requests")
    op.drop_column("load_test_runs", "failed_requests")
    op.drop_column("load_test_runs", "avg_response_time_ms")
    op.drop_column("load_test_runs", "min_response_time_ms")
    op.drop_column("load_test_runs", "max_response_time_ms")
    op.drop_column("load_test_runs", "p95_response_time_ms")
    op.drop_column("load_test_runs", "p99_response_time_ms")

    # Step 13: Drop old column from load_test_results
    op.drop_column("load_test_results", "load_test_run_id")


def downgrade() -> None:
    # Reverse the migration - this is complex and may lose data
    # Add back old columns
    op.add_column("load_test_runs", sa.Column("project_id", sa.String(length=36), nullable=True))
    op.add_column("load_test_runs", sa.Column("webhook_id", sa.String(length=36), nullable=True))
    op.add_column("load_test_runs", sa.Column("name", sa.String(length=255), nullable=True))
    op.add_column("load_test_runs", sa.Column("concurrent_users", sa.Integer(), nullable=True))
    op.add_column("load_test_runs", sa.Column("duration_seconds", sa.Integer(), nullable=True))
    op.add_column("load_test_runs", sa.Column("requests_per_second", sa.Integer(), nullable=True))
    op.add_column("load_test_runs", sa.Column("total_requests", sa.Integer(), nullable=True))
    op.add_column("load_test_runs", sa.Column("successful_requests", sa.Integer(), nullable=True))
    op.add_column("load_test_runs", sa.Column("failed_requests", sa.Integer(), nullable=True))
    op.add_column("load_test_runs", sa.Column("avg_response_time_ms", sa.Integer(), nullable=True))
    op.add_column("load_test_runs", sa.Column("min_response_time_ms", sa.Integer(), nullable=True))
    op.add_column("load_test_runs", sa.Column("max_response_time_ms", sa.Integer(), nullable=True))
    op.add_column("load_test_runs", sa.Column("p95_response_time_ms", sa.Integer(), nullable=True))
    op.add_column("load_test_runs", sa.Column("p99_response_time_ms", sa.Integer(), nullable=True))

    # Migrate data back (simplified - may lose some data)
    connection = op.get_bind()
    connection.execute(
        text(
            """
        UPDATE load_test_runs ltr
        INNER JOIN load_test_configurations ltc ON ltr.load_test_configuration_id = ltc.id
        LEFT JOIN load_test_reports ltr2 ON ltr.id = ltr2.load_test_run_id
        SET ltr.project_id = ltc.project_id,
            ltr.webhook_id = ltc.webhook_id,
            ltr.name = ltc.name,
            ltr.concurrent_users = ltc.concurrent_users,
            ltr.duration_seconds = ltc.duration_seconds,
            ltr.requests_per_second = ltc.requests_per_second,
            ltr.total_requests = ltr2.total_requests,
            ltr.successful_requests = ltr2.successful_requests,
            ltr.failed_requests = ltr2.failed_requests,
            ltr.avg_response_time_ms = ltr2.avg_response_time_ms,
            ltr.min_response_time_ms = ltr2.min_response_time_ms,
            ltr.max_response_time_ms = ltr2.max_response_time_ms,
            ltr.p95_response_time_ms = ltr2.p95_response_time_ms,
            ltr.p99_response_time_ms = ltr2.p99_response_time_ms
    """
        )
    )

    op.add_column("load_test_results", sa.Column("load_test_run_id", sa.String(length=36), nullable=True))
    connection.execute(
        text(
            """
        UPDATE load_test_results ltr
        INNER JOIN load_test_reports ltr2 ON ltr.load_test_report_id = ltr2.id
        SET ltr.load_test_run_id = ltr2.load_test_run_id
    """
        )
    )

    # Drop new tables and columns
    op.drop_index("idx_load_test_results_report_id", "load_test_results")
    op.drop_constraint("fk_load_test_results_report_id", "load_test_results", type_="foreignkey")
    op.drop_column("load_test_results", "load_test_report_id")
    op.drop_column("load_test_results", "load_test_run_id")  # Will be recreated

    op.drop_index("idx_load_test_runs_config_id", "load_test_runs")
    op.drop_constraint("fk_load_test_runs_config_id", "load_test_runs", type_="foreignkey")
    op.drop_column("load_test_runs", "load_test_configuration_id")

    op.drop_table("load_test_reports")
    op.drop_table("load_test_configurations")

    # Recreate old structure
    op.add_column("load_test_results", sa.Column("load_test_run_id", sa.String(length=36), nullable=False))
    op.create_foreign_key(
        "load_test_results_ibfk_1",
        "load_test_results",
        "load_test_runs",
        ["load_test_run_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("idx_load_test_results_run_id", "load_test_results", ["load_test_run_id"], unique=False)

    op.create_foreign_key(
        "load_test_runs_ibfk_1", "load_test_runs", "projects", ["project_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "load_test_runs_ibfk_2", "load_test_runs", "webhooks", ["webhook_id"], ["id"], ondelete="CASCADE"
    )
    op.create_index("idx_load_test_runs_project_id", "load_test_runs", ["project_id"], unique=False)
    op.create_index("idx_load_test_runs_webhook_id", "load_test_runs", ["webhook_id"], unique=False)
