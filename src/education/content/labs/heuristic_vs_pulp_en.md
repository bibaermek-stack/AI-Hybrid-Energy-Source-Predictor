# Lab theory: heuristic dispatch vs PuLP

## Learning objectives
1. Contrast rule-based PV→load→battery→grid with horizon optimization.
2. Compare grid import and CO₂ proxy under the same solar/load day.
3. Explain when prices / CO₂ weights change optimal battery use.

## Two engines
| Engine | Where | Policy |
|--------|--------|--------|
| Heuristic | `run_day_simulation` | Instantaneous priority rules |
| PuLP LP | `HybridEnergyOptimizer` | Minimize cost/CO₂ over the day with SOC constraints |

## Formulas (KaTeX)

Heuristic cost proxy:

$$
C_{heur} = c_{imp}\,E_{imp}^{heur} - c_{exp}\,E_{exp}^{heur}
$$

Import gap (lab KPI):

$$
\Delta E_{imp} = E_{imp}^{heur} - E_{imp}^{\mathrm{PuLP}}
$$

## Tasks (compute)
1. Run both engines; report $\Delta E_{imp}$ (kWh).
2. With $c_{imp}=0.12$, $c_{exp}=0.06$, compute $C_{heur}$ from metric cards.
3. Switch mode to min_co2: does $E_{imp}^{\mathrm{PuLP}}$ fall?
