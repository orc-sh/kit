# User Context Implementation Summary

## Overview

I've successfully created a plain Python `User` class that can be initialized during middleware authentication and stored in a thread-safe context for use throughout your application. This implementation uses Python's `contextvars` module to provide request-scoped, thread-safe access to the authenticated user.

## Files Created/Modified

### New Files

1. **`app/models/user.py`** - Plain Python User dataclass
   - `User` class with all user fields from Supabase JWT
   - Factory methods: `from_jwt_payload()`, `from_supabase_user()`
   - Utility methods: `to_dict()`, `has_role()`, `is_email_confirmed()`, etc.

2. **`app/context/user_context.py`** - Thread-safe context management
   - `set_current_user_context(user)` - Set user in context (called by middleware)
   - `get_current_user_context()` - Get user from context (returns None if not set)
   - `require_current_user_context()` - Get user or raise RuntimeError
   - `clear_current_user_context()` - Clear user from context

3. **`app/context/__init__.py`** - Context module exports

4. **`app/dependencies/user.py`** - FastAPI dependencies
   - `get_current_user_from_context()` - Optional user dependency
   - `require_user_from_context()` - Required user dependency (raises 401 if not authenticated)

5. **`app/dependencies/__init__.py`** - Dependencies module exports

6. **`app/context/README.md`** - Comprehensive documentation with examples

7. **`examples/user_context_example.py`** - Complete examples showing all usage patterns

### Modified Files

1. **`app/middleware/auth_middleware.py`**
   - Updated to create `User` instance from JWT payload
   - Sets user in context using `set_current_user_context()`
   - Returns `User` object instead of dict

2. **`app/models/__init__.py`**
   - Added `User` to model exports

3. **`app/controllers/auth_controller.py`**
   - Updated type hints from `dict` to `User` for authenticated endpoints

## How It Works

### 1. Authentication Flow

```
Request with JWT Token
    ↓
Authentication Middleware (auth_middleware.py)
    ↓
Verify JWT Token
    ↓
Create User Instance (User.from_jwt_payload)
    ↓
Set in Context (set_current_user_context)
    ↓
Set in Request State (request.state.user)
    ↓
Continue to Route Handler
```

### 2. Context Storage

- Uses Python's `contextvars.ContextVar` for thread-safe storage
- Each request gets its own isolated context
- Automatically cleaned up after request completes
- Works with both sync and async code

### 3. Access Patterns

#### Pattern A: FastAPI Dependency (Recommended)

```python
from fastapi import APIRouter, Depends
from app.dependencies import require_user_from_context
from app.models.user import User

router = APIRouter()

@router.get("/profile")
async def get_profile(user: User = Depends(require_user_from_context)):
    return {"email": user.email, "id": user.id}
```

#### Pattern B: Direct Context Access

```python
from app.context.user_context import get_current_user_context

def some_service_method():
    user = get_current_user_context()
    if user:
        print(f"Current user: {user.email}")
```

#### Pattern C: Traditional Middleware Dependency

```python
from app.middleware.auth_middleware import get_current_user
from app.models.user import User

@router.get("/settings")
async def get_settings(user: User = Depends(get_current_user)):
    return {"user_id": user.id}
```

## User Class Structure

```python
@dataclass
class User:
    id: str                                    # User ID from Supabase
    email: Optional[str] = None                # User email
    phone: Optional[str] = None                # Phone number
    role: Optional[str] = None                 # User role
    aud: Optional[str] = None                  # JWT audience
    session_id: Optional[str] = None           # Session ID
    app_metadata: Optional[Dict] = None        # App metadata
    user_metadata: Optional[Dict] = None       # User metadata
    created_at: Optional[datetime] = None      # Creation timestamp
    updated_at: Optional[datetime] = None      # Update timestamp
    email_confirmed_at: Optional[datetime] = None
    phone_confirmed_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    last_sign_in_at: Optional[datetime] = None
```

### Useful Methods

