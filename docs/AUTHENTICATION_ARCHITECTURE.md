# Authentication Architecture

## Overview

This document describes the authentication architecture after migrating to a microservices approach. Authentication functionality has been separated into its own standalone service.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                        │
│                      http://localhost:3000                       │
└────────────┬────────────────────────────────┬───────────────────┘
             │                                │
             │ OAuth Flow                     │ API Requests
             │                                │ (with JWT token)
             ▼                                ▼
┌────────────────────────┐      ┌────────────────────────────────┐
│   Auth Service         │      │    Scheduler Service           │
│   Port: 8001          │◄─────│    Port: 8000                  │
│                        │      │                                │
│ Responsibilities:      │      │ Responsibilities:              │
│ - OAuth initiation     │      │ - Business logic               │
│ - Token generation     │      │ - Job scheduling               │
│ - Token refresh        │      │ - Protected endpoints          │
│ - User info endpoints  │      │ - JWT validation (local)       │
└────────┬───────────────┘      └────────┬───────────────────────┘
         │                               │
         │ JWT Secret                    │ JWT Secret
         │ (shared)                      │ (shared)
         │                               │
         ▼                               ▼
┌────────────────────────────────────────────────────────────────┐
│                        Supabase                                 │
│                                                                 │
│  - User Management                                             │
│  - OAuth Providers (Google, GitHub)                            │
│  - JWT Token Signing                                           │
└────────────────────────────────────────────────────────────────┘
```

## Services

### 1. Authentication Service (`services/auth`)

**Port:** 8001  
**Purpose:** Centralized authentication and authorization

#### Components

- **`app/controllers/auth_controller.py`** - API endpoints for authentication
- **`app/services/auth_service.py`** - Business logic for OAuth and Supabase
- **`app/middleware/auth_middleware.py`** - JWT verification middleware
- **`app/models/user.py`** - User data model
- **`app/context/user_context.py`** - Thread-safe user context
- **`config/environment.py`** - Configuration management

#### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/oauth/providers` | List available OAuth providers |
| GET | `/auth/oauth/{provider}` | Initiate OAuth flow |
| POST | `/auth/oauth/callback` | Handle OAuth callback |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Sign out user |
| GET | `/auth/me` | Get current user info |
| GET | `/health` | Health check |

### 2. Scheduler Service (`services/scheduler`)

**Port:** 8000  
**Purpose:** Business logic and job scheduling

#### Authentication Integration

The scheduler service:
1. **Does NOT** handle OAuth flows (delegated to auth service)
2. **DOES** validate JWT tokens locally for performance
3. **DOES** maintain copies of:
   - `app/middleware/auth_middleware.py` - For local token validation
   - `app/models/user.py` - For user data structure
   - `app/context/user_context.py` - For request-scoped user context

#### New Component

- **`app/clients/auth_client.py`** - HTTP client for communicating with auth service (optional use)

## Authentication Flow

### 1. OAuth Login Flow

```
1. User clicks "Login with Google" on Frontend
   ↓
2. Frontend → Auth Service: GET /auth/oauth/google
   ↓
3. Auth Service → Frontend: Returns OAuth URL
   ↓
4. Frontend redirects user to Google OAuth
   ↓
5. User authorizes → Google redirects to frontend/auth/callback?code=...
   ↓
6. Frontend → Auth Service: POST /auth/oauth/callback {code}
   ↓
7. Auth Service → Supabase: Exchange code for session
   ↓
8. Auth Service → Frontend: Returns {access_token, refresh_token, user}
   ↓
9. Frontend stores tokens (localStorage/cookie)
```

### 2. Authenticated API Request Flow

```
1. Frontend makes API request to Scheduler Service
   Headers: Authorization: Bearer <access_token>
   ↓
2. Scheduler Service → Auth Middleware: Verify JWT
   ↓
3. Middleware validates JWT locally using shared JWT secret
   (No network call to auth service needed!)
   ↓
4. If valid: Request proceeds with user context
   If invalid: Return 401 Unauthorized
```

