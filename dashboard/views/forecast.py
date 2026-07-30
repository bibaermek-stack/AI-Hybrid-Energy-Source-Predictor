from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from dashboard.components.icons import icon_text
from dotenv import load_dotenv

from dashboard.utils.api_client import create_session_with_retries
from dashboard.utils.config import FORECAST_URL, SOLARMAN_FC_URL

from dashboard.utils.i18n import get_texts

load_dotenv()


def render(lang: str, texts: dict | None = None, models_status: dict | None = None) -> None:
    models_status = models_status or {"solar": False, "wind": False, "lstm": False}
    texts = {**get_texts(lang), **(texts or {})}

    can_forecast = bool(models_status.get("solar") or models_status.get("forecast"))
    if not can_forecast:
        st.warning(
            "Болжам моделі қолжетімсіз (solar_model.pkl)."
            if lang == "kk"
            else "Forecast model unavailable (solar_model.pkl)."
        )
        st.info(
            "API Offline немесе solar_model.pkl жүктелмеген. Backend /health тексеріңіз."
            if lang == "kk"
            else "API offline or solar_model.pkl not loaded. Check backend /health."
        )
        return

    st.caption(
        "Болжам: RandomForest · artifacts/solar_model.pkl"
        if lang == "kk"
        else "Forecast: RandomForest · artifacts/solar_model.pkl"
    )

    try:
        _feat_path = (
            Path(__file__).resolve().parents[2]
            / "data"
            / "processed"
            / "build_features.csv"
        )
        if not _feat_path.is_file():
            _feat_path = Path("data/processed/build_features.csv")
        if not _feat_path.is_file():
            raise FileNotFoundError(
                f"Feature dataset missing: {_feat_path}. "
                "Commit data/processed/build_features.csv or run feature build pipeline."
            )
        df_features = pd.read_csv(_feat_path)
        df_features = df_features.reset_index(drop=True)
        df_features["DATE_TIME"] = pd.to_datetime(df_features["DATE_TIME"])
        df_features["date_only"] = df_features["DATE_TIME"].dt.date

        valid_dates = []
        for d in sorted(df_features["date_only"].unique()):
            date_recs = df_features[df_features["date_only"] == d]
            if len(date_recs) > 0 and int(date_recs.index[0]) >= 24:
                valid_dates.append(d)

        if not valid_dates:
            st.error("No valid dates found in dataset with sufficient preceding history.")
        else:
            with st.container(border=True):
                selected_date = st.selectbox(texts["select_date"], valid_dates, index=0)

            if st.button(texts["forecast_btn"], width="stretch"):
                date_records = df_features[df_features["date_only"] == selected_date]
                feature_cols = [
                    "IRRADIATION",
                    "AMBIENT_TEMPERATURE",
                    "MODULE_TEMPERATURE",
                    "hour",
                    "day",
                    "month",
                ]
                sequences = []
                for idx in date_records.index:
                    i = int(idx)
                    if i < 24:
                        continue
                    seq_df = df_features.loc[i - 24 : i - 1, feature_cols]
                    if len(seq_df) != 24:
                        continue
                    sequences.append(seq_df.values.tolist())

                if not sequences:
                    st.error(
                        "Осы күнге 24 сағаттық history жеткіліксіз."
                        if lang == "kk"
                        else "Not enough history rows to build 24h sequences for this date."
                    )
                else:
                    try:
                        with st.spinner(
                            "Болжам есептелуде..."
                            if lang == "kk"
                            else "Running forecast..."
                        ):
                            session = create_session_with_retries()
                            resp = session.post(
                                FORECAST_URL, json={"sequences": sequences}, timeout=60
                            )

                        if resp.status_code == 200:
                            body = resp.json()
                            preds = body.get("predictions", [])
                            backend = body.get("model") or "unknown"
                            actuals = date_records["AC_POWER"].values.tolist()
                            # Align lengths if RF returns fewer (skip early rows)
                            n = min(len(preds), len(actuals))
                            preds = preds[:n]
                            actuals = actuals[:n]
                            hours = (
                                pd.to_datetime(date_records["DATE_TIME"])
                                .dt.strftime("%H:%M")
                                .tolist()[:n]
                            )

                            st.caption(f"API model: **{backend}**")

                            fig_fc = go.Figure()
                            fig_fc.add_trace(
                                go.Scatter(
                                    x=hours,
                                    y=actuals,
                                    mode="lines+markers",
                                    name=texts["fc_actual"],
                                    line=dict(color="#4CAF50", width=3),
                                )
                            )
                            fig_fc.add_trace(
                                go.Scatter(
                                    x=hours,
                                    y=preds,
                                    mode="lines+markers",
                                    name=texts.get("fc_predicted") or "Predicted",
                                    line=dict(color="#FF9800", width=3, dash="dash"),
                                )
                            )
                            fig_fc.update_layout(
                                title=texts["fc_title"].format(date=selected_date),
                                xaxis_title="Time" if lang == "en" else "Уақыты",
                                yaxis_title="Power (kW)" if lang == "en" else "Қуат (кВт)",
                                plot_bgcolor="rgba(0,0,0,0)",
                                paper_bgcolor="rgba(0,0,0,0)",
                                font_color="#c9d1d9",
                                legend=dict(
                                    yanchor="top", y=0.99, xanchor="left", x=0.01
                                ),
                            )
                            st.plotly_chart(fig_fc, width="stretch")

                            tot_actual = sum(actuals)
                            tot_pred = sum(preds)
                            mae = float(
                                np.mean(np.abs(np.array(actuals) - np.array(preds)))
                            )
                            peak_hour = hours[int(np.argmax(preds))] if preds else "—"

                            s_col1, s_col2, s_col3, s_col4 = st.columns(4)
                            with s_col1:
                                st.markdown(
                                    f"""
                                    <div class="energy-card">
                                        <div style="font-size:0.85rem;color:#8b949e;">{texts["fc_total_actual"]}</div>
                                        <div class="metric-value">{round(tot_actual, 2)} kW</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )
                            with s_col2:
                                st.markdown(
                                    f"""
                                    <div class="energy-card">
                                        <div style="font-size:0.85rem;color:#8b949e;">{texts["fc_total_pred"]}</div>
                                        <div class="metric-value" style="background: linear-gradient(90deg, #FF9800 0%, #FFB74D 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{round(tot_pred, 2)} kW</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )
                            with s_col3:
                                st.markdown(
                                    f"""
                                    <div class="energy-card">
                                        <div style="font-size:0.85rem;color:#8b949e;">{texts["fc_mae"]}</div>
                                        <div class="metric-value" style="background: linear-gradient(90deg, #f44336 0%, #ef5350 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{round(mae, 2)} kW</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )
                            with s_col4:
                                st.markdown(
                                    f"""
                                    <div class="energy-card">
                                        <div style="font-size:0.85rem;color:#8b949e;">{texts["fc_peak"]}</div>
                                        <div class="metric-value" style="background: linear-gradient(90deg, #00BCD4 0%, #4DD0E1 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{peak_hour}</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )
                        else:
                            st.error(
                                f"Error calling forecast API: {resp.status_code} {resp.text[:200]}"
                            )
                    except Exception as e:
                        st.error(f"Forecasting task failed: {e}")
    except Exception as e:
        st.error(f"Could not load feature dataset: {e}")

    # Live 24h weather-based forecast (WeatherAPI + solar model on backend)
    st.markdown("---")
    st.markdown(
        icon_text("zap", texts.get("sm_fc_header") or "24h live forecast", size=20, as_heading=True, level=3),
        unsafe_allow_html=True,
    )

    with st.spinner(texts.get("sm_fc_loading") or "Loading..."):
        try:
            from datetime import datetime

            sm_dc_cap_val = st.session_state.get("sm_dc_cap_val", 50.0)
            fc_resp = requests.get(
                f"{SOLARMAN_FC_URL}?dc_capacity_kwp={sm_dc_cap_val}", timeout=15
            )
            if fc_resp.status_code == 200:
                fc_data = fc_resp.json().get("forecasts", [])
                if not fc_data:
                    st.info("No live forecast rows returned.")
                    return

                fc_times = [
                    datetime.fromisoformat(item["time"]).strftime("%H:%M")
                    for item in fc_data
                ]
                fc_powers = [item["predicted_power_kw"] for item in fc_data]
                fc_clouds = [item["cloud_cover"] for item in fc_data]
                fc_temps = [item["temperature"] for item in fc_data]

                daytime_clouds = [
                    c
                    for item, c in zip(fc_data, fc_clouds)
                    if 8 <= datetime.fromisoformat(item["time"]).hour <= 17
                ]
                avg_clouds = np.mean(daytime_clouds) if daytime_clouds else 0.0

                if avg_clouds > 70.0:
                    st.warning(texts.get("sm_fc_alert_low") or "Low generation risk")
                elif avg_clouds < 30.0 and len(daytime_clouds) > 0:
                    st.success(texts.get("sm_fc_alert_high") or "Good solar day")

                fig_fc = go.Figure()
                fig_fc.add_trace(
                    go.Bar(
                        x=fc_times,
                        y=fc_powers,
                        name="Predicted Power (kW)"
                        if lang == "en"
                        else "Болжалды қуат (кВт)",
                        marker_color="#FF9800",
                        opacity=0.75,
                    )
                )
                fig_fc.add_trace(
                    go.Scatter(
                        x=fc_times,
                        y=fc_clouds,
                        name="Cloud Cover (%)" if lang == "en" else "Бұлттылық (%)",
                        yaxis="y2",
                        line=dict(color="#90A4AE", width=2, dash="dot"),
                    )
                )
                fig_fc.add_trace(
                    go.Scatter(
                        x=fc_times,
                        y=fc_temps,
                        name="Temperature (°C)" if lang == "en" else "Температура (°C)",
                        yaxis="y2",
                        line=dict(color="#EF5350", width=2),
                    )
                )
                fig_fc.update_layout(
                    title=(
                        "Live 24-Hour Solar Production & Weather Forecast (Turkistan)"
                        if lang == "en"
                        else "Күн өндірісі мен ауа райының 24 сағаттық болжамы (Түркістан)"
                    ),
                    xaxis_title="Time (HH:MM)" if lang == "en" else "Уақыты (HH:MM)",
                    yaxis=dict(
                        title=dict(
                            text="Predicted Power (kW)"
                            if lang == "en"
                            else "Болжалды қуат (кВт)",
                            font=dict(color="#FF9800"),
                        ),
                        tickfont=dict(color="#FF9800"),
                    ),
                    yaxis2=dict(
                        title=dict(
                            text="Clouds (%) / Temp (°C)"
                            if lang == "en"
                            else "Бұлттылық (%) / Темп (°C)",
                            font=dict(color="#90A4AE"),
                        ),
                        tickfont=dict(color="#90A4AE"),
                        overlaying="y",
                        side="right",
                    ),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#c9d1d9",
                    legend=dict(x=0.01, y=0.99),
                )
                st.plotly_chart(fig_fc, width="stretch", key="fc_chart_tab2")
            else:
                st.error(
                    f"Could not load live forecast. API returned: {fc_resp.status_code}"
                )
        except Exception as e:
            st.error(f"Live weather forecast monitoring is temporarily offline: {e}")
