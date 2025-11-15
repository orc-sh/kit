# User Context Management

This module provides thread-safe context storage for the authenticated user throughout the application lifecycle.

## Overview

The user context system uses Python's `contextvars` module to store the current authenticated user in a thread-safe manner. This allows you to access the current user anywhere in your application without explicitly passing it through function parameters.

## How It Works

1. **Authentication Middleware**: When a request is authenticated, the middleware creates a `User` instance from the JWT token and stores it in the context.

2. **Thread-Safe Storage**: Each request gets its own isolated context using `contextvars`, which is thread-safe and async-safe.

3. **Access Throughout Application**: Any part of your application can access the current user from the context.

## Usage Examples

### In FastAPI Route Handlers

#### Using the Dependency (Recommended)

```python
from fastapi import APIRouter, Depends
from app.dependencies import require_user_from_context
from app.models.user import User

router = APIRouter()

@router.get("/my-endpoint")
async def my_endpoint(user: User = Depends(require_user_from_context)):
    # User is automatically injected from context
    return {"user_id": user.id, "email": user.email}
```

#### Using get_current_user (from middleware - with Request object)

```python
from fastapi import APIRouter, Depends
from app.middleware.auth_middleware import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/my-endpoint")
async def my_endpoint(user: User = Depends(get_current_user)):
    # This also authenticates and sets context
    return {"user_id": user.id, "email": user.email}
```

### In Service Classes

```python
from app.context.user_context import get_current_user_context, require_current_user_context
from app.models.user import User

class MyService:
    def process_data(self):
        # Get user if available (returns None if not authenticated)
        user = get_current_user_context()
        if user:
            print(f"Processing for user: {user.email}")
        
    def process_authenticated(self):
        # Require user (raises RuntimeError if not authenticated)
        user = require_current_user_context()
        print(f"User {user.email} is authenticated")
```

### In Background Tasks

```python
from fastapi import BackgroundTasks
from app.context.user_context import get_current_user_context

def background_task():
    # Get the user from the context
    user = get_current_user_context()
    if user:
        print(f"Background task for user: {user.email}")

@router.post("/trigger-task")
async def trigger_task(
    background_tasks: BackgroundTasks,
    user: User = Depends(require_user_from_context)
):
    # User is in context and will be available in background task
    background_tasks.add_task(background_task)
    return {"message": "Task scheduled"}
```

### In Utility Functions

```python
from app.context.user_context import get_current_user_context

def log_user_action(action: str):
    """Log an action with the current user's information."""
    user = get_current_user_context()
    if user:
        print(f"User {user.email} performed action: {action}")
    else:
        print(f"Anonymous user performed action: {action}")
```

## User Model

The `User` class is a plain Python dataclass (not a database model) with the following attributes:

```python
@dataclass
class User:
    id: str                                    # User ID from Supabase
    email: Optional[str]                       # User email
    phone: Optional[str]                       # User phone number
    role: Optional[str]                        # User role
    aud: Optional[str]                         # Audience claim from JWT
    session_id: Optional[str]                  # Session ID
    app_metadata: Optional[Dict[str, Any]]     # Application metadata
    user_metadata: Optional[Dict[str, Any]]    # User metadata
    created_at: Optional[datetime]             # Account creation timestamp
    updated_at: Optional[datetime]             # Last update timestamp
    email_confirmed_at: Optional[datetime]     # Email confirmation timestamp
    phone_confirmed_at: Optional[datetime]     # Phone confirmation timestamp
    confirmed_at: Optional[datetime]           # General confirmation timestamp
    last_sign_in_at: Optional[datetime]        # Last sign-in timestamp
```

### User Methods

```python
# Create from JWT payload
user = User.from_jwt_payload(jwt_payload)

# Create from Supabase user object
user = User.from_supabase_user(user_data)

# Convert to dictionary
user_dict = user.to_dict()

# Check role
if user.has_role("admin"):
    print("User is an admin")

# Check email confirmation
if user.is_email_confirmed():
    print("Email is confirmed")
```

## API Reference

### Context Functions

#### `set_current_user_context(user: Optional[User]) -> None`
Set the current user in the context. Called by authentication middleware.

#### `get_current_user_context() -> Optional[User]`
Get the current user from the context. Returns `None` if not set.

#### `require_current_user_context() -> User`
Get the current user from the context. Raises `RuntimeError` if not set.

#### `clear_current_user_context() -> None`
Clear the current user from the context.

### FastAPI Dependencies

#### `get_current_user_from_context() -> Optional[User]`
FastAPI dependency that returns the current user or `None`.

#### `require_user_from_context() -> User`
FastAPI dependency that returns the current user or raises `HTTPException(401)`.

## Best Practices

1. **Use Dependencies**: In FastAPI route handlers, prefer using dependencies (`Depends(require_user_from_context)`) for automatic authentication checks.

2. **Check for None**: When using `get_current_user_context()` directly, always check if the result is `None` before accessing user properties.

3. **Use require_* for Protected Routes**: Use `require_user_from_context()` or `require_current_user_context()` for routes that require authentication.

4. **Don't Store User in Class Attributes**: Since the context is request-scoped, don't store the user in class-level variables. Always retrieve it from context when needed.

5. **Thread Safety**: The context is automatically thread-safe and async-safe. You don't need to worry about race conditions.

## Migration Guide

If you were previously using `user: dict = Depends(get_current_user)`, you can now use:

```python
# Old way
user: dict = Depends(get_current_user)
user_id = user.get("sub")
user_email = user.get("email")

# New way
user: User = Depends(get_current_user)
user_id = user.id
user_email = user.email
```

Or use the context-based approach:

```python
user: User = Depends(require_user_from_context)
```

