# Lab theory: solar inverter subsystem in 3D

## Learning objectives
1. Name the parts of a small grid-tied PV system on a real CAD assembly and say what each does.
2. Diagnose a fault from what the plant shows: the inverter display, the meter and the monitoring app.
3. Fix it safely, in the right order, and confirm the plant exports again.

## The system (left to right)
| Part | What it does |
|------|--------------|
| **PV array DC isolator** | Switches the PV string off so the inverter can be worked on. Live whenever the sun shines. |
| **DC cables PV+ / PV−** | Bring the array's direct current to the inverter; MC4 plugs at the ends. |
| **Inverter DC inputs** | DC− (blue tag) and DC+ (red tag). PV+ must land on DC+. |
| **Inverter** | Turns DC into 230 V AC in step with the grid. The display shows Pac or the fault. |
| **AC cable** | Line L, neutral N and protective earth PE to the AC isolator. |
| **AC isolator** | Disconnects the inverter from the grid; holds the L, N and PE terminals. |
| **Generation meter** | Counts the exported energy; its LED flashes 1000 times per kWh. |
| **Wi-Fi data logger** | On the COM port; sends data to the monitoring app (added to the model for this lab). |

## What the plant shows
The inverter checks, in this order: PV input, DC polarity, insulation/earth, then the grid.

| Display | Cause |
|---------|-------|
| No PV input · Vpv 0 V (screen dark) | DC isolator OFF |
| DC polarity error | PV+ and PV− swapped at the DC inputs |
| Insulation / earth fault | PE not connected |
| Grid lost · Vac 0 V | AC isolator OFF |
| Grid fault: L/N | Line and neutral swapped |
| Exporting · Pac 3.2 kW | Healthy — the meter counts |

A pulled-out logger does not stop production: the meter keeps counting but the app shows the plant offline.

## Formulas (KaTeX)

$$
P_{AC} = \eta_{inv}\,P_{DC} \quad \text{only with DC input, correct polarity, PE, and a healthy grid}
$$

Meter LED rate at 1000 imp/kWh: $f = P_{AC}\,[\mathrm{kW}] \times 1000 / 3600$ flashes per second
(3.2 kW → about 0.9 per second).

## Safety (the inverter's own labels)
*Dual supply — isolate AC and DC before carrying out work.* *Do not disconnect DC plugs under load — turn off the
AC supply first.* On a real plant: AC isolator OFF, then DC isolator OFF, prove dead, then disconnect. This lab is a
digital trainer only.

## How to use the lab
1. **Explore**: tap each part and read what it is.
2. **Fix faults**: choose a scenario, read the display and the readings, tap parts to inspect and operate them,
   then press **Check the system**.
3. **Test**: 7 questions — three are answered by tapping the model, one by fixing a system in 3D.
