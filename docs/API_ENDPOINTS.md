# Authentication Service API Endpoints

## Base URL

- **Development:** `http://localhost:8001`
- **Production:** Set via `AUTH_SERVICE_URL` environment variable

## API Routes

All authentication routes are prefixed with `/api` for consistency.

### OAuth Endpoints (`/api/oauth`)

#### 1. List OAuth Providers

```
GET /api/oauth/providers
```

**Description:** Get list of available OAuth providers

**Response:**
```json
[
  {
    "name": "google",
    "display_name": "Google"
  },
  {
    "name": "github",
    "display_name": "GitHub"
  }
]
```

#### 2. Initiate OAuth Flow

```
GET /api/oauth/{provider}
```

**Description:** Get OAuth authorization URL for a specific provider

**Parameters:**
- `provider` (path): OAuth provider name (google, github)

**Response:**
```json
{
  "url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "provider": "google"
}
```

**Errors:**
- `400`: Provider not supported
- `500`: Failed to initiate OAuth flow

#### 3. OAuth Callback

```
POST /api/oauth/callback
```

**Description:** Exchange OAuth authorization code for session tokens

**Request Body:**
```json
{
  "code": "authorization_code_from_oauth_provider"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": 1234567890,
  "user": {
    "id": "user-uuid",
    "email": "user@example.com",
    "user_metadata": {}
  }
}
```

**Errors:**
- `400`: Failed to exchange code for session

### Authentication Endpoints (`/api/auth`)

#### 4. Refresh Token

```
POST /api/auth/refresh
```

**Description:** Refresh an expired access token

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": 1234567890
}
```

**Errors:**
- `401`: Failed to refresh token (invalid or expired refresh token)

#### 5. Logout

```
POST /api/auth/logout
```

**Description:** Sign out the current user

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

**Errors:**
- `401`: Unauthorized (missing or invalid token)
- `500`: Failed to log out

#### 6. Get Current User

```
GET /api/auth/me
```

**Description:** Get current authenticated user's information

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "user_metadata": {
    "full_name": "John Doe",
    "avatar_url": "https://..."
  }
}
```

**Errors:**
- `401`: Invalid or expired token

### Health Check

#### 7. Health Check

```
GET /health
```

**Description:** Check if the service is healthy

**Response:**
```json
{
  "status": "healthy",
  "service": "auth"
}
```

## Authentication Flow

### 1. OAuth Login

```
1. Frontend → GET /api/oauth/{provider}
2. Backend → Returns OAuth URL
3. Frontend → Redirects user to OAuth URL
4. User authorizes on provider
5. Provider → Redirects to frontend with code
6. Frontend → POST /api/oauth/callback with code
7. Backend → Returns tokens and user info
```

### 2. Using Protected Endpoints

```
Include the access token in the Authorization header:

Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 3. Token Refresh

```
When you receive a 401 Unauthorized:

1. Frontend → POST /api/auth/refresh with refresh_token
2. Backend → Returns new tokens
3. Frontend → Retries original request with new access_token
```

## Code Examples

### JavaScript/TypeScript

```typescript
// Get OAuth URL
const response = await fetch('http://localhost:8001/api/oauth/google');
const { url } = await response.json();
window.location.href = url;

// Exchange code for tokens
const response = await fetch('http://localhost:8001/api/oauth/callback', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ code: 'authorization_code' })
});
const { access_token, refresh_token, user } = await response.json();

// Get current user
const response = await fetch('http://localhost:8001/api/auth/me', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
const user = await response.json();

// Refresh token
const response = await fetch('http://localhost:8001/api/auth/refresh', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ refresh_token })
});
const { access_token: newToken } = await response.json();
```

### Python

```python
import httpx

# Get OAuth URL
async with httpx.AsyncClient() as client:
    response = await client.get('http://localhost:8001/api/oauth/google')
    data = response.json()
    oauth_url = data['url']

# Exchange code for tokens
async with httpx.AsyncClient() as client:
    response = await client.post(
        'http://localhost:8001/api/oauth/callback',
        json={'code': 'authorization_code'}
    )
    data = response.json()
    access_token = data['access_token']

# Get current user
async with httpx.AsyncClient() as client:
    response = await client.get(
        'http://localhost:8001/api/auth/me',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    user = response.json()
```

## Migration from Previous Version

If you were using the old paths without `/api` prefix:

| Old Path | New Path |
|----------|----------|
| `/auth/oauth/providers` | `/api/oauth/providers` |
| `/auth/oauth/{provider}` | `/api/oauth/{provider}` |
| `/auth/oauth/callback` | `/api/oauth/callback` |
| `/auth/refresh` | `/api/auth/refresh` |
| `/auth/logout` | `/api/auth/logout` |
| `/auth/me` | `/api/auth/me` |

Simply add `/api` before the existing paths in your frontend code.

## Testing

```bash
# Health check
curl http://localhost:8001/health

# List providers
curl http://localhost:8001/api/oauth/providers

# Get user info (with valid token)
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8001/api/auth/me
```

## Interactive Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI:** http://localhost:8001/docs
- **ReDoc:** http://localhost:8001/redoc

