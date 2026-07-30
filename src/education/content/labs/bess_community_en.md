# Lab theory: BESS timestep and DoD

## Learning objectives
1. Apply a single BESS energy step with half-cycle efficiency.
2. Enforce DoD via \(E_{min} = E_{cap}(1-\mathrm{DoD})\).
3. Interpret terminal real energy vs theoretical intent.

## Adapted from CACER `BESS(...)` (BSD-3)
Pure function `bess_step` / `simulate_bess_series` — no Excel I/O.

Positive terminal intent → charge; negative → discharge.  
Clamping at min/max capacity creates losses relative to unconstrained intent.

## Formulas (KaTeX)

DoD floor:

$$
E_{\min} = E_{cap}\,(1-\mathrm{DoD})
$$

Half-cycle efficiency maps theoretical terminal energy to real SOC change (see `bess_step`).

## Tasks (compute)
1. $E_{cap}=50\,\mathrm{kWh}$, $\mathrm{DoD}=0.8$ → find $E_{\min}$.
2. Run series with $\mathrm{DoD}=0.5$ vs $0.9$; compare final $SOC$.
3. Lower $\eta$: report increase in $\sum E_{loss}$.
