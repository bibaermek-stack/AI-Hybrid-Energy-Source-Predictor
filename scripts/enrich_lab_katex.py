"""Enrich lab theory markdown with KaTeX formula + compute tasks (EN/KK)."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src" / "education" / "content" / "labs"

EXTRA: dict[str, dict[str, str]] = {
    "pv_physics": {
        "en": r"""
## Formulas (KaTeX)

$$
P_{DC} = \eta_{eff} \, A_{total} \, G
$$

$$
\eta_{eff} = \eta_0 \bigl(1 - \gamma \max(T-25,\,0)\bigr)
$$

where $G$ is irradiance (W/m²), $A_{total}$ total area (m²), $T$ module temperature (°C).

## Tasks (compute)
1. Given $\eta_0=0.20$, $\gamma=0.004$, $T=45^{\circ}\mathrm{C}$, $A_{total}=160\,\mathrm{m}^2$, $G=900\,\mathrm{W/m}^2$ — compute $\eta_{eff}$ and $P_{DC}$ (kW).
2. Double $G$ with $T$ fixed: by what factor does $P_{DC}$ change in this model?
3. If $\gamma$ rises from $0.003$ to $0.005$ at $T=50^{\circ}\mathrm{C}$, estimate relative loss vs $25^{\circ}\mathrm{C}$.
""",
        "kk": r"""
## Формулалар (KaTeX)

$$
P_{DC} = \eta_{eff} \, A_{total} \, G
$$

$$
\eta_{eff} = \eta_0 \bigl(1 - \gamma \max(T-25,\,0)\bigr)
$$

мұнда $G$ — сәулелену (Вт/м²), $A_{total}$ — жалпы аудан (м²), $T$ — панель температурасы (°C).

## Тапсырмалар (есеп)
1. $\eta_0=0.20$, $\gamma=0.004$, $T=45^{\circ}\mathrm{C}$, $A_{total}=160\,\mathrm{m}^2$, $G=900\,\mathrm{W/m}^2$ — $\eta_{eff}$ және $P_{DC}$ (кВт) есептеңіз.
2. $T$ тұрақты, $G$ екі еселенсе: $P_{DC}$ қанша есе өзгереді?
3. $T=50^{\circ}\mathrm{C}$ кезінде $\gamma$ $0.003 \to 0.005$ болса, $25^{\circ}\mathrm{C}$-пен салыстырғанда салыстырмалы жоғалтуды бағалаңыз.
""",
    },
    "mppt": {
        "en": r"""
## Formulas (KaTeX)

P&O update idea (sign of power change):

$$
V_{k+1} = V_k + \Delta V \cdot \mathrm{sign}\bigl(P_k - P_{k-1}\bigr)
$$

with panel power $P = V \cdot I$.

## Tasks (compute)
1. If $P_k > P_{k-1}$ and the last step was $+\Delta V$, what is the next voltage step?
2. Compare $\Delta V = 0.2\,\mathrm{V}$ vs $1.5\,\mathrm{V}$: which converges smoother near the MPP?
3. At fixed $G$, explain why $P(V)$ has a single peak (one MPP).
""",
        "kk": r"""
## Формулалар (KaTeX)

P&O жаңарту идеясы:

$$
V_{k+1} = V_k + \Delta V \cdot \mathrm{sign}\bigl(P_k - P_{k-1}\bigr)
$$

мұнда $P = V \cdot I$.

## Тапсырмалар (есеп)
1. $P_k > P_{k-1}$ және соңғы қадам $+\Delta V$ болса, келесі кернеу қадамы қандай?
2. $\Delta V = 0.2\,\mathrm{V}$ пен $1.5\,\mathrm{V}$ салыстырыңыз: MPP маңында қайсысы тегісірек?
3. Тұрақты $G$ кезінде неге $P(V)$ бір шыңды (бір MPP) болады?
""",
    },
    "bess_soc": {
        "en": r"""
## Formulas (KaTeX)

$$
SOC_{t+1} = SOC_t + \frac{\eta\,P_{ch}\Delta t - P_{dis}\Delta t/\eta}{E_{cap}}
$$

