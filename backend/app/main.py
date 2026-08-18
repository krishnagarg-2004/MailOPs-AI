from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1.ai import router as ai_router
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.gmail import router as gmail_router
from backend.app.core.config import settings


app = FastAPI(
    title=settings.APP_NAME,
    description="FastAPI Backend for MailOps AI work-intelligence platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(gmail_router, prefix=settings.API_V1_STR)
app.include_router(ai_router, prefix=settings.API_V1_STR)





@app.get("/health", tags=["Health"])
@app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify backend operational readiness."""
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "0.1.0",
    }
