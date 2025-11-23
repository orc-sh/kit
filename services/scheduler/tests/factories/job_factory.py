"""
Job-specific test data factories and helpers.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.jobs import Job


class JobFactory:
    """Factory for creating Job test objects."""

    @staticmethod
    def create(
        db: Session,
        project_id: str,
        name: Optional[str] = None,
        schedule: str = "0 9 * * *",
        job_type: int = 1,
        timezone: str = "UTC",
        enabled: bool = True,
        job_id: Optional[str] = None,
        next_run_at: Optional[datetime] = None,
        last_run_at: Optional[datetime] = None,
    ) -> Job:
        """
        Create a job in the database.

        Args:
            db: Database session
            project_id: ID of the project this job belongs to
            name: Name of the job
            schedule: Cron schedule expression
            job_type: Job type identifier
            timezone: Timezone for scheduling
            enabled: Whether job is enabled
            job_id: Optional specific job ID
            next_run_at: Optional next run datetime
            last_run_at: Optional last run datetime

        Returns:
            Created Job instance
        """
        job = Job(
            id=job_id or str(uuid.uuid4()),
            project_id=project_id,
            name=name or f"Test Job {uuid.uuid4().hex[:8]}",
            schedule=schedule,
            type=job_type,
            timezone=timezone,
            enabled=enabled,
            next_run_at=next_run_at or datetime.now() + timedelta(hours=1),
            last_run_at=last_run_at,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def create_batch(
        db: Session, project_id: str, count: int = 5, name_prefix: Optional[str] = None, **kwargs
    ) -> list[Job]:
        """
        Create multiple jobs in the database.

        Args:
            db: Database session
            project_id: ID of the project
            count: Number of jobs to create
            name_prefix: Optional prefix for job names
            **kwargs: Additional job attributes

        Returns:
            List of created Job instances
        """
        jobs: list[Job] = []
        for i in range(count):
            name = f"{name_prefix} {i + 1}" if name_prefix else f"Test Job {i + 1}"
            job = JobFactory.create(db=db, project_id=project_id, name=name, **kwargs)
            jobs.append(job)
        return jobs

    @staticmethod
    def build(
        project_id: str,
        name: Optional[str] = None,
        schedule: str = "0 9 * * *",
        job_type: int = 1,
        timezone: str = "UTC",
        enabled: bool = True,
        job_id: Optional[str] = None,
    ) -> Job:
        """
        Build a job object without saving to database.

        Args:
            project_id: ID of the project
            name: Name of the job
            schedule: Cron schedule expression
            job_type: Job type identifier
            timezone: Timezone for scheduling
            enabled: Whether job is enabled
            job_id: Optional specific job ID

        Returns:
            Job instance (not saved to DB)
        """
        return Job(
            id=job_id or str(uuid.uuid4()),
            project_id=project_id,
            name=name or f"Test Job {uuid.uuid4().hex[:8]}",
            schedule=schedule,
            type=job_type,
            timezone=timezone,
            enabled=enabled,
            next_run_at=datetime.now() + timedelta(hours=1),
        )


def create_test_job_data(
    name: Optional[str] = None,
    schedule: str = "0 9 * * *",
    job_type: int = 1,
    timezone: str = "UTC",
    enabled: bool = True,
) -> dict:
    """
    Create raw job data dictionary (not model instance).

    Args:
        name: Job name
        schedule: Cron schedule expression
        job_type: Job type identifier
        timezone: Timezone for scheduling
        enabled: Whether job is enabled

    Returns:
        Dictionary with job data
    """
    return {
        "name": name or f"Test Job {uuid.uuid4().hex[:8]}",
        "schedule": schedule,
        "type": job_type,
        "timezone": timezone,
        "enabled": enabled,
    }


def create_job_update_data(
    name: Optional[str] = None,
    schedule: Optional[str] = None,
    job_type: Optional[int] = None,
    timezone: Optional[str] = None,
    enabled: Optional[bool] = None,
) -> dict:
    """
    Create job update data dictionary.

    Args:
        name: Optional new name
        schedule: Optional new schedule
        job_type: Optional new type
        timezone: Optional new timezone
        enabled: Optional new enabled status

    Returns:
        Dictionary with update data
    """
    data = {}
    if name is not None:
        data["name"] = name
    if schedule is not None:
        data["schedule"] = schedule
    if job_type is not None:
        data["type"] = job_type
    if timezone is not None:
        data["timezone"] = timezone
    if enabled is not None:
        data["enabled"] = enabled
    return data
