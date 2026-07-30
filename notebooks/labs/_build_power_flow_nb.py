"""One-shot builder for power_flow.ipynb (run from repo root)."""
from __future__ import annotations

import json
from pathlib import Path

CELLS = [
    (
        "markdown",
        """# Lab (P4 elective): Power flow intro with pandapower

**EcoPradict-Ai offline notebook** — not run inside the production Streamlit/Docker image.

## Goals
1. Build a tiny radial network (bus–line–load–PV).
2. Run a load flow and inspect bus voltages / line loading.
3. Raise PV injection and observe voltage rise (export stress).

## Setup
```bash
pip install -e ".[sim-cacer]"
# or: pip install -r requirements-sim-cacer.txt
git submodule update --init --recursive third_party/CACER_Simulator
```

## Related material
- CACER Tutorial 4: `third_party/CACER_Simulator/4. Tutorial_power_flow_simulator.ipynb` (BSD-3)
- Streamlit Labs page: `lab_grid_impact` (offline hub)
- Attribution: `third_party/NOTICE.md`

> Educational toy network. Not a full Italian CACER / ARERA engine and not a real feeder model for Kazakhstan.
""",
    ),
    (
        "code",
        """from pathlib import Path
import sys

ROOT = Path.cwd()
if (ROOT / "src").is_dir():
    PROJECT = ROOT
elif (ROOT.parent.parent / "src").is_dir():
    PROJECT = ROOT.parent.parent
else:
    PROJECT = ROOT
if str(PROJECT) not in sys.path:
    sys.path.insert(0, str(PROJECT))

from src.simulation.community.cacer_path import get_cacer_root, sim_cacer_status

status = sim_cacer_status()
for k, v in status.items():
    print(f"{k}: {v}")

assert status["pandapower"], (
    'pandapower missing. Install: pip install -e ".[sim-cacer]"'
)
""",
    ),
    (
        "markdown",
        """## 1. Create a small radial network

External grid → bus0 (HV) — transformer — bus1 (MV) — line — bus2 (load + PV).
""",
    ),
    (
        "code",
        """import pandapower as pp


def build_toy_net(pv_mw: float = 0.05, load_mw: float = 0.08):
    \"\"\"Minimal educational network (MW, 0.4 kV LV style).\"\"\"
    net = pp.create_empty_network(name="ecopredict_toy")
    b0 = pp.create_bus(net, vn_kv=20.0, name="HV")
    b1 = pp.create_bus(net, vn_kv=0.4, name="LV_main")
    b2 = pp.create_bus(net, vn_kv=0.4, name="LV_prosumer")
    pp.create_ext_grid(net, bus=b0, vm_pu=1.0, name="grid")
    pp.create_transformer_from_parameters(
        net,
        hv_bus=b0,
        lv_bus=b1,
        sn_mva=0.25,
        vn_hv_kv=20.0,
        vn_lv_kv=0.4,
        vkr_percent=1.0,
        vk_percent=6.0,
        pfe_kw=0.5,
        i0_percent=0.1,
        name="TR",
    )
    pp.create_line_from_parameters(
        net,
        from_bus=b1,
        to_bus=b2,
        length_km=0.15,
        r_ohm_per_km=0.642,
        x_ohm_per_km=0.083,
        c_nf_per_km=210,
        max_i_ka=0.142,
        name="feeder",
    )
    pp.create_load(net, bus=b2, p_mw=load_mw, q_mvar=load_mw * 0.3, name="load")
    if pv_mw > 0:
        pp.create_sgen(net, bus=b2, p_mw=pv_mw, q_mvar=0.0, name="pv")
    return net


net = build_toy_net(pv_mw=0.02, load_mw=0.08)
pp.runpp(net)
print(net.res_bus)
print(net.res_line)
""",
    ),
    (
        "markdown",
        """## 2. Sweep PV injection

Increase community PV at the prosumer bus and track `vm_pu` and line loading.
""",
    ),
    (
        "code",
        """import pandas as pd

rows = []
for pv in [0.0, 0.02, 0.05, 0.08, 0.12, 0.15]:
    n = build_toy_net(pv_mw=pv, load_mw=0.08)
    try:
        pp.runpp(n)
        prosumer_idx = n.bus.index[n.bus.name == "LV_prosumer"][0]
        vm = float(n.res_bus.loc[prosumer_idx, "vm_pu"])
        loading = float(n.res_line["loading_percent"].iloc[0])
        ploss = float(n.res_line["pl_mw"].sum())
        ok = True
        msg = "ok"
    except Exception as e:
        vm = loading = ploss = float("nan")
        ok = False
        msg = str(e)
    rows.append(
        {
            "pv_mw": pv,
            "vm_pu": vm,
            "line_loading_pct": loading,
            "ploss_mw": ploss,
            "ok": ok,
            "msg": msg,
        }
    )

df = pd.DataFrame(rows)
print(df)

try:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(1, 2, figsize=(10, 3.5))
    ax[0].plot(df["pv_mw"], df["vm_pu"], marker="o")
    ax[0].set_xlabel("PV MW")
    ax[0].set_ylabel("Bus voltage pu")
    ax[0].set_title("Voltage vs PV")
    ax[0].axhline(1.05, color="r", ls="--", alpha=0.5, label="1.05 pu")
    ax[0].legend()
    ax[1].plot(df["pv_mw"], df["line_loading_pct"], marker="o", color="orange")
    ax[1].set_xlabel("PV MW")
    ax[1].set_ylabel("Line loading %")
    ax[1].set_title("Loading vs PV")
    plt.tight_layout()
    plt.show()
except Exception as e:
    print("Plot skipped:", e)
""",
    ),
    (
        "markdown",
        """## 3. Reflection

1. At what PV level does `vm_pu` approach or exceed 1.05?
2. Does high export always mean high line loading? Why or why not?
3. How would a community BESS change the *net* injection seen by the feeder?

Mark progress in EcoPradict Streamlit Labs → **Power flow intro** → *Mark offline lab reviewed*.

For the full RSE CACER power-flow tutorial (Italian case files), open the submodule notebook after `git submodule update --init`.
""",
    ),
    (
        "code",
        """root = get_cacer_root()
if root:
    tut = root / "4. Tutorial_power_flow_simulator.ipynb"
    print("CACER tutorial:", tut if tut.is_file() else "(file missing)")
    print("Open in JupyterLab / VS Code from that path.")
else:
    print(
        "Submodule missing. Run: "
        "git submodule update --init --recursive third_party/CACER_Simulator"
    )
""",
    ),
]


def main() -> None:
    out = Path(__file__).with_name("power_flow.ipynb")
    cells = []
    for kind, src in CELLS:
        cell = {
            "cell_type": kind,
            "metadata": {},
            "source": [line + "\n" for line in src.strip("\n").split("\n")],
        }
        if kind == "code":
            cell["execution_count"] = None
            cell["outputs"] = []
        cells.append(cell)
    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "cells": cells,
    }
    out.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
    print("wrote", out)


if __name__ == "__main__":
    main()
