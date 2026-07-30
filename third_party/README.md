# Third-party sources

## CACER_Simulator (git submodule)

| Field | Value |
|-------|--------|
| Path | `third_party/CACER_Simulator` |
| Upstream | https://github.com/RSE-CoLabs/CACER_Simulator |
| License | BSD 3-Clause (see `LICENSE.txt` and `NOTICE.md`) |

### Clone / init

```bash
# After cloning EcoPradict-Ai:
git submodule update --init --recursive third_party/CACER_Simulator

# Or first-time add (maintainers):
# git submodule add https://github.com/RSE-CoLabs/CACER_Simulator.git third_party/CACER_Simulator
```

### Override path

```bash
export ECOPREDICT_CACER_ROOT=/path/to/CACER_Simulator
```

### How EcoPradict uses it

- **Read-only vendor** for tutorials and attribution.
- **Do not** put `third_party/CACER_Simulator/src` on `PYTHONPATH` as top-level `src`.
- Education kernels live under EcoPradict `src/simulation/community/` (pure adapters).
- Full Italian market / Excel / xlwings workflow stays **outside** production Docker.
- Optional scientific deps: `pip install -e ".[sim-cacer]"` (pvlib, pandapower).

### Elective notebook

See `notebooks/labs/power_flow.ipynb` and CACER  
`4. Tutorial_power_flow_simulator.ipynb`.
