# Lab theory: domestic load emulation

## Learning objectives
1. Build a synthetic daily load with morning and evening peaks.
2. Rescale to a target peak kW.
3. Understand why synthetic loads are useful without smart meters.

## Shape model
Base load + Gaussian bumps near 08:00 and 19:00, with night valley and optional noise.  
Inspired by CACER domestic load emulator tutorials (simplified; no Italian registry Excel).

## Formulas (KaTeX)

Peak rescale:

$$
P'_t = P_t \cdot \frac{P_{peak}^{\mathrm{target}}}{\max_t P_t}
$$

Daily energy:

$$
E_{load} = \sum_{t} P'_t \,\Delta t
$$

## Tasks (compute)
1. Set evening peak high; compute $E_{load}$ for 24 h.
2. Change seed; is $E_{load}$ approximately stable (within ~10%)?
3. If $P_{peak}^{\mathrm{target}}=5\,\mathrm{kW}$ and raw max is $3.5\,\mathrm{kW}$, what scale factor is applied?
