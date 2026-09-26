"""
One engine for the 12 labs, shared by the website and the mobile app.

Each lab has a parameter spec (what the student can set: sliders and choices,
with ranges and defaults, labelled in kk/en) and a run function that calls the
simulation kernels and returns plain JSON:

    {
      "lab_id": ..., "params": {validated values},
      "metrics": [{"key", "label": {en, kk}, "value", "unit", "digits"}],
      "charts": [{"id", "title": {en, kk}, "x", "x_label": {en, kk}, "y_label",
                  "series": [{"name": {en, kk}, "values": [...]}],
                  "limits": [{"value", "label": {en, kk}}]}],
      "notes": [{en, kk}],
    }

The Streamlit page renders that; the API returns it to the phone
(POST /labs/{lab_id}/run). Tests grade "run" questions by calling the same
functions, so the answer a student reads off a run is the answer the test
expects.
"""

from __future__ import annotations

import math
from typing import Any, Callable

import numpy as np

from src.education.inverter_lab import CONTROLS, CORRECT, grade_wiring
from src.simulation.adapters.weather_profile import load_weather_profile, synthetic_day_profile
from src.simulation.community.bess_step import simulate_bess_series
from src.simulation.community.financial_kpis import community_project_kpis
from src.simulation.community.load_profile import scale_profile, synthetic_load_profile
from src.simulation.community.shared_energy import run_shared_energy_day
from src.simulation.grid.lv_feeder import CABLES, V_MAX_PU, V_MIN_PU, feeder_day
from src.simulation.microgrid.compare_pulp import compare_heuristic_vs_pulp
from src.simulation.microgrid.engine import run_day_simulation, run_mppt_trace, summarize_day
from src.simulation.microgrid.solar_panel import SolarArray, SolarPanelConfig

# Turkistan, the site the weather sample and the Solarman plant are from.
DEFAULT_LAT, DEFAULT_LON = 43.2973, 68.2517


def _L(en: str, kk: str) -> dict[str, str]:
    return {"en": en, "kk": kk}


def slider(
    key: str, en: str, kk: str, lo: float, hi: float, step: float, default: float, unit: str = ""
) -> dict[str, Any]:
    return {
        "key": key,
        "kind": "slider",
        "label": _L(en, kk),
        "min": lo,
        "max": hi,
        "step": step,
        "default": default,
        "unit": unit,
    }


def select(
    key: str, en: str, kk: str, options: list[tuple[str, dict[str, str]]], default: str
) -> dict[str, Any]:
    return {
        "key": key,
        "kind": "select",
        "label": _L(en, kk),
        "options": [{"id": oid, "label": lab} for oid, lab in options],
        "default": default,
    }


WEATHER = select(
    "weather",
    "Weather day",
    "Ауа райы күні",
    [
        ("sample", _L("Measured sample day (Turkistan)", "Өлшенген үлгі күн (Түркістан)")),
        ("synthetic", _L("Clear synthetic day", "Ашық синтетикалық күн")),
        ("open-meteo", _L("Today's forecast (Open-Meteo)", "Бүгінгі болжам (Open-Meteo)")),
    ],
    "sample",
)


def metric(
    key: str, en: str, kk: str, value: float | None, unit: str = "", digits: int = 1
) -> dict[str, Any]:
    v = (
        None
        if value is None or (isinstance(value, float) and not math.isfinite(value))
        else float(value)
    )
    return {"key": key, "label": _L(en, kk), "value": v, "unit": unit, "digits": digits}


def chart(
    cid: str,
    title: dict[str, str],
    x: list[Any],
    x_label: dict[str, str],
    y_label: str,
    series: list[tuple[dict[str, str], list[float]]],
    limits: list[tuple[float, dict[str, str]]] | None = None,
) -> dict[str, Any]:
    return {
        "id": cid,
        "title": title,
        "x": [float(v) if isinstance(v, (int, float, np.floating, np.integer)) else v for v in x],
        "x_label": x_label,
        "y_label": y_label,
        "series": [{"name": name, "values": [_num(v) for v in values]} for name, values in series],
        "limits": [{"value": float(v), "label": lab} for v, lab in (limits or [])],
    }


def _num(v: Any) -> float | None:
    f = float(v)
    return round(f, 6) if math.isfinite(f) else None


HOUR = _L("Hour of day", "Тәулік сағаты")


def _weather(source: str):
    if source == "synthetic":
        df = synthetic_day_profile()
        df.attrs.setdefault("source", "synthetic")
        return df
    if source == "open-meteo":
        return load_weather_profile(lat=DEFAULT_LAT, lon=DEFAULT_LON, prefer="open-meteo")
    return load_weather_profile(prefer="sample")


