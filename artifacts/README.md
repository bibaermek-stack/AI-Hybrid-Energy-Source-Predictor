# Artifacts

Production and research model artifacts live here.

## Versioning convention

| Path pattern | Purpose |
|--------------|---------|
| `solar_model.pkl` | Production solar RF (API `/predict`) |
| `wind_model.pkl` | Production wind XGB |
| `solar_forecast_*.pkl` | Optional ensemble forecast artifacts |
| `*_elpv_*.pt` | Local PyTorch CNN/ELPV weights (**not** in git) |
| `*_probe.pt` | Frozen-backbone probes (**not** in git) |
| `model_metrics.json` | Machine-readable metrics snapshot (committed) |
| `cnn_fault_metrics.json` | CNN retrain summary (committed) |
| `elpv_cnn_metrics.json` | ELPV retrain summary (committed) |

## Demo metrics package (always in git)

When YOLO/CNN `.pt` weights are **missing**, the dashboard still shows:

| File | Role |
|------|------|
| `model_metrics.json` | Solar RF/XGB/LSTM R², YOLO mAP, production model notes |
| `cnn_fault_metrics.json` | CNN retrain summary |
| `elpv_cnn_metrics.json` | ELPV probe summary |

UI: Overview → **Models offline** banner + expander “Demo metrics package”.  
Paper: `docs/PAPER_METRICS_LOCKED.md` (locked table for GCAITMD).

## Policy

1. **Do not commit** large binary weights (`.pt`, large `.h5`). See root `.gitignore`.
2. **Do commit** JSON metrics and this README so CI and docs stay reproducible.
3. Optional: use [DVC](https://dvc.org/) for remote storage of large weights:

```bash
pip install dvc dvc-s3   # or dvc-gdrive
dvc init
dvc add artifacts/solar_model.pkl
dvc remote add -d storage s3://your-bucket/ecopredict
dvc push
```

4. Document training commands that regenerate weights:

```bash
python -m src.training.train_pipeline
python -m src.fault_detection.cnn_models.train_cnn --method probe
python -m src.fault_detection.cnn_models.train_elpv --no-finetune
```

## Registry (optional)

For multi-environment deploys, tag metrics files by git SHA:

```text
artifacts/model_metrics.json          # current
artifacts/history/model_metrics.<sha>.json  # optional archive
```
