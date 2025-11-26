"""
Celery task for running load tests in the background.

Handles load test execution, status updates, and error handling.
"""

import asyncio
import logging
from typing import Optional

from celery import Task
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.celery import scheduler as celery_app
from app.services.load_test_service import get_load_test_service
from config.environment import init

# Initialize environment
init()

logger = logging.getLogger(__name__)


class RunLoadTestTask(Task):
    """Custom Celery task class for load test execution."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        logger.error(f"Load test task {task_id} failed: {exc}", exc_info=einfo)
        if args and len(args) > 0:
            run_id = args[0]
            _update_load_test_status(run_id, "failed", error=str(exc))


@celery_app.task(
    bind=True,
    base=RunLoadTestTask,
    acks_late=True,
    max_retries=0,  # No automatic retries for load tests
    time_limit=None,  # No hard timeout (load tests can run for hours)
    soft_time_limit=None,  # No soft timeout
)
def run_load_test(self, run_id: str):
    """
    Execute a load test run in the background.

    This task:
    1. Loads the load test run from the database
    2. Executes the load test asynchronously
    3. Updates status and results in the database
    4. Handles errors and updates status accordingly

    Args:
        run_id: Load test run ID
    """
    db = _get_db_session()
    worker_id = self.request.hostname

    try:
        # Get load test service
        load_test_service = get_load_test_service(db)

        # Check if load test run exists
        load_test_run = load_test_service.get_load_test_run(run_id)
        if not load_test_run:
            logger.error(f"Load test run {run_id} not found")
            return

        # Update status to running if still pending
        if load_test_run.status == "pending":
            load_test_run.status = "running"
            db.commit()
            logger.info(f"Starting load test run {run_id} (worker: {worker_id})")

        # Run the async load test
        # Since Celery tasks are synchronous, we need to run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(load_test_service.run_load_test(run_id))
            logger.info(f"Load test run {run_id} completed successfully")
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Unexpected error executing load test {run_id}: {e}", exc_info=True)
        _update_load_test_status_in_db(db, run_id, "failed", error=str(e))
        db.commit()
    finally:
        db.close()


def _update_load_test_status(
    run_id: str,
    status: str,
    error: Optional[str] = None,
):
    """Update load test status (creates new DB session)."""
    db = _get_db_session()
    try:
        _update_load_test_status_in_db(db, run_id, status, error=error)
        db.commit()
    finally:
        db.close()


def _update_load_test_status_in_db(
    db: Session,
    run_id: str,
    status: str,
    error: Optional[str] = None,
):
    """Update load test status in database."""
    from datetime import datetime

    from app.models.load_test_runs import LoadTestRun

    load_test_run = db.query(LoadTestRun).filter(LoadTestRun.id == run_id).first()
    if load_test_run:
        load_test_run.status = status
        if status == "failed":
            load_test_run.completed_at = datetime.utcnow()
            # Store error if provided
            if error:
                # Since description was removed, we could log it or store in a separate error field
                # For now, just log it
                logger.error(f"Load test {run_id} failed: {error}")


def _get_db_session() -> Session:
    """Get a database session."""
    import os

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")

    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