def _weather_note(df, requested: str) -> list[dict[str, str]]:
    used = str(df.attrs.get("source") or requested)
    if used == requested:
        return []
    return [
        _L(
            f"Weather: '{requested}' was unavailable, the '{used}' day was used.",
            f"Ауа райы: '{requested}' қолжетімсіз, орнына '{used}' күні алынды.",
        )
    ]


# ------------------------------------------------------------------ labs


def _pv_physics(p: dict[str, Any]) -> dict[str, Any]:
    cfg = SolarPanelConfig(area=p["area"], efficiency=p["eta"], temp_coefficient=p["gamma"])
    arr = SolarArray(cfg, num_panels=int(p["n"]))
    p_kw = arr.calculate_power(p["irr"], p["temp"]) / 1000.0
    eta_eff = cfg.efficiency * (1.0 - max(0.0, (p["temp"] - 25.0) * cfg.temp_coefficient))
    gs = [float(g) for g in range(0, 1201, 50)]
    return {
        "metrics": [
            metric("p_dc_kw", "DC power P_DC", "DC қуаты P_DC", p_kw, "kW", 2),
            metric("area_m2", "Array area", "Массив ауданы", arr.total_area, "m²", 1),
            metric("eta_eff", "Effective efficiency η_eff", "Тиімді ПӘК η_eff", eta_eff, "", 3),
        ],
        "charts": [
            chart(
                "p_vs_g",
                _L("DC power vs irradiance", "DC қуаты мен сәулелену"),
                gs,
                _L("Irradiance G, W/m²", "Сәулелену G, Вт/м²"),
                "kW",
                [
                    (
                        _L(f"T = {p['temp']:.0f} °C", f"T = {p['temp']:.0f} °C"),
                        [arr.calculate_power(g, p["temp"]) / 1000 for g in gs],
                    ),
                    (
                        _L("T = 25 °C (reference)", "T = 25 °C (эталон)"),
                        [arr.calculate_power(g, 25.0) / 1000 for g in gs],
                    ),
                ],
            )
        ],
    }


def _mppt(p: dict[str, Any]) -> dict[str, Any]:
    df = run_mppt_trace(p["irr"], step_size=p["step"], steps=int(p["steps"]))
    v, i = SolarArray(SolarPanelConfig(), 1).get_iv_curve(p["irr"])
    p_mpp = float((v * i).max())
    tail = df["p"].tail(min(20, len(df)))
    eff = 100.0 * float(tail.mean()) / p_mpp if p_mpp > 0 else 0.0
    ripple = float(tail.max() - tail.min())
    return {
        "metrics": [
            metric(
                "p_mpp_w", "True maximum power P_MPP", "Нақты максимал қуат P_MPP", p_mpp, "W", 1
            ),
            metric(
                "tracking_pct",
                "Tracking efficiency (last 20 steps)",
                "Іздеу тиімділігі (соңғы 20 қадам)",
                eff,
                "%",
                1,
            ),
            metric(
                "ripple_w", "Power ripple at the peak", "Шыңдағы қуат тербелісі", ripple, "W", 1
            ),
            metric(
                "v_ref_final", "Final V_ref", "Соңғы V_ref", float(df["v_ref"].iloc[-1]), "V", 2
            ),
        ],
        "charts": [
            chart(
                "trace_p",
                _L("P&O trace: power", "P&O ізі: қуат"),
                df["step"].tolist(),
                _L("Step", "Қадам"),
                "W",
                [
                    (_L("P measured", "Өлшенген P"), df["p"].tolist()),
                    (_L("P_MPP", "P_MPP"), [p_mpp] * len(df)),
                ],
            ),
            chart(
                "trace_v",
                _L("P&O trace: voltage reference", "P&O ізі: кернеу эталоны"),
                df["step"].tolist(),
                _L("Step", "Қадам"),
                "V",
                [(_L("V_ref", "V_ref"), df["v_ref"].tolist())],
            ),
        ],
    }


