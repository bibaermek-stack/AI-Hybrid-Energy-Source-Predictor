# Lab theory: MPPT (perturb & observe)

## Learning objectives
1. Explain why PV has a maximum power point (MPP).
2. Describe one P&O step: perturb voltage, measure power, keep or reverse.
3. Relate step size to tracking speed vs oscillation.

## Idea
At fixed irradiance and temperature the panel has a **P–V curve** with a single peak.  
P&O changes \(V\) by \(\Delta V\) and keeps the direction that increases \(P = V \cdot I\).

## Formulas (KaTeX)

P&O update idea (sign of power change):

$$
V_{k+1} = V_k + \Delta V \cdot \mathrm{sign}\bigl(P_k - P_{k-1}\bigr)
$$

with panel power $P = V \cdot I$.

## Tasks (compute)
1. If $P_k > P_{k-1}$ and the last step was $+\Delta V$, what is the next voltage step?
2. Compare $\Delta V = 0.2\,\mathrm{V}$ vs $1.5\,\mathrm{V}$: which converges smoother near the MPP?
3. At fixed $G$, explain why $P(V)$ has a single peak (one MPP).
