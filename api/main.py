from fastapi import FastAPI, Request
import logging
from api.routes import router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="EcoPredict AI API",
    description="Predict solar and wind energy output with AI models"
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log incoming requests and responses"""
    logger.info(f"Incoming: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code} for {request.method} {request.url.path}")
    return response


app.include_router(router)