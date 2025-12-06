# Authentication Service

A standalone authentication service for handling OAuth-based authentication using Supabase.

## Features

- OAuth authentication (Google, GitHub)
- JWT token verification and validation
- Token refresh functionality
- User session management
- Thread-safe user context management

## Architecture

This service is responsible for:
- Handling OAuth flows with external providers
- Managing user authentication sessions
- Verifying and validating JWT tokens
- Providing user information endpoints

## Setup

### Environment Variables

Create a `.env` file in the service root:

```env
SUPABASE_PROJECT_URL=your_supabase_url
SUPABASE_ANON_PUBLIC_KEY=your_supabase_anon_key
SUPABASE_JWT_SECRET=your_supabase_jwt_secret
FRONTEND_URL=http://localhost:3000
AUTH_SERVICE_HOST=0.0.0.0
AUTH_SERVICE_PORT=8001
```

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Service

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

## API Endpoints

### Authentication

- `GET /auth/oauth/providers` - List available OAuth providers
- `GET /auth/oauth/{provider}` - Initiate OAuth flow
- `POST /auth/oauth/callback` - Handle OAuth callback
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Sign out user
- `GET /auth/me` - Get current user information

### Health

- `GET /health` - Service health check

## Account Structure

```
services/auth/
├── app/
│   ├── controllers/       # API route handlers
│   ├── middleware/        # Authentication middleware
│   ├── models/           # Data models
│   ├── services/         # Business logic
│   ├── context/          # User context management
│   └── main.py          # FastAPI application
├── config/
│   └── environment.py    # Configuration management
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Development

### Code Style

This account follows PEP 8 guidelines. Use `black` for formatting and `flake8` for linting.

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

## Integration with Other Services

Other services can authenticate requests by:
1. Obtaining a JWT token from this service's OAuth flow
2. Including the token in the `Authorization: Bearer <token>` header
3. Validating tokens using the shared JWT secret

## Security Considerations

- All authentication endpoints use HTTPS in production
- JWT secrets must be kept secure and shared only with trusted services
- Tokens have expiration times and should be refreshed regularly
- OAuth callbacks validate state parameters to prevent CSRF attacks

