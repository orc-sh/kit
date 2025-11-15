# Quick Start - Authentication Service

## 📋 What Changed

Authentication has been moved from the scheduler service to a **separate authentication service** running on **port 8001**.

## 🚀 Quick Setup

### 1. Create Environment File

Create `services/auth/.env` with your credentials:

```bash
cd services/auth
cp .env.example .env
# Edit .env with your actual values
```

### 2. Install Dependencies

```bash
cd services/auth
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run Auth Service

**Option A - Using run script:**
```bash
cd services/auth
./run.sh
```

**Option B - Direct command:**
```bash
cd services/auth
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

**Option C - Docker:**
```bash
# From project root
docker-compose up -d auth
```

### 4. Verify It's Running

```bash
# Health check
curl http://localhost:8001/health

# Should return: {"status":"healthy","service":"auth"}
```

## 🔧 Update Frontend

Change your frontend auth URLs from port 8000 to 8001:

```typescript
// Before
const AUTH_URL = 'http://localhost:8000/auth';

// After
const AUTH_URL = 'http://localhost:8001/auth';
```

Or use environment variable:
```env
NEXT_PUBLIC_AUTH_SERVICE_URL=http://localhost:8001
```

## 📝 Scheduler Service Changes

The scheduler service (`services/scheduler`) now:
- ✅ Validates JWT tokens locally (no auth service call needed)
- ❌ No longer handles OAuth flows
- ✅ Still protects endpoints with authentication middleware

**No changes needed** in how you call protected endpoints - just include the JWT token as before.

## 🔐 Environment Variables

### Auth Service (.env)

```env
SUPABASE_PROJECT_URL=https://your-project.supabase.co
SUPABASE_ANON_PUBLIC_KEY=your_anon_key
SUPABASE_JWT_SECRET=your_jwt_secret
FRONTEND_URL=http://localhost:3000
AUTH_SERVICE_HOST=0.0.0.0
AUTH_SERVICE_PORT=8001
```

### Scheduler Service (.env)

Add this to your existing scheduler `.env`:

```env
AUTH_SERVICE_URL=http://localhost:8001
```

⚠️ **Important:** `SUPABASE_JWT_SECRET` must be **identical** in both services!

## 📚 API Endpoints

### Auth Service (Port 8001)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/auth/oauth/providers` | GET | List OAuth providers |
| `/auth/oauth/{provider}` | GET | Start OAuth flow |
| `/auth/oauth/callback` | POST | Handle OAuth callback |
| `/auth/refresh` | POST | Refresh access token |
| `/auth/logout` | POST | Sign out user |
| `/auth/me` | GET | Get user info |

### Scheduler Service (Port 8000)

- Auth endpoints **removed** from scheduler
- Protected endpoints still work with JWT tokens
- Include token: `Authorization: Bearer YOUR_TOKEN`

## 🧪 Testing

```bash
# Test auth service
curl http://localhost:8001/health
curl http://localhost:8001/auth/oauth/providers

# Test with token
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8001/auth/me

# Test scheduler service (protected endpoint)
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/some-endpoint
```

## 🐳 Docker Setup

Run both services with Docker:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f auth

# Stop services
docker-compose down
```

## 📖 More Information

- **Architecture Details:** See `AUTHENTICATION_ARCHITECTURE.md`
- **Migration Guide:** See `services/auth/MIGRATION_GUIDE.md`
- **Complete Summary:** See `REFACTORING_SUMMARY.md`
- **Auth Service Docs:** See `services/auth/README.md`

## ✅ Checklist

Before going to production:

- [ ] Environment variables set in both services
- [ ] JWT secret matches in both services
- [ ] Both services can start independently
- [ ] Frontend updated to use port 8001 for auth
- [ ] CORS configured correctly
- [ ] OAuth redirect URLs updated in Supabase dashboard
- [ ] Tested OAuth flow end-to-end
- [ ] Tested protected endpoints on scheduler
- [ ] Tested token refresh flow

## 🆘 Troubleshooting

**Service won't start:**
- Check all environment variables are set
- Verify port 8001 is not already in use

**Token validation fails:**
- Ensure `SUPABASE_JWT_SECRET` is identical in both services
- Check token hasn't expired

**CORS errors:**
- Verify `FRONTEND_URL` is set correctly
- Check browser console for specific CORS error

**OAuth redirect fails:**
- Verify redirect URL in Supabase dashboard matches your setup
- Check callback URL in auth service matches frontend expectation

## 🎉 Success!

Your authentication is now running as a separate microservice!

Benefits:
- ✅ Independent scaling
- ✅ Cleaner separation of concerns  
- ✅ Reusable across multiple services
- ✅ Easier to maintain and test

Happy coding! 🚀