### 3. Token Refresh Flow

```
1. Frontend detects expired token (401 response)
   ↓
2. Frontend → Auth Service: POST /auth/refresh {refresh_token}
   ↓
3. Auth Service → Supabase: Verify refresh token
   ↓
4. Auth Service → Frontend: Returns new {access_token, refresh_token}
   ↓
5. Frontend stores new tokens and retries original request
```

## Security

### Shared JWT Secret

Both services share the same `SUPABASE_JWT_SECRET` for token validation:
- Tokens signed by Supabase (via auth service)
- Tokens validated by both services
- This enables local validation without network calls

### Environment Variables

#### Auth Service (`.env`)
```env
SUPABASE_PROJECT_URL=https://your-project.supabase.co
SUPABASE_ANON_PUBLIC_KEY=your_anon_key
SUPABASE_JWT_SECRET=your_jwt_secret
FRONTEND_URL=http://localhost:3000
AUTH_SERVICE_HOST=0.0.0.0
AUTH_SERVICE_PORT=8001
```

#### Scheduler Service (`.env`)
```env
SUPABASE_JWT_SECRET=your_jwt_secret  # Same as auth service!
AUTH_SERVICE_URL=http://localhost:8001
FRONTEND_URL=http://localhost:3000
# ... other config
```

### CORS Configuration

Both services allow:
- Frontend origin (`http://localhost:3000`)
- Each other's origins (for inter-service communication)

## Why This Architecture?

### ✅ Benefits

1. **Separation of Concerns**
   - Auth logic isolated from business logic
   - Easier to maintain and test

2. **Performance**
   - JWT validation is local (no network overhead)
   - Only OAuth flows hit the auth service

3. **Scalability**
   - Scale auth service independently
   - Can handle different load patterns

4. **Reusability**
   - Other services can use the same auth service
   - Consistent auth across microservices

5. **Security**
   - Centralized auth management
   - Easier to audit and secure

### 📊 Performance Considerations

**Local JWT Validation vs Remote Validation:**
- Local validation: ~0.1ms (in-memory)
- Remote validation: ~10-50ms (network call)

Since protected endpoints need auth on EVERY request, local validation is crucial for performance.

## Development Workflow

### Running Services

**Option 1: Manual**
```bash
# Terminal 1 - Auth Service
cd services/auth
source venv/bin/activate
uvicorn app.main:app --reload --port 8001

# Terminal 2 - Scheduler Service
cd services/scheduler
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Option 2: Docker Compose**
```bash
docker-compose up -d
```

### Testing

**Test Auth Service:**
```bash
# Health check
curl http://localhost:8001/health

# List providers
curl http://localhost:8001/auth/oauth/providers

# Test token validation
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8001/auth/me
```

**Test Scheduler Service:**
```bash
# Health check
curl http://localhost:8000/health

# Protected endpoint (requires valid JWT)
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/some-endpoint
```

## Migration Notes

See [services/auth/MIGRATION_GUIDE.md](services/auth/MIGRATION_GUIDE.md) for detailed migration information.

## Future Enhancements

- [ ] Add rate limiting to auth endpoints
- [ ] Implement refresh token rotation
- [ ] Add audit logging for auth events
- [ ] Support additional OAuth providers
- [ ] Implement session management
- [ ] Add 2FA support
- [ ] Create admin endpoints for user management

## Troubleshooting

### Common Issues

**Issue:** Token validation fails in scheduler service  
**Solution:** Ensure `SUPABASE_JWT_SECRET` is identical in both services

**Issue:** CORS errors between frontend and auth service  
**Solution:** Check `FRONTEND_URL` is set correctly in auth service config

**Issue:** Auth service can't start  
**Solution:** Check all required environment variables are set

**Issue:** OAuth callback fails  
**Solution:** Verify redirect URLs are configured correctly in Supabase dashboard

## Contact

For questions or issues, please refer to the README files in each service directory.

