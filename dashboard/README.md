# EcoPredict AI — Dashboard

Premium Streamlit UI for the hybrid renewable energy educational platform.

## Run

```bash
# from project root (EcoPredict AI/)
streamlit run dashboard/app.py
```

With API (recommended):

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8001
streamlit run dashboard/app.py
```

Or production process manager:

```bash
python run_app.py
```

## Structure

| Path | Role |
|------|------|
| `app.py` | **Main shell** — hero, tabs, footer, wires all modules |
| `styles/custom_css.py` | Dark / light glassmorphism theme (2026) |
| `components/ui_kit.py` | Hero, metric cards, section headers, tiles, footer |
| `components/sidebar.py` | Brand, language, site, opt mode, theme, API health |
| `views/*` | Feature content (forecast, faults, optimize, …) |
| `pages/*` | Optional multipage routes (legacy deep-links) |

## Tabs (unified app)

1. Overview  
2. Forecasting  
3. Fault Detection  
4. Optimization  
5. AI Advisor  
6. Learn & Explore  
7. Sustainability  
8. Live Monitoring  

## Integrate a new module

1. Add logic under `src/<module>/…`  
2. Create `dashboard/views/my_module.py` with:

```python
def render(lang: str, texts: dict | None = None, models_status: dict | None = None) -> None:
    ...
```

3. Import and add a tab in `dashboard/app.py`  

## UI primitives

```python
from dashboard.components.ui_kit import hero, section_header, metric_row, footer
from dashboard.styles.custom_css import inject_theme

inject_theme("Dark")  # or "Light"
section_header("Dispatch", "24h PuLP schedule")
metric_row([{"label": "Solar", "value": "12.4 kW", "icon": "☀", "variant": "solar"}])
```

## Theme tokens

Dark: navy `#070b14` · teal `#2dd4bf` · sky `#38bdf8` · glass surfaces  
Light: slate/white with the same accent language  

Toggle via sidebar **Theme / Тема**.
