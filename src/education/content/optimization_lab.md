# Lab: Hybrid battery optimization

## Goal

Minimize cost / CO₂ over 24 hours using solar + wind forecasts and a battery.

## Model

`HybridEnergyOptimizer` (PuLP) balances:

```
solar + wind + discharge + grid_import
  = load + charge + grid_export + curtail
```

## Modes

| Mode | Focus |
|------|--------|
| `max_profit` | Grid arbitrage / export revenue |
| `min_co2` | Reduce grid imports |
| `balanced` | Equal weights |

## Try

1. Set battery capacity 50–200 kWh.  
2. Raise evening load.  
3. Compare CO₂ and profit between modes.  
