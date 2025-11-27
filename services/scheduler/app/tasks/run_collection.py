"""
Celery task for running collections in the background.

Handles collection execution, status updates, and error handling.
"""

import asyncio
import logging
from typing import Optional

from celery import Task
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.celery import scheduler as celery_app
from app.services.collection_service import get_collection_service
from config.environment import init

# Initialize environment
init()

logger = logging.getLogger(__name__)


class RunCollectionTask(Task):
    """Custom Celery task class for collection execution."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        logger.error(f"Collection task {task_id} failed: {exc}", exc_info=einfo)
        if args and len(args) > 0:
            run_id = args[0]
            _update_collection_status(run_id, "failed", error=str(exc))


@celery_app.task(
    bind=True,
    base=RunCollectionTask,
    acks_late=True,
    max_retries=0,  # No automatic retries for collections
    time_limit=None,  # No hard timeout (collections can run for hours)
    soft_time_limit=None,  # No soft timeout
)
def run_collection(self, run_id: str):
    """
    Execute a collection run in the background.

    This task:
    1. Loads the collection run from the database
    2. Executes the collection asynchronously
    3. Updates status and results in the database
    4. Handles errors and updates status accordingly

    Args:
        run_id: Collection run ID
    """
    db = _get_db_session()
    worker_id = self.request.hostname

    try:
        # Get collection service
        collection_service = get_collection_service(db)

        # Check if collection run exists
        collection_run = collection_service.get_collection_run(run_id)
        if not collection_run:
            logger.error(f"Collection run {run_id} not found")
            return

        # Update status to running if still pending
        if collection_run.status == "pending":
            collection_run.status = "running"
            db.commit()
            logger.info(f"Starting collection run {run_id} (worker: {worker_id})")

        # Run the async collection
        # Since Celery tasks are synchronous, we need to run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(collection_service.run_collection(run_id))
            logger.info(f"Collection run {run_id} completed successfully")
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Unexpected error executing collection {run_id}: {e}", exc_info=True)
        _update_collection_status_in_db(db, run_id, "failed", error=str(e))
        db.commit()
    finally:
        db.close()


def _update_collection_status(
    run_id: str,
    status: str,
    error: Optional[str] = None,
):
    """Update collection status (creates new DB session)."""
    db = _get_db_session()
    try:
        _update_collection_status_in_db(db, run_id, status, error=error)
        db.commit()
    finally:
        db.close()


def _update_collection_status_in_db(
    db: Session,
    run_id: str,
    status: str,
    error: Optional[str] = None,
):
    """Update collection status in database."""
    from datetime import datetime

    from app.models.collection_runs import CollectionRun

    collection_run = db.query(CollectionRun).filter(CollectionRun.id == run_id).first()
    if collection_run:
        collection_run.status = status
        if status == "failed":
            collection_run.completed_at = datetime.utcnow()
            # Store error if provided
            if error:
                # Since description was removed, we could log it or store in a separate error field
                # For now, just log it
                logger.error(f"Collection {run_id} failed: {error}")


def _get_db_session() -> Session:
    """Get a database session."""
    import os

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")

    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