def _bess_soc(p: dict[str, Any]) -> dict[str, Any]:
    w = _weather(p["weather"])
    df = run_day_simulation(
        w,
        num_panels=int(p["n"]),
        battery_kwh=p["bat"],
        load_kw=p["load"],
        min_soc_frac=1 - p["dod"],
    )
    s = summarize_day(df)
    x = list(range(len(df)))
    return {
        "metrics": [
            metric("soc_min_pct", "SOC minimum", "SOC минимумы", df["soc"].min() * 100, "%", 1),
            metric("soc_max_pct", "SOC maximum", "SOC максимумы", df["soc"].max() * 100, "%", 1),
            metric(
                "soc_end_pct",
                "SOC at the end of the day",
                "Тәулік соңындағы SOC",
                df["soc"].iloc[-1] * 100,
                "%",
                1,
            ),
            metric("pv_kwh", "PV energy", "PV энергиясы", s["pv_kwh"], "kWh", 1),
        ],
        "charts": [
            chart(
                "power",
                _L("PV and load", "PV және жүктеме"),
                x,
                HOUR,
                "kW",
                [
                    (_L("PV", "PV"), df["pv_kw"].tolist()),
                    (_L("Load", "Жүктеме"), df["load_kw"].tolist()),
                ],
            ),
            chart(
                "soc",
                _L("Battery state of charge", "Батарея заряд деңгейі"),
                x,
                HOUR,
                "%",
                [(_L("SOC", "SOC"), (df["soc"] * 100).tolist())],
                limits=[(100 * (1 - p["dod"]), _L("SOC floor = 1 − DoD", "SOC шегі = 1 − DoD"))],
            ),
        ],
        "notes": _weather_note(w, p["weather"]),
    }


def _microgrid(p: dict[str, Any]) -> dict[str, Any]:
    w = _weather(p["weather"])
    df = run_day_simulation(
        w,
        num_panels=int(p["n"]),
        battery_kwh=p["bat"],
        load_kw=p["load"],
        inverter_kw=p["inv"],
        min_soc_frac=1 - p["dod"],
    )
    s = summarize_day(df)
    x = list(range(len(df)))
    return {
        "metrics": [
            metric("pv_kwh", "PV energy", "PV энергиясы", s["pv_kwh"], "kWh", 1),
            metric("load_kwh", "Load energy", "Жүктеме энергиясы", s["load_kwh"], "kWh", 1),
            metric("import_kwh", "Grid import", "Желіден импорт", s["import_kwh"], "kWh", 1),
            metric("export_kwh", "Grid export", "Желіге экспорт", s["export_kwh"], "kWh", 1),
            metric(
                "self_consumption_pct",
                "Self-consumption",
                "Өзіндік тұтыну",
                s["self_consumption_pct"],
                "%",
                1,
            ),
            metric(
                "final_soc_pct",
                "SOC at the end of the day",
                "Тәулік соңындағы SOC",
                s["final_soc"] * 100,
                "%",
                0,
            ),
        ],
        "charts": [
            chart(
                "balance",
                _L("Power balance", "Қуат балансы"),
                x,
                HOUR,
                "kW",
                [
                    (_L("PV", "PV"), df["pv_kw"].tolist()),
                    (_L("Load", "Жүктеме"), df["load_kw"].tolist()),
                    (_L("Import", "Импорт"), df["grid_import_kw"].tolist()),
                    (_L("Export", "Экспорт"), df["grid_export_kw"].tolist()),
                ],
            ),
            chart(
                "soc",
                _L("Battery state of charge", "Батарея заряд деңгейі"),
                x,
                HOUR,
                "%",
                [(_L("SOC", "SOC"), (df["soc"] * 100).tolist())],
            ),
        ],
        "notes": _weather_note(w, p["weather"]),
    }


def _heuristic_vs_pulp(p: dict[str, Any]) -> dict[str, Any]:
    w = _weather(p["weather"])
    res = compare_heuristic_vs_pulp(
        w,
        num_panels=int(p["n"]),
        battery_kwh=p["bat"],
        load_kw=p["load"],
        price_import=p["price_import"],
        price_export=p["price_export"],
        mode=p["mode"],
    )
    h = res["heuristic_summary"]
    hdf, pdf = res["heuristic_df"], res["pulp_schedule"]
    x = list(range(len(hdf)))
    heur_cost = p["price_import"] * h["import_kwh"] - p["price_export"] * h["export_kwh"]
    series = [(_L("Import — rules", "Импорт — ереже"), hdf["grid_import_kw"].tolist())]
    for col in ("grid_import", "grid_import_kw"):
        if col in pdf.columns:
            series.append((_L("Import — PuLP", "Импорт — PuLP"), pdf[col].tolist()[: len(x)]))
            break
    return {
        "metrics": [
            metric(
                "heur_import_kwh",
                "Import, rule-based",
                "Импорт, ережелік",
                h["import_kwh"],
                "kWh",
                1,
            ),
            metric(
                "pulp_import_kwh", "Import, PuLP", "Импорт, PuLP", res["pulp_import_kwh"], "kWh", 1
            ),
            metric(
                "delta_import_kwh",
                "ΔE_imp = rules − PuLP",
                "ΔE_imp = ереже − PuLP",
                res["delta_import_kwh"],
                "kWh",
                1,
            ),
            metric("heur_cost", "Net cost, rule-based", "Таза шығын, ережелік", heur_cost, "$", 2),
            metric(
                "pulp_profit",
                "PuLP objective (profit)",
                "PuLP мақсаты (пайда)",
                res["pulp_profit"],
                "$",
                2,
            ),
        ],
        "charts": [
            chart(
                "import",
                _L("Grid import: rules vs PuLP", "Желіден импорт: ереже мен PuLP"),
                x,
                HOUR,
                "kW",
                series,
            )
        ],
        "notes": _weather_note(w, p["weather"]),
    }


