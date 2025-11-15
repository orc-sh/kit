from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controllers import auth_controller, health_controller
from app.models.base import Base
from config.environment import get_frontend_url, init
from db.engine import engine

# Initialize environment variables FIRST before importing modules that need them
init()

# Create tables if they do not exist
Base.metadata.create_all(bind=engine)

# Create the FastAPI application
app = FastAPI(title="Scheduler API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        get_frontend_url(),
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include each router with a specific prefix and tags for better organization
app.include_router(health_controller.router, prefix="", tags=["Health"])
app.include_router(auth_controller.router, prefix="/auth", tags=["Authentication"])
