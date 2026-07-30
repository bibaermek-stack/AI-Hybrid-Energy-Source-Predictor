# EcoPredict AI — Model Metrics Report

Metrics extracted from training logs, notebooks, dashboard-reported runs, and YOLO `results.csv` (as of project inspection).

> **Paper lock:** for abstract / final paper **headline numbers**, use  
> [`docs/PAPER_METRICS_LOCKED.md`](PAPER_METRICS_LOCKED.md) (do not invent new %).

---

## 1. Solar power forecasting (tabular / sequence)

**Data:** Plant_1 generation + weather (merged ~3,157 records)  
**Target:** `AC_POWER` (kW)  
**Source:** Dashboard Trainer Hub last-run summary (`dashboard/app.py`) + `solar-power-generation-forecast.ipynb`

| Model | Algorithm | R² | MAE (kW) | Notes |
|-------|-----------|-----|----------|--------|
| Solar forecast RF | Random Forest | **0.9967** | **227** | Strong tabular fit on plant data |
| Solar forecast XGB | XGBoost | **0.9971** | **213** | Best of the three on this run |
| Solar LSTM | 2-layer LSTM | **0.9137** | **1336** | Sequence model; higher error, captures temporal dynamics |

**Production API solar model:** `artifacts/solar_model.pkl` — RandomForest (n_estimators=200, max_depth=10), trained via `src/training/train_pipeline.py` on `data/processed/build_features.csv` (features: irradiation, ambient/module temp, hour, day, month).

**Production wind model:** `artifacts/wind_model.pkl` — XGBoost (n_estimators=200, lr=0.05), features: wind speed, direction, theoretical power curve.

> Re-run evaluation after retraining:
> `python -m src.evaluation.model_comparsion` (solar baselines)  
> `python src/training/train_pipeline.py` / `train_wind_pipeline.py` / `train_lstm_pipeline.py`

---

## 2. YOLOv11-nano solar panel fault detection

**Framework:** Ultralytics YOLO11n  
**Classes:** Clean, Dust, Bird, Electrical, Physical, Snow  
**Train set:** ImageSet ~6,924 images | **100 epochs**  
**Log:** `yolo_fault_detection/runs/runs/detect/train/results.csv`

### Best checkpoint (by mAP50, epoch 49)

| Metric | Value |
|--------|------:|
| Precision | **0.926** |
| Recall | **0.836** |
| mAP@50 | **0.972** |
| mAP@50-95 | **0.950** |

### Last epoch (100)

| Metric | Value |
|--------|------:|
| Precision | 0.892 |
| Recall | 0.865 |
| mAP@50 | 0.948 |
| mAP@50-95 | 0.945 |

### Train-set evaluation snapshot (`Train result.png`)

| Class | Images | P | R | mAP50 | mAP50-95 |
|-------|-------:|--:|--:|------:|---------:|
| all | 82 | 0.905 | 0.926 | **0.969** | **0.959** |
| Clean | 19 | 0.946 | 0.842 | 0.941 | 0.941 |
| Dust | 19 | 1.000 | 0.774 | 0.968 | 0.968 |
| Bird | 16 | 0.794 | 0.966 | 0.956 | 0.956 |
| Electrical | 10 | 0.792 | 1.000 | 0.959 | 0.896 |
| Physical | 6 | 1.000 | 0.976 | 0.995 | 0.995 |
| Snow | 12 | 0.898 | 1.000 | 0.995 | 0.995 |

### Test-set evaluation snapshot (`Test Result.png`, 88 images)

| Class | Images | P | R | mAP50 | mAP50-95 |
|-------|-------:|--:|--:|------:|---------:|
| **all** | **88** | **0.888** | **0.931** | **0.931** | **0.923** |
| Clean | 20 | 0.914 | 0.950 | 0.990 | 0.990 |
| Dust | 19 | 1.000 | 0.540 | 0.876 | 0.876 |
| Bird | 17 | 0.757 | 0.915 | 0.910 | 0.910 |
| Electrical | 11 | 0.965 | 0.818 | 0.889 | 0.840 |
| Physical | 8 | 0.738 | 0.875 | 0.927 | 0.927 |
| Snow | 13 | 0.954 | 1.000 | 0.995 | 0.995 |

**Weights:** `yolo_fault_detection/runs/runs/detect/train/weights/best.pt`

---

## 3. CNN classifiers (notebooks)

| Notebook | Claim / title | Notebook-stored evaluate output |
|----------|---------------|----------------------------------|
| `fault-detection-using-resnet50-with-83-accuracy.ipynb` | ~83% (title) | Last evaluate in saved outputs: **Test accuracy ~10%** (incomplete / undertrained run in notebook history) |
| `cnn-vgg16-used-for-solar-panel-fault-detection.ipynb` | multi-class faults | Best val_accuracy in outputs ~**0.20**; final evaluate ~**15%** |

**Interpretation:** Packaged `.h5` weights in `artifacts/` may come from other runs; notebook cells do **not** currently prove the 83% claim. Prefer **YOLO metrics** above for fault detection quality until CNNs are re-evaluated cleanly.

Binary datasets available for retrain:

- `dataset/` — clean (502) / dirty (340)
- `Detect_solar_dust/` — Clean (1493) / Dusty (1069)

---

## 4. Hybrid optimizer (software, not ML)

After the rewrite (`src/optimization/hybrid_optimizer.py`):

- Multi-source **economic / hybrid dispatch** (merit order by LCOE when costs differ)
- Optional **load** and **battery** balancing
- Outputs: mix shares, shortfall, curtailment, reliability index
- Recommendation: `Solar` | `Wind` | `Hybrid` (not simple max)

See unit tests: `tests/test_models.py`

---

## 5. How to refresh this report

```bash
# YOLO (after retrain)
# read last row / best mAP50 from:
#   yolo_fault_detection/runs/runs/detect/train/results.csv

# Forecast models (from Trainer Hub or notebook)
#   artifacts/solar_forecast_rf.pkl | xgb | lstm
```