def _pv_yield(p: dict[str, Any]) -> dict[str, Any]:
    w = _weather(p["weather"])
    cfg = SolarPanelConfig(efficiency=p["eta"])
    arr = SolarArray(cfg, num_panels=int(p["n"]))
    kw = [
        arr.calculate_power(float(r["irradiance_w_m2"]), float(r["temperature_c"])) / 1000
        for _, r in w.iterrows()
    ]
    kwp = arr.total_area * cfg.efficiency  # kW at 1000 W/m², 25 °C
    total = float(sum(kw))
    return {
        "metrics": [
            metric("yield_kwh", "Daily yield", "Тәуліктік өндіріс", total, "kWh", 1),
            metric("peak_kw", "Peak power", "Шың қуаты", max(kw) if kw else 0.0, "kW", 2),
            metric("kwp", "Installed power (STC)", "Орнатылған қуат (STC)", kwp, "kWp", 1),
            metric(
                "specific_yield",
                "Specific yield",
                "Меншікті өндіріс",
                total / kwp if kwp else 0.0,
                "kWh/kWp",
                2,
            ),
        ],
        "charts": [
            chart(
                "yield",
                _L("PV production profile", "PV өндіріс профилі"),
                list(range(len(kw))),
                HOUR,
                "kW",
                [(_L("PV", "PV"), kw)],
            )
        ],
        "notes": _weather_note(w, p["weather"]),
    }


def _load_shape(p: dict[str, Any]) -> dict[str, Any]:
    df = synthetic_load_profile(
        int(p["hours"]),
        base_kw=p["base"],
        morning_peak_kw=p["morning"],
        evening_peak_kw=p["evening"],
        noise_pct=p["noise"],
        seed=int(p["seed"]),
    )
    df = scale_profile(df, p["peak"])
    load = df["load_kw"]
    return {
        "metrics": [
            metric("energy_kwh", "Energy", "Энергия", float(load.sum()), "kWh", 1),
            metric("peak_kw", "Peak", "Шың", float(load.max()), "kW", 2),
            metric("mean_kw", "Mean", "Орташа", float(load.mean()), "kW", 2),
            metric(
                "load_factor",
                "Load factor (mean / peak)",
                "Жүктеме коэффициенті (орташа / шың)",
                float(load.mean() / load.max()),
                "",
                2,
            ),
        ],
        "charts": [
            chart(
                "load",
                _L("Household load", "Тұрмыстық жүктеме"),
                df["hour"].tolist(),
                _L("Hour", "Сағат"),
                "kW",
                [(_L("Load", "Жүктеме"), load.tolist())],
            )
        ],
    }


def _bess_community(p: dict[str, Any]) -> dict[str, Any]:
    # Intent series: midday surplus to store, evening deficit to cover (kWh per hour).
    amp = p["amp"]
    net = [
        amp * (1.0 - abs(h - 12) / 6.0) if 9 <= h <= 15 else (-amp * 0.7 if 17 <= h <= 22 else 0.0)
        for h in range(24)
    ]
    steps = simulate_bess_series(
        net, capacity_kwh=p["cap"], dod=p["dod"], eta_halfcycle=p["eta"], initial_soc_frac=0.5
    )
    soc = [s.soc_frac * 100 for s in steps]
    loss = float(sum(s.e_loss_kwh for s in steps))
    return {
        "metrics": [
            metric("final_soc_pct", "Final SOC", "Соңғы SOC", soc[-1], "%", 1),
            metric("min_soc_pct", "Minimum SOC", "Минимал SOC", min(soc), "%", 1),
            metric("loss_kwh", "Conversion losses", "Түрлендіру шығындары", loss, "kWh", 2),
            metric(
                "e_min_kwh",
                "Energy floor E_min",
                "Энергия шегі E_min",
                p["cap"] * (1 - p["dod"]),
                "kWh",
                1,
            ),
        ],
        "charts": [
            chart(
                "intent",
                _L("Charge (+) / discharge (−) request", "Заряд (+) / разряд (−) сұранысы"),
                list(range(24)),
                HOUR,
                "kWh",
                [(_L("Request", "Сұраныс"), net)],
            ),
            chart(
                "soc",
                _L("State of charge", "Заряд деңгейі"),
                list(range(24)),
                HOUR,
                "%",
                [(_L("SOC", "SOC"), soc)],
                limits=[(100 * (1 - p["dod"]), _L("SOC floor = 1 − DoD", "SOC шегі = 1 − DoD"))],
            ),
        ],
    }


