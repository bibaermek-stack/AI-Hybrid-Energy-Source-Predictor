"""
EcoPredict AI - FastAPI Mobile & Cloud Backend.
Reads DATABASE_URL from environment variables for PostgreSQL on Railway.
"""

import logging
import os
import sys
from pathlib import Path

# Add project directory to Python path
_DIR = Path(__file__).resolve().parent
if str(_DIR) not in sys.path:
    sys.path.insert(0, str(_DIR))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ecopredict-api")

# Database URL configuration
DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
db_status = "disconnected"

if DATABASE_URL:
    logger.info("DATABASE_URL detected: %s", DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else "configured")
    try:
        import sqlalchemy
        engine = sqlalchemy.create_engine(DATABASE_URL, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
        db_status = "connected"
        logger.info("PostgreSQL Database connected successfully!")
    except Exception as exc:
        logger.warning("Database connection attempt failed: %s", str(exc))
        db_status = "error_fallback"
else:
    logger.info("No DATABASE_URL set. Running in stateless mode.")

app = FastAPI(
    title="EcoPredict AI Mobile & Cloud API",
    description="FastAPI Backend for EcoPredict AI Mobile App & Dashboards",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "EcoPredict AI Mobile Backend",
        "database_url_configured": bool(DATABASE_URL),
        "database_status": db_status,
        "version": "2.0.0",
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": db_status,
        "models_loaded": {"solar": True, "wind": True},
    }

# Include API routes
try:
    from api.routes import router as api_router
    app.include_router(api_router)
    logger.info("API Router included successfully.")
except Exception as err:
    logger.warning("Could not include api_router: %s", err)

# Serve static files
static_dir = _DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    logger.info("Starting uvicorn server on 0.0.0.0:%d", port)
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
