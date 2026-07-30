# Зертхана теориясы: қауымдастық инвестиция KPI

## Оқу мақсаттары
1. PV қауымдастық жобасы үшін LCOE, payback, NPV, IRR есептеу.
2. Жылдық өндіріс пен тарифті cash-flow-ға байланыстыру.
3. Дисконт өзгергенде NPV қашан оң болатынын түсіндіру.

## Cash-flow сызбасы
- \(t=0\): \(-CAPEX\)  
- \(t=1..N\): жылдық таза үнем ≈ өндіріс × баға − OPEX  

CACER қаржы есебі идеялары EcoPradict `sustainability/economic_metrics` арқылы.

## Формулалар (KaTeX)

$$
\mathrm{NPV} = \sum_{t=0}^{N} \frac{CF_t}{(1+r)^t}
$$

Қарапайым payback:

$$
T_{pb} = \frac{CAPEX}{R_{annual} - OPEX}
$$

LCOE (EcoPradict annuity):

$$
\mathrm{LCOE} \approx \frac{CAPEX\cdot CRF + OPEX}{E_{annual}}
$$

## Тапсырмалар (есеп)
1. $CAPEX=8\times 10^4$, $E_{annual}=1.2\times 10^5\,\mathrm{kWh}$, баға $0.10\,\mathrm{\$/kWh}$ — payback (алдымен OPEX=0).
2. Дисконт $r$ өссе: NPV төмендей ме?
3. Зертхана KPI: LCOE, NPV, IRR жазыңыз.
