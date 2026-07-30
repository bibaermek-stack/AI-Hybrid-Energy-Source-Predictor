from __future__ import annotations
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
"""View extracted from legacy monolith tab."""

import os
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from dashboard.components.icons import icon, icon_text, strip_emoji
from dotenv import load_dotenv

from dashboard.utils.api_client import create_session_with_retries
from dashboard.utils.config import (
    API_URL,
    CHAT_URL,
    EXPLAIN_URL,
    FORECAST_URL,
    HEALTH_URL,
    SOLARMAN_ALERT_URL,
    SOLARMAN_CONFIGURE_URL,
    SOLARMAN_FC_URL,
    SOLARMAN_HISTORY_URL,
    SOLARMAN_LIVE_URL,
    SOLARMAN_PROCESS_URL,
    SOLARMAN_ROI_URL,
    SOLARMAN_STATUS_URL,
    SOLARMAN_WEATHER_URL,
)
from dashboard.utils.i18n import get_texts

load_dotenv()


def render(lang: str, texts: dict | None = None, models_status: dict | None = None) -> None:
    models_status = models_status or {"solar": False, "wind": False, "lstm": False}
    texts = {**get_texts(lang), **(texts or {})}

    if st.button(" Load Solarman Telemetry Data / Solarman телеметриясын жүктеу", key="load_sm_tab1", width='stretch'):
        st.session_state["irradiation_val"] = int(st.session_state.get("sm_irrad_val", 900))
        st.session_state["temp_val"] = int(st.session_state.get("sm_amb_temp_val", 30))
        st.session_state["module_val"] = int(st.session_state.get("sm_module_temp_val", 38))
        st.success("Solarman data successfully loaded into sliders!" if lang == "en" else "Solarman деректері жүгірткілерге сәтті жүктелді!")
        st.rerun()

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown(icon_text("sun", texts["solar_header"], size=20, as_heading=True, level=3), unsafe_allow_html=True)
            irradiation = st.slider(texts["irradiation"], 0, 1500, st.session_state.get("irradiation_val", 800))
            temp = st.slider(texts["temp"], -10, 60, st.session_state.get("temp_val", 30))
            module = st.slider(texts["module_temp"], -10, 80, st.session_state.get("module_val", 35))
            hour = st.slider(texts["hour"], 0, 23, 12)
            day = st.slider(texts["day"], 1, 31, 15)
            month = st.slider(texts["month"], 1, 12, 6)
    
    with col2:
        with st.container(border=True):
            st.markdown(icon_text("wind", texts["wind_header"], size=20, as_heading=True, level=3), unsafe_allow_html=True)
            wind_speed = st.slider(texts["wind_speed"], 0, 25, 6)
            direction = st.slider(texts["direction"], 0, 360, 250)
            theoretical = st.slider(texts["theoretical"], 0, 2000, 700)

    with st.container(border=True):
        st.markdown(icon_text("sliders", texts["opt_dispatch"], size=20, as_heading=True, level=3), unsafe_allow_html=True)
        d1, d2, d3 = st.columns(3)
        with d1:
            load_kw_ui = st.number_input(texts["opt_load"], min_value=0.0, value=0.0, step=50.0)
            battery_kw_ui = st.number_input(texts["opt_battery"], min_value=0.0, value=0.0, step=10.0)
        with d2:
            solar_cost_ui = st.number_input(texts["opt_solar_cost"], min_value=0.0, value=1.0, step=0.1)
            wind_cost_ui = st.number_input(texts["opt_wind_cost"], min_value=0.0, value=1.0, step=0.1)
        with d3:
            strategy_ui = st.selectbox(
                texts["opt_strategy"],
                ["hybrid", "min_cost", "max_power", "balanced"],
                index=0,
            )
    
    if st.button(texts["predict_btn"], width='stretch'):
        params = {
            "irradiation": irradiation,
            "temperature": temp,
            "module": module,
            "hour": hour,
            "day": day,
            "month": month,
            "wind_speed": wind_speed,
            "direction": direction,
            "theoretical": theoretical,
            "battery_kw": float(battery_kw_ui),
            "solar_cost_per_kwh": float(solar_cost_ui),
            "wind_cost_per_kwh": float(wind_cost_ui),
            "strategy": strategy_ui,
        }
        # 0 load → full offtake (omit field / send null)
        if load_kw_ui and float(load_kw_ui) > 0:
            params["load_kw"] = float(load_kw_ui)
        else:
            params["load_kw"] = None
    
        try:
            session = create_session_with_retries()
            response = session.post(API_URL, json=params, timeout=10)
        
            if response.status_code != 200:
                try:
                    error_msg = response.json().get("detail", response.text)
                except Exception:
                    error_msg = response.text
                st.error(texts["api_error"].format(code=response.status_code, msg=error_msg))
                st.stop()
            
            data = response.json()
        
            # Extract output values
            solar = float(data["solar_power"])
            wind = float(data["wind_power"])
            total = float(data["total_energy"])
            source = str(data["recommended_source"])
            st.session_state["last_solar"] = solar
            st.session_state["last_wind"] = wind
            st.session_state["last_recommendation"] = source
        
            # Display Custom Metrics in HTML Cards
            m_col1, m_col2, m_col3 = st.columns(3)
            with m_col1:
                st.markdown(f"""
                <div class="energy-card">
                    <div style="font-size:0.9rem;color:#8b949e;text-transform:uppercase;">{texts["solar_metric"]}</div>
                    <div class="metric-value" style="background: linear-gradient(90deg, #FDB462 0%, #ffc107 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{round(solar, 2)} kW</div>
                </div>
                """, unsafe_allow_html=True)
            with m_col2:
                st.markdown(f"""
                <div class="energy-card">
                    <div style="font-size:0.9rem;color:#8b949e;text-transform:uppercase;">{texts["wind_metric"]}</div>
                    <div class="metric-value" style="background: linear-gradient(90deg, #80B1D3 0%, #2196F3 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{round(wind, 2)} kW</div>
                </div>
                """, unsafe_allow_html=True)
            with m_col3:
                st.markdown(f"""
                <div class="energy-card">
                    <div style="font-size:0.9rem;color:#8b949e;text-transform:uppercase;">{texts["total_metric"]}</div>
                    <div class="metric-value" style="background: linear-gradient(90deg, #4CAF50 0%, #8BC34A 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{round(total, 2)} kW</div>
                </div>
                """, unsafe_allow_html=True)

            if source == "Solar":
                mapped_source = texts["solar_label"]
            elif source == "Wind":
                mapped_source = texts["wind_label"]
            else:
                mapped_source = texts["hybrid_label"]
            st.success(texts["recommended"].format(source=mapped_source))
        
            # Plotly Output chart
            chart_data = {
                texts["chart_x"]: [texts["solar_label"], texts["wind_label"]],
                texts["chart_y"]: [solar, wind]
            }
            fig = px.bar(
                chart_data,
                x=texts["chart_x"],
                y=texts["chart_y"],
                title=texts["chart_title"],
                labels={texts["chart_y"]: texts["chart_y"], texts["chart_x"]: texts["chart_x"]},
                color=texts["chart_x"],
                color_discrete_map={texts["solar_label"]: "#FDB462", texts["wind_label"]: "#80B1D3"}
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#c9d1d9"
            )
            st.plotly_chart(fig, width='stretch')
        
            # Optimization Details card
            with st.container(border=True):
                st.markdown(icon_text("gauge", texts["opt_header"], size=20, as_heading=True, level=3), unsafe_allow_html=True)
                st.write(texts["opt_solar"].format(val=round(solar, 2)))
                st.write(texts["opt_wind"].format(val=round(wind, 2)))
                st.write(texts["opt_combined"].format(val=round(total, 2)))
                st.write(texts["opt_better"].format(source=mapped_source))
                s_share = float(data.get("solar_share") or 0)
                w_share = float(data.get("wind_share") or 0)
                h_share = float(data.get("hybrid_share") or 0)
                st.write(texts["opt_shares"].format(s=s_share, w=w_share, h=h_share))
                st.write(texts["opt_reliability"].format(val=float(data.get("reliability_index") or 0)))
                st.write(texts["opt_shortfall"].format(val=round(float(data.get("shortfall_kw") or 0), 2)))
                st.write(texts["opt_curtailment"].format(val=round(float(data.get("curtailment_kw") or 0), 2)))
                st.write(texts["opt_battery_used"].format(val=round(float(data.get("battery_used") or 0), 2)))
                st.caption(f"strategy={data.get('strategy', strategy_ui)} · estimated_cost={data.get('estimated_cost', '—')}")
        
            # AI advisor explanation via API (map Hybrid → hybrid knowledge)
            explanation = "..."
            explain_source = "Hybrid" if source.lower() == "hybrid" else source
            try:
                explain_response = session.post(
                    EXPLAIN_URL,
                    json={"source": explain_source if explain_source != "Hybrid" else "hybrid", "lang": lang},
                    timeout=5,
                )
                if explain_response.status_code == 200:
                    explanation = explain_response.json().get("explanation", "")
            except Exception as e:
                explanation = f"Error: {e}"
            
            with st.container(border=True):
                st.markdown(icon_text("bot", texts["advisor_header"], size=20, as_heading=True, level=3), unsafe_allow_html=True)
                st.info(explanation)
        
        except requests.exceptions.Timeout:
            st.error(texts["timeout_error"])
        except requests.exceptions.ConnectionError:
            st.error(texts["conn_error"])
        except Exception as e:
            st.error(texts["unexpected_error"].format(error=str(e)))

