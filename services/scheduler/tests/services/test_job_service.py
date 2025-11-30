"""
Unit tests for JobService.

These tests verify the service layer logic for job CRUD operations
without making actual API requests.
"""

from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.services.job_service import JobService, get_job_service
from tests.factories import AccountFactory, JobFactory


@pytest.mark.unit
class TestJobServiceCreate:
    """Tests for job creation."""

    def test_create_job_success(self, db_session: Session, test_user):
        """Test creating a job successfully."""
        account = AccountFactory.create(db_session, test_user.id, "Test Account")
        service = JobService(db_session)

        job = service.create_job(
            account_id=account.id,
            name="My New Job",
            schedule="0 9 * * *",
            job_type=1,
            timezone="UTC",
            enabled=True,
        )

        assert job.id is not None
        assert job.account_id == account.id
        assert job.name == "My New Job"
        assert job.schedule == "0 9 * * *"
        assert job.type == 1
        assert job.timezone == "UTC"
        assert job.enabled is True
        assert job.next_run_at is not None
        assert job.created_at is not None

    def test_create_job_generates_uuid(self, db_session: Session, test_user):
        """Test that job ID is auto-generated as UUID."""
        account = AccountFactory.create(db_session, test_user.id, "Test Account")
        service = JobService(db_session)

        job = service.create_job(
            account_id=account.id,
            name="Test Job",
            schedule="0 9 * * *",
            job_type=1,
        )

        # Check UUID format
        assert len(job.id) == 36  # UUID format: 8-4-4-4-12
        assert job.id.count("-") == 4

    def test_create_job_calculates_next_run(self, db_session: Session, test_user):
        """Test that next_run_at is calculated from cron schedule."""
        account = AccountFactory.create(db_session, test_user.id, "Test Account")
        service = JobService(db_session)

        before = datetime.now()
        job = service.create_job(
            account_id=account.id,
            name="Test Job",
            schedule="0 9 * * *",
            job_type=1,
        )

        # next_run_at should be in the future
        assert job.next_run_at > before

    def test_create_job_invalid_cron_schedule(self, db_session: Session, test_user):
        """Test that invalid cron schedule raises ValueError."""
        account = AccountFactory.create(db_session, test_user.id, "Test Account")
        service = JobService(db_session)

        with pytest.raises(ValueError, match="Invalid cron schedule"):
            service.create_job(
                account_id=account.id,
                name="Test Job",
                schedule="invalid cron",
                job_type=1,
            )

    def test_create_job_with_timezone(self, db_session: Session, test_user):
        """Test creating a job with custom timezone."""
        account = AccountFactory.create(db_session, test_user.id, "Test Account")
        service = JobService(db_session)

        job = service.create_job(
            account_id=account.id,
            name="Test Job",
            schedule="0 9 * * *",
            job_type=1,
            timezone="America/New_York",
        )

        assert job.timezone == "America/New_York"

    def test_create_job_disabled(self, db_session: Session, test_user):
        """Test creating a disabled job."""
        account = AccountFactory.create(db_session, test_user.id, "Test Account")
        service = JobService(db_session)

        job = service.create_job(
            account_id=account.id,
            name="Test Job",
            schedule="0 9 * * *",
            job_type=1,
            enabled=False,
        )

        assert job.enabled is False


@pytest.mark.unit
class TestJobServiceGet:
    """Tests for retrieving jobs."""

    def test_get_job_by_id_success(self, db_session: Session, test_user):
        """Test retrieving a specific job by ID."""
        account = AccountFactory.create(db_session, test_user.id, "Test Account")
        created_job = JobFactory.create(db_session, account.id, "Test Job")

        service = JobService(db_session)
        job = service.get_job(created_job.id)

        assert job is not None
        assert job.id == created_job.id
        assert job.name == "Test Job"

    def test_get_job_not_found(self, db_session: Session):
        """Test retrieving a non-existent job returns None."""
        service = JobService(db_session)

        job = service.get_job("non-existent-id")

        assert job is None

    def test_get_jobs_by_account_empty(self, db_session: Session, test_user):
        """Test retrieving jobs when account has none."""
        account = AccountFactory.create(db_session, test_user.id, "Test Account")
        service = JobService(db_session)

        jobs = service.get_jobs_by_account(account.id)

        assert jobs == []

    def test_get_jobs_by_account_multiple(self, db_session: Session, test_user):
        """Test retrieving all jobs for a account."""
        account = AccountFactory.create(db_session, test_user.id, "Test Account")
        JobFactory.create_batch(db_session, account.id, count=3, name_prefix="Job")

        service = JobService(db_session)
        jobs = service.get_jobs_by_account(account.id)

        assert len(jobs) == 3
        assert all(j.account_id == account.id for j in jobs)

    def test_get_jobs_by_account_filters_by_account(self, db_session: Session, test_user):
        """Test that get_jobs_by_account only returns the specified account's jobs."""
        account1 = AccountFactory.create(db_session, test_user.id, "Account 1")
        account2 = AccountFactory.create(db_session, test_user.id, "Account 2")

        JobFactory.create_batch(db_session, account1.id, count=2)
        JobFactory.create_batch(db_session, account2.id, count=3)

        service = JobService(db_session)
        jobs = service.get_jobs_by_account(account1.id)

        assert len(jobs) == 2
        assert all(j.account_id == account1.id for j in jobs)

    def test_get_jobs_with_pagination(self, db_session: Session, test_user):
        """Test retrieving jobs with skip and limit."""
        account = AccountFactory.create(db_session, test_user.id, "Test Account")
        JobFactory.create_batch(db_session, account.id, count=10)

        service = JobService(db_session)

        # Get first 5
        jobs_page1 = service.get_jobs_by_account(account.id, skip=0, limit=5)
        assert len(jobs_page1) == 5

        # Get next 5
        jobs_page2 = service.get_jobs_by_account(account.id, skip=5, limit=5)
        assert len(jobs_page2) == 5

        # Ensure they're different jobs
        page1_ids = {j.id for j in jobs_page1}
        page2_ids = {j.id for j in jobs_page2}
        assert page1_ids.isdisjoint(page2_ids)


