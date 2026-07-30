# Lab theory: power flow intro (P4 offline elective)

## Status
This lab is **not executed inside the production Streamlit/Docker image**.  
Heavy dependency: **pandapower** (optional extra `[sim-cacer]`).

## Learning objectives
1. Explain why high PV export can raise local voltage on a feeder.
2. Run a toy load-flow and read bus `vm_pu` and line loading.
3. Contrast community energy KPIs (Labs P3) with grid physics (this notebook).

## Setup
```bash
pip install -e ".[sim-cacer]"
# or: pip install -r requirements-sim-cacer.txt
git submodule update --init --recursive third_party/CACER_Simulator
```

## Where to run
| Resource | Path |
|----------|------|
| EcoPradict notebook | `notebooks/labs/power_flow.ipynb` |
| CACER Tutorial 4 | `third_party/CACER_Simulator/4. Tutorial_power_flow_simulator.ipynb` |

Optional: `ECOPREDICT_CACER_ROOT` points to a local CACER checkout.

## What is *not* included
- Full Italian CACER / ARERA incentive engine  
- xlwings / Excel market workflows  
- Production Docker image packages for pandapower  

## Attribution
CACER_Simulator — BSD 3-Clause — Copyright (c) 2025 Aleotti Federico, Rollo Antonino / RSE s.p.a.  
https://github.com/RSE-CoLabs/CACER_Simulator · see `third_party/NOTICE.md`

## Formulas (KaTeX)

Approximate voltage rise on a radial feeder (toy model):

$$
\Delta V \approx \frac{R\,P + X\,Q}{V}
$$

Per-unit bus voltage from load flow: $V_{\mathrm{pu}} = |V|/V_{nom}$.

## Tasks (compute / offline notebook)
1. In `power_flow.ipynb`, sweep PV MW and plot $V_{\mathrm{pu}}(P_{pv})$.
2. Find the smallest $P_{pv}$ with $V_{\mathrm{pu}} \ge 1.05$ (if any).
3. Relate reverse power flow to the sign of $P$ in the $\Delta V$ formula.
