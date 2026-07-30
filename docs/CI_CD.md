# CI/CD

## Pipeline file

[`.github/workflows/ci-cd.yml`](../.github/workflows/ci-cd.yml)

### Triggers

- `push` to `main`
- `pull_request` targeting `main`

### Jobs

| Job | Steps |
|-----|--------|
| **lint-and-test** | Checkout → Python 3.11 + pip cache → `requirements.txt` + `requirements-dev.txt` → `ruff check` → `black --check` → `unittest discover -s tests` |
| **docker** | Buildx build (no push on PR) → Trivy scan (`continue-on-error`) |
| **deploy** | Only on **push** to `main`: Railway CLI and/or Render deploy hook; optional Slack webhook |

### Secrets

| Secret | Purpose |
|--------|---------|
| `RAILWAY_TOKEN` | Railway CLI deploy |
| `RAILWAY_SERVICE` | Optional service name (default `ecopredict`) |
| `RENDER_DEPLOY_HOOK` | HTTPS deploy hook URL |
| `SLACK_WEBHOOK_URL` | Optional deploy notification |

Unset secrets cause the corresponding deploy step to be skipped (no hard failure on empty token checks depending on runner evaluation; hooks use soft failure).

### Local parity

```bash
pip install -r requirements.txt -r requirements-dev.txt
ruff check api src dashboard tests run_app.py
black --check api src dashboard tests run_app.py
python -m unittest discover -s tests -p "test_*.py" -v
docker build -t ecopredict-ai:local .
```

### Docker ignore

See [`.dockerignore`](../.dockerignore): excludes venv, large datasets, YOLO runs, docs, `.pt`/large weights, local logs.
