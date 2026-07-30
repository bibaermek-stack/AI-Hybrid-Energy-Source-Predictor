# EcoPredict AI — FastAPI (8001) + Streamlit (PORT)
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

WORKDIR /app

# System libs for OpenCV headless / scientific wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
# Note: do NOT install requirements-sim-cacer.txt / extras [sim-cacer] here.
# pandapower + CACER tutorials are offline electives (see notebooks/labs/, third_party/).

COPY . .

# Optional runtime dirs
RUN mkdir -p logs vector_db data/sample

EXPOSE 8080 8001

# Health: Streamlit is public; API is internal on 8001
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -fsS "http://127.0.0.1:8001/health" || exit 1

CMD ["python", "run_app.py"]
