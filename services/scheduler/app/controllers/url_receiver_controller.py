"""
URL receiver controller for handling incoming requests to URL endpoints.
This endpoint is public and doesn't require authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.services.url_service import get_url_service
from db.client import client

router = APIRouter()


@router.post("/{unique_identifier}", status_code=status.HTTP_200_OK)
@router.get("/{unique_identifier}", status_code=status.HTTP_200_OK)
@router.put("/{unique_identifier}", status_code=status.HTTP_200_OK)
@router.patch("/{unique_identifier}", status_code=status.HTTP_200_OK)
@router.delete("/{unique_identifier}", status_code=status.HTTP_200_OK)
async def receive_request(
    unique_identifier: str,
    request: Request,
    db: Session = Depends(client),
):
    """
    Receive incoming requests to a URL endpoint.
    This endpoint accepts all HTTP methods and logs the request.

    Args:
        unique_identifier: Unique identifier for the URL
        request: FastAPI request object
        db: Database session

    Returns:
        Success response

    Raises:
        HTTPException: 404 if URL not found
    """
    url_service = get_url_service(db)
    url = url_service.get_url_by_identifier(unique_identifier)

    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"URL with identifier '{unique_identifier}' not found",
        )

    # Extract request data
    method = request.method
    headers = dict(request.headers)
    query_params = dict(request.query_params)

    # Get request body if available
    body = None
    try:
        if request.method in ["POST", "PUT", "PATCH"]:
            body_bytes = await request.body()
            if body_bytes:
                body = body_bytes.decode("utf-8")
    except Exception:
        pass

    # Get client IP and user agent
    ip_address = request.client.host if request.client else None
    user_agent = headers.get("user-agent")

    # Create log entry
    url_log = url_service.create_url_log(
        url_id=str(url.id),
        method=method,
        headers=headers,
        query_params=query_params,
        body=body,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Return success response
    return {
        "success": True,
        "message": "Request received and logged",
        "log_id": str(url_log.id),
        "url_id": str(url.id),
    }
