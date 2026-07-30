# Third-party notices

## RenewableEnergySim

- **Project:** RenewableEnergySim  
- **Upstream:** https://github.com/nabilkhondaker/RenewableEnergySim  
- **License:** MIT  
- **Use in EcoPradict-Ai:** Physics models under `src/simulation/microgrid/`  
  (solar panel, battery ESS, inverter, MPPT, load balancer, day engine) adapted for
  education labs. Heuristic vs PuLP comparison uses the same day engine plus EcoPradict
  `HybridEnergyOptimizer`.

Copyright (c) 2026 Nabil Khondaker A (see upstream LICENSE).

## CACER Simulator

- **Project:** CACER_Simulator  
- **Upstream:** https://github.com/RSE-CoLabs/CACER_Simulator  
- **Broken alias (404):** https://github.com/RSE-CoLabs/CACER_Sim  
- **License:** BSD 3-Clause  
- **Copyright:** Copyright (c) 2025, Aleotti Federico, Rollo Antonino / RSE s.p.a.  
  Full text: `third_party/CACER_Simulator/LICENSE.txt`  
- **Vendored as:** git submodule `third_party/CACER_Simulator`  
- **Optional env:** `ECOPREDICT_CACER_ROOT`  
- **Optional pip extra:** `pip install -e ".[sim-cacer]"` → pvlib, pandapower, numpy-financial  
  (**not** xlwings / pywin32 / full CACER `requirements.txt`)

### Use in EcoPradict-Ai

| Path | Role |
|------|------|
| `third_party/CACER_Simulator/` | Read-only tutorials, config samples, attribution |
| `src/simulation/community/` | Pure adapters (BESS step, load, shared energy, finance) |
| `notebooks/labs/power_flow.ipynb` | Offline pandapower elective (excluded from Docker) |
| `dashboard/views/labs.py` → `lab_grid_impact` | Offline instructions + submodule status |

**Not** bulk-merged: Italian ARERA incentive engine, Excel/xlwings I/O, full CACER Streamlit dashboard.

When redistributing adapted source, retain the above copyright notice, conditions, and disclaimer.

## Implementation status (labs)

| Phase | Scope | Status |
|-------|--------|--------|
| P1 | Microgrid physics + PV / MPPT / SOC / dispatch labs | Integrated |
| P2 | Heuristic vs PuLP lab | Integrated |
| P3 | Community BESS, load, shared energy, finance labs | Integrated (adapters) |
| P4 | Submodule + `[sim-cacer]` + power-flow notebook + Labs offline hub | Integrated (elective) |

See `docs/INTEGRATION_EDU_LABS.md` and `third_party/README.md`.
