# Integration plan: open-source simulators → EcoPradict-Ai education labs

**Target project:** EcoPradict-Ai (FastAPI + Streamlit, `src/education/`, PuLP hybrid optimizer, forecasting, YOLO faults)  
**Date of analysis:** 2026-07-16  

**Note on repository B:** The path `https://github.com/RSE-CoLabs/CACER_Sim` returns 404. The active repository is:

**https://github.com/RSE-CoLabs/CACER_Simulator**

---

# A. RenewableEnergySim

## 1. Repository analysis

| Field | Value |
|-------|--------|
| **GitHub** | https://github.com/nabilkhondaker/RenewableEnergySim |
| **License** | MIT |
| **Stack** | Python 3.9+, NumPy, Pandas, Streamlit, Plotly, PyYAML, Requests, pytest |

**Summary (2–3 sentences):**  
RenewableEnergySim is a modular Python microgrid simulator for solar PV, battery ESS, inverter efficiency, MPPT (perturb & observe), and simple PV–battery–grid load balancing. It supports headless runs via a simulation engine and an interactive Streamlit dashboard with KPI cards and Plotly charts. Weather is driven by Open-Meteo/NREL-style fetchers with CSV fallback.

**Relevance to EcoPradict-Ai:**

| Area | Fit |
|------|-----|
| Hybrid optimization / microgrid simulation | High — PV + BESS + grid import/export loop |
| Educational content | High — compact physics models suitable for labs |
| Interactive dashboards | High — Streamlit + Plotly pattern mirrors EcoPradict |
| Forecasting | Low–medium — weather inputs only, no ML forecast models |
| Fault detection / YOLO | None |

---

## 2. Reusable components

### Worth reusing / adapting

| Path | Content | Use in labs |
|------|---------|-------------|
| `src/models/solar_panel.py` | `SolarPanelConfig`, `SolarArray.calculate_power`, I–V curve helper | Lab: PV physics vs temperature/irradiance |
| `src/models/battery.py` | `BatteryESS` charge/discharge/SOC | Lab: BESS dynamics (compare to EcoPradict `BatteryParams`) |
| `src/models/inverter.py` | Load-dependent DC→AC efficiency | Lab: inverter η vs load |
| `src/core/mppt.py` | `MPPTController` P&O | Lab: MPPT step-size experiment |
| `src/core/load_balancer.py` | `LoadBalancer.dispatch` | Lab: priority dispatch (load → battery → grid) |
| `src/core/engine.py` | Hourly simulation loop | Scaffold for multi-hour lab runner |
| `src/data_fetchers/weather_api.py` | Weather profile fetch | Align with EcoPradict `src/monitoring/api_client.py` |
| `config/settings.yaml` | Grid prices, timestep, feature flags | Lab default parameters |
| `data/historical_weather.csv` | Offline weather | Demo without API keys |
| `dashboard/app.py` | Streamlit control + sim loop | Pattern for lab UI (do not merge as second app root) |
| `dashboard/components/kpi_cards.py`, `live_charts.py` | KPI + dual-axis charts | Adapt to EcoPradict design tokens |
| `tests/test_models.py`, `test_mppt.py` | Unit tests | Port as `tests/test_sim_labs.py` |

### Direct clone vs modify

| Approach | Items |
|----------|--------|
| **Adapt (copy + rewrite imports)** | All `src/models/*`, `mppt.py`, `load_balancer.py` — rename packages to `src/simulation/microgrid/` |
| **Reuse pattern only** | Streamlit dashboard layout; implement with EcoPradict `dashboard/components/*` and `tokens.py` |
| **Do not vendor as nested app** | Top-level `dashboard/app.py` (conflicts with EcoPradict multipage shell) |
| **Optional thin wrap** | Weather fetcher → call EcoPradict Open-Meteo client |

### Dependencies / data

- **Runtime:** numpy, pandas, pyyaml, requests, plotly (already in EcoPradict).
- **Data:** `historical_weather.csv` (small); optional live Open-Meteo (no key).
- **No** TensorFlow, YOLO, or PuLP required for these physics labs.

---

## 3. Integration plan (RenewableEnergySim → EcoPradict)

### Recommended layout

