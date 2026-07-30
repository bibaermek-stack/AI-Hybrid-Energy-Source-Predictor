# EcoPredict AI — Architecture (paper-aligned)

**Theme:** Artificial Intelligence-Driven Optimization of Renewable Energy Systems: A Smart Educational Platform.

## Layered design

```
┌─────────────────────────────────────────────────────────────┐
│  dashboard/  Streamlit multipage UI (EN + KK)               │
│  pages: Predictions · Forecast · Solarman · Faults ·        │
│         Training · Learn · Optimization · Advisor · Impact  │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP
┌───────────────────────────▼─────────────────────────────────┐
│  api/  FastAPI  (:8001)  health · predict · forecast ·      │
│        chat · solarman · hybrid dispatch                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│  src/  modular packages                                     │
│  forecasting │ fault_detection │ optimization │ rag         │
│  education   │ monitoring      │ sustainability │ utils     │
└───────────────────────────┬─────────────────────────────────┘
                            │
          artifacts/ · knowledge_base/ · vector_db/ · data/
```

## Recommended tree ↔ actual paths

| Paper / recommended module | Path in this repo |
|----------------------------|-------------------|
| `src/forecasting/` | `src/forecasting/` (+ legacy `src/models/`, `src/training/`) |
| `src/fault_detection/` | `src/fault_detection/` (+ `yolo_fault_detection/`, artifacts `*.h5`) |
| `src/optimization/` | `src/optimization/` (`hybrid_optimizer`, `battery_model`, `objectives`) |
| `src/rag/` | `src/rag/` (ChromaDB under `vector_db/`, texts in `knowledge_base/`) |
| `src/education/` | `src/education/` + `content/` |
| `src/monitoring/` | `src/monitoring/` (`api_client`, `live_data`, `model_monitor`) |
| `src/sustainability/` | `src/sustainability/` (CO₂, LCOE, ROI, impact) |
| `src/utils/` | `src/utils/` (`config`, `logging_config`, `visualization`, Solarman) |
| `dashboard/pages/*` | Existing 1–6 + **7 Optimization**, **8 AI Advisor**, **9 Sustainability** |
| Docker | `Dockerfile`, `docker-compose.yml` |
| Docs | `docs/architecture.md`, `docs/paper_draft.md`, `docs/METRICS.md` |

Legacy packages (`src/llm_agent`, `src/data_pipeline`, `src/evaluation`) remain as **thin facades / training utilities** so existing API imports keep working.

## Ports

| Port | Service |
|------|---------|
| **8001** | FastAPI `api.main:app` |
| **$PORT` / 8080** | Streamlit (`run_app.py` production) |
| **8501** | Streamlit local default |

## Production notes

- Forecast backend: **Random Forest** (no TensorFlow on Railway).
- Weather: **WeatherAPI.com** if `WEATHERAPI_KEY` set; else **Open-Meteo** fallback via `src/monitoring/api_client.py`.
- Optimizer: **PuLP** multi-hour LP in `HybridEnergyOptimizer`.
