import os

from dotenv import load_dotenv


# Load environment variables from the .env file
def init():
    load_dotenv()


def get_supabase_url() -> str:
    """Get Supabase account URL from environment"""
    url = os.getenv("SUPABASE_PROJECT_URL")
    if not url:
        raise ValueError("SUPABASE_PROJECT_URL environment variable is not set")
    return url


def get_supabase_key() -> str:
    """Get Supabase anon/public key from environment"""
    key = os.getenv("SUPABASE_ANON_PUBLIC_KEY")
    if not key:
        raise ValueError("SUPABASE_ANON_PUBLIC_KEY environment variable is not set")
    return key


def get_supabase_jwt_secret() -> str:
    """Get Supabase JWT secret for token verification"""
    secret = os.getenv("SUPABASE_JWT_SECRET")
    if not secret:
        raise ValueError("SUPABASE_JWT_SECRET environment variable is not set")
    return secret


def get_frontend_url() -> str:
    """Get frontend URL for CORS and redirects"""
    return os.getenv("FRONTEND_URL", "https://www.localhooks.com")


def get_auth_service_port() -> int:
    """Get port for auth service"""
    return int(os.getenv("AUTH_SERVICE_PORT", "8001"))


def get_auth_service_host() -> str:
    """Get host for auth service"""
    return os.getenv("AUTH_SERVICE_HOST", "0.0.0.0")