```text
EcoPradict-Ai/
  src/simulation/                    # NEW package
    __init__.py
    microgrid/
      __init__.py
      solar_panel.py                 # from RES SolarArray
      battery_ess.py                 # from RES BatteryESS (name clash with optimization.battery_model)
      inverter.py
      mppt.py
      load_balancer.py
      engine.py                      # simplified SimulationEngine
    adapters/
      weather_profile.py             # bridge to monitoring.api_client
  src/education/
    labs/
      __init__.py
      lab_registry.py                # lab ids, titles EN/KK, objectives
      lab_pv_physics.py              # theory + param schema
      lab_bess_dispatch.py
      lab_mppt.py
    content/
      labs/
        pv_physics_en.md / _kk.md
        bess_dispatch_en.md / _kk.md
  dashboard/views/
    labs.py                          # Streamlit lab hub
  dashboard/pages/
    10_Labs.py                       # multipage entry (optional)
  tests/
    test_simulation_microgrid.py
  third_party/NOTICE.md              # MIT attribution for RenewableEnergySim
```

### Step-by-step adaptation

1. **Vendor core models**  
   Copy `solar_panel.py`, `battery.py`, `inverter.py`, `mppt.py`, `load_balancer.py` into `src/simulation/microgrid/`.  
   Rewrite imports: `from src.models.X` → `from src.simulation.microgrid.X`.  
   Keep MIT copyright headers.

2. **Resolve naming conflicts**  
   - EcoPradict already has `src.optimization.battery_model.BatteryParams` (LP parameters).  
   - Keep simulation class as `BatteryESS` (runtime SOC simulator).  
   - Do not merge with PuLP `BatteryParams`; document both in lab theory.

3. **Engine API**  
   Expose a pure function for labs:

   ```python
   def run_day_simulation(
       num_panels: int,
       battery_kwh: float,
       load_kw: float,
       weather_df: pd.DataFrame,
   ) -> pd.DataFrame:
       ...
   ```

   Returns columns: `time, pv_kw, load_kw, soc, grid_import_kw, grid_export_kw`.

4. **Weather bridge**  
   Prefer EcoPradict `src.monitoring.api_client.fetch_hourly_weather` → map to columns `irradiance_w_m2`, `temperature_c`.  
   Fallback: ship a copy of `historical_weather.csv` under `data/sample/`.

5. **Dashboard integration**  
   - Add tab or page **Labs** calling `dashboard.views.labs.render`.  
   - Use `dashboard.components.metric_card`, `states`, `plotly_theme` — not RES CSS/`st.markdown` style injection.

6. **Optimization link (advanced lab)**  
   After physics dispatch, optional step: feed same `solar`/`load` series into `HybridEnergyOptimizer` and compare heuristic balancer vs PuLP schedule (same horizon).

7. **Tests**  
   Port RES unit tests; assert energy conservation within tolerance (import + pv ≈ load + export + battery_delta).

### Conflicts and resolution

| Conflict | Resolution |
|----------|------------|
| Dual `src/` package names | Vendor under `src/simulation/`, never as nested `RenewableEnergySim/src` |
| Streamlit second app | No separate Streamlit process; single EcoPradict `dashboard/app.py` |
| Battery model duplication | Document: ESS = discrete-time SOC; BatteryParams = LP bounds |
| Pin-tight RES requirements | Rely on EcoPradict versions; no need for RES-pinned streamlit 1.32 |
| CFD flag in settings | Leave disabled; out of scope |

### Code quality

- Type hints on public lab APIs.  
- No side effects at import (lazy weather calls).  
- `tests/test_simulation_microgrid.py` in CI (`unittest discover`).  
- Attribution file `third_party/NOTICE.md`.

---

## 4. Educational labs (from RenewableEnergySim)

### P1 implementation status

| Path | Role |
|------|------|
| `src/simulation/microgrid/*` | Vendored physics (MIT) |
| `src/simulation/adapters/weather_profile.py` | Sample / synthetic / Open-Meteo |
| `src/education/labs/*` | Registry + lab metadata |
| `src/education/content/labs/*` | Theory EN/KK |
| `dashboard/views/labs.py` | Streamlit lab hub |
| `dashboard/pages/10_Labs.py` | Multipage entry |
| `dashboard/app.py` | **Labs** tab |
| `tests/test_simulation_microgrid.py` | Unit tests |
| `third_party/NOTICE.md` | Attribution |
| `data/sample/historical_weather.csv` | Offline weather |

