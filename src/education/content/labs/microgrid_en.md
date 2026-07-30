# Lab theory: microgrid day dispatch

## Learning objectives
1. Explain energy balance among PV, load, battery, and grid.
2. Interpret SOC over 24 hours.
3. Compute self-consumption and grid import energy.

## Dispatch priority (heuristic)
1. Convert PV DC → AC (inverter η).  
2. Meet local load.  
3. Charge battery with surplus; export remainder.  
4. Discharge battery on deficit; import remainder.

## Contrast with EcoPradict PuLP optimizer
This lab uses a **rule-based** balancer. The Optimization tab uses **linear programming** over a horizon with prices and CO₂ weights. Compare results on the same solar/load shape in a follow-up exercise.

## Formulas (KaTeX)

Power balance (hourly, kW):

$$
P_{pv} + P_{dis} + P_{import} = P_{load} + P_{ch} + P_{export}
$$

Self-consumption:

$$
SC\% = 100 \cdot \frac{E_{pv,\,\mathrm{used\,on\,site}}}{E_{pv}}
$$

## Tasks (compute)
1. Run default day; record $E_{import}$, $E_{export}$, final $SOC$.
2. Set $P_{load}=30\,\mathrm{kW}$, $E_{bat}=20\,\mathrm{kWh}$ — report evening import (kWh).
3. If $E_{pv}=120\,\mathrm{kWh}$ and on-site use is $90\,\mathrm{kWh}$, compute $SC\%$.
