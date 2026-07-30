# EcoPredict AI — overview

## What it does
EcoPredict AI predicts solar and wind generation, optimizes hybrid dispatch, monitors a live Solarman inverter (SN 2501221272 class devices), estimates ROI in KZT, and provides RAG-based energy Q&A.

## Models (production)
- **Solar**: RandomForest (`artifacts/solar_model.pkl`) — features: irradiation, ambient/module temperature, hour, day, month.
- **Wind**: XGBoost (`artifacts/wind_model.pkl`).
- **Forecast page**: RF batch on historical feature sequences + live weather-based 24h generation estimate for Turkistan.
- **Fault detection**: vision models (YOLO / CNN) when images are uploaded.

## Architecture
- **FastAPI** on internal port 8001: predict, forecast-batch, solarman/*, health.
- **Streamlit** multipage UI on public `$PORT` (Railway).
- **RAG**: `knowledge_base/` documents indexed into ChromaDB under `vector_db/`.

## Languages
Kazakh (kk), English (en), Russian (ru) for dashboard copy and advisor responses where implemented.
