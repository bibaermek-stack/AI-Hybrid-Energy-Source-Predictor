# Lab theory: PV production profiles

## Learning objectives
1. Link hourly irradiance/temperature to array AC/DC power.
2. Integrate power over the day to get yield (kWh).
3. See site weather impact (sample vs synthetic vs Open-Meteo).

## Concept (CACER Tutorial 1 style)
A production profile is the time series of PV output used later for shared energy and bills.  
Here we use EcoPradict’s panel model + weather adapter (no full CACER Excel stack).

## Formulas (KaTeX)

Daily yield (hourly steps $\Delta t = 1\,\mathrm{h}$):

$$
E_{day} = \sum_{t=1}^{24} P_t \,\Delta t
$$

## Tasks (compute)
1. For 80 panels, report $E_{day}$ (kWh) and $P_{\max}$.
2. Double panels: is $E_{day}' / E_{day} \approx 2$?
3. Compare sample vs synthetic weather: relative yield $\delta = (E_a - E_b)/E_a$.
