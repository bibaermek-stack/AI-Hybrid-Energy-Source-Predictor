# Lab theory: PV on a low-voltage feeder (power flow)

## Learning objectives
1. Explain why PV export raises the voltage along a feeder.
2. Run a load flow over a day and read the voltage limits (EN 50160: 0.90–1.10 pu).
3. Try the counter-measures: a thicker cable, a lower transformer tap, reactive power from the PV inverters.

## The model
A radial 0.4 kV feeder from the transformer's low-voltage busbar to *N* houses at equal spacing.
Every house has the same PV system and the same household load; both follow a daily profile (clear-sky PV,
morning and evening demand peaks). The lab solves the feeder for each hour with the **backward/forward sweep**
— the method pandapower uses for radial networks — and reports the highest and lowest bus voltage.

Cables (per phase, 20 °C): NAYY 4×50 mm² (R = 0.642 Ω/km), 4×95 mm² (0.320 Ω/km), 4×150 mm² (0.206 Ω/km).

## Formulas (KaTeX)

Voltage change across a line segment carrying active power $P$ and reactive power $Q$ toward the transformer:

$$
\Delta V \approx \frac{R\,P + X\,Q}{V}
$$

Export ($P > 0$ flowing back) makes $\Delta V$ positive: the voltage **rises** toward the end of the feeder.
An inverter that absorbs reactive power ($Q < 0$, power factor below 1) makes the $X\,Q$ term negative and
offsets part of the rise.

Per-unit voltage: $V_{\mathrm{pu}} = |V| / V_{nom}$, with $V_{nom} = 230\,\mathrm{V}$ phase-to-neutral (400 V line-to-line).

## What to try
1. Default settings: note the hour of the highest voltage. Why is it around midday?
2. Increase the PV per house until the highest voltage passes 1.10 pu.
3. Keep that PV and change only the cable to 4×150 mm². What happens to the rise?
4. Set the inverter power factor to 0.90. Compare with 1.00.
5. Lower the transformer voltage to 0.98 pu. Why does this help at noon but hurt in the evening?

## Attribution
The previous offline notebook (notebooks/labs/power_flow.ipynb, pandapower) and CACER_Simulator Tutorial 4
(BSD 3-Clause, RSE s.p.a.) remain available for advanced study; this lab no longer needs them.