def _shared_energy(p: dict[str, Any]) -> dict[str, Any]:
    w = _weather(p["weather"])
    out = run_shared_energy_day(
        w,
        n_users=int(p["n_users"]),
        pv_users=int(p["pv_users"]),
        panels_per_user=int(p["panels"]),
        peak_load_kw=p["peak"],
        community_battery_kwh=p["bat"],
        dod=p["dod"],
        price_import=p["price_import"],
        price_export=p["price_export"],
        seed=42,
    )
    ts = out["timeseries"]
    return {
        "metrics": [
            metric(
                "shared_kwh", "Shared energy", "Бөлісілген энергия", out["shared_kwh"], "kWh", 1
            ),
            metric(
                "self_consumption_pct",
                "Self-consumption in each home",
                "Әр үйдегі өзіндік тұтыну",
                out["self_consumption_pct"],
                "%",
                1,
            ),
            metric(
                "shared_pct_of_pv",
                "Shared, share of PV",
                "Бөлісілгені, PV үлесі",
                out["shared_pct_of_pv"],
                "%",
                1,
            ),
            metric("import_kwh", "Grid import", "Желіден импорт", out["import_kwh"], "kWh", 1),
            metric("net_bill", "Net bill", "Таза төлем", out["net_bill_proxy"], "$", 2),
        ],
        "charts": [
            chart(
                "flows",
                _L("Community energy flows", "Қауымдастық энергия ағындары"),
                ts["hour"].tolist(),
                HOUR,
                "kW",
                [
                    (_L("PV", "PV"), ts["pv_kw"].tolist()),
                    (_L("Load", "Жүктеме"), ts["load_kw"].tolist()),
                    (_L("Shared", "Бөлісілген"), ts["shared_kw"].tolist()),
                    (_L("Import", "Импорт"), ts["import_kw"].tolist()),
                ],
            ),
            chart(
                "soc",
                _L("Community battery SOC", "Қауымдастық батареясының SOC"),
                ts["hour"].tolist(),
                HOUR,
                "%",
                [(_L("SOC", "SOC"), (ts["soc"] * 100).tolist())],
            ),
        ],
        "notes": _weather_note(w, p["weather"]),
    }


def _rec_finance(p: dict[str, Any]) -> dict[str, Any]:
    args = dict(
        capex=p["capex"],
        annual_generation_kwh=p["gen"],
        price_per_kwh=p["price"],
        opex_annual=p["opex"],
        lifetime_years=int(p["life"]),
    )
    k = community_project_kpis(discount_rate=p["rate"], **args)
    rates = [r / 100 for r in range(0, 16)]
    npvs = [community_project_kpis(discount_rate=r, **args)["npv"] for r in rates]
    irr = k.get("irr")
    return {
        "metrics": [
            metric("lcoe", "LCOE", "LCOE", k.get("lcoe", k.get("lcoe_check")), "$/kWh", 4),
            metric(
                "payback_years",
                "Simple payback",
                "Қарапайым өтелу",
                k.get("payback_years"),
                "yr",
                1,
            ),
            metric("npv", "NPV", "NPV", k.get("npv"), "$", 0),
            metric(
                "irr_pct",
                "IRR",
                "IRR",
                irr * 100 if irr is not None and irr == irr else None,
                "%",
                1,
            ),
        ],
        "charts": [
            chart(
                "npv",
                _L("NPV vs discount rate", "NPV мен дисконт мөлшерлемесі"),
                [r * 100 for r in rates],
                _L("Discount rate, %", "Дисконт, %"),
                "$",
                [(_L("NPV", "NPV"), npvs)],
                limits=[(0.0, _L("NPV = 0", "NPV = 0"))],
            )
        ],
    }


