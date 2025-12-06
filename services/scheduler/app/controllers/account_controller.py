"""
Account controller for managing account CRUD operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.schemas.request.account_schemas import CreateAccountRequest, UpdateAccountRequest
from app.schemas.response.account_schemas import AccountResponse
from app.schemas.response.pagination_schemas import PaginatedResponse, PaginationMetadata
from app.services.account_service import get_account_service
from db.client import client

router = APIRouter()


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    request: CreateAccountRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Create a new account for the authenticated user.

    Args:
        request: Account creation request with name
        user: Current authenticated user
        db: Database session

    Returns:
        Created account data

    Raises:
        HTTPException: 401 if not authenticated
    """
    account_service = get_account_service(db)
    account = account_service.create_account(user_id=user.id, name=request.name, user=user)
    return account


@router.get("", response_model=PaginatedResponse[AccountResponse])
async def get_accounts(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page (max: 100)"),
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Get all accounts for the authenticated user with pagination.

    Args:
        page: Page number (default: 1, min: 1)
        page_size: Number of items per page (default: 10, max: 100)
        user: Current authenticated user
        db: Database session

    Returns:
        Paginated response with accounts and pagination metadata including:
        - data: List of accounts for the current page
        - pagination: Metadata with current_page, total_pages, total_entries,
          next_page, previous_page, has_next, has_previous

    Raises:
        HTTPException: 401 if not authenticated
    """
    account_service = get_account_service(db)
    accounts, pagination_metadata = account_service.get_accounts_paginated(
        user_id=user.id, page=page, page_size=page_size
    )

    # Convert accounts to response models
    account_responses = [AccountResponse.model_validate(account) for account in accounts]

    return PaginatedResponse(
        data=account_responses,
        pagination=PaginationMetadata(**pagination_metadata),
    )


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Get a specific account by ID.

    Args:
        account_id: ID of the account to retrieve
        user: Current authenticated user
        db: Database session

    Returns:
        Account data

    Raises:
        HTTPException: 401 if not authenticated, 404 if account not found or not owned by user
    """
    account_service = get_account_service(db)
    account = account_service.get_account(account_id=account_id, user_id=user.id)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with ID '{account_id}' not found",
        )

    return account


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str,
    request: UpdateAccountRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Update an existing account.

    Args:
        account_id: ID of the account to update
        request: Account update request with new name
        user: Current authenticated user
        db: Database session

    Returns:
        Updated account data

    Raises:
        HTTPException: 401 if not authenticated, 404 if account not found or not owned by user
    """
    account_service = get_account_service(db)
    account = account_service.update_account(account_id=account_id, user_id=user.id, name=request.name)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with ID '{account_id}' not found",
        )

    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(client),
):
    """
    Delete a account.

    Args:
        account_id: ID of the account to delete
        user: Current authenticated user
        db: Database session

    Returns:
        No content on success

    Raises:
        HTTPException: 401 if not authenticated, 404 if account not found or not owned by user
    """
    account_service = get_account_service(db)
    deleted = account_service.delete_account(account_id=account_id, user_id=user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account with ID '{account_id}' not found",
        )

    return None
