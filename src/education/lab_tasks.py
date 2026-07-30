"""
Gradable lab tasks: student answers checked with feedback (correct / wrong / try again).

Each task is deterministic (fixed numbers or multiple choice) so grading works without
re-running the full simulation UI state.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _L(en: str, kk: str) -> dict[str, str]:
    return {"en": en, "kk": kk}


def _task(
    tid: str,
    *,
    prompt: dict[str, str],
    kind: str = "number",
    answer: float | int | None = None,
    tolerance: float = 0.05,
    choices: list[dict[str, str]] | None = None,
    correct_index: int | None = None,
    unit: str = "",
    hint: dict[str, str] | None = None,
    explain: dict[str, str] | None = None,
    formula: str | None = None,
) -> dict[str, Any]:
    return {
        "id": tid,
        "prompt": prompt,
        "kind": kind,  # number | choice
        "answer": answer,
        "tolerance": float(tolerance),
        "choices": choices or [],
        "correct_index": correct_index,
        "unit": unit,
        "hint": hint or _L("Check the formula in Theory.", "Теориядағы формуланы қараңыз."),
        "explain": explain
        or _L("See the worked solution after a correct answer.", "Дұрыс жауаптан кейін шешімді қараңыз."),
        "formula": formula,
    }


# ---------------------------------------------------------------------------
# Task bank keyed by lab_id
# ---------------------------------------------------------------------------

LAB_TASKS: dict[str, list[dict[str, Any]]] = {
    "lab_pv_physics": [
        _task(
            "eta_eff",
            prompt=_L(
                r"Given $\eta_0=0.20$, $\gamma=0.004$, $T=45^\circ\mathrm{C}$: compute $\eta_{eff}$.",
                r"$\eta_0=0.20$, $\gamma=0.004$, $T=45^\circ\mathrm{C}$: $\eta_{eff}$ есептеңіз.",
            ),
            kind="number",
            # 0.20 * (1 - 0.004*20) = 0.184
            answer=0.184,
            tolerance=0.002,
            unit="",
            formula=r"\eta_{eff}=\eta_0(1-\gamma\max(T-25,0))",
            hint=_L(
                r"$\eta_{eff}=\eta_0(1-\gamma\max(T-25,0))$",
                r"$\eta_{eff}=\eta_0(1-\gamma\max(T-25,0))$",
            ),
            explain=_L(
                r"$\max(45-25,0)=20$, so $\eta_{eff}=0.20\times(1-0.004\times20)=0.20\times0.92=0.184$.",
                r"$\max(45-25,0)=20$, демек $\eta_{eff}=0.20\times0.92=0.184$.",
            ),
        ),
        _task(
            "p_dc_kw",
            prompt=_L(
                r"Same params, $A_{total}=160\,\mathrm{m}^2$, $G=900\,\mathrm{W/m}^2$: $P_{DC}$ in kW?",
                r"Сол параметрлер, $A_{total}=160\,\mathrm{m}^2$, $G=900$: $P_{DC}$ (кВт)?",
            ),
            kind="number",
            # 0.184 * 160 * 900 / 1000 = 26.496 kW
            answer=26.5,
            tolerance=0.15,
            unit="kW",
            formula=r"P_{DC}=\eta_{eff} A_{total} G",
            hint=_L(
                r"$P_{DC}=\eta_{eff}\,A\,G$ (W), then /1000 for kW.",
                r"$P_{DC}=\eta_{eff}\,A\,G$ (Вт), сосын /1000 → кВт.",
            ),
            explain=_L(
                r"$P=0.184\times160\times900=26496\,\mathrm{W}\approx26.5\,\mathrm{kW}$.",
                r"$P=0.184\times160\times900=26496\,\mathrm{W}\approx26.5\,\mathrm{kW}$.",
            ),
        ),
        _task(
            "double_g",
            prompt=_L(
                r"If $G$ doubles at fixed $T$ and $\eta_{eff}$, $P_{DC}$ becomes…",
                r"$T$ және $\eta_{eff}$ тұрақты, $G$ екі еселенсе, $P_{DC}$…",
            ),
            kind="choice",
            choices=[
                _L("Unchanged", "Өзгермейді"),
                _L("Doubled (×2)", "Екі еселенеді (×2)"),
                _L("Halved", "Екі есе азаяды"),
                _L("Squared (×4)", "Төрт еселенеді (×4)"),
            ],
            correct_index=1,
            explain=_L(
                r"In this model $P_{DC}\propto G$, so doubling $G$ doubles power.",
                r"Модельде $P_{DC}\propto G$, сондықтан $G$ екі еселенсе қуат та екі еселенеді.",
            ),
        ),
    ],
    "lab_mppt_po": [
        _task(
            "po_direction",
            prompt=_L(
                r"If $P_k>P_{k-1}$ and the last step was $+\Delta V$, the next step is…",
                r"$P_k>P_{k-1}$ және соңғы қадам $+\Delta V$ болса, келесі қадам…",
            ),
            kind="choice",
            choices=[
                _L("$-\\Delta V$ (reverse)", "$-\\Delta V$ (кері)"),
                _L("$+\\Delta V$ (same direction)", "$+\\Delta V$ (сол бағыт)"),
                _L("Jump to 0 V", "0 V-қа секіру"),
                _L("Disable MPPT", "MPPT өшіру"),
            ],
            correct_index=1,
            formula=r"V_{k+1}=V_k+\Delta V\cdot\mathrm{sign}(P_k-P_{k-1})",
            explain=_L(
                "P&O keeps the direction that increased power.",
                "P&O қуатты өсірген бағытты сақтайды.",
            ),
        ),
        _task(
            "step_size",
            prompt=_L(
                r"Which $\Delta V$ usually tracks the MPP more smoothly (less oscillation)?",
                r"Қай $\Delta V$ MPP-ны тегісірек іздейді (аз тербеліс)?",
            ),
            kind="choice",
            choices=[
                _L("$\\Delta V = 1.5\\,\\mathrm{V}$ (large)", "$\\Delta V = 1.5\\,\\mathrm{V}$ (үлкен)"),
                _L("$\\Delta V = 0.2\\,\\mathrm{V}$ (small)", "$\\Delta V = 0.2\\,\\mathrm{V}$ (кіші)"),
                _L("Any random step", "Кездейсоқ қадам"),
                _L("Only zero step", "Тек нөл қадам"),
            ],
            correct_index=1,
            explain=_L(
                "Smaller steps reduce oscillation around the peak (slower but smoother).",
                "Кіші қадам шың маңындағы тербелісті азайтады (баяу, бірақ тегіс).",
            ),
        ),
    ],
    "lab_bess_soc": [
        _task(
            "soc_after_charge",
            prompt=_L(
                r"$E_{cap}=40\,\mathrm{kWh}$, $SOC_0=0.5$, charge $P_{ch}=10\,\mathrm{kW}$ for $1\,\mathrm{h}$, $\eta=0.95$. Find $SOC_1$ (fraction 0–1).",
                r"$E_{cap}=40\,\mathrm{kWh}$, $SOC_0=0.5$, $P_{ch}=10\,\mathrm{kW}$, $1\,\mathrm{h}$, $\eta=0.95$. $SOC_1$ (0–1).",
            ),
            kind="number",
            # 0.5 + 0.95*10/40 = 0.5 + 0.2375 = 0.7375
            answer=0.7375,
            tolerance=0.015,
            formula=r"SOC_{t+1}=SOC_t+\eta P_{ch}\Delta t/E_{cap}",
            hint=_L(
                r"Stored energy $=\eta P_{ch}\Delta t$; divide by $E_{cap}$.",
                r"Жинақталған $=\eta P_{ch}\Delta t$; $E_{cap}$-қа бөліңіз.",
            ),
            explain=_L(
                r"$\Delta E=0.95\times10=9.5\,\mathrm{kWh}$, $SOC_1=0.5+9.5/40=0.7375$.",
                r"$\Delta E=9.5\,\mathrm{kWh}$, $SOC_1=0.5+9.5/40=0.7375$.",
            ),
        ),
        _task(
            "soc_min_dod",
            prompt=_L(
                r"With $\mathrm{DoD}=0.8$, minimum allowed $SOC$ is…",
                r"$\mathrm{DoD}=0.8$ болса, минималды $SOC$…",
            ),
            kind="number",
            answer=0.2,
            tolerance=0.01,
            formula=r"SOC_{\min}=1-\mathrm{DoD}",
            explain=_L(
                r"$SOC_{\min}=1-0.8=0.2$ (20%).",
                r"$SOC_{\min}=1-0.8=0.2$ (20%).",
            ),
        ),
    ],
    "lab_microgrid_dispatch": [
        _task(
            "self_cons_pct",
            prompt=_L(
                r"If $E_{pv}=120\,\mathrm{kWh}$ and on-site PV use $=90\,\mathrm{kWh}$, self-consumption $SC\%$ is…",
                r"$E_{pv}=120\,\mathrm{kWh}$, жергілікті қолдану $=90\,\mathrm{kWh}$: $SC\%$…",
            ),
            kind="number",
            answer=75.0,
            tolerance=0.5,
            unit="%",
            formula=r"SC\%=100\cdot E_{used}/E_{pv}",
            explain=_L(
                r"$SC\%=100\times90/120=75\%$.",
                r"$SC\%=100\times90/120=75\%$.",
            ),
        ),
        _task(
            "balance_concept",
            prompt=_L(
                "On a deficit hour after battery is empty, residual demand is covered by…",
                "Батарея бос және жетіспеу сағатында қалдық жүктемені жабады…",
            ),
            kind="choice",
            choices=[
                _L("Only PV export", "Тек PV экспорт"),
                _L("Grid import", "Grid импорт"),
                _L("Negative CAPEX", "Теріс CAPEX"),
                _L("Turning off physics", "Физиканы өшіру"),
            ],
            correct_index=1,
            explain=_L(
                "Heuristic: load ← PV ← battery ← grid import.",
                "Эвристика: жүктеме ← PV ← батарея ← grid импорт.",
            ),
        ),
    ],
    "lab_heuristic_vs_pulp": [
        _task(
            "delta_def",
            prompt=_L(
                r"Lab KPI $\Delta E_{imp}$ is defined as…",
                r"Зертхана KPI $\Delta E_{imp}$ анықтамасы…",
            ),
            kind="choice",
            choices=[
                _L(
                    r"$E_{imp}^{heur}-E_{imp}^{PuLP}$",
                    r"$E_{imp}^{heur}-E_{imp}^{PuLP}$",
                ),
                _L(
                    r"$E_{imp}^{PuLP}-E_{imp}^{heur}$ only if negative",
                    r"Тек теріс болса $E_{imp}^{PuLP}-E_{imp}^{heur}$",
                ),
                _L("Always zero", "Әрқашан нөл"),
                _L("CAPEX only", "Тек CAPEX"),
            ],
            correct_index=0,
            formula=r"\Delta E_{imp}=E_{imp}^{heur}-E_{imp}^{PuLP}",
            explain=_L(
                "Positive $\\Delta$ means heuristic imported more than PuLP.",
                "Оң $\\Delta$ — эвристика PuLP-тан көбірек импорттаған.",
            ),
        ),
        _task(
            "cost_proxy",
            prompt=_L(
                r"$c_{imp}=0.12$, $c_{exp}=0.06$, $E_{imp}=20\,\mathrm{kWh}$, $E_{exp}=5\,\mathrm{kWh}$. Cost proxy $C=c_{imp}E_{imp}-c_{exp}E_{exp}$?",
                r"$c_{imp}=0.12$, $c_{exp}=0.06$, $E_{imp}=20$, $E_{exp}=5$. $C=c_{imp}E_{imp}-c_{exp}E_{exp}$?",
            ),
            kind="number",
            # 0.12*20 - 0.06*5 = 2.4 - 0.3 = 2.1
            answer=2.1,
            tolerance=0.05,
            unit="$",
            formula=r"C=c_{imp}E_{imp}-c_{exp}E_{exp}",
            explain=_L(
                r"$C=0.12\times20-0.06\times5=2.4-0.3=2.1$.",
                r"$C=2.4-0.3=2.1$.",
            ),
        ),
    ],
    "lab_pv_yield": [
        _task(
            "daily_yield",
            prompt=_L(
                r"Hourly powers (kW): $[0,0,2,4,6,4,2,0]$. $\Delta t=1\,\mathrm{h}$. $E_{day}=\sum P_t\Delta t$ (kWh)?",
                r"Сағаттық қуат (кВт): $[0,0,2,4,6,4,2,0]$. $\Delta t=1\,\mathrm{h}$. $E_{day}$ (кВт·сағ)?",
            ),
            kind="number",
            # 0+0+2+4+6+4+2+0 = 18
            answer=18.0,
            tolerance=0.1,
            unit="kWh",
            formula=r"E_{day}=\sum_t P_t\Delta t",
            explain=_L(
                r"$E_{day}=2+4+6+4+2=18\,\mathrm{kWh}$.",
                r"$E_{day}=18\,\mathrm{kWh}$.",
            ),
        ),
        _task(
            "scale_panels",
            prompt=_L(
                "In the simple linear panel model, doubling panel count at fixed weather roughly…",
                "Қарапайым сызықты модельде панель санын екі еселеу (ауа райы тұрақты) шамамен…",
            ),
            kind="choice",
            choices=[
                _L("Halves daily yield", "Тәуліктік yield-ті екі есе азайтады"),
                _L("Doubles daily yield", "Тәуліктік yield-ті екі еселейді"),
                _L("Does not change yield", "Yield өзгермейді"),
                _L("Sets yield to zero", "Yield-ті нөл етеді"),
            ],
            correct_index=1,
            explain=_L(
                r"$P\propto N_{panels}$, so $E_{day}\propto N$ at fixed weather.",
                r"$P\propto N_{panels}$, сондықтан $E_{day}\propto N$.",
            ),
        ),
    ],
    "lab_load_shape": [
        _task(
            "scale_factor",
            prompt=_L(
                r"Raw peak $=3.5\,\mathrm{kW}$, target peak $=5.0\,\mathrm{kW}$. Scale factor $k=P_{target}/\max P$?",
                r"Шикі шың $=3.5\,\mathrm{kW}$, мақсат $=5.0\,\mathrm{kW}$. $k=P_{target}/\max P$?",
            ),
            kind="number",
            # 5/3.5 ≈ 1.42857
            answer=1.429,
            tolerance=0.02,
            formula=r"k=P_{peak}^{target}/\max_t P_t",
            explain=_L(
                r"$k=5/3.5\approx1.429$.",
                r"$k=5/3.5\approx1.429$.",
            ),
        ),
        _task(
            "energy_sum",
            prompt=_L(
                r"Scaled hourly loads $[1,2,3,2,1]$ kW, $\Delta t=1\,\mathrm{h}$. Energy $E=\sum P_t$ (kWh)?",
                r"Масштабталған $[1,2,3,2,1]$ кВт, $\Delta t=1\,\mathrm{h}$. $E=\sum P_t$ (кВт·сағ)?",
            ),
            kind="number",
            answer=9.0,
            tolerance=0.1,
            unit="kWh",
            explain=_L(r"$1+2+3+2+1=9\,\mathrm{kWh}$.", r"$1+2+3+2+1=9\,\mathrm{kWh}$."),
        ),
    ],
    "lab_bess_community": [
        _task(
            "e_min",
            prompt=_L(
                r"$E_{cap}=50\,\mathrm{kWh}$, $\mathrm{DoD}=0.8$. Floor $E_{\min}=E_{cap}(1-\mathrm{DoD})$ (kWh)?",
                r"$E_{cap}=50\,\mathrm{kWh}$, $\mathrm{DoD}=0.8$. $E_{\min}$ (кВт·сағ)?",
            ),
            kind="number",
            answer=10.0,
            tolerance=0.1,
            unit="kWh",
            formula=r"E_{\min}=E_{cap}(1-\mathrm{DoD})",
            explain=_L(
                r"$E_{\min}=50\times(1-0.8)=10\,\mathrm{kWh}$.",
                r"$E_{\min}=50\times0.2=10\,\mathrm{kWh}$.",
            ),
        ),
        _task(
            "higher_dod",
            prompt=_L(
                "Higher DoD means…",
                "Жоғары DoD дегеніміз…",
            ),
            kind="choice",
            choices=[
                _L("Higher $E_{\\min}$ (less usable energy)", "Жоғары $E_{\\min}$ (аз пайдалы энергия)"),
                _L("Lower $E_{\\min}$ (more usable energy)", "Төмен $E_{\\min}$ (көбірек пайдалы энергия)"),
                _L("Battery removed", "Батарея алынады"),
                _L("$\\eta=0$ always", "Әрқашан $\\eta=0$"),
            ],
            correct_index=1,
            explain=_L(
                r"$E_{\min}=E_{cap}(1-\mathrm{DoD})$ falls when DoD rises.",
                r"DoD өссе $E_{\min}$ төмендейді — пайдалы диапазон кеңейеді.",
            ),
        ),
    ],
    "lab_shared_energy": [
        _task(
            "shared_def",
            prompt=_L(
                "In this lab, shared energy is mainly…",
                "Осы зертханада бөліскен энергия негізінен…",
            ),
            kind="choice",
            choices=[
                _L(
                    "Matching residual surplus to residual deficit among users",
                    "Пайдаланушылар арасында қалдық артықты жетіспеуге сәйкестендіру",
                ),
                _L("Only grid import", "Тек grid импорт"),
                _L("CAPEX depreciation", "CAPEX амортизациясы"),
                _L("YOLO mAP", "YOLO mAP"),
            ],
            correct_index=0,
            explain=_L(
                r"$E_{shared,t}=\min(S_t,D_t)\Delta t$ after individual self-consumption.",
                r"Жеке өз тұтынудан кейін $E_{shared,t}=\min(S_t,D_t)\Delta t$.",
            ),
        ),
        _task(
            "pre_battery_shared",
            prompt=_L(
                "If battery DoD increases, pre-battery shared energy usually…",
                "Батарея DoD өссе, батареяға дейінгі бөліскен энергия әдетте…",
            ),
            kind="choice",
            choices=[
                _L("Always doubles", "Әрқашан екі еселенеді"),
                _L("Does not change (shared is before BESS)", "Өзгермейді (shared BESS-ке дейін)"),
                _L("Becomes negative forever", "Мәңгі теріс болады"),
                _L("Deletes all users", "Барлық пайдаланушыны жояды"),
            ],
            correct_index=1,
            explain=_L(
                "DoD affects residual grid/BESS after the shared match step.",
                "DoD shared қадамынан кейінгі BESS/grid-ке әсер етеді.",
            ),
        ),
        _task(
            "bill_proxy",
            prompt=_L(
                r"$c_{imp}=0.12$, $E_{import}=50\,\mathrm{kWh}$, $c_{exp}=0.06$, $E_{export}=10\,\mathrm{kWh}$. Net bill $B=c_{imp}E_{imp}-c_{exp}E_{exp}$?",
                r"$c_{imp}=0.12$, $E_{import}=50$, $c_{exp}=0.06$, $E_{export}=10$. $B$?",
            ),
            kind="number",
            # 6 - 0.6 = 5.4
            answer=5.4,
            tolerance=0.1,
            unit="$",
            formula=r"B=c_{imp}E_{import}-c_{exp}E_{export}",
            explain=_L(
                r"$B=0.12\times50-0.06\times10=6-0.6=5.4$.",
                r"$B=6-0.6=5.4$.",
            ),
        ),
    ],
    "lab_rec_finance": [
        _task(
            "payback",
            prompt=_L(
                r"$CAPEX=80000$, $E_{annual}=120000\,\mathrm{kWh}$, price $=0.10\,\mathrm{\$/kWh}$, $OPEX=0$. Simple payback years?",
                r"$CAPEX=80000$, $E_{annual}=120000$, баға $=0.10\,\mathrm{\$/kWh}$, $OPEX=0$. Payback (жыл)?",
            ),
            kind="number",
            # 80000 / 12000 = 6.666...
            answer=6.67,
            tolerance=0.1,
            unit="years",
            formula=r"T_{pb}=CAPEX/(E_{annual}\cdot price)",
            explain=_L(
                r"Annual savings $=120000\times0.10=12000$, $T_{pb}=80000/12000\approx6.67$ years.",
                r"Жылдық үнем $=12000$, $T_{pb}=80000/12000\approx6.67$ жыл.",
            ),
        ),
        _task(
            "npv_rate",
            prompt=_L(
                "Raising the discount rate $r$ typically…",
                "Дисконт $r$ өссе, әдетте…",
            ),
            kind="choice",
            choices=[
                _L("Increases NPV", "NPV-ны өсіреді"),
                _L("Decreases NPV of future savings", "Болашақ үнем NPV-сын төмендетеді"),
                _L("Sets IRR to 100% always", "IRR әрқашан 100%"),
                _L("Removes CAPEX", "CAPEX-ті жояды"),
            ],
            correct_index=1,
            formula=r"\mathrm{NPV}=\sum_t CF_t/(1+r)^t",
            explain=_L(
                "Higher $r$ discounts future cash flows more heavily.",
                "Жоғары $r$ болашақ ағындарды күштірек дисконттайды.",
            ),
        ),
    ],
    "lab_grid_impact": [
        _task(
            "voltage_rise",
            prompt=_L(
                "High PV export on a weak feeder often causes…",
                "Әлсіз фидерде жоғары PV экспорт жиі тудырады…",
            ),
            kind="choice",
            choices=[
                _L("Local voltage rise", "Жергілікті кернеу өсімі"),
                _L("Negative speed of light", "Жарық жылдамдығының теріс болуы"),
                _L("CAPEX = 0", "CAPEX = 0"),
                _L("Removal of all loads", "Барлық жүктеменің жойылуы"),
            ],
            correct_index=0,
            formula=r"\Delta V \approx (RP+XQ)/V",
            explain=_L(
                "Reverse power flow can push bus voltage above nominal.",
                "Кері қуат ағыны шина кернеуін номиналдан жоғарылатуы мүмкін.",
            ),
        ),
        _task(
            "vpu_def",
            prompt=_L(
                r"If $|V|=0.42\,\mathrm{kV}$ and $V_{nom}=0.4\,\mathrm{kV}$, $V_{pu}=|V|/V_{nom}$ is…",
                r"$|V|=0.42\,\mathrm{kV}$, $V_{nom}=0.4\,\mathrm{kV}$: $V_{pu}$…",
            ),
            kind="number",
            answer=1.05,
            tolerance=0.01,
            formula=r"V_{\mathrm{pu}}=|V|/V_{nom}",
            explain=_L(
                r"$V_{pu}=0.42/0.4=1.05$.",
                r"$V_{pu}=0.42/0.4=1.05$.",
            ),
        ),
    ],
    "lab_inverter_wiring": [
        _task(
            "dc_polarity",
            prompt=_L(
                "PV string + must connect to which inverter terminal?",
                "PV тізбек + қай инвертор терминалына қосылуы керек?",
            ),
            kind="choice",
            choices=[
                _L("DC−", "DC−"),
                _L("DC+", "DC+"),
                _L("AC N only", "Тек AC N"),
                _L("Logger COM", "Logger COM"),
            ],
            correct_index=1,
            explain=_L(
                "Positive PV conductor → DC+; reverse polarity can prevent start or damage.",
                "PV оң өткізгіш → DC+; кері полярлық іске қосуды бөгеуі / зақымдауы мүмкін.",
            ),
        ),
        _task(
            "isolator_export",
            prompt=_L(
                "AC isolator left OFF after service. Expected grid export?",
                "Қызметтен кейін AC ажыратқыш OFF. Күтілетін grid экспорт?",
            ),
            kind="choice",
            choices=[
                _L("Full rated power always", "Әрқашан толық номинал"),
                _L("Zero export until isolator ON", "Ажыратқыш ON болмайынша экспорт 0"),
                _L("Only night export", "Тек түнгі экспорт"),
                _L("Negative CAPEX", "Теріс CAPEX"),
            ],
            correct_index=1,
            explain=_L(
                "Open isolator isolates AC path — no export despite PV DC.",
                "Ашық ажыратқыш AC жолын үзеді — PV DC бар болса да экспорт жоқ.",
            ),
        ),
        _task(
            "logger_effect",
            prompt=_L(
                "Data logger stick unplugged from COM. What usually still works?",
                "Data logger COM-нан суырылған. Әдетте не жұмыс істейді?",
            ),
            kind="choice",
            choices=[
                _L("Local AC production can continue; cloud telemetry is lost", "Жергілікті AC жалғасуы мүмкін; cloud телеметрия жоғалады"),
                _L("PV modules melt immediately", "PV панельдер бірден ериді"),
                _L("Grid frequency becomes 0 Hz", "Grid жиілігі 0 Гц болады"),
                _L("Battery DoD becomes negative", "Батарея DoD теріс болады"),
            ],
            correct_index=0,
            explain=_L(
                "Logger is for monitoring/comms; power path is separate (if hardware allows).",
                "Logger — мониторинг/байланыс; қуат жолы бөлек (аппарат рұқсат етсе).",
            ),
        ),
        _task(
            "swap_ac",
            prompt=_L(
                "Installer swapped AC L and N. Correct fix is…",
                "Монтажник AC L мен N-ді ауыстырған. Дұрыс түзету…",
            ),
            kind="choice",
            choices=[
                _L("Leave as-is", "Солай қалдыру"),
                _L("Reconnect L→Grid L and N→Grid N", "L→Желі L, N→Желі N қайта қосу"),
                _L("Only reverse DC cables", "Тек DC кабельдерді кері бұру"),
                _L("Delete the 3D model", "3D модельді жою"),
            ],
            correct_index=1,
            explain=_L(
                "Restore AC polarity/phase assignment per manufacturer terminal map.",
                "Өндіруші терминал картасы бойынша AC фаза/нольді қалпына келтіріңіз.",
            ),
        ),
    ],
}


def list_lab_task_ids(lab_id: str) -> list[str]:
    return [t["id"] for t in LAB_TASKS.get(lab_id, [])]


def get_lab_tasks(lab_id: str, lang: str = "en") -> list[dict[str, Any]]:
    """Resolved task strings for UI."""
    lang = "kk" if lang == "kk" else "en"
    raw = LAB_TASKS.get(lab_id, [])
    out: list[dict[str, Any]] = []
    for t in raw:
        item = {
            "id": t["id"],
            "kind": t["kind"],
            "prompt": t["prompt"][lang],
            "unit": t.get("unit") or "",
            "tolerance": t.get("tolerance", 0.05),
            "hint": t["hint"][lang],
            "explain": t["explain"][lang],
            "formula": t.get("formula"),
            "choices": [c[lang] for c in t.get("choices") or []],
        }
        out.append(item)
    return out


def check_task_answer(
    lab_id: str,
    task_id: str,
    *,
    number: float | None = None,
    choice_index: int | None = None,
) -> dict[str, Any]:
    """
    Grade one task.

    Returns::
        {
          "ok": bool,
          "status": "correct" | "wrong" | "missing" | "unknown_task",
          "message_en": str,
          "message_kk": str,
          "explain_en": str,
          "explain_kk": str,
          "expected": optional,
        }
    """
    tasks = {t["id"]: t for t in LAB_TASKS.get(lab_id, [])}
    t = tasks.get(task_id)
    if not t:
        return {
            "ok": False,
            "status": "unknown_task",
            "message_en": "Unknown task.",
            "message_kk": "Белгісіз тапсырма.",
            "explain_en": "",
            "explain_kk": "",
        }

    if t["kind"] == "number":
        if number is None:
            return {
                "ok": False,
                "status": "missing",
                "message_en": "Enter a number.",
                "message_kk": "Сан енгізіңіз.",
                "explain_en": t["hint"]["en"],
                "explain_kk": t["hint"]["kk"],
            }
        expected = float(t["answer"])
        tol = float(t.get("tolerance") or 0.05)
        # Relative tolerance also for large values
        rel = abs(expected) * 0.02 if abs(expected) > 1 else 0.0
        limit = max(tol, rel)
        ok = abs(float(number) - expected) <= limit
        if ok:
            return {
                "ok": True,
                "status": "correct",
                "message_en": "Correct! Well done.",
                "message_kk": "Дұрыс! Жарайсың.",
                "explain_en": t["explain"]["en"],
                "explain_kk": t["explain"]["kk"],
                "expected": expected,
            }
        return {
            "ok": False,
            "status": "wrong",
            "message_en": "Incorrect. Try again.",
            "message_kk": "Қате. Қайтадан көріңіз.",
            "explain_en": t["hint"]["en"],
            "explain_kk": t["hint"]["kk"],
            "expected": None,  # don't leak until correct (or after many tries — keep hidden)
        }

    if t["kind"] == "choice":
        if choice_index is None:
            return {
                "ok": False,
                "status": "missing",
                "message_en": "Select an option.",
                "message_kk": "Нұсқаны таңдаңыз.",
                "explain_en": t["hint"]["en"],
                "explain_kk": t["hint"]["kk"],
            }
        ok = int(choice_index) == int(t["correct_index"])
        if ok:
            return {
                "ok": True,
                "status": "correct",
                "message_en": "Correct! Well done.",
                "message_kk": "Дұрыс! Жарайсың.",
                "explain_en": t["explain"]["en"],
                "explain_kk": t["explain"]["kk"],
            }
        return {
            "ok": False,
            "status": "wrong",
            "message_en": "Incorrect. Try again.",
            "message_kk": "Қате. Қайтадан көріңіз.",
            "explain_en": t["hint"]["en"],
            "explain_kk": t["hint"]["kk"],
        }

    return {
        "ok": False,
        "status": "unknown_task",
        "message_en": "Unsupported task type.",
        "message_kk": "Қолдау көрсетілмейтін тапсырма түрі.",
        "explain_en": "",
        "explain_kk": "",
    }


def lab_tasks_progress(lab_id: str, done_ids: list[str] | set[str]) -> dict[str, Any]:
    ids = list_lab_task_ids(lab_id)
    done = [i for i in ids if i in done_ids]
    total = len(ids)
    return {
        "total": total,
        "done": len(done),
        "done_ids": done,
        "complete": total > 0 and len(done) >= total,
        "percent": round(100.0 * len(done) / total, 1) if total else 0.0,
    }