- `user.has_role(role: str) -> bool` - Check if user has a specific role
- `user.is_email_confirmed() -> bool` - Check if email is confirmed
- `user.is_phone_confirmed() -> bool` - Check if phone is confirmed
- `user.to_dict() -> dict` - Convert to dictionary
- `User.from_jwt_payload(payload) -> User` - Create from JWT
- `User.from_supabase_user(data) -> User` - Create from Supabase user object

## Usage Examples

### Example 1: Protected Route

```python
from fastapi import APIRouter, Depends
from app.dependencies import require_user_from_context
from app.models.user import User

router = APIRouter()

@router.get("/dashboard")
async def dashboard(user: User = Depends(require_user_from_context)):
    """Requires authentication - will return 401 if not authenticated."""
    return {
        "user_id": user.id,
        "email": user.email,
        "is_admin": user.has_role("admin")
    }
```

### Example 2: Optional Authentication

```python
from typing import Optional
from app.dependencies import get_current_user_from_context

@router.get("/content")
async def get_content(user: Optional[User] = Depends(get_current_user_from_context)):
    """Works with or without authentication."""
    if user:
        return {"personalized": True, "user_email": user.email}
    else:
        return {"personalized": False, "content": "public data"}
```

### Example 3: Service Layer

```python
from app.context.user_context import get_current_user_context

class MyService:
    def process_data(self):
        # Access user from context in any service method
        user = get_current_user_context()
        if user:
            print(f"Processing for user: {user.email}")
            # Use user.id, user.role, etc.
```

### Example 4: Utility Function

```python
from app.context.user_context import require_current_user_context

def audit_log(action: str):
    """Log actions with user information."""
    user = require_current_user_context()
    print(f"User {user.email} performed: {action}")
```

### Example 5: Role-Based Access Control

```python
def require_admin(user: User = Depends(require_user_from_context)) -> User:
    if not user.has_role("admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

@router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin: User = Depends(require_admin)):
    # Only admins can access this endpoint
    return {"deleted": user_id, "by": admin.email}
```

## Benefits

1. **Type Safety**: Use `User` class instead of raw dictionaries
2. **Thread Safety**: Context is automatically isolated per request
3. **Clean API**: Access user anywhere without passing through parameters
4. **Backwards Compatible**: Existing code using `request.state.user` still works
5. **Easy Testing**: Can set user in context for testing
6. **No Database Model**: User data stays in Supabase, no local DB pollution

## Migration Guide

### Before (using dict)
```python
user: dict = Depends(get_current_user)
user_id = user.get("sub")
user_email = user.get("email")
```

### After (using User class)
```python
user: User = Depends(get_current_user)
user_id = user.id
user_email = user.email
```

## Testing

### Setting User in Context for Tests

```python
from app.models.user import User
from app.context.user_context import set_current_user_context

def test_my_endpoint():
    # Create a test user
    test_user = User(
        id="test-123",
        email="test@example.com",
        role="admin"
    )
    
    # Set in context
    set_current_user_context(test_user)
    
    # Now your code can access the user from context
    # ... run your test ...
```

## Best Practices

1. ✅ **Use dependencies** in route handlers for automatic auth checks
2. ✅ **Use context access** in services and utilities for clean code
3. ✅ **Check for None** when using `get_current_user_context()`
4. ✅ **Use require_*** variants for routes that need authentication
5. ❌ **Don't store** user in class-level variables
6. ❌ **Don't manually** set context (let middleware do it)
7. ✅ **Always use** type hints: `user: User` not `user: dict`

## Documentation

- Full documentation: `app/context/README.md`
- Complete examples: `examples/user_context_example.py`
- Model definition: `app/models/user.py`
- Context implementation: `app/context/user_context.py`

## Next Steps

You can now use the User class throughout your application! The middleware automatically:
1. Authenticates requests
2. Creates User instances from JWT tokens
3. Sets them in the thread-safe context
4. Makes them available to all your code

Simply use `user: User = Depends(require_user_from_context)` in your route handlers, or call `get_current_user_context()` from anywhere in your services.

