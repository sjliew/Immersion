from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import users, conversations, expressions, progress, audio, practice, admin, admin_import, voice_samples, completions, journal, characters
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Express Language Learning API",
    version="1.0.0",
    description="Backend API for Express language learning mobile app"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
app.include_router(expressions.router, prefix="/api/expressions", tags=["expressions"])
app.include_router(progress.router, prefix="/api/progress", tags=["progress"])
app.include_router(audio.router, prefix="/api/audio", tags=["audio"])
app.include_router(practice.router, prefix="/api/practice", tags=["practice"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(admin_import.router, prefix="/api/import", tags=["import"])
# app.include_router(test_import.router, prefix="/api/test", tags=["test"])  # Disabled for production
app.include_router(voice_samples.router, prefix="/api/voices", tags=["voices"])
app.include_router(completions.router, prefix="/api/completions", tags=["completions"])
app.include_router(journal.router, prefix="/api/journal", tags=["journal"])
app.include_router(characters.router, prefix="/api/characters", tags=["characters"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "Express Language Learning API",
        "version": "1.0.0",
        "status": "running"
    }

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.environment
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info(f"🚀 Server starting in {settings.environment} mode")
    logger.info(f"📝 Supabase URL: {settings.supabase_url}")
    logger.info(f"🔗 CORS Origins: {settings.cors_origins}")
    
    # Initialize Supabase infrastructure in development
    if settings.is_development:
        try:
            from app.config.infrastructure import infrastructure
            await infrastructure.initialize_infrastructure()
            logger.info("✅ Supabase infrastructure initialized")
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize infrastructure: {e}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Server shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development
    )