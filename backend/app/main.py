import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.config import settings
from app.routers import upload, chat, database
from app.models.database import Base, engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables using Alembic migrations instead of direct creation
try:
    # Import and run Alembic migrations
    from alembic import command
    from alembic.config import Config
    
    # Create Alembic config
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)
    
    # Run migrations
    command.upgrade(alembic_cfg, "head")
    logger.info("Database migrations applied successfully")
except Exception as e:
    logger.error(f"Error applying database migrations: {e}")
    # Fallback to direct table creation if migrations fail
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully (fallback)")
    except Exception as fallback_error:
        logger.error(f"Error creating database tables: {fallback_error}")

# Create uploads directory
try:
    os.makedirs(settings.upload_dir, exist_ok=True)
    logger.info(f"Upload directory created: {settings.upload_dir}")
except Exception as e:
    logger.error(f"Error creating upload directory: {e}")

app = FastAPI(
    title="QLens - Data Conversation API",
    description="An AI-powered data conversation platform for analyzing Excel, CSV, and PostgreSQL data",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(database.router, prefix="/api/v1")

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "QLens Data Conversation API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/api/v1/info")
async def api_info():
    """API information endpoint"""
    return {
        "name": "QLens API",
        "version": "1.0.0",
        "features": [
            "File upload (CSV, Excel)",
            "PostgreSQL database connections",
            "AI-powered data analysis",
            "Chart generation",
            "Real-time chat interface"
        ],
        "endpoints": {
            "upload": "/api/v1/upload",
            "chat": "/api/v1/chat",
            "database": "/api/v1/database"
        }
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting QLens API server...")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )