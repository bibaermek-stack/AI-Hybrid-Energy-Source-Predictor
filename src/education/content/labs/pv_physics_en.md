# Lab theory: PV power

## Learning objectives
1. Compute DC power from irradiance, area, and efficiency.
2. Apply temperature derating above 25 °C.
3. See how array size scales output.

## Model
\[
P_{DC} = \eta_{eff} \cdot A_{total} \cdot G
\]
where \(\eta_{eff} = \eta_0 (1 - \gamma \max(T - 25, 0))\), \(G\) is irradiance (W/m²).

## Formulas (KaTeX)

$$
P_{DC} = \eta_{eff} \, A_{total} \, G
$$

$$
\eta_{eff} = \eta_0 \bigl(1 - \gamma \max(T-25,\,0)\bigr)
$$

where $G$ is irradiance (W/m²), $A_{total}$ total area (m²), $T$ module temperature (°C).

## Tasks (compute)
1. Given $\eta_0=0.20$, $\gamma=0.004$, $T=45^{\circ}\mathrm{C}$, $A_{total}=160\,\mathrm{m}^2$, $G=900\,\mathrm{W/m}^2$ — compute $\eta_{eff}$ and $P_{DC}$ (kW).
2. Double $G$ with $T$ fixed: by what factor does $P_{DC}$ change in this model?
3. If $\gamma$ rises from $0.003$ to $0.005$ at $T=50^{\circ}\mathrm{C}$, estimate relative loss vs $25^{\circ}\mathrm{C}$.
