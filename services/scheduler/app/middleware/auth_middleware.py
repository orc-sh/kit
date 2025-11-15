from typing import Optional

import jwt
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer

from app.context.user_context import set_current_user_context
from app.models.user import User
from config.environment import get_supabase_jwt_secret

security = HTTPBearer()


class AuthMiddleware:
    """Middleware for JWT token verification"""

    _instance = None
    _jwt_secret = None

    def __init__(self):
        # Lazy initialization - only load secret when first needed
        if AuthMiddleware._jwt_secret is None:
            AuthMiddleware._jwt_secret = get_supabase_jwt_secret()
        self.jwt_secret = AuthMiddleware._jwt_secret

    def verify_token(self, token: str) -> dict:
        """
        Verify JWT token and extract user information

        Args:
            token: JWT token string

        Returns:
            Decoded token payload containing user info

        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            # Decode and verify the JWT token
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"], audience="authenticated")
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def __call__(self, request: Request) -> Optional[User]:
        """
        Extract and verify token from request headers

        Args:
            request: FastAPI request object

        Returns:
            User object with authentication information

        Raises:
            HTTPException: If authentication fails
        """
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            # Extract token from "Bearer <token>" format
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify token and extract user info
        jwt_payload = self.verify_token(token)

        # Create User instance from JWT payload
        user = User.from_jwt_payload(jwt_payload)

        # Set user in thread-safe context for access throughout the application
        set_current_user_context(user)

        # Also add to request state for backwards compatibility
        request.state.user = user

        return user


# Lazy singleton instance
_auth_middleware_instance: Optional[AuthMiddleware] = None


def get_auth_middleware() -> AuthMiddleware:
    """Get or create the singleton AuthMiddleware instance"""
    global _auth_middleware_instance
    if _auth_middleware_instance is None:
        _auth_middleware_instance = AuthMiddleware()
    return _auth_middleware_instance


async def get_current_user(request: Request) -> User:
    """
    Dependency function to get current authenticated user

    Args:
        request: FastAPI request object

    Returns:
        User object with authentication information
    """
    auth_middleware = get_auth_middleware()
    user = await auth_middleware(request)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return user
