"""Embed Solarman inverter 3D (Meshy) with live telemetry (no simulation).

Supports:
  - Inverter2501221272 → models/inverter/
  - Inverter2411046235 → models/inverter_2411046235/  (Meshy_AI__0722080659, +90°X +180°Z)
"""
from __future__ import annotations

from datetime import datetime
from urllib.parse import quote

import streamlit as st

from dashboard.components.icons import icon_text
from dashboard.utils.inverter_catalog import list_inverter_choices, resolve_inverter


def resolve_viewer_base() -> tuple[str | None, str]:
    try:
        try:
            from dashboard.static_server import resolve_viewer_base_url
        except ImportError:
            from static_server import resolve_viewer_base_url
        return resolve_viewer_base_url()
    except Exception as e:
        return None, str(e)


def render_inverter_3d(
    lang: str,
    dash: dict | None,
    height: int | None = None,
    *,
    model_key: str | None = None,
    sn_override: str | None = None,
) -> None:
    """
    Show 3D model of the selected Solarman inverter + live telemetry.
    Only passes real telemetry into the viewer — no power simulation.
    """
    if height is None:
        try:
            from dashboard.utils.layout import iframe_3d_height

            height = iframe_3d_height(600, 400)
        except Exception:
            height = 560

    basic = (dash or {}).get("basic") or {}
    gen = (dash or {}).get("generation") or {}
    sn_from_api = str(basic.get("sn") or "2501221272")
    sn = str(sn_override or sn_from_api)
    inv = resolve_inverter(sn=sn, model_key=model_key)
    label = inv["label"]

    st.markdown(
        icon_text(
            "model3d",
            f"3D model · {label}" if lang == "en" else f"3D модель · {label}",
            size=20,
            as_heading=True,
            level=3,
        ),
        unsafe_allow_html=True,
    )
    st.caption(
        f"EcoPredict AI · Solarman — {label} Meshy 3D + live API (no simulation)"
        if lang == "en"
        else f"EcoPredict AI · Solarman — {label} Meshy 3D + live API (симуляция жоқ)"
    )
    # Catalog hint under title so both plant units are always discoverable
    _others = [c["label"] for c in list_inverter_choices() if c["sn"] != sn]
    if _others:
        st.caption(
            ("Also available: " if lang == "en" else "Басқа: ")
            + " · ".join(_others)
            + (" — pick above" if lang == "en" else " — жоғарыдағы тізімнен таңдаңыз")
        )

    if not dash:
        st.info(
            "Load live data first."
            if lang == "en"
            else "Алдымен live дерек жүктеңіз."
        )
        return

    device_id = basic.get("device_id") or ""
    grid = basic.get("grid_status") or ""
    rated = float(basic.get("rated_power_kw") or inv.get("rated_kw_hint") or 25)
    ac_kw = float(gen.get("ac_active_power_kw") or 0)
    dc_kw = float(gen.get("dc_total_kw") or 0)
    e_today = float(gen.get("e_today_kwh") or 0)
    e_total = float(gen.get("e_total_kwh") or 0)
    inv_temp = float(gen.get("temperature_c") or 0)
    amb_temp = inv_temp - 15.0 if inv_temp > 20 else inv_temp
    hour_now = datetime.now().hour + datetime.now().minute / 60.0
    hour_now = max(6.0, min(18.0, hour_now))

    base, src = resolve_viewer_base()
    if not base:
        st.error(
            f"3D server unavailable: {src}"
            if lang == "en"
            else f"3D сервер жоқ: {src}"
        )
        return

    # Never iframe private LAN URLs on a public page
    if "127.0.0.1" in base or "localhost" in base:
        try:
            from dashboard.static_server import browser_public_origin

            origin = browser_public_origin()
            if origin and "localhost" not in origin and "127.0.0.1" not in origin:
                base = f"{origin}/app/static"
                src = "streamlit-static"
        except Exception:
            pass

    viewer_path = f"{base.rstrip('/')}/model_viewer.html"
    qs = (
        f"sn={quote(sn)}"
        f"&model={quote(str(inv['model_key']))}"
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
    # v= cache-bust when model_viewer / mesh assets change
    # bump v= when texture/mesh changes so browser does not keep old PNG
    iframe_url = f"{viewer_path}?{qs}&embedded=1&v=tex20260722d"
    fullscreen_url = f"{viewer_path}?{qs}&embedded=0&v=tex20260722d"

    st.caption(
        "Model auto-rotates · closer view. Full screen = manual orbit/zoom."
        if lang == "en"
        else "Модель автоматты айналады · жақынырақ. Толық экран = қолмен бұру/зум."
    )
    st.markdown(
        f'<a href="{fullscreen_url}" target="_blank" rel="noopener noreferrer" '
        f'style="font-weight:600;font-size:1.05rem;">'
        f'{"3D full screen" if lang == "en" else "3D толық экран"}'
        f"</a>",
        unsafe_allow_html=True,
    )

    if "127.0.0.1" in iframe_url or "localhost" in iframe_url:
        st.warning(
            "3D URL is localhost. Set Railway `PUBLIC_BASE_URL=https://www.ecopredict.kz`."
            if lang == "en"
            else "3D URL localhost. Railway: `PUBLIC_BASE_URL=https://www.ecopredict.kz`."
        )
    elif "/component/" in iframe_url:
        st.caption("legacy component URL")

    try:
        # Streamlit ≥1.50 st.iframe: no `scrolling` kw (unlike components.v1.iframe)
        if hasattr(st, "iframe"):
            st.iframe(iframe_url, height=int(height), width="stretch")
        else:
            st.components.v1.iframe(src=iframe_url, height=int(height), scrolling=False)
    except TypeError:
        # Very old API variants
        try:
            st.components.v1.iframe(src=iframe_url, height=int(height))
        except Exception as e:
            st.error(f"iframe: {e}")
            st.markdown(f"[3D толық экран]({fullscreen_url})")
    except Exception as e:
        st.error(f"iframe: {e}")
        st.markdown(f"[3D толық экран]({fullscreen_url})")
