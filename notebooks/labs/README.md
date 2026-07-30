# Education lab notebooks (offline electives)

These notebooks are **not** executed by the production Streamlit/Docker image
(see `.dockerignore`).

| Notebook | Purpose | Extra deps |
|----------|---------|------------|
| `power_flow.ipynb` | Toy pandapower feeder; voltage vs PV export | `pip install -e ".[sim-cacer]"` |

## CACER upstream tutorials

After:

```bash
git submodule update --init --recursive third_party/CACER_Simulator
```

open e.g. `third_party/CACER_Simulator/4. Tutorial_power_flow_simulator.ipynb`.

License: BSD-3-Clause — see `third_party/NOTICE.md`.
