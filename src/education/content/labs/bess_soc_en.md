# Lab theory: battery SOC over a day

## Learning objectives
1. Define state of charge (SOC) as stored energy / capacity.
2. See charging when PV exceeds load and discharging when load exceeds PV.
3. Note that efficiency and power limits slow SOC swings.

## Formulas (KaTeX)

$$
SOC_{t+1} = SOC_t + \frac{\eta\,P_{ch}\Delta t - P_{dis}\Delta t/\eta}{E_{cap}}
$$

with $0 \le SOC \le 1$ (or DoD floor $SOC_{\min} = 1-\mathrm{DoD}$).

## Tasks (compute)
1. $E_{cap}=40\,\mathrm{kWh}$, $SOC_0=0.5$, charge $P_{ch}=10\,\mathrm{kW}$ for $1\,\mathrm{h}$ at $\eta=0.95$. Find $SOC_1$.
2. Same battery, discharge $8\,\mathrm{kW}$ for $1\,\mathrm{h}$. New SOC?
3. With $\mathrm{DoD}=0.8$, what is the minimum allowed $SOC$?
