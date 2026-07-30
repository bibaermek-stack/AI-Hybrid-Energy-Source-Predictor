# Solar panel and inverter faults (EcoPredict)

## Hotspots
Local overheating on a cell or string lowers power and can damage EVA. Causes: partial shading, cracked cells, failed bypass diodes. Thermal mode on the 3D inverter view highlights elevated temperatures.

## Soiling and dust
Dust on glass reduces irradiance reaching the cell (typical loss 5–25% in dry climates). Look for lower AC power at high clear-sky irradiance.

## PID (potential induced degradation)
High system voltage and humidity can cause progressive power loss. Mitigation: proper grounding, night-time PID recovery modes on some inverters.

## Inverter faults
- Grid undervoltage / overvoltage: check utility voltage and inverter grid profile (Kazakhstan grid code).
- Islanding / anti-islanding trips: unstable grid or phase imbalance.
- MPPT faults: string open circuit, reverse polarity, or severe mismatch.
- Arc fault (if supported): inspect DC connectors and cable damage.

## Communication loss
Solarman / Datalogger offline: check Wi‑Fi/4G, SN binding, and OpenAPI credentials. Live dashboard shows last good telemetry.

## Diagnostic tips
Compare DC string powers (MPPT1 vs MPPT2). Large imbalance often means soiling, shade, or a bad string. Use Fault Detection (YOLO/CNN) for visual panel defects when photos are available.
