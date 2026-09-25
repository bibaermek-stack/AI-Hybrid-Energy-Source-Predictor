# ⚡ EcoPredict AI

AI platform for **hybrid solar + wind** prediction, dispatch optimization, panel fault detection, Solarman economics (KZT / Turkistan), and **bilingual educational labs**.

Stack: **FastAPI** · **Streamlit** · **RandomForest / XGBoost / LSTM** · **YOLOv11** · **PuLP**

**Repo:** [bibaermek-stack/AI-Hybrid-Energy-Source-Predictor](https://github.com/bibaermek-stack/AI-Hybrid-Energy-Source-Predictor) (canonical; `EcoPradict-Ai` is an older copy)

---

## Features

| Area | What it does |
|------|----------------|
| Real-time optimization | Predict solar & wind kW; hybrid dispatch (load + battery) |
| Forecasting | Tabular RF/XGB + optional LSTM sequence |
| Solarman & economics | PR, ROI (KZT), weather, Telegram alerts |
| Fault diagnostics | YOLOv11 + clean/dirty CNN (weights optional offline) |
| AI advisor | EN/KK RAG (ChromaDB) |
| Sustainability | CO₂, LCOE, ROI, payback, NPV helpers |
| **Education labs (12)** | Theory EN/KK · KaTeX · graded tasks · ProgressTracker |

**Languages:** English + Қазақша (UI).

### What is *not* on the home page

- **No home-page Sketchfab / solar-panel 3D hero** (removed on purpose).  
- Interactive **3D is only** under **Labs → Inverter 3D wiring trainer** (optional embed; default is wiring board + full-screen 3D).

---

## Educational laboratories (12)

| Phase | Lab IDs (summary) |
|-------|-------------------|
| **P1** RES microgrid | `lab_pv_physics`, `lab_mppt_po`, `lab_bess_soc`, `lab_microgrid_dispatch` |
| **P2** | `lab_heuristic_vs_pulp` (rule-based vs PuLP) |
| **P3** CACER-inspired | `lab_pv_yield`, `lab_load_shape`, `lab_bess_community`, `lab_shared_energy`, `lab_rec_finance` |
| **P4** elective | `lab_grid_impact` (offline notebook / pandapower optional) |
| **HW** | `lab_inverter_wiring` (wiring board + optional 3D full screen) |

Sources: RenewableEnergySim (MIT) · CACER_Simulator concepts (BSD-3) · thin adapters under `src/simulation/`.  
Plan: [`docs/INTEGRATION_EDU_LABS.md`](docs/INTEGRATION_EDU_LABS.md) · notices: [`third_party/NOTICE.md`](third_party/NOTICE.md)

Optional CACER scientific stack (not in Docker):

```bash
pip install -e ".[sim-cacer]"
# or: pip install -r requirements-sim-cacer.txt
git submodule update --init --recursive third_party/CACER_Simulator
```

---

## Architecture

Paper-aligned modular layout ([`docs/architecture.md`](docs/architecture.md)):

```
src/
  forecasting/      # RF / XGB (+ optional LSTM)
  fault_detection/  # YOLO + CNN
  optimization/     # HybridEnergyOptimizer (PuLP)
  rag/              # EN/KK advisor (ChromaDB)
  education/        # lessons, labs, quizzes, lab_tasks
  simulation/       # microgrid (RES) + community (CACER-inspired)
  monitoring/       # weather / live
  sustainability/   # CO₂, LCOE, ROI, NPV
  utils/            # config, Solarman, logging

dashboard/
  app.py            # unified Streamlit shell
  views/            # overview, forecast, labs, live, …
  static/           # model_viewer + inverter lab assets
```

```
Streamlit ($PORT / 8501)
        │  HTTP
FastAPI  (port 8001)
        │
artifacts/  +  optimizer  +  Solarman  +  RAG  +  labs
```

| Port | Service |
|------|---------|
| **8001** | FastAPI (`api.main:app`) |
| **8501** | Streamlit (local) |
| **8080 / $PORT** | Streamlit (Docker / Railway via `run_app.py`) |

### Docker

```bash
docker compose up --build
# Streamlit: http://localhost:8080  ·  API: http://localhost:8001/health
```

Docker **does not** install `[sim-cacer]` / pandapower / full CACER stack.

### CI/CD

[`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) · [`docs/CI_CD.md`](docs/CI_CD.md)

| Stage | Action |
|-------|--------|
| Lint | ruff, black |
| Test | `python -m unittest discover -s tests` |
| Docker | Buildx + Trivy |
| Deploy | `main` → Railway/Render (optional secrets) |

### UI system

Design tokens + components · [`docs/UI_SYSTEM.md`](docs/UI_SYSTEM.md)

---

## Artifacts & “models offline”

| Committed | Not in git (local / DVC) |
|-----------|---------------------------|
| `artifacts/solar_model.pkl`, `wind_model.pkl` (if present) | Large `.pt` YOLO/CNN weights |
| `artifacts/model_metrics.json`, `cnn_fault_metrics.json` | Full ImageSet / ELPV datasets |
| Metrics docs | Training runs under `yolo_fault_detection/runs/` |

- If API cannot load weights, the dashboard shows a clear **Models offline** banner (see Overview).  
- Paper numbers still come from committed **metrics JSON** (not from missing `.pt` files).  
- Details: [`artifacts/README.md`](artifacts/README.md)

---

## Model metrics (paper-locked)

**Canonical table for GCAITMD / paper:** [`docs/PAPER_METRICS_LOCKED.md`](docs/PAPER_METRICS_LOCKED.md)  
Full notes: [`docs/METRICS.md`](docs/METRICS.md) · JSON: [`artifacts/model_metrics.json`](artifacts/model_metrics.json)

| Model | Metric | Value |
|-------|--------|------:|
| Solar forecast RF | R² / MAE | **0.9967** / 227 kW |
| Solar forecast XGB | R² / MAE | **0.9971** / 213 kW |
| Solar LSTM | R² / MAE | **0.9137** / 1336 kW |
| YOLO11n (best) | mAP@50 | **0.972** |
| YOLO11n (test) | mAP@50 / mAP@50-95 | **0.931** / **0.923** |
| ResNet50 clean/dirty (probe) | Val acc | **≈ 80.9%** |
| VGG16 clean/dirty (probe) | Val acc | **≈ 78.4%** |

Abstract draft: [`docs/GCAITMD25_EcoPredict_Abstract.md`](docs/GCAITMD25_EcoPredict_Abstract.md)

---

## Hybrid optimizer

`src/optimization/hybrid_optimizer.py` — multi-hour LP (PuLP): solar, wind, BESS, grid import/export; modes `balanced` | `max_profit` | `min_co2`.

---

## Installation

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

- Prefer **Python 3.10–3.12** for TensorFlow/LSTM.  
- YOLO needs `ultralytics` + PyTorch; without `best.pt`, CV UI stays offline (metrics still documented).

```env
API_URL=http://127.0.0.1:8001/predict
HEALTH_URL=http://127.0.0.1:8001/health
MODEL_PATH=artifacts

# Guards the credential routes (/solarman/configure, /solarman/status).
# Unset = those two routes stay disabled (503). Everything else is unaffected.
ECOPREDICT_API_KEY=<long-random-string>
```

---

## Running

```bash
python run_app.py
# API http://127.0.0.1:8001  ·  Dashboard http://127.0.0.1:8501
```

Dev (two terminals):

```bash
uvicorn api.main:app --reload --host 127.0.0.1 --port 8001
streamlit run dashboard/app.py --server.port 8501
```

```bash
curl http://127.0.0.1:8001/health
python -m unittest discover -s tests -v
```

---

## Main API routes

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Model load status |
| POST | `/predict` | Solar+wind + hybrid dispatch |
| POST | `/forecast` / `/forecast-batch` | LSTM sequences |
| POST | `/explain`, `/chat` | EN/KK advisor |
| POST | `/solarman/*` | Process, ROI, alert, … |
| GET | `/solarman/weather` | Turkistan weather |
| POST | `/solarman/configure` | 🔒 Set OpenAPI credentials — needs `X-API-Key` |
| GET | `/solarman/status` | 🔒 Credential status — needs `X-API-Key` |
| GET | `/metrics` | Paper metrics (`artifacts/model_metrics.json`) + live model feature importances |
| POST | `/sustainability/impact` | CO₂ avoided, tree/car equivalents, self-sufficiency (`src/sustainability`) |
| POST | `/labs/microgrid-day` | 24 h PV + battery + grid lab simulation (`src/simulation`) |

🔒 = requires the `X-API-Key` header matching `ECOPREDICT_API_KEY`. These two routes
read/write the Solarman credentials the whole process authenticates with, and the API
is reachable from the public internet through the Railway TCP proxy, so they are
fail-closed: with no key configured they return `503` instead of accepting anyone.

```bash
curl -X POST http://127.0.0.1:8001/solarman/configure -H "X-API-Key: $ECOPREDICT_API_KEY" -H 'Content-Type: application/json' -d '{"app_id":"...","app_secret":"...","email":"...","password":"..."}'
```

OpenAPI: http://127.0.0.1:8001/docs

---

## Project layout

```
.
├── api/
├── dashboard/app.py + views/ + static/
├── src/education/ labs · lab_tasks · progress
├── src/simulation/ microgrid · community
├── third_party/ NOTICE · CACER submodule (optional)
├── artifacts/   # metrics JSON + production pickles
├── docs/        # METRICS, PAPER_METRICS_LOCKED, GCAITMD, UI, CI
├── tests/
├── run_app.py
└── requirements.txt
```

---

## License / third-party

- EcoPredict educational project.  
- Adapted RES microgrid concepts: MIT (RenewableEnergySim).  
- CACER-inspired community labs: BSD-3 (see `third_party/NOTICE.md`).  
- YOLO tree may carry its own license.

---

## 📱 Cross-Platform Mobile Application (Flet Framework)

EcoPredict AI includes a cross-platform mobile application built with **Flet** (Flutter UI engine powered by Python).

### Running Mobile App

Pinned to **flet 1.0.1** (`mobile/pyproject.toml`). Install the same version locally:
`pip install "flet[all]==1.0.1"`.

```bash
# Desktop preview window (iPhone 16 frame, 393x852)
python run_mobile.py

# Web browser mode (http://localhost:8550)
python run_mobile.py --web

# Point the preview at a local API instead of production
ECOPREDICT_API_BASE=http://127.0.0.1:8001 python run_mobile.py
```

### Backend

The app talks to one backend: the Railway service deployed from **this** repository,
`https://ecopradict-mobile-production.up.railway.app` (`mobile/config.py`).
That service must run the full API from the repository root:

| Railway setting | Value |
|---|---|
| Root Directory | *(empty — repository root)* |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Variables | `WEATHERAPI_KEY`, `ECOPREDICT_API_KEY`, `SOLARMAN_APP_ID`, `SOLARMAN_APP_SECRET`, `SOLARMAN_EMAIL`, `SOLARMAN_PASSWORD` |

Check it with `curl https://ecopradict-mobile-production.up.railway.app/health` —
it must report `"api": "full"`. `"api": "stub"` means Root Directory still points at `mobile/`.
[`backend-health.yml`](.github/workflows/backend-health.yml) runs the same check every six hours.

### Mobile Features:
- **Bilingual (KK / EN)**: Instant language switcher (Қазақша / English).
- **Screens**: Overview, ML predictions, 24h forecast, YOLO fault diagnostics, model training,
  optimization, sustainability, labs, AI advisor, Solarman live, settings.

### Building Mobile Binaries:
```bash
pip install "flet[cli]==1.0.1"

# Android APK (flet installs the Flutter/Android toolchain it needs)
flet build apk mobile --yes

# iOS — needs macOS + Xcode; an installable .ipa also needs Apple signing
flet build ios-simulator mobile --yes
flet build ipa mobile --yes --ios-team-id <TEAM_ID> --ios-export-method app-store-connect \
  --ios-provisioning-profile <PROFILE> --ios-signing-certificate "Apple Distribution"
```

CI builds these too: [`build-android.yml`](.github/workflows/build-android.yml) runs on every
push touching `mobile/`; [`build-ios.yml`](.github/workflows/build-ios.yml) runs on demand and
on `v*` tags. Signing secrets are listed at the top of each workflow.
`tests/test_mobile_smoke.py` builds every screen against the pinned flet.

