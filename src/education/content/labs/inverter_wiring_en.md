# Lab theory: inverter 3D wiring trainer

## Learning objectives
1. Identify major parts on the **Solar Inverter Subsystem** CAD assembly (DC, AC, PE, isolator, logger).
2. Diagnose common install faults: reversed DC, open isolator, swapped L/N, loose logger.
3. Restore a **healthy topology** on the digital wiring board and verify with **Check**.

## Healthy topology
| Port | Correct connection |
|------|--------------------|
| DC+ | PV string **+** |
| DC− | PV string **−** |
| PE | Site earth bar |
| AC L | Grid L |
| AC N | Grid N |
| AC isolator | **ON** (closed) to export |
| Data logger | Seated on COM |

## Safety note
This is a **digital trainer**. On a real plant: isolate energy, lock-out/tag-out, follow local electrical codes. Never reverse DC polarity under load.

## How to use the lab
1. Select a **fault scenario** (A–E).
2. Inspect the **3D model** (click red DC+, blue DC−, purple isolator, pink logger…).
3. Fix the same ports on the **wiring board**.
4. Press **Check wiring** → Correct / Incorrect (try again).
5. Solve the graded theory tasks below.

## Formulas (KaTeX)

DC power into inverter (ideal):

$$
P_{DC} \approx V_{string} \cdot I_{string}
$$

AC export only if isolator closed and grid connection healthy:

$$
P_{AC} = \eta_{inv}\,P_{DC}\quad (\text{isolator ON, grid OK})
$$

## Tasks (compute / procedure)
1. In scenario **reversed_dc**, which two ports must be swapped?
2. Isolator OFF → expected grid export is $0$ even if $P_{DC}>0$. True or false?
3. Logger loose: does plant stop producing AC, or only lose telemetry?
