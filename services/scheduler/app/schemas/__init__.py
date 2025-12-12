# Schemas for scheduler service
# Authentication schemas are in the auth service
# Add scheduler-specific schemas here (jobs, webhooks, accounts, etc.)

from .request import CreateAccountRequest, UpdateAccountRequest
from .response import AccountResponse, PaginatedResponse, PaginationMetadata

__all__ = [
    "CreateAccountRequest",
    "UpdateAccountRequest",
    "PaginatedResponse",
    "PaginationMetadata",
    "AccountResponse",
]
