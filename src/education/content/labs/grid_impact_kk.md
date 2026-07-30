# Зертхана теориясы: қуат ағыны (P4 офлайн)

## Күйі
Бұл зертхана **production Streamlit/Docker бейнесінде іске қосылмайды**.  
Ауыр тәуелділік: **pandapower** (опционалды extra `[sim-cacer]`).

## Оқу мақсаттары
1. Жоғары PV экспорт неге жергілікті кернеуді көтеретінін түсіндіру.
2. Кішкентай load-flow іске қосып, `vm_pu` және сызық жүктемесін оқу.
3. P3 қауымдастық KPI мен желі физикасын ажырату.

## Орнату
```bash
pip install -e ".[sim-cacer]"
# немесе: pip install -r requirements-sim-cacer.txt
git submodule update --init --recursive third_party/CACER_Simulator
```

## Қайда іске қосу
| Ресурс | Жол |
|--------|-----|
| EcoPradict notebook | `notebooks/labs/power_flow.ipynb` |
| CACER Tutorial 4 | `third_party/CACER_Simulator/4. Tutorial_power_flow_simulator.ipynb` |

Қосымша: `ECOPREDICT_CACER_ROOT`.

## Не кірмейді
- Толық итальяндық CACER / ARERA  
- xlwings / Excel  
- Docker-дегі pandapower  

## Атрибуция
CACER_Simulator — BSD 3-Clause — RSE / Aleotti, Rollo  
https://github.com/RSE-CoLabs/CACER_Simulator · `third_party/NOTICE.md`

## Формулалар (KaTeX)

Радиалды фидердегі жуық кернеу өсімі (ойыншық модель):

$$
\Delta V \approx \frac{R\,P + X\,Q}{V}
$$

Load flow: $V_{\mathrm{pu}} = |V|/V_{nom}$.

## Тапсырмалар (есеп / офлайн notebook)
1. `power_flow.ipynb` ішінде PV MW sweep; $V_{\mathrm{pu}}(P_{pv})$ графигі.
2. $V_{\mathrm{pu}} \ge 1.05$ болатын ең кіші $P_{pv}$ (бар болса).
3. Кері қуат ағынын $\Delta V$ формуласындағы $P$ таңбасымен байланыстырыңыз.