@pytest.mark.unit
class TestJobServiceUpdate:
    """Tests for job updates."""

    def test_update_job_name(self, db_session: Session, test_user):
        """Test updating a job's name."""
        account = AccountFactory.create(db_session, test_user.id, "Test Account")
        created_job = JobFactory.create(db_session, account.id, "Original Name")

        service = JobService(db_session)
        updated_job = service.update_job(created_job.id, name="Updated Name")

        assert updated_job is not None
        assert updated_job.id == created_job.id
        assert updated_job.name == "Updated Name"

    def test_update_job_schedule(self, db_session: Session, test_user):
        """Test updating a job's schedule updates next_run_at."""
        account = AccountFactory.create(db_session, test_user.id, "Test Account")
        created_job = JobFactory.create(db_session, account.id, schedule="0 9 * * *")
        original_next_run = created_job.next_run_at

        service = JobService(db_session)
        updated_job = service.update_job(created_job.id, schedule="0 10 * * *")

        assert updated_job is not None
        assert updated_job.schedule == "0 10 * * *"
        # next_run_at should be recalculated
        assert updated_job.next_run_at != original_next_run

    def test_update_job_invalid_schedule(self, db_session: Session, test_user):
        """Test updating with invalid schedule raises ValueError."""
        account = AccountFactory.create(db_session, test_user.id, "Test Account")
        created_job = JobFactory.create(db_session, account.id)

        service = JobService(db_session)

        with pytest.raises(ValueError, match="Invalid cron schedule"):
            service.update_job(created_job.id, schedule="invalid cron")

    def test_update_job_enabled_status(self, db_session: Session, test_user):
        """Test updating a job's enabled status."""
        account = AccountFactory.create(db_session, test_user.id, "Test Account")
        created_job = JobFactory.create(db_session, account.id, enabled=True)

        service = JobService(db_session)
        updated_job = service.update_job(created_job.id, enabled=False)

        assert updated_job is not None
        assert updated_job.enabled is False

    def test_update_job_type(self, db_session: Session, test_user):
        """Test updating a job's type."""
        account = AccountFactory.create(db_session, test_user.id, "Test Account")
        created_job = JobFactory.create(db_session, account.id, job_type=1)

        service = JobService(db_session)
        updated_job = service.update_job(created_job.id, job_type=2)

        assert updated_job is not None
        assert updated_job.type == 2

    def test_update_job_timezone(self, db_session: Session, test_user):
        """Test updating a job's timezone."""
        account = AccountFactory.create(db_session, test_user.id, "Test Account")
        created_job = JobFactory.create(db_session, account.id, timezone="UTC")

        service = JobService(db_session)
        updated_job = service.update_job(created_job.id, timezone="America/New_York")

        assert updated_job is not None
        assert updated_job.timezone == "America/New_York"

    def test_update_job_multiple_fields(self, db_session: Session, test_user):
        """Test updating multiple job fields at once."""
        account = AccountFactory.create(db_session, test_user.id, "Test Account")
        created_job = JobFactory.create(db_session, account.id, "Original", job_type=1)

        service = JobService(db_session)
        updated_job = service.update_job(
            created_job.id,
            name="Updated Name",
            job_type=2,
            enabled=False,
        )

        assert updated_job is not None
        assert updated_job.name == "Updated Name"
        assert updated_job.type == 2
        assert updated_job.enabled is False

    def test_update_job_not_found(self, db_session: Session):
        """Test updating a non-existent job returns None."""
        service = JobService(db_session)

        result = service.update_job("non-existent-id", name="New Name")

        assert result is None


@pytest.mark.unit
class TestJobServiceDelete:
    """Tests for job deletion."""

    def test_delete_job_success(self, db_session: Session, test_user):
        """Test deleting a job successfully."""
        account = AccountFactory.create(db_session, test_user.id, "Test Account")
        created_job = JobFactory.create(db_session, account.id, "To Delete")
        job_id = created_job.id

        service = JobService(db_session)
        result = service.delete_job(job_id)

        assert result is True

        # Verify it's gone
        deleted_job = service.get_job(job_id)
        assert deleted_job is None

    def test_delete_job_not_found(self, db_session: Session):
        """Test deleting a non-existent job returns False."""
        service = JobService(db_session)

        result = service.delete_job("non-existent-id")

        assert result is False


@pytest.mark.unit
class TestJobServiceFactory:
    """Tests for the service factory function."""

    def test_get_job_service_returns_instance(self, db_session: Session):
        """Test that factory function returns JobService instance."""
        service = get_job_service(db_session)

        assert isinstance(service, JobService)
        assert service.db == db_session

    def test_get_job_service_creates_new_instances(self, db_session: Session):
        """Test that factory creates new instances each time."""
        service1 = get_job_service(db_session)
        service2 = get_job_service(db_session)

        # Should be different instances
        assert service1 is not service2
        # But should share the same db session
        assert service1.db is service2.db


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