with $0 \le SOC \le 1$ (or DoD floor $SOC_{\min} = 1-\mathrm{DoD}$).

## Tasks (compute)
1. $E_{cap}=40\,\mathrm{kWh}$, $SOC_0=0.5$, charge $P_{ch}=10\,\mathrm{kW}$ for $1\,\mathrm{h}$ at $\eta=0.95$. Find $SOC_1$.
2. Same battery, discharge $8\,\mathrm{kW}$ for $1\,\mathrm{h}$. New SOC?
3. With $\mathrm{DoD}=0.8$, what is the minimum allowed $SOC$?
""",
        "kk": r"""
## Формулалар (KaTeX)

$$
SOC_{t+1} = SOC_t + \frac{\eta\,P_{ch}\Delta t - P_{dis}\Delta t/\eta}{E_{cap}}
$$

$0 \le SOC \le 1$ (немесе DoD едені $SOC_{\min} = 1-\mathrm{DoD}$).

## Тапсырмалар (есеп)
1. $E_{cap}=40\,\mathrm{kWh}$, $SOC_0=0.5$, $P_{ch}=10\,\mathrm{kW}$, $1\,\mathrm{h}$, $\eta=0.95$. $SOC_1$ табыңыз.
2. Сол батареядан $8\,\mathrm{kW}$ разряд $1\,\mathrm{h}$. Жаңа SOC?
3. $\mathrm{DoD}=0.8$ болса, минималды $SOC$ қанша?
""",
    },
    "microgrid": {
        "en": r"""
## Formulas (KaTeX)

Power balance (hourly, kW):

$$
P_{pv} + P_{dis} + P_{import} = P_{load} + P_{ch} + P_{export}
$$

Self-consumption:

$$
SC\% = 100 \cdot \frac{E_{pv,\,\mathrm{used\,on\,site}}}{E_{pv}}
$$

## Tasks (compute)
1. Run default day; record $E_{import}$, $E_{export}$, final $SOC$.
2. Set $P_{load}=30\,\mathrm{kW}$, $E_{bat}=20\,\mathrm{kWh}$ — report evening import (kWh).
3. If $E_{pv}=120\,\mathrm{kWh}$ and on-site use is $90\,\mathrm{kWh}$, compute $SC\%$.
""",
        "kk": r"""
## Формулалар (KaTeX)

Сағаттық қуат балансы (кВт):

$$
P_{pv} + P_{dis} + P_{import} = P_{load} + P_{ch} + P_{export}
$$

Өз тұтыну:

$$
SC\% = 100 \cdot \frac{E_{pv,\,\mathrm{local}}}{E_{pv}}
$$

## Тапсырмалар (есеп)
1. Әдепкі күн; $E_{import}$, $E_{export}$, соңғы $SOC$ жазыңыз.
2. $P_{load}=30\,\mathrm{kW}$, $E_{bat}=20\,\mathrm{kWh}$ — кешкі импортты (кВт·сағ) есептеңіз.
3. $E_{pv}=120\,\mathrm{kWh}$, жергілікті қолдану $90\,\mathrm{kWh}$ болса, $SC\%$ табыңыз.
""",
    },
    "heuristic_vs_pulp": {
        "en": r"""
## Formulas (KaTeX)

Heuristic cost proxy:

$$
C_{heur} = c_{imp}\,E_{imp}^{heur} - c_{exp}\,E_{exp}^{heur}
$$

Import gap (lab KPI):

$$
\Delta E_{imp} = E_{imp}^{heur} - E_{imp}^{\mathrm{PuLP}}
$$

## Tasks (compute)
1. Run both engines; report $\Delta E_{imp}$ (kWh).
2. With $c_{imp}=0.12$, $c_{exp}=0.06$, compute $C_{heur}$ from metric cards.
3. Switch mode to min_co2: does $E_{imp}^{\mathrm{PuLP}}$ fall?
""",
        "kk": r"""
## Формулалар (KaTeX)

