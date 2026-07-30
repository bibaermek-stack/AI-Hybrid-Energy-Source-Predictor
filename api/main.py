from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import os
from api.routes import router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="EcoPredict AI API",
    description="Predict solar and wind energy output with AI models"
)

# Add CORS Middleware to support requests from Streamlit & Flet frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log incoming requests and responses"""
    logger.info(f"Incoming: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code} for {request.method} {request.url.path}")
    return response

# Mount static directory for 3D model serving
static_dir = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static")
)
if not os.path.isdir(static_dir):
    logger.error("Static directory missing: %s", static_dir)
else:
    logger.info("Serving static files from %s", static_dir)
    app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")

app.include_router(router)