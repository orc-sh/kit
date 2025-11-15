# User Context Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        HTTP Request                              │
│                  (with Authorization header)                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Authentication Middleware                       │
│                  (auth_middleware.py)                            │
│                                                                   │
│  1. Extract JWT token from Authorization header                 │
│  2. Verify and decode JWT token                                 │
│  3. Create User instance from JWT payload                       │
│     user = User.from_jwt_payload(payload)                       │
│  4. Set user in thread-safe context                             │
│     set_current_user_context(user)                              │
│  5. Set user in request state (backward compat)                 │
│     request.state.user = user                                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Thread-Safe Context                           │
│                   (user_context.py)                              │
│                                                                   │
│  ┌──────────────────────────────────────────────────┐           │
│  │  ContextVar[User] = current_user                 │           │
│  │  - Isolated per request                          │           │
│  │  - Thread-safe                                   │           │
│  │  - Async-safe                                    │           │
│  │  - Auto cleanup after request                    │           │
│  └──────────────────────────────────────────────────┘           │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Route      │  │  Service    │  │  Utility    │
│  Handlers   │  │  Layer      │  │  Functions  │
└─────────────┘  └─────────────┘  └─────────────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │  Access User via:      │
            │                        │
            │  1. Dependency:        │
            │     Depends(require_   │
            │       user_from_       │
            │       context)         │
            │                        │
            │  2. Direct Context:    │
            │     get_current_user_  │
            │       context()        │
            │                        │
            │  3. Request State:     │
            │     request.state.user │
            └────────────────────────┘
```

## Data Flow

```
JWT Token
    │
    ▼
┌───────────────────────────────────────┐
│ JWT Payload Example:                  │
│ {                                     │
│   "sub": "user-123",                  │
│   "email": "user@example.com",        │
│   "role": "admin",                    │
│   "aud": "authenticated",             │
│   "session_id": "session-456",        │
│   "app_metadata": {...},              │
│   "user_metadata": {...},             │
│   "created_at": "2024-01-01T...",     │
│   ...                                 │
│ }                                     │
└───────────────┬───────────────────────┘
                │
                ▼
┌───────────────────────────────────────┐
│ User.from_jwt_payload(payload)        │
└───────────────┬───────────────────────┘
                │
                ▼
┌───────────────────────────────────────┐
│ User Instance:                        │
│ @dataclass                            │
│ class User:                           │
│   id: str = "user-123"                │
│   email: str = "user@example.com"     │
│   role: str = "admin"                 │
│   aud: str = "authenticated"          │
│   session_id: str = "session-456"     │
│   app_metadata: dict = {...}          │
│   user_metadata: dict = {...}         │
│   created_at: datetime = ...          │
│   ...                                 │
└───────────────┬───────────────────────┘
                │
                ▼
┌───────────────────────────────────────┐
│ set_current_user_context(user)        │
│                                       │
│ Stores in:                            │
│ _current_user: ContextVar[User]       │
└───────────────┬───────────────────────┘
                │
                ▼
┌───────────────────────────────────────┐
│ Available throughout request:         │
│                                       │
│ user = get_current_user_context()     │
│ # Returns: User instance or None      │
│                                       │
│ user = require_current_user_context() │
│ # Returns: User or raises error       │
└───────────────────────────────────────┘
```

## Component Relationships

```
┌──────────────────────────────────────────────────────────────┐
│                        Application                            │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                   Controllers                         │   │
│  │  - auth_controller.py                                 │   │
│  │  - health_controller.py                               │   │
│  │  - ... (your other controllers)                       │   │
│  └────────────┬──────────────────┬──────────────────────┘   │
│               │                  │                           │
│               │                  │                           │
│  ┌────────────▼────────┐  ┌──────▼──────────────────────┐   │
│  │   Middleware        │  │   Dependencies              │   │
│  │  ┌──────────────┐   │  │  ┌──────────────────────┐  │   │
│  │  │ auth_        │   │  │  │ get_current_user_    │  │   │
│  │  │  middleware  │───┼──┼──▶  from_context()      │  │   │
│  │  └──────────────┘   │  │  └──────────────────────┘  │   │
│  │         │            │  │  ┌──────────────────────┐  │   │
│  │         │            │  │  │ require_user_from_   │  │   │
│  │         │            │  │  │  context()           │  │   │
│  │         │            │  │  └──────────────────────┘  │   │
│  │         │            │  └─────────────┬──────────────┘   │
│  │         │            │                │                  │
│  │         ▼            │                ▼                  │
│  │  ┌──────────────┐   │  ┌──────────────────────────┐    │
│  │  │ User Model   │◀──┼──│  Context Management      │    │
│  │  │ (Plain       │   │  │  - set_current_user_     │    │
│  │  │  Python      │   │  │      context()           │    │
│  │  │  Class)      │   │  │  - get_current_user_     │    │
│  │  │              │   │  │      context()           │    │
│  │  │ - from_jwt_  │   │  │  - require_current_user_ │    │
│  │  │    payload() │   │  │      context()           │    │
│  │  │ - to_dict()  │   │  │                          │    │
│  │  │ - has_role() │   │  │  Thread-Safe Storage:    │    │
│  │  │ - ...        │   │  │  ContextVar[User]        │    │
│  │  └──────────────┘   │  └──────────────────────────┘    │
│  └─────────────────────┘                                   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                   Services                            │  │
│  │  - auth_service.py                                    │  │
│  │  - ... (your other services)                          │  │
│  │                                                        │  │
│  │  Can access user via:                                 │  │
│  │  user = get_current_user_context()                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Access Patterns Comparison

### Pattern 1: FastAPI Dependency (Recommended for Routes)

