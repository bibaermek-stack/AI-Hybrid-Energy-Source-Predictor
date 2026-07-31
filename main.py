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

# Include API routes.
# Everything the mobile app calls (/predict, /chat, /solarman/*) lives in this
# router. When it fails to import, the service still answers — but with only "/"
# and "/health" — which is how a deployment ends up 404-ing every feature while
# still looking healthy. Record the failure so /health can report it.
api_router_loaded = False
api_router_error: str | None = None
try:
    from api.routes import router as api_router

    app.include_router(api_router)
    api_router_loaded = True
    logger.info("API Router included successfully.")
except Exception as err:
    api_router_error = f"{type(err).__name__}: {err}"
    logger.error(
        "Could not include api_router — /predict, /chat and /solarman/* will 404: %s",
        err,
        exc_info=True,
    )


def _real_models_loaded() -> dict:
    """Actual model state rather than a hardcoded guess."""
    if not api_router_loaded:
        return {"solar": False, "wind": False}
    try:
        from api import routes

        return {
            "solar": routes.solar_model is not None,
            "wind": routes.wind_model is not None,
        }
    except Exception:
        return {"solar": False, "wind": False}


@app.get("/")
async def root():
    return {
        "status": "online",
        "service": "EcoPredict AI Mobile Backend",
        "database_url_configured": bool(DATABASE_URL),
        "database_status": db_status,
        "api_router_loaded": api_router_loaded,
        "version": "2.0.0",
    }


@app.get("/health")
async def health_check():
    """
    Degraded-mode health reply.

    `api` is the field clients use to tell a fully-wired backend from this stub —
    it must never say "full" unless the feature routes are actually mounted.
    """
    models = _real_models_loaded()
    return {
        "status": "healthy" if api_router_loaded and all(models.values()) else "degraded",
        "api": "full" if api_router_loaded else "stub",
        "database": db_status,
        "models_loaded": models,
        "api_router_error": api_router_error,
    }

# Serve static files
static_dir = _DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    logger.info("Starting uvicorn server on 0.0.0.0:%d", port)
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