def _grid_impact(p: dict[str, Any]) -> dict[str, Any]:
    d = feeder_day(
        n_houses=int(p["houses"]),
        length_m=p["length"],
        cable=p["cable"],
        pv_kw_peak=p["pv_kw"],
        load_kw_peak=p["load_kw"],
        pv_power_factor=p["pf"],
        v_source_pu=p["v_source"],
    )
    notes = []
    if d["worst_max_current_a"] > d["cable_i_max_a"]:
        notes.append(
            _L(
                f"Cable overloaded: {d['worst_max_current_a']:.0f} A > {d['cable_i_max_a']:.0f} A rating.",
                f"Кабель асқын жүктелген: {d['worst_max_current_a']:.0f} А > {d['cable_i_max_a']:.0f} А.",
            )
        )
    limits = [
        (V_MAX_PU, _L("1.10 pu upper limit (EN 50160)", "1.10 pu жоғарғы шек (EN 50160)")),
        (V_MIN_PU, _L("0.90 pu lower limit", "0.90 pu төменгі шек")),
    ]
    return {
        "metrics": [
            metric(
                "v_max_pu",
                "Highest voltage in the day",
                "Тәуліктегі ең жоғары кернеу",
                d["day_max_pu"],
                "pu",
                3,
            ),
            metric(
                "v_min_pu",
                "Lowest voltage in the day",
                "Тәуліктегі ең төмен кернеу",
                d["day_min_pu"],
                "pu",
                3,
            ),
            metric(
                "hours_over",
                "Hours above 1.10 pu",
                "1.10 pu-дан жоғары сағаттар",
                d["hours_over_limit"],
                "h",
                0,
            ),
            metric(
                "worst_hour",
                "Hour of the highest voltage",
                "Ең жоғары кернеу сағаты",
                d["worst_hour"],
                "h",
                0,
            ),
            metric(
                "i_max_a",
                "Highest cable current",
                "Кабельдегі ең үлкен ток",
                d["worst_max_current_a"],
                "A",
                0,
            ),
            metric(
                "losses_kwh",
                "Line losses in the day",
                "Тәуліктік желі шығыны",
                d["energy_losses_kwh"],
                "kWh",
                1,
            ),
        ],
        "charts": [
            chart(
                "v_day",
                _L("Voltage extremes over the day", "Тәулік бойы кернеу шектері"),
                d["hours"],
                HOUR,
                "pu",
                [
                    (_L("Highest bus voltage", "Ең жоғары кернеу"), d["v_max_pu"]),
                    (_L("Lowest bus voltage", "Ең төмен кернеу"), d["v_min_pu"]),
                ],
                limits,
            ),
            chart(
                "v_profile",
                _L(
                    f"Voltage along the feeder at {d['worst_hour']}:00",
                    f"{d['worst_hour']}:00 кезінде желі бойы кернеу",
                ),
                d["distance_m"],
                _L("Distance from the transformer, m", "Трансформатордан қашықтық, м"),
                "pu",
                [(_L("Voltage", "Кернеу"), d["worst_profile_pu"])],
                limits,
            ),
        ],
        "notes": notes,
    }


def _inverter(p: dict[str, Any]) -> dict[str, Any]:
    g = grade_wiring({k: p[k] for k in CONTROLS})
    st = g["status"]
    return {
        "metrics": [
            metric("score", "Correct items", "Дұрыс тармақтар", g["score"], f"/ {g['total']}", 0),
            metric("pac_kw", "Output Pac", "Шығыс Pac", st["pac_kw"], "kW", 1),
        ],
        "charts": [],
        "notes": [st["display"]],
        "grade": g,
    }


def _inverter_params() -> list[dict[str, Any]]:
    return [
        select(
            k,
            c["label"]["en"],
            c["label"]["kk"],
            [(s["id"], {"en": s["en"], "kk": s["kk"]}) for s in c["states"]],
            CORRECT[k],
        )
        for k, c in CONTROLS.items()
    ]


CABLE_OPTIONS = [(cid, _L(spec["label"], spec["label"])) for cid, spec in CABLES.items()]
PRICE_I = slider("price_import", "Import price", "Импорт бағасы", 0.01, 1.0, 0.01, 0.12, "$/kWh")
PRICE_E = slider("price_export", "Export price", "Экспорт бағасы", 0.0, 1.0, 0.01, 0.06, "$/kWh")