Эвристика құн проксиі:

$$
C_{heur} = c_{imp}\,E_{imp}^{heur} - c_{exp}\,E_{exp}^{heur}
$$

Импорт айырмасы:

$$
\Delta E_{imp} = E_{imp}^{heur} - E_{imp}^{\mathrm{PuLP}}
$$

## Тапсырмалар (есеп)
1. Екі қозғалтқыш; $\Delta E_{imp}$ (кВт·сағ) жазыңыз.
2. $c_{imp}=0.12$, $c_{exp}=0.06$ — карточкалардан $C_{heur}$ есептеңіз.
3. min_co2 режимі: $E_{imp}^{\mathrm{PuLP}}$ төмендей ме?
""",
    },
    "pv_yield": {
        "en": r"""
## Formulas (KaTeX)

Daily yield (hourly steps $\Delta t = 1\,\mathrm{h}$):

$$
E_{day} = \sum_{t=1}^{24} P_t \,\Delta t
$$

## Tasks (compute)
1. For 80 panels, report $E_{day}$ (kWh) and $P_{\max}$.
2. Double panels: is $E_{day}' / E_{day} \approx 2$?
3. Compare sample vs synthetic weather: relative yield $\delta = (E_a - E_b)/E_a$.
""",
        "kk": r"""
## Формулалар (KaTeX)

Тәуліктік yield ($\Delta t = 1\,\mathrm{h}$):

$$
E_{day} = \sum_{t=1}^{24} P_t \,\Delta t
$$

## Тапсырмалар (есеп)
1. 80 панель үшін $E_{day}$ (кВт·сағ) және $P_{\max}$ жазыңыз.
2. Панельді екі еселеңіз: $E_{day}' / E_{day} \approx 2$ ме?
3. Sample vs synthetic: $\delta = (E_a - E_b)/E_a$ салыстырмалы айырма.
""",
    },
    "load_shape": {
        "en": r"""
## Formulas (KaTeX)

Peak rescale:

$$
P'_t = P_t \cdot \frac{P_{peak}^{\mathrm{target}}}{\max_t P_t}
$$

Daily energy:

$$
E_{load} = \sum_{t} P'_t \,\Delta t
$$

## Tasks (compute)
1. Set evening peak high; compute $E_{load}$ for 24 h.
2. Change seed; is $E_{load}$ approximately stable (within ~10%)?
3. If $P_{peak}^{\mathrm{target}}=5\,\mathrm{kW}$ and raw max is $3.5\,\mathrm{kW}$, what scale factor is applied?
""",
        "kk": r"""
## Формулалар (KaTeX)

Шыңды масштабтау:

$$
P'_t = P_t \cdot \frac{P_{peak}^{\mathrm{target}}}{\max_t P_t}
$$

Тәуліктік энергия:

$$
E_{load} = \sum_{t} P'_t \,\Delta t
$$

## Тапсырмалар (есеп)
1. Кешкі шыңды жоғарылатыңыз; 24 сағ $E_{load}$ есептеңіз.
2. Seed өзгертіңіз; $E_{load}$ ~10% ішінде тұрақты ма?
3. $P_{peak}^{\mathrm{target}}=5\,\mathrm{kW}$, шикі max $3.5\,\mathrm{kW}$ — масштаб коэффициенті?
""",
    },
    "bess_community": {
        "en": r"""
## Formulas (KaTeX)

DoD floor:

$$
E_{\min} = E_{cap}\,(1-\mathrm{DoD})
$$

Half-cycle efficiency maps theoretical terminal energy to real SOC change (see `bess_step`).

## Tasks (compute)
1. $E_{cap}=50\,\mathrm{kWh}$, $\mathrm{DoD}=0.8$ → find $E_{\min}$.
2. Run series with $\mathrm{DoD}=0.5$ vs $0.9$; compare final $SOC$.
3. Lower $\eta$: report increase in $\sum E_{loss}$.
""",
        "kk": r"""
## Формулалар (KaTeX)

DoD едені:

$$
E_{\min} = E_{cap}\,(1-\mathrm{DoD})
$$

Жартылай цикл тиімділігі теориялық терминал энергиясын нақты SOC өзгерісіне айналдырады (`bess_step`).

## Тапсырмалар (есеп)
1. $E_{cap}=50\,\mathrm{kWh}$, $\mathrm{DoD}=0.8$ → $E_{\min}$ табыңыз.
2. $\mathrm{DoD}=0.5$ пен $0.9$; соңғы $SOC$ салыстырыңыз.
3. $\eta$ төмендесе: $\sum E_{loss}$ өсімін жазыңыз.
""",
    },
    "shared_energy": {
        "en": r"""
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
""",
        "kk": r"""
## Формулалар (KaTeX)

Пайдаланушы өз тұтынуы:

$$
E_{self,u,t} = \min(P_{pv,u,t},\,P_{load,u,t})\,\Delta t
$$

Бөліскен сәйкестік:

$$
E_{shared,t} = \min\bigl(S_t,\,D_t\bigr)\,\Delta t
$$

$S_t=\sum_u (P_{pv,u}-P_{load,u})_+$, $D_t=\sum_u (P_{load,u}-P_{pv,u})_+$.

## Тапсырмалар (есеп)
1. $N=3$: $E_{shared}$, $E_{import}$, $SC\%$ жазыңыз.
2. DoD өссе: батареяға **дейінгі** $E_{shared}$ өзгере ме? Неге?
3. Шот проксиі: $B = c_{imp} E_{import} - c_{exp} E_{export}$.
""",
    },
    "rec_finance": {
        "en": r"""
## Formulas (KaTeX)

$$
\mathrm{NPV} = \sum_{t=0}^{N} \frac{CF_t}{(1+r)^t}
$$

Simple payback:

$$
T_{pb} = \frac{CAPEX}{R_{annual} - OPEX}
$$

LCOE (annuity form used in EcoPradict):

$$
\mathrm{LCOE} \approx \frac{CAPEX\cdot CRF + OPEX}{E_{annual}}
$$

## Tasks (compute)
1. $CAPEX=8\times 10^4$, $E_{annual}=1.2\times 10^5\,\mathrm{kWh}$, price $0.10\,\mathrm{\$/kWh}$ — find payback (ignore OPEX first).
2. Raise discount $r$: does NPV fall?
3. From lab metrics, report LCOE, NPV, IRR.
""",
        "kk": r"""
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
""",
    },
    "grid_impact": {
        "en": r"""
## Formulas (KaTeX)

Approximate voltage rise on a radial feeder (toy model):

$$
\Delta V \approx \frac{R\,P + X\,Q}{V}
$$

Per-unit bus voltage from load flow: $V_{\mathrm{pu}} = |V|/V_{nom}$.

## Tasks (compute / offline notebook)
1. In `power_flow.ipynb`, sweep PV MW and plot $V_{\mathrm{pu}}(P_{pv})$.
2. Find the smallest $P_{pv}$ with $V_{\mathrm{pu}} \ge 1.05$ (if any).
3. Relate reverse power flow to the sign of $P$ in the $\Delta V$ formula.
""",
        "kk": r"""
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
""",
    },
}


def main() -> None:
    for stem, langs in EXTRA.items():
        for lang, block in langs.items():
            path = ROOT / f"{stem}_{lang}.md"
            if not path.is_file():
                print("skip missing", path.name)
                continue
            text = path.read_text(encoding="utf-8")
            if "## Formulas (KaTeX)" in text or "## Формулалар (KaTeX)" in text:
                print("already", path.name)
                continue
            cut = None
            for marker in ("## Tasks", "## Formulas", "## Тапсырма", "## Формула"):
                i = text.find(marker)
                if i >= 0 and (cut is None or i < cut):
                    cut = i
            if cut is not None:
                text = text[:cut].rstrip() + "\n"
            text = text.rstrip() + "\n" + block
            path.write_text(text, encoding="utf-8")
            print("updated", path.name)
    print("done")


if __name__ == "__main__":
    main()
