# Lab theory: community investment KPIs

## Learning objectives
1. Compute LCOE, simple payback, NPV, and IRR for a PV community project.
2. Link annual generation and tariff to cash flows.
3. Interpret when NPV becomes positive as discount rate changes.

## Cash-flow sketch
- \(t=0\): \(-CAPEX\)  
- \(t=1..N\): annual net savings ≈ generation × price − OPEX  

Maps CACER-style financial reporting ideas onto EcoPradict `sustainability/economic_metrics`.

## Formulas (KaTeX)

$$
\mathrm{NPV} = \sum_{t=0}^{N} \frac{CF_t}{(1+r)^t}
$$

Simple payback:

$$
T_{pb} = \frac{CAPEX}{R_{annual} - OPEX}
$$

LCOE (annuity form used in EcoPradict):

$$
\mathrm{LCOE} \approx \frac{CAPEX\cdot CRF + OPEX}{E_{annual}}
$$

## Tasks (compute)
1. $CAPEX=8\times 10^4$, $E_{annual}=1.2\times 10^5\,\mathrm{kWh}$, price $0.10\,\mathrm{\$/kWh}$ — find payback (ignore OPEX first).
2. Raise discount $r$: does NPV fall?
3. From lab metrics, report LCOE, NPV, IRR.