**Implemented labs:** `lab_pv_physics`, `lab_mppt_po`, `lab_microgrid_dispatch`.

### Lab catalogue

| Lab ID | Title (EN) | Source modules | Status |
|--------|------------|----------------|--------|
| `lab_pv_physics` | PV power vs irradiance and temperature | `solar_panel` | Done |
| `lab_mppt_po` | Maximum power point tracking (P&O) | `mppt` + I–V curve | Done |
| `lab_bess_soc` | Battery SOC over a day | `battery` + weather | Use microgrid lab |
| `lab_microgrid_dispatch` | PV–BESS–grid balancing | `load_balancer` + `engine` | Done |
| `lab_heuristic_vs_pulp` | Rule-based dispatch vs PuLP | RES balancer + EcoPradict optimizer | Planned |

### Standard lab structure

```text
1. Theory (EN/KK markdown or lesson sections)
2. Learning objectives (checklist)
3. Parameters (Streamlit sliders / number_input)
4. Simulation (run button + spinner / loading_state)
5. Results (metric cards + Plotly charts)
6. Reflection / quiz hook (ProgressTracker + quiz id)
```

### Interactive UI (Streamlit)

- **Sliders:** panel count, battery kWh, load kW, MPPT step size, temp coefficient.  
- **Select:** site (reuse sidebar `ep_site` lat/lon).  
- **Run:** `primary_button` → `loading_state` → `run_day_simulation`.  
- **Results:** `metric_row` (energy import, export, self-consumption %); `themed_line` for power and SOC.  
- **Empty/error:** `empty_state` before first run; `error_state` on weather/API failure.

### Theory and objectives (example: `lab_microgrid_dispatch`)

- **Objectives:** (1) Explain energy balance; (2) Observe SOC under surplus/deficit; (3) Quantify grid import under low irradiance.  
- **Formulas:** power balance; SOC update with efficiency (from RES README concepts).  
- **Tasks:** “Set load to 30 kW and battery to 20 kWh; report evening import.”  
- **Bilingual:** `title_en`/`title_kk`, content files `*_en.md` / `*_kk.md`, labels via `_t(lang, en, kk)`.

### Progress / assessment

```python
from src.education.progress import ProgressTracker
progress = ProgressTracker.from_session(st.session_state)
progress.mark_exercise("lab_microgrid_dispatch")
# optional: short quiz after lab
progress.record_quiz("lab_microgrid_quiz", score_percent)
```

Extend `ProgressTracker` with `labs_done: list[str]` if not already covered by `exercises`.

---

# B. CACER Simulator

## 1. Repository analysis

| Field | Value |
|-------|--------|
| **GitHub (correct)** | https://github.com/RSE-CoLabs/CACER_Simulator |
| **Broken alias** | https://github.com/RSE-CoLabs/CACER_Sim → 404 |
| **License** | BSD 3-Clause (RSE / Aleotti, Rollo et al.) |
| **Stack** | Python 3.11, Jupyter, Streamlit, pvlib, PuLP, pandapower, Plotly, numpy-financial, large scientific stack |

**Summary (2–3 sentences):**  
CACER_Simulator evaluates energy communities and collective self-consumption: PV production, load profiles, shared energy, bills, incentives, and financial KPIs (NPV, IRR, payback). Logic lives in large `src/Functions_*.py` modules plus tutorial notebooks (PV, load emulator, power flow, reporting). Configuration and Italian market/tariff assumptions are driven by `config.yml` and files under `files/`.

**Relevance to EcoPradict-Ai:**

| Area | Fit |
|------|-----|
| Educational notebooks / labs | High — numbered tutorials 0–5 |
| PV simulation (pvlib) | High — production profiles |
| BESS / energy model | High — `BESS()` and energy flows |
| Financial / sustainability KPIs | High — NPV, IRR, payback (align with EcoPradict `sustainability/`) |
| Grid power flow (pandapower) | Medium — advanced elective lab |
| Italian CACER regulation / incentives | Medium — teach as case study; adapt for Kazakhstan tariffs |
| Forecasting / YOLO | Low |

---

## 2. Reusable components

### Worth reusing / adapting