LABS: dict[str, dict[str, Any]] = {
    "lab_pv_physics": {
        "run": _pv_physics,
        "params": [
            slider("n", "Number of panels", "Панель саны", 10, 400, 10, 100),
            slider("area", "Panel area", "Панель ауданы", 1.0, 3.0, 0.1, 1.6, "m²"),
            slider("eta", "Efficiency η₀", "ПӘК η₀", 0.10, 0.25, 0.01, 0.20),
            slider(
                "gamma",
                "Temperature coefficient γ",
                "Температура коэффициенті γ",
                0.001,
                0.008,
                0.001,
                0.004,
                "1/°C",
            ),
            slider("irr", "Irradiance G", "Сәулелену G", 0, 1200, 50, 900, "W/m²"),
            slider("temp", "Cell temperature T", "Ұяшық температурасы T", -10, 70, 1, 35, "°C"),
        ],
    },
    "lab_mppt_po": {
        "run": _mppt,
        "params": [
            slider("irr", "Irradiance G", "Сәулелену G", 200, 1000, 50, 800, "W/m²"),
            slider("step", "Step ΔV", "Қадам ΔV", 0.1, 2.0, 0.1, 0.5, "V"),
            slider("steps", "Iterations", "Итерация саны", 20, 150, 10, 80),
        ],
    },
    "lab_bess_soc": {
        "run": _bess_soc,
        "params": [
            slider("n", "Number of panels", "Панель саны", 20, 400, 10, 100),
            slider("bat", "Battery capacity", "Батарея сыйымдылығы", 5, 300, 5, 40, "kWh"),
            slider("load", "Constant load", "Тұрақты жүктеме", 1, 40, 1, 12, "kW"),
            slider("dod", "Depth of discharge DoD", "Разряд тереңдігі DoD", 0.5, 1.0, 0.05, 0.8),
            WEATHER,
        ],
    },
    "lab_microgrid_dispatch": {
        "run": _microgrid,
        "params": [
            slider("n", "Number of panels", "Панель саны", 20, 400, 10, 100),
            slider("bat", "Battery capacity", "Батарея сыйымдылығы", 5, 300, 5, 50, "kWh"),
            slider("load", "Constant load", "Тұрақты жүктеме", 1, 50, 1, 15, "kW"),
            slider("inv", "Inverter rating", "Инвертор қуаты", 5, 100, 5, 40, "kW"),
            slider("dod", "Depth of discharge DoD", "Разряд тереңдігі DoD", 0.5, 1.0, 0.05, 0.8),
            WEATHER,
        ],
    },
    "lab_heuristic_vs_pulp": {
        "run": _heuristic_vs_pulp,
        "params": [
            slider("n", "Number of panels", "Панель саны", 20, 300, 10, 100),
            slider("bat", "Battery capacity", "Батарея сыйымдылығы", 10, 200, 5, 50, "kWh"),
            slider("load", "Constant load", "Тұрақты жүктеме", 5, 40, 1, 15, "kW"),
            select(
                "mode",
                "PuLP objective",
                "PuLP мақсаты",
                [
                    ("balanced", _L("Balanced", "Теңгерімді")),
                    ("max_profit", _L("Maximum profit", "Максимал пайда")),
                    ("min_co2", _L("Minimum CO₂", "Минимал CO₂")),
                ],
                "balanced",
            ),
            PRICE_I,
            PRICE_E,
            WEATHER,
        ],
    },
    "lab_pv_yield": {
        "run": _pv_yield,
        "params": [
            slider("n", "Number of panels", "Панель саны", 10, 500, 10, 80),
            slider("eta", "Efficiency η₀", "ПӘК η₀", 0.12, 0.24, 0.01, 0.20),
            WEATHER,
        ],
    },
    "lab_load_shape": {
        "run": _load_shape,
        "params": [
            slider("base", "Base load", "Базалық жүктеме", 0.2, 3.0, 0.1, 0.8, "kW"),
            slider("morning", "Morning peak", "Таңғы шың", 0.5, 8.0, 0.1, 2.0, "kW"),
            slider("evening", "Evening peak", "Кешкі шың", 0.5, 10.0, 0.1, 3.5, "kW"),
            slider("peak", "Rescale to peak", "Шыңға масштабтау", 0.5, 20.0, 0.5, 5.0, "kW"),
            slider("noise", "Noise", "Шу", 0, 20, 1, 5, "%"),
            slider("seed", "Random seed", "Кездейсоқ seed", 0, 999, 1, 42),
            slider("hours", "Hours", "Сағат саны", 24, 168, 24, 24, "h"),
        ],
    },
    "lab_bess_community": {
        "run": _bess_community,
        "params": [
            slider("cap", "Capacity", "Сыйымдылық", 5, 200, 5, 50, "kWh"),
            slider("dod", "Depth of discharge DoD", "Разряд тереңдігі DoD", 0.3, 1.0, 0.05, 0.8),
            slider("eta", "Half-cycle efficiency η", "Жарты цикл ПӘК η", 0.85, 1.0, 0.01, 0.95),
            slider(
                "amp", "Midday surplus amplitude", "Түскі артықтық амплитудасы", 1, 20, 1, 8, "kWh"
            ),
        ],
    },
    "lab_shared_energy": {
        "run": _shared_energy,
        "params": [
            slider("n_users", "Households N", "Үй саны N", 2, 8, 1, 4),
            slider("pv_users", "Households with PV", "PV-сі бар үйлер", 0, 8, 1, 2),
            slider("panels", "Panels per household", "Бір үйге панель", 10, 100, 5, 40),
            slider(
                "peak",
                "Peak load per household",
                "Бір үйдің шың жүктемесі",
                1.0,
                12.0,
                0.5,
                4.0,
                "kW",
            ),
            slider("bat", "Community battery", "Қауымдастық батареясы", 0, 200, 5, 30, "kWh"),
            slider("dod", "Depth of discharge DoD", "Разряд тереңдігі DoD", 0.4, 1.0, 0.05, 0.8),
            PRICE_I,
            PRICE_E,
            WEATHER,
        ],
    },
    "lab_rec_finance": {
        "run": _rec_finance,
        "params": [
            slider(
                "capex", "Investment CAPEX", "Инвестиция CAPEX", 10_000, 500_000, 5_000, 80_000, "$"
            ),
            slider(
                "gen",
                "Annual generation",
                "Жылдық өндіріс",
                10_000,
                1_000_000,
                5_000,
                120_000,
                "kWh",
            ),
            slider("price", "Energy price", "Энергия бағасы", 0.01, 0.5, 0.01, 0.10, "$/kWh"),
            slider("opex", "Annual O&M", "Жылдық пайдалану шығыны", 0, 20_000, 100, 2_000, "$"),
            slider("life", "Lifetime", "Қызмет мерзімі", 5, 30, 1, 20, "yr"),
            slider("rate", "Discount rate", "Дисконт мөлшерлемесі", 0.0, 0.15, 0.01, 0.05),
        ],
    },
    "lab_grid_impact": {
        "run": _grid_impact,
        "params": [
            slider("houses", "Houses on the feeder", "Желідегі үйлер", 2, 30, 1, 12),
            slider("length", "Feeder length", "Желі ұзындығы", 100, 1000, 50, 500, "m"),
            select("cable", "Cable", "Кабель", CABLE_OPTIONS, "nayy_4x95"),
            slider("pv_kw", "PV per house (peak)", "Бір үйдің PV қуаты (шың)", 0, 15, 0.5, 8, "kW"),
            slider(
                "load_kw",
                "Evening peak load per house",
                "Бір үйдің кешкі шың жүктемесі",
                0.5,
                8,
                0.5,
                3,
                "kW",
            ),
            slider(
                "pf",
                "PV inverter power factor (absorbing)",
                "PV инвертордың қуат коэффициенті (сіңіру)",
                0.85,
                1.0,
                0.01,
                1.0,
            ),
            slider(
                "v_source",
                "Transformer LV voltage",
                "Трансформатордың ТК кернеуі",
                0.95,
                1.05,
                0.01,
                1.02,
                "pu",
            ),
        ],
    },
    "lab_inverter_wiring": {"run": _inverter, "params": _inverter_params()},
}


