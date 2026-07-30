# Paper metrics — locked snapshot for GCAITMD / final write-up

**Status:** LOCKED for proceedings abstract and main paper claims  
**Date locked:** 2026-07-20  
**Sources (do not invent new headline numbers without re-eval):**

| Source | Path |
|--------|------|
| Narrative metrics | [`docs/METRICS.md`](METRICS.md) |
| Machine-readable | [`artifacts/model_metrics.json`](../artifacts/model_metrics.json) |
| CNN retrain | [`artifacts/cnn_fault_metrics.json`](../artifacts/cnn_fault_metrics.json) |
| Abstract draft | [`docs/GCAITMD25_EcoPredict_Abstract.md`](GCAITMD25_EcoPredict_Abstract.md) |

---

## 1. Headline table (use this in abstract / results)

| Module | Model | Metric | Locked value | Report as |
|--------|--------|--------|-------------:|-----------|
| Solar forecast | Random Forest | R² | **0.9967** | **99.67%** |
| Solar forecast | Random Forest | MAE | **227 kW** | 227 kW |
| Solar forecast | XGBoost | R² | **0.9971** | **99.71%** |
| Solar forecast | XGBoost | MAE | **213 kW** | 213 kW |
| Solar forecast | LSTM (seq.) | R² | **0.9137** | **91.37%** |
| Solar forecast | LSTM | MAE | **1336 kW** | 1336 kW |
| Fault detection | YOLOv11n best (ep. 49) | mAP@50 | **0.972** | **97.2%** |
| Fault detection | YOLOv11n best | mAP@50-95 | **0.950** | 95.0% |
| Fault detection | YOLOv11n best | Precision / Recall | **0.926 / 0.836** | 92.6% / 83.6% |
| Fault detection | YOLOv11n test (88 img) | mAP@50 | **0.931** | **93.1%** |
| Fault detection | YOLOv11n test | mAP@50-95 | **0.923** | 92.3% |
| Fault detection | ResNet50 clean/dirty probe | Val accuracy | **80.94%** | **≈ 80.9%** |
| Fault detection | VGG16 clean/dirty probe | Val accuracy | **≈ 78.4%** | **≈ 78.4%** |
| Optimization | PuLP hybrid LP | Horizon | 24–48 h | Optimal when feasible |
| Education | Interactive labs | Count | **12** | 12 labs EN/KK |

---

## 2. Wording rules (consistency)

1. **Solar RF/XGB** — always quote **R² ≈ 99.67–99.71%** (range) or exact row values; never “>99.9%” without retrain.  
2. **YOLO** — distinguish **best checkpoint mAP@50 = 97.2%** vs **test-set mAP@50 = 93.1%**.  
3. **CNN clean/dirty** — use **probe / improved** numbers (≈81% / ≈78%), not notebook title “83%” (notebook history is inconsistent; see METRICS §3).  
4. **Multi-class CNN** — if mentioned, report probe val accuracy ~60–62% and state data limits; do **not** lead the abstract with multi-class CNN.  
5. **Optimizer** — qualitative “PuLP LP, 24–48 h, profit vs CO₂ modes”; no fake optimality gaps unless measured.  
6. **Education** — “interactive Streamlit laboratories (n=12)” with bilingual theory and graded tasks.

---

## 3. Abstract-ready one-liner (EN)

> On plant generation and weather data, Random Forest and XGBoost solar models achieve **R² ≈ 99.67–99.71%**, while a sequence LSTM baseline reaches **R² ≈ 91.37%**. YOLOv11 fault detection attains **mAP@50 up to 97.2%** (best checkpoint) and **≈ 93.1%** on a held-out test set. Clean/dirty CNN probes (ResNet50 / VGG16) reach about **81% / 78%** validation accuracy.

(This matches [`GCAITMD25_EcoPredict_Abstract.md`](GCAITMD25_EcoPredict_Abstract.md) §English abstract.)

---

## 4. Reproducibility note

- Large `.pt` weights are **not** required to cite the locked table if JSON metrics are committed.  
- To regenerate: retrain pipelines + refresh `artifacts/model_metrics.json` + update this file with a new “Date locked”.  
- Prefer citing **test mAP@50** for generalization; cite **best mAP@50** only with “checkpoint” qualifier.

---

## 5. Change control

| Date | Change |
|------|--------|
| 2026-07-20 | Initial lock from METRICS.md + model_metrics.json + GCAITMD abstract table |

*Do not edit headline numbers in abstract/paper without bumping this lock date and re-running evaluation.*
