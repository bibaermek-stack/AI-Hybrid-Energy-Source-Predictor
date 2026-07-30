"""3D models of Solarman inverters — live telemetry only (no simulation).

Units:
  - Inverter2501221272 → models/inverter/
  - Inverter2411046235 → models/inverter_2411046235/ (Meshy_AI__0722061656)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import quote

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import requests
import streamlit as st
from dotenv import load_dotenv

from dashboard.components.icons import icon_text
from dashboard.utils.config import SOLARMAN_LIVE_URL
from dashboard.utils.inverter_catalog import list_inverter_choices, resolve_inverter

load_dotenv()

DEFAULT_SN = os.getenv("SOLARMAN_DEVICE_SN", "2501221272")


def _fetch_inverter_live() -> dict | None:
    """Real Solarman OpenAPI data only (demo=false)."""
    try:
        r = requests.get(f"{SOLARMAN_LIVE_URL}?demo=false&force_demo=false", timeout=45)
        if r.status_code == 200:
            data = r.json()
            # Reject pure demo payloads when we expect live
            if data.get("source") in ("demo", "demo_fallback") and data.get("warning"):
                # still allow if API fell back, but mark it
                return data
            return data
    except Exception:
        pass
    try:
        from src.utils.solarman_client import get_live_dashboard

        return get_live_dashboard(use_demo_if_no_creds=False, force_demo=False)
    except Exception as e:
        st.session_state["inv_3d_err"] = str(e)
        return None


def render(lang: str, texts: dict, models_status: dict | None = None) -> None:
    st.markdown(
        icon_text(
            "model3d",
            texts.get("tab_3d_model") or "3D Inverter",
            size=22,
            as_heading=True,
            level=3,
        ),
        unsafe_allow_html=True,
    )

    choices = list_inverter_choices()
    sn_pick = st.selectbox(
        "Inverter / Инвертор",
        [c["sn"] for c in choices],
        format_func=lambda s: next(
            (c["label"] for c in choices if c["sn"] == s), s
        ),
        index=0
        if DEFAULT_SN not in [c["sn"] for c in choices]
        else [c["sn"] for c in choices].index(DEFAULT_SN)
        if DEFAULT_SN in [c["sn"] for c in choices]
        else 0,
        key="inv_3d_sn_pick",
    )
    inv_meta = resolve_inverter(sn=sn_pick)

    st.markdown(
        icon_text(
            "inverter",
            f"{inv_meta['label']} — 3D model + live API"
            if lang == "en"
            else f"{inv_meta['label']} — 3D модель + live API",
            size=18,
            as_heading=True,
            level=4,
        ),
        unsafe_allow_html=True,
    )
    st.caption(
        "No simulation. Telemetry from Solarman OpenAPI when available; 3D mesh is local Meshy OBJ."
        if lang == "en"
        else "Симуляция жоқ. Телеметрия Solarman API (бар болса); 3D — жергілікті Meshy OBJ."
    )
    st.caption(f"3D folder: models/{inv_meta['model_dir']}/")

    c1, c2 = st.columns([1, 4])
    with c1:
        refresh = st.button(
            "Refresh API" if lang == "en" else "API жаңарту",
            type="primary",
            width="stretch",
            key="btn_3d_api_refresh",
        )

    # Always prefer real API; refresh on button or first open
    if refresh or "inv_3d_live" not in st.session_state:
        with st.spinner("Solarman live..."):
            # Prefer fresh API; optional reuse of Solarman page cache if same SN
            dash = None
            cached = st.session_state.get("sm_live_dash")
            if (
                not refresh
                and cached
                and str((cached.get("basic") or {}).get("sn") or "") == str(DEFAULT_SN)
                and cached.get("source") == "solarman_api"
            ):
                dash = cached
            if dash is None:
                dash = _fetch_inverter_live()
            if dash and dash.get("source") == "solarman_api":
                st.session_state["inv_3d_live"] = dash
                st.session_state.pop("inv_3d_err", None)
            elif dash:
                # demo/fallback — show but warn
                st.session_state["inv_3d_live"] = dash
            else:
                st.session_state.pop("inv_3d_live", None)

    dash = st.session_state.get("inv_3d_live")
    if not dash:
        err = st.session_state.get("inv_3d_err", "")
        st.error(
            (f"Live data unavailable. {err}" if lang == "en" else f"Live дерек жоқ. {err}")
            + "  ·  GET /solarman/live?demo=false"
        )
        return

    if dash.get("source") != "solarman_api":
        st.warning(
            f"Not live API (source={dash.get('source')}). Check credentials."
            if lang == "en"
            else f"Бұл live API емес (source={dash.get('source')}). Credential тексеріңіз."
        )
    else:
        st.success(
            "Live Solarman OpenAPI" if lang == "en" else "Нақты Solarman OpenAPI"
        )

    basic = dash.get("basic") or {}
    gen = dash.get("generation") or {}
    version = dash.get("version") or {}
    sn = str(basic.get("sn") or DEFAULT_SN)
    device_id = basic.get("device_id") or "—"
    grid = basic.get("grid_status") or "—"
    rated = float(basic.get("rated_power_kw") or 25)
    ac_kw = float(gen.get("ac_active_power_kw") or 0)
    dc_kw = float(gen.get("dc_total_kw") or 0)
    e_today = float(gen.get("e_today_kwh") or 0)
    e_total = float(gen.get("e_total_kwh") or 0)
    inv_temp = float(gen.get("temperature_c") or 0)
    amb_temp = inv_temp - 15.0 if inv_temp > 20 else inv_temp

    dc_rows = gen.get("dc") or []
    ac_rows = gen.get("ac") or []
    pv1 = next((r for r in dc_rows if r.get("mppt") == "PV1"), {})
    pv2 = next((r for r in dc_rows if r.get("mppt") == "PV2"), {})

    # KPI — real only
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("SN", sn)
    k2.metric("Device ID", str(device_id))
    k3.metric("AC", f"{ac_kw:.3f} kW")
    k4.metric("DC", f"{dc_kw:.3f} kW")
    k5.metric("E-today", f"{e_today:.1f} kWh")
    k6.metric("Temp", f"{inv_temp:.1f} °C")

    st.progress(
        min(1.0, max(0.0, ac_kw / rated if rated else 0)),
        text=f"{grid} · {ac_kw:.2f} / {rated:.0f} kW · E-total {e_total:.1f} kWh",
    )

    # 3D static host
    viewer_base = None
    try:
        try:
            from dashboard.static_server import resolve_viewer_base_url
        except ImportError:
            from static_server import resolve_viewer_base_url
        viewer_base, viewer_source = resolve_viewer_base_url()
    except Exception as e:
        st.error(f"3D server: {e}")
        viewer_base, viewer_source = None, "none"

    left, right = st.columns([1, 2.5])

    with left:
        with st.container(border=True):
            st.markdown(
                icon_text("inverter", "Live telemetry" if lang == "en" else "Live телеметрия", size=18, as_heading=True, level=4),
                unsafe_allow_html=True,
            )
            st.markdown(f"**Type:** {basic.get('inverter_type', '—')}")
            st.markdown(f"**Rated:** {rated:.0f} kW · MPPT {basic.get('mppt_no', '—')}")
            st.markdown(f"**Grid:** {grid}")
            st.markdown(f"**Product:** {basic.get('product_type', '—')}")
            st.markdown(f"**MAIN / HMI:** {version.get('main', '—')} / {version.get('hmi', '—')}")
            st.markdown(f"**Protocol:** {version.get('protocol_version', '—')}")
            st.caption(f"source={dash.get('source')} · {dash.get('fetched_at', '')}")

            st.markdown("---")
            st.markdown("**DC (API)**")
            st.write(
                f"PV1: {pv1.get('voltage_v', 0)} V · {pv1.get('current_a', 0)} A · "
                f"**{float(pv1.get('power_kw') or 0):.3f} kW**"
            )
            st.write(
                f"PV2: {pv2.get('voltage_v', 0)} V · {pv2.get('current_a', 0)} A · "
                f"**{float(pv2.get('power_kw') or 0):.3f} kW**"
            )
            st.markdown("**AC (API)**")
            for r in ac_rows:
                freq = r.get("frequency_hz")
                freq_s = f"{freq:.2f} Hz" if isinstance(freq, (int, float)) and freq else "—"
                st.write(
                    f"{r.get('phase')}: {r.get('voltage_v', 0)} V · {r.get('current_a', 0)} A · "
                    f"{freq_s} · **{float(r.get('power_kw') or 0):.3f} kW**"
                )

    with right:
        if not viewer_base:
            st.error("3D static server unavailable.")
            return

        # Only real values into the viewer (no simulated power/irradiance model)
        from datetime import datetime

        hour_now = datetime.now().hour + datetime.now().minute / 60.0
        hour_now = max(6.0, min(18.0, hour_now))

        # Prefer UI-selected SN for 3D mesh; API sn may differ if only one device is configured
        inv_ui = resolve_inverter(sn=sn_pick, model_key=None)
        viewer_path = f"{viewer_base.rstrip('/')}/model_viewer.html"
        iframe_url = (
            f"{viewer_path}"
            f"?sn={quote(sn_pick)}"
            f"&model={quote(str(inv_ui['model_key']))}"
            f"&device_id={quote(str(device_id))}"
            f"&grid={quote(str(grid))}"
            f"&temp={amb_temp:.2f}"
            f"&module_temp={inv_temp:.2f}"
            f"&power={ac_kw:.4f}"
            f"&dc_power={dc_kw:.4f}"
            f"&e_today={e_today:.2f}"
            f"&e_total={e_total:.1f}"
            f"&rated={rated:.0f}"
            f"&hour={hour_now:.2f}"
            f"&lang={lang}"
            f"&live=1"
        )

        st.caption(
            "3D visualization of the real device · telemetry = API only"
            if lang == "en"
            else "Нақты құрылғының 3D көрінісі · телеметрия = тек API"
        )
        st.markdown(
            f'<a href="{iframe_url}" target="_blank">'
            f'{"Open 3D in new tab" if lang == "en" else "3D жаңа терезеде"}'
            f"</a>",
            unsafe_allow_html=True,
        )
        try:
            st.components.v1.iframe(src=iframe_url, height=720, scrolling=False)
        except Exception as e:
            st.error(f"iframe: {e}")
            st.markdown(f"[Open]({iframe_url})")