| Path | Content | Lab use |
|------|---------|---------|
| `1. Tutorial_photovoltaic_simulator.ipynb` | PV profile generation workflow | Lab: annual/daily PV yield |
| `2./3. Tutorial_domestic_load_emulator_*.ipynb` | Synthetic load profiles | Lab: demand shape parameters |
| `0. Tutorial_CACER_simulator.ipynb` | End-to-end energy community run | Capstone lab (simplified) |
| `4. Tutorial_power_flow_simulator.ipynb` | Grid impact | Advanced elective |
| `5. Reporting.ipynb` | KPI reporting | Report generation pattern |
| `src/Functions_Energy_Model.py` | `BESS(...)`, energy balance helpers | Core for BESS/shared-energy labs |
| `src/Functions_Financial_Model.py` | Cash-flow, NPV/IRR-style metrics | Link to LCOE/ROI education |
| `src/Functions_Load_Emulator_and_DSM.py` (+ v2) | Load synthesis | Synthetic demand without meters |
| `src/Functions_Grid_Simulator_*.py` | pandapower-based analysis | Optional; heavy dependency |
| `documentation/docs/modules/*.md` | Module theory | Translate key pages EN/KK for theory pane |
| `documentation/docs/tutorials/*.md` | Tutorial text | Student handouts |
| `config.yml` | Simulation horizon, DoD, efficiencies | Lab defaults (strip Italy-only keys for intro labs) |
| `dashboard/users_cacer_dashboard.py` | Streamlit entry | Pattern only; not full port |

### Direct clone vs modify

| Approach | Items |
|----------|--------|
| **Selective extract** | `BESS` and related pure functions; load-emulator pure functions that do not need xlwings/Excel |
| **Notebook → Streamlit lab** | Tutorials 1–3 as primary education path |
| **Do not bulk-merge** | Entire `requirements.txt` (Windows `pywin32`, `xlwings`, `playwright`, pinned huge stack) |
| **Case-study only** | Italian tariff/incentive blocks; replace with KZ tariff parameters for local labs |
| **Read-only vendor** | Optionally submodule under `third_party/CACER_Simulator` for attribution + notebooks |

### Dependencies / data