def list_params(lab_id: str) -> list[dict[str, Any]]:
    if lab_id not in LABS:
        raise KeyError(lab_id)
    return LABS[lab_id]["params"]


def default_params(lab_id: str) -> dict[str, Any]:
    return {p["key"]: p["default"] for p in list_params(lab_id)}


def validate_params(lab_id: str, params: dict[str, Any] | None) -> dict[str, Any]:
    """Defaults for missing keys; numbers clamped to their range; unknown choices rejected."""
    out: dict[str, Any] = {}
    for spec in list_params(lab_id):
        key = spec["key"]
        raw = (params or {}).get(key, spec["default"])
        if spec["kind"] == "slider":
            try:
                v = float(raw)
            except (TypeError, ValueError):
                raise ValueError(f"{key}: not a number: {raw!r}") from None
            if not math.isfinite(v):
                raise ValueError(f"{key}: not a finite number")
            out[key] = min(max(v, float(spec["min"])), float(spec["max"]))
        else:
            ids = [o["id"] for o in spec["options"]]
            if raw not in ids:
                raise ValueError(f"{key}: expected one of {ids}, got {raw!r}")
            out[key] = raw
    return out


def run_lab(lab_id: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if lab_id not in LABS:
        raise KeyError(lab_id)
    p = validate_params(lab_id, params)
    fn: Callable[[dict[str, Any]], dict[str, Any]] = LABS[lab_id]["run"]
    res = fn(p)
    return {
        "lab_id": lab_id,
        "params": p,
        "metrics": res["metrics"],
        "charts": res["charts"],
        "notes": res.get("notes", []),
        **({"grade": res["grade"]} if "grade" in res else {}),
    }


def metric_value(result: dict[str, Any], key: str) -> float | None:
    for m in result["metrics"]:
        if m["key"] == key:
            return m["value"]
    raise KeyError(key)
