"""
Service for managing load test configurations.
"""

import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.load_test_configurations import LoadTestConfiguration


class LoadTestConfigurationService:
    """Service class for load test configuration operations"""

    def __init__(self, db: Session):
        """
        Initialize the service with a database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create_configuration(
        self,
        project_id: str,
        webhook_id: str,
        name: str,
        concurrent_users: int = 10,
        duration_seconds: int = 60,
        requests_per_second: Optional[int] = None,
    ) -> LoadTestConfiguration:
        """
        Create a new load test configuration.

        Args:
            project_id: ID of the project
            webhook_id: ID of the webhook configuration
            name: Name of the load test configuration
            concurrent_users: Number of concurrent users
            duration_seconds: Duration in seconds
            requests_per_second: Optional rate limit

        Returns:
            Created LoadTestConfiguration instance
        """
        configuration = LoadTestConfiguration(
            id=str(uuid.uuid4()),
            project_id=project_id,
            webhook_id=webhook_id,
            name=name,
            concurrent_users=concurrent_users,
            duration_seconds=duration_seconds,
            requests_per_second=requests_per_second,
        )
        self.db.add(configuration)
        self.db.commit()
        self.db.refresh(configuration)
        return configuration

    def get_configuration(self, config_id: str) -> Optional[LoadTestConfiguration]:
        """
        Get a load test configuration by ID.

        Args:
            config_id: ID of the configuration

        Returns:
            LoadTestConfiguration instance if found, None otherwise
        """
        return self.db.query(LoadTestConfiguration).filter(LoadTestConfiguration.id == config_id).first()

    def get_configurations_by_project(
        self, project_id: str, skip: int = 0, limit: int = 100
    ) -> List[LoadTestConfiguration]:
        """
        Get all load test configurations for a project.

        Args:
            project_id: ID of the project
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of LoadTestConfiguration instances
        """
        return (
            self.db.query(LoadTestConfiguration)
            .filter(LoadTestConfiguration.project_id == project_id)
            .order_by(LoadTestConfiguration.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_configuration(
        self,
        config_id: str,
        name: Optional[str] = None,
        concurrent_users: Optional[int] = None,
        duration_seconds: Optional[int] = None,
        requests_per_second: Optional[int] = None,
    ) -> Optional[LoadTestConfiguration]:
        """
        Update a load test configuration.

        Args:
            config_id: ID of the configuration
            name: New name
            concurrent_users: New concurrent users
            duration_seconds: New duration
            requests_per_second: New rate limit

        Returns:
            Updated LoadTestConfiguration instance if found, None otherwise
        """
        configuration = self.get_configuration(config_id)
        if not configuration:
            return None

        if name is not None:
            configuration.name = name
        if concurrent_users is not None:
            configuration.concurrent_users = concurrent_users
        if duration_seconds is not None:
            configuration.duration_seconds = duration_seconds
        if requests_per_second is not None:
            configuration.requests_per_second = requests_per_second

        self.db.commit()
        self.db.refresh(configuration)
        return configuration

    def delete_configuration(self, config_id: str) -> bool:
        """
        Delete a load test configuration and all its runs.

        Args:
            config_id: ID of the configuration

        Returns:
            True if deleted, False if not found
        """
        configuration = self.get_configuration(config_id)
        if not configuration:
            return False

        self.db.delete(configuration)
        self.db.commit()
        return True


def get_load_test_configuration_service(db: Session) -> LoadTestConfigurationService:
    """
    Factory function to create a LoadTestConfigurationService instance.

    Args:
        db: SQLAlchemy database session

    Returns:
        LoadTestConfigurationService instance
    """
    return LoadTestConfigurationService(db)
