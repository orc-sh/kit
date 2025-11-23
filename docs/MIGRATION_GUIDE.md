# Authentication Service Migration Guide

This document describes the migration of authentication functionality from the scheduler service to a standalone authentication service.

## Overview

Authentication logic has been extracted into a separate microservice (`services/auth`) to:
- Improve separation of concerns
- Enable independent scaling of auth operations
- Simplify maintenance and testing
- Allow other services to use the same authentication infrastructure

## What Was Moved

### From `services/scheduler/app/` to `services/auth/app/`:

1. **Controllers**
   - `controllers/auth_controller.py` → Authentication API endpoints

2. **Services**
   - `services/auth_service.py` → OAuth and Supabase integration logic

3. **Middleware**
   - `middleware/auth_middleware.py` → JWT verification middleware

4. **Models**
   - `models/user.py` → User data model

5. **Context**
   - `context/user_context.py` → Thread-safe user context management

## What Stayed in Scheduler Service

The scheduler service still contains:
- A **copy** of the auth middleware for local JWT token validation
- A **copy** of the user model and context for authenticated requests
- References to these for dependency injection in protected routes

**Why?** Token validation needs to happen on every authenticated request. Keeping the middleware local avoids network overhead of calling the auth service for every request.

## Architecture

```
┌─────────────┐         ┌─────────────┐         ┌──────────────┐
│   Frontend  │────────▶│Auth Service │────────▶│   Supabase   │
│             │         │   (8001)    │         │              │
└─────────────┘         └─────────────┘         └──────────────┘
      │                                                  ▲
      │ Bearer Token                                     │
      │                                                  │
      ▼                                                  │
┌─────────────┐                                         │
│  Scheduler  │─────────────────────────────────────────┘
│  Service    │         (validates JWT locally)
│   (8000)    │
└─────────────┘
```

## API Changes

### Before Migration

All auth endpoints were on the scheduler service:
- `http://localhost:8000/auth/oauth/providers`
- `http://localhost:8000/auth/oauth/{provider}`
- `http://localhost:8000/auth/oauth/callback`
- etc.

### After Migration

Auth endpoints are now on the auth service:
- `http://localhost:8001/auth/oauth/providers`
- `http://localhost:8001/auth/oauth/{provider}`
- `http://localhost:8001/auth/oauth/callback`
- etc.

Protected endpoints on the scheduler service still work the same way - just include the JWT token in the `Authorization: Bearer <token>` header.

## Frontend Changes Required

Update your frontend to point to the new auth service URL:

```typescript
// Before
const AUTH_BASE_URL = 'http://localhost:8000/auth';

// After
const AUTH_BASE_URL = 'http://localhost:8001/auth';
```

Or better yet, use an environment variable:

```typescript
const AUTH_BASE_URL = process.env.NEXT_PUBLIC_AUTH_SERVICE_URL || 'http://localhost:8001/auth';
```

## Running the Services

### Development

1. **Start the auth service:**
   ```bash
   cd services/auth
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8001
   ```

   Or use the run script:
   ```bash
   cd services/auth
   ./run.sh
   ```

2. **Start the scheduler service** (as before):
   ```bash
   cd services/scheduler
   # ... existing setup
   ```

### Using Docker Compose

The `docker-compose.yml` has been updated to include the auth service:

```bash
# Start all services
docker-compose up -d

# Or start just the auth service
docker-compose up -d auth
```

## Environment Variables

### Auth Service

Create `services/auth/.env`:

```env
SUPABASE_PROJECT_URL=your_url
SUPABASE_ANON_PUBLIC_KEY=your_key
SUPABASE_JWT_SECRET=your_secret
FRONTEND_URL=http://localhost:3000
AUTH_SERVICE_HOST=0.0.0.0
AUTH_SERVICE_PORT=8001
```

### Scheduler Service

Add to `services/scheduler/.env`:

```env
AUTH_SERVICE_URL=http://localhost:8001
```

## Testing the Migration

1. **Start both services**
2. **Test auth endpoints:**
   ```bash
   # Health check
   curl http://localhost:8001/health
   
   # List OAuth providers
   curl http://localhost:8001/auth/oauth/providers
   ```

3. **Test protected endpoints on scheduler:**
   ```bash
   # This should still work with a valid JWT token
   curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/some-protected-endpoint
   ```

## Rollback Plan

If you need to roll back:

1. Remove the auth service from `docker-compose.yml`
2. In `services/scheduler/app/main.py`, restore:
   ```python
   from app.controllers import auth_controller
   app.include_router(auth_controller.router, prefix="/auth", tags=["Authentication"])
   ```
3. Update frontend to point back to the scheduler service

## Benefits

✅ **Separation of Concerns**: Auth logic is isolated  
✅ **Independent Scaling**: Scale auth separately from scheduler  
✅ **Reusability**: Other services can use the same auth service  
✅ **Simplified Testing**: Test auth independently  
✅ **Better Security**: Easier to audit and secure a focused service  

## Notes

- Both services share the same `SUPABASE_JWT_SECRET` for token validation
- The middleware in both services uses the same JWT verification logic
- Tokens issued by the auth service are valid for both services
- CORS is configured to allow communication between services