```python
# ✅ Best for route handlers
# ✅ Automatic authentication check
# ✅ Type-safe
# ✅ FastAPI documentation integration

from app.dependencies import require_user_from_context

@router.get("/profile")
async def get_profile(user: User = Depends(require_user_from_context)):
    return {"email": user.email}
```

### Pattern 2: Direct Context Access (Best for Services)

```python
# ✅ Best for service layer
# ✅ No dependency injection needed
# ✅ Works in any function
# ⚠️  Need to handle None case

from app.context.user_context import get_current_user_context

class MyService:
    def process(self):
        user = get_current_user_context()
        if user:
            print(f"Processing for {user.email}")
```

### Pattern 3: Traditional Middleware (For Authentication)

```python
# ✅ Performs authentication
# ✅ Sets user in context
# ✅ Returns User object
# ⚠️  Requires Request object

from app.middleware.auth_middleware import get_current_user

@router.get("/settings")
async def settings(user: User = Depends(get_current_user)):
    return {"user_id": user.id}
```

## Thread Safety and Context Isolation

```
Request 1              Request 2              Request 3
    │                      │                      │
    ▼                      ▼                      ▼
┌─────────┐          ┌─────────┐          ┌─────────┐
│ User A  │          │ User B  │          │ User C  │
│ Context │          │ Context │          │ Context │
└─────────┘          └─────────┘          └─────────┘
    │                      │                      │
    │ Isolated             │ Isolated             │ Isolated
    │ (Thread-Safe)        │ (Thread-Safe)        │ (Thread-Safe)
    │                      │                      │
    ▼                      ▼                      ▼
Route Handler        Route Handler        Route Handler
Service Layer        Service Layer        Service Layer
Utilities            Utilities            Utilities
Background Tasks     Background Tasks     Background Tasks
    │                      │                      │
    ▼                      ▼                      ▼
Auto Cleanup         Auto Cleanup         Auto Cleanup
(After Request)      (After Request)      (After Request)
```

Each request gets its own isolated context. No cross-contamination!

## File Structure

```
scheduler/
├── app/
│   ├── models/
│   │   ├── __init__.py          # Exports User
│   │   ├── user.py              # ⭐ User dataclass
│   │   ├── projects.py
│   │   ├── jobs.py
│   │   └── ...
│   │
│   ├── context/
│   │   ├── __init__.py          # Exports context functions
│   │   ├── user_context.py      # ⭐ Thread-safe context
│   │   └── README.md            # Documentation
│   │
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── auth_middleware.py   # ⭐ Sets user in context
│   │
│   ├── dependencies/
│   │   ├── __init__.py          # Exports dependencies
│   │   └── user.py              # ⭐ FastAPI dependencies
│   │
│   ├── controllers/
│   │   ├── auth_controller.py   # Uses User type
│   │   └── ...
│   │
│   └── services/
│       ├── auth_service.py
│       └── ...
│
├── tests/
│   └── test_user_context.py     # ⭐ Context tests
│
├── examples/
│   └── user_context_example.py  # ⭐ Usage examples
│
├── USER_CONTEXT_IMPLEMENTATION.md   # ⭐ Implementation guide
└── ARCHITECTURE_USER_CONTEXT.md     # ⭐ This file
```

## Key Benefits

1. **Type Safety** 🎯
   - Use `User` class instead of `dict`
   - Full IDE autocomplete support
   - Catch errors at development time

2. **Thread Safety** 🔒
   - Each request gets isolated context
   - No race conditions
   - Works with async/await

3. **Clean Architecture** 🏗️
   - No need to pass user through layers
   - Access user anywhere in your code
   - Separation of concerns

4. **Backward Compatible** ↩️
   - `request.state.user` still works
   - Gradual migration possible
   - No breaking changes

5. **Easy Testing** 🧪
   - Set user in context for tests
   - Mock user easily
   - Isolated test contexts

6. **No Database Coupling** 💾
   - User data stays in Supabase
   - No local user table needed
   - True microservice pattern

## Performance

- **Minimal Overhead**: ContextVar is highly optimized
- **No Database Queries**: User data comes from JWT
- **Single Authentication**: Once per request
- **Memory Efficient**: Auto cleanup after request
- **Async Compatible**: Works with FastAPI async routes

## Security Considerations

✅ **JWT Verification**: Token verified before creating User  
✅ **Thread Isolation**: User context isolated per request  
✅ **Automatic Cleanup**: Context cleared after request  
✅ **No Token Storage**: Token not stored in context  
✅ **Immutable User**: User is a frozen dataclass  

## Common Pitfalls to Avoid

❌ **Don't store user in class attributes**
```python
# BAD
class MyService:
    def __init__(self):
        self.user = get_current_user_context()  # ❌ Don't do this!
```

✅ **Do retrieve user when needed**
```python
# GOOD
class MyService:
    def process(self):
        user = get_current_user_context()  # ✅ Retrieve when needed
```

❌ **Don't assume user is always present**
```python
# BAD
user = get_current_user_context()
print(user.email)  # ❌ Might be None!
```

✅ **Do check for None or use require_***
```python
# GOOD
user = get_current_user_context()
if user:
    print(user.email)  # ✅ Safe

# OR
user = require_current_user_context()  # ✅ Raises if None
print(user.email)
```

## Summary

The User Context system provides a **clean, type-safe, thread-safe** way to access authenticated user information throughout your FastAPI application. It leverages Python's `contextvars` for request-scoped storage and integrates seamlessly with FastAPI's dependency injection system.

**Start using it today!** Just add `user: User = Depends(require_user_from_context)` to your route handlers.

