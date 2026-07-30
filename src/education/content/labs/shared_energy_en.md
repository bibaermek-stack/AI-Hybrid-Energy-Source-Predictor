# Lab theory: shared renewable energy (simplified REC)

## Learning objectives
1. Define individual self-consumption, community shared energy, residual grid import.
2. Compute the three KPIs for a toy multi-user community.
3. Observe how community battery and user count change shared %.

## Accounting rules (educational, not full CACER/ARERA)
1. Each user self-consumes \(\min(P_{pv}, P_{load})\).  
2. Residual surpluses and deficits form a pool; matched volume is **shared energy**.  
3. Community BESS then charges/discharges the residual.  
4. Remainder is grid import or export.

Regulatory incentives (Italian CACER) are a reading assignment — this lab uses KZ-like import/export prices as a bill proxy.

## Formulas (KaTeX)

Per-user self-consumption at hour $t$:

$$
E_{self,u,t} = \min(P_{pv,u,t},\,P_{load,u,t})\,\Delta t
$$

Shared match from residual pools:

$$
E_{shared,t} = \min\bigl(S_t,\,D_t\bigr)\,\Delta t
$$

where $S_t=\sum_u (P_{pv,u}-P_{load,u})_+$ and $D_t=\sum_u (P_{load,u}-P_{pv,u})_+$.

## Tasks (compute)
1. For $N=3$ users, report $E_{shared}$, $E_{import}$, $SC\%$.
2. Raise DoD: does **pre-battery** $E_{shared}$ change? Why?
3. Bill proxy: $B = c_{imp} E_{import} - c_{exp} E_{export}$.