| Dependency | For intro labs | For full CACER |
|------------|----------------|----------------|
| pandas, numpy, plotly | Required | Required |
| pvlib | Recommended (PV lab) | Required |
| PuLP | Optional (EcoPradict already has) | Used in parts of stack |
| pandapower | Skip initially | Grid lab |
| xlwings / Excel | Avoid | Full workflow |
| files/*.xlsx, market YAMLs | Sample subset | Full |
| Python | EcoPradict 3.11 | 3.11 |

---

## 3. Integration plan (CACER → EcoPradict)

### Recommended layout

```text
EcoPradict-Ai/
  third_party/
    CACER_Simulator/          # optional git submodule (BSD-3 NOTICE)
  src/simulation/
    community/                # thin adapters, not full CACER dump
      __init__.py
      bess_step.py            # wrap/port BESS timestep logic
      pv_profile.py           # pvlib-based daily profile helper
      load_profile.py         # simplified synthetic load
      financial_kpis.py       # NPV/payback wrappers → sustainability
  src/education/
    labs/
      lab_pv_profile_cacer.py
      lab_load_emulator.py
      lab_shared_energy.py    # simplified shared energy accounting
      lab_finance_rec.py      # NPV/payback for community investment
    content/labs/
      ...
  dashboard/views/
    labs.py                   # hub listing RES + CACER-derived labs
  docs/
    INTEGRATION_EDU_LABS.md   # this file
```

### Step-by-step adaptation

1. **Submodule or pin**  
   ```bash
   git submodule add https://github.com/RSE-CoLabs/CACER_Simulator.git third_party/CACER_Simulator
   ```  
   Record BSD-3 attribution in `third_party/NOTICE.md`.

2. **Extract pure functions**  
   Port `BESS` from `Functions_Energy_Model.py` into `src/simulation/community/bess_step.py` with typed signature and unit tests.  
   Remove `xlwings` / Excel I/O from critical path.

3. **PV lab via pvlib**  
   Add optional dependency `pvlib` to `requirements.txt` or extras:  
   `pip install pvlib`  
   Implement `pv_profile.py` generating 24h or multi-day series for Turkistan lat/lon (from `ep_site`).

4. **Load lab**  
   Implement simplified `load_profile.py` (daily shape + noise) inspired by load emulator tutorials; avoid shipping full Italian registry Excel unless needed for advanced course.

5. **Shared energy lab (simplified CACER concept)**  
   Define N prosumers with PV and load series; compute:  
   - individual self-consumption  
   - “shared” surplus among community (simple proportional rule)  
   - residual grid import  
   Do **not** reimplement full ARERA incentive engine in v1; document regulatory origin as reading assignment.

6. **Financial lab**  
   Map CACER cash-flow ideas to EcoPradict `src/sustainability/economic_metrics.py` (LCOE, payback, ROI already present).  
   Add NPV/IRR helpers if missing (numpy-financial optional).

7. **Dashboard**  
   Labs hub page lists RES- and CACER-derived labs with difficulty tags.  
   Do not run full CACER Streamlit dashboard inside EcoPradict.

8. **Grid lab (phase 2)**  
   Optional: pandapower tutorial as advanced notebook under `notebooks/labs/`, not production Docker image (keep Docker slim).

### Conflicts and resolution

| Conflict | Resolution |
|----------|------------|
| Dependency weight | Optional extras: `[sim-cacer]` in packaging; Docker stays lean |
| Italy-specific config | Parameterize tariffs; default KZ-like prices for EcoPradict |
| Windows Excel (xlwings) | Exclude from automated labs and CI |
| Namespace `src.Functions_*` | Never install CACER as top-level `src` on PYTHONPATH alongside EcoPradict; use `third_party` + adapters |
| PuLP dual use | EcoPradict hybrid LP vs CACER MILP — keep separate lab narratives |
| License | BSD-3: retain copyright notices on redistributed code |

### Code quality

- Adapters only import CACER if path configured (`ECOPREDICT_CACER_ROOT`).  
- Unit tests for BESS energy balance without full CACER install.  
- CI: do not install full CACER requirements; test EcoPradict adapters only.

---

## 4. Educational labs (from CACER)

### Lab catalogue (proposed)

| Lab ID | Title (EN) | Source |
|--------|------------|--------|
| `lab_pv_yield` | PV production profiles (pvlib) | Tutorial 1 + pvlib |
| `lab_load_shape` | Domestic load emulation | Tutorials 2–3 (simplified) |
| `lab_bess_community` | BESS timestep and DoD limits | `BESS` function |
| `lab_shared_energy` | Shared renewable energy (simplified REC) | Energy model concepts |
| `lab_rec_finance` | Community investment KPIs | Financial model + EcoPradict sustainability |
| `lab_grid_impact` | Power flow intro (optional) | Tutorial 4 / pandapower |

### Theory → Parameters → Simulation → Results → Reflection

Example **lab_shared_energy**:

1. **Theory:** definition of self-consumption, shared energy, residual import (EN/KK).  
2. **Objectives:** compute three KPIs for a 3-user toy community.  
3. **Parameters:** number of users, PV kWp, battery kWh, tariff import/export.  
4. **Simulation:** hourly loop 24–168 h using EcoPradict weather + simplified PV/load.  
5. **Results:** stacked energy chart; metric cards for shared energy %, grid import kWh, bill proxy.  
6. **Reflection:** quiz “If battery DoD increases, shared energy…?”; `ProgressTracker.mark_exercise`.

### Bilingual

- Lab registry: `title_en`, `title_kk`, `objectives_en/kk`.  
- Theory markdown pairs under `src/education/content/labs/`.  
- UI strings: same pattern as `dashboard/views/optimization.py` `_t(lang, en, kk)`.

### Progress / assessment

- Lab completion flags in `ProgressTracker`.  
- Short post-lab quizzes in `src/education/quiz.py` (`lab_shared_energy_quiz`).  
- Optional: export student CSV of parameters + KPIs for instructor review (no PII).

---

# Cross-cutting integration architecture

```text
dashboard/views/labs.py
        │
        ▼
src/education/labs/lab_registry.py  →  metadata + lesson links
        │
        ├── src/simulation/microgrid/*     (from RenewableEnergySim, MIT)
        └── src/simulation/community/*     (from CACER concepts/adapters, BSD-3)
        │
        ├── src/optimization/*             (existing PuLP)
        ├── src/monitoring/*               (weather)
        └── src/sustainability/*           (economic KPIs)
```

### Implementation phases

| Phase | Scope | Effort driver |
|-------|--------|----------------|
| **P1** | `src/simulation/microgrid` + 2 labs (PV physics, microgrid dispatch) + Labs page | Low dependency risk |
| **P2** | MPPT lab + heuristic vs PuLP comparison | Links RES + EcoPradict optimizer |
| **P3** | CACER adapters: BESS + shared energy + finance labs | Careful dependency control |
| **P4** | Optional pandapower notebook; full CACER submodule for advanced course | Heavy stack |

### Priority for EcoPradict education value

1. RenewableEnergySim physics stack (fast path to interactive labs).  
2. CACER simplified shared-energy + finance narrative (community scale).  
3. Full Italian CACER configuration engine (research elective only).

---

# Lab interface checklist (both sources)

- [ ] Registry entry with EN/KK titles and estimated minutes  
- [ ] Theory pane from markdown  
- [ ] Parameter form (sliders) with defaults documented  
- [ ] Deterministic seed for reproducibility  
- [ ] Loading / empty / error states (`dashboard/components/states.py`)  
- [ ] Results: metrics + Plotly with `plotly_theme`  
- [ ] Reflection questions + quiz id  
- [ ] `ProgressTracker` exercise mark  
- [ ] Unit tests for simulation kernel  
- [ ] License NOTICE updated  

---

# References

- RenewableEnergySim: https://github.com/nabilkhondaker/RenewableEnergySim (MIT)  
- CACER_Simulator: https://github.com/RSE-CoLabs/CACER_Simulator (BSD-3-Clause)  
- EcoPradict education: `src/education/`, `dashboard/views/learn.py`  
- EcoPradict optimization: `src/optimization/hybrid_optimizer.py`  
- EcoPradict UI system: `docs/UI_SYSTEM.md`

---

# Implementation status (auto)

**Updated:** 2026-07-17

| Phase | Deliverable | Location | Status |
|-------|-------------|----------|--------|
| P1 | Microgrid physics | `src/simulation/microgrid/` | Done |
| P1 | Labs UI hub | `dashboard/views/labs.py`, `pages/10_Labs.py` | Done |
| P1 | Theory EN/KK | `src/education/content/labs/` | Done |
| P2 | Heuristic vs PuLP | `microgrid/compare_pulp.py` + lab | Done |
| P3 | Community adapters | `src/simulation/community/` | Done (no full CACER deps) |
| P3 | Shared energy / load / finance labs | registry + Labs view | Done |
| P3 | Progress `labs_done` + lab quizzes | `progress.py`, `quiz.py` | Done |
| P4 | pandapower / CACER submodule | optional | Deferred (theory placeholder) |

### Lab interface checklist

- [x] Registry entry with EN/KK titles and estimated minutes
- [x] Theory pane from markdown
- [x] Parameter form (sliders) with defaults
- [x] Deterministic seed where applicable (load / shared energy)
- [x] Loading / empty / error states
- [x] Results: metrics + Plotly themed charts
- [x] Reflection quiz id + `ProgressTracker.mark_lab`
- [x] Unit tests for simulation kernels
- [x] License NOTICE updated


---

# P4 delivery (submodule + sim-cacer + offline power flow)

**Updated:** 2026-07-17

| Item | Location |
|------|----------|
| Git submodule | `third_party/CACER_Simulator` (BSD-3) |
| NOTICE / clone help | `third_party/NOTICE.md`, `third_party/README.md` |
| Optional deps | `pyproject.toml` extra `[sim-cacer]`, `requirements-sim-cacer.txt` |
| EcoPradict notebook | `notebooks/labs/power_flow.ipynb` (Docker-ignored) |
| Labs hub | `lab_grid_impact` offline status + mark reviewed |
| Path helper | `src/simulation/community/cacer_path.py` (`ECOPREDICT_CACER_ROOT`) |

```bash
git submodule update --init --recursive third_party/CACER_Simulator
pip install -e ".[sim-cacer]"
jupyter notebook notebooks/labs/power_flow.ipynb
```

**Excluded from Docker / production:** pandapower, full CACER stack, xlwings, notebooks.
