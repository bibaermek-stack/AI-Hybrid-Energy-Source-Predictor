import os
import requests
import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from dotenv import load_dotenv
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

load_dotenv()

# API Configuration
API_URL = os.getenv("API_URL", "http://127.0.0.1:8001/predict")
EXPLAIN_URL = os.getenv("EXPLAIN_URL", "http://127.0.0.1:8001/explain")
HEALTH_URL = os.getenv("HEALTH_URL", "http://127.0.0.1:8001/health")
FORECAST_URL = os.getenv("FORECAST_URL", "http://127.0.0.1:8001/forecast-batch")
CHAT_URL = os.getenv("CHAT_URL", "http://127.0.0.1:8001/chat")

# Localization Dictionary
LOCALIZATION = {
    "en": {
        "title": "⚡ EcoPredict AI Platform",
        "subtitle": "Predict and Optimize Hybrid Solar & Wind Generation",
        "tab_predict": "🔮 Real-Time Optimization",
        "tab_forecast": "📈 24-Hour Forecasting",
        "tab_chat": "💬 AI Chatbot Advisor",
        
        # Tab 1: Predict
        "solar_header": "☀️ Solar Inputs",
        "irradiation": "Irradiation (W/m²)",
        "temp": "Ambient Temperature (°C)",
        "module_temp": "Module Temp (°C)",
        "hour": "Hour of Day",
        "day": "Day of Month",
        "month": "Month",
        "wind_header": "💨 Wind Inputs",
        "wind_speed": "Wind Speed (m/s)",
        "direction": "Wind Direction (°)",
        "theoretical": "Theoretical Power (kW)",
        "predict_btn": "🔮 Predict Energy",
        
        "solar_metric": "☀️ Solar Power",
        "wind_metric": "💨 Wind Power",
        "total_metric": "⚡ Total Energy",
        "recommended": "✅ Recommended Source: **{source}**",
        "chart_title": "Energy Output Comparison",
        "chart_y": "Power (kW)",
        "chart_x": "Source",
        "opt_header": "📊 Hybrid Optimization Analysis",
        "opt_solar": "- **Solar Output**: {val} kW",
        "opt_wind": "- **Wind Output**: {val} kW",
        "opt_combined": "- **Combined Output**: {val} kW",
        "opt_better": "- **Better Source**: {source} ({val} kW)",
        "advisor_header": "🤖 AI Energy Advisor Explanation",
        
        # Tab 2: Forecast
        "select_date": "Select Forecast Date:",
        "forecast_btn": "📈 Run 24-Hour LSTM Forecast",
        "fc_actual": "Actual AC Power",
        "fc_predicted": "Predicted Solar Power (LSTM)",
        "fc_title": "24-Hour Solar Forecasting Comparison ({date})",
        "fc_summary_title": "Daily Forecast Summary",
        "fc_total_actual": "Total Actual Output:",
        "fc_total_pred": "Total Predicted Output:",
        "fc_mae": "Forecast Mean Absolute Error:",
        "fc_peak": "Peak Solar Output Time:",
        "fc_no_lstm": "⚠️ LSTM Forecasting is disabled. Please check backend server.",
        
        # Tab 3: Chatbot
        "chat_header": "🤖 Ask anything about Hybrid Renewable Energy Systems!",
        "chat_placeholder": "Type your question here (e.g., 'How does temperature affect solar panels?')",
        "chat_submit": "Send",
        "chat_preset_title": "Preset Questions:",
        "chat_preset_1": "Why does high temperature reduce solar output?",
        "chat_preset_2": "What are cut-in and cut-out wind speeds?",
        "chat_preset_3": "Why are hybrid solar-wind systems more efficient?",
        "chat_preset_4": "What role does battery storage play in smart grids?",
        
        # Errors & Status
        "api_error": "❌ API Error {code}: {msg}",
        "invalid_json": "❌ API returned invalid JSON.",
        "missing_fields": "❌ API response missing fields: {fields}",
        "invalid_types": "❌ Invalid data types in API response: {error}",
        "api_response": "✅ API Response Data:",
        "solar_label": "Solar",
        "wind_label": "Wind",
        "timeout_error": "⏱️ API request timed out.",
        "conn_error": "🌐 Cannot connect to API. Is the backend server running?",
        "unexpected_error": "❌ Unexpected error: {error}"
    },
    "kk": {
        "title": "⚡ EcoPredict AI платформасы",
        "subtitle": "Гибридті күн және жел энергиясын болжау және оңтайландыру",
        "tab_predict": "🔮 Реалды уақыттағы оңтайландыру",
        "tab_forecast": "📈 24 сағаттық болжам",
        "tab_chat": "💬 AI чат-кеңесші",
        
        # Tab 1: Predict
        "solar_header": "☀️ Күн энергиясы деректері",
        "irradiation": "Күн сәулесінің түсуі (Вт/м²)",
        "temp": "Қоршаған орта температурасы (°C)",
        "module_temp": "Панель температурасы (°C)",
        "hour": "Күн сағаты",
        "day": "Күн (айдың күні)",
        "month": "Ай",
        "wind_header": "💨 Жел энергиясы деректері",
        "wind_speed": "Жел жылдамдығы (м/с)",
        "direction": "Жел бағыты (°)",
        "theoretical": "Теориялық қуат (кВт)",
        "predict_btn": "🔮 Энергияны болжау",
        
        "solar_metric": "☀️ Күн қуаты",
        "wind_metric": "💨 Жел қуаты",
        "total_metric": "⚡ Жалпы энергия",
        "recommended": "✅ Ұсынылатын көз: **{source}**",
        "chart_title": "Энергия өндірісін салыстыру",
        "chart_y": "Қуат (кВт)",
        "chart_x": "Энергия көзі",
        "opt_header": "📊 Гибридті оңтайландыруды талдау",
        "opt_solar": "- **Күн қуаты**: {val} кВт",
        "opt_wind": "- **Жел қуаты**: {val} кВт",
        "opt_combined": "- **Қосынды қуат**: {val} кВт",
        "opt_better": "- **Тиімді көз**: {source} ({val} кВт)",
        "advisor_header": "🤖 AI Энергетикалық кеңесшісінің түсіндірмесі",
        
        # Tab 2: Forecast
        "select_date": "Болжау күнін таңдаңыз:",
        "forecast_btn": "📈 24 сағаттық LSTM болжамын жасау",
        "fc_actual": "Нақты қуат",
        "fc_predicted": "Болжалды күн қуаты (LSTM)",
        "fc_title": "24 сағаттық күн энергиясының болжамы ({date})",
        "fc_summary_title": "Тәуліктік болжам қорытындысы",
        "fc_total_actual": "Нақты өндірілген энергия:",
        "fc_total_pred": "Болжалды өндірілген энергия:",
        "fc_mae": "Болжамның орташа абсолютті қатесі (MAE):",
        "fc_peak": "Ең жоғары күн қуаты өндірілген уақыт:",
        "fc_no_lstm": "⚠️ LSTM болжамы сөндірулі. Бэкенд серверін тексеріңіз.",
        
        # Tab 3: Chatbot
        "chat_header": "🤖 Гибридті баламалы энергия жүйелері туралы сұраңыз!",
        "chat_placeholder": "Сұрағыңызды енгізіңіз (мысалы, 'Температура күн панеліне қалай әсер етеді?')",
        "chat_submit": "Жіберу",
        "chat_preset_title": "Дайын сұрақтар:",
        "chat_preset_1": "Неліктен жоғары температура күн панелінің қуатын азайтады?",
        "chat_preset_2": "Турбинаның іске қосылу және тоқтау жылдамдығы деген не?",
        "chat_preset_3": "Неліктен гибридті күн-жел жүйелері тиімдірек?",
        "chat_preset_4": "Ақылды желілерде батареялық сақтау қандай рөл атқарады?",
        
        # Errors & Status
        "api_error": "❌ API Қатесі {code}: {msg}",
        "invalid_json": "❌ API жарамсыз JSON қайтарды.",
        "missing_fields": "❌ API жауабында мына өрістер жетіспейді: {fields}",
        "invalid_types": "❌ API жауабындағы деректер типі жарамсыз: {error}",
        "api_response": "✅ API жауап деректері:",
        "solar_label": "Күн",
        "wind_label": "Жел",
        "timeout_error": "⏱️ API сұранысының уақыты бітті.",
        "conn_error": "🌐 API-ге қосылу мүмкін емес. Бэкенд сервері қосулы ма?",
        "unexpected_error": "❌ Күтпеген қате: {error}"
    }
}

# st.set_page_config must be the first Streamlit command
st.set_page_config(page_title="EcoPredict AI", page_icon="⚡", layout="wide")

# Inject Custom CSS for Premium Design (Glassmorphism & animations)
st.markdown("""
<style>
    /* Styling headers and fonts */
    h1, h2, h3 {
        font-family: 'Outfit', 'Inter', sans-serif !important;
        font-weight: 700 !important;
    }
    
    /* Background gradients */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 100%) !important;
        color: #c9d1d9 !important;
    }
    
    /* Custom Card Design & Streamlit Containers */
    .energy-card, [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(22, 27, 34, 0.7) !important;
        border: 1px solid rgba(240, 246, 252, 0.1) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
        backdrop-filter: blur(8px) !important;
        -webkit-backdrop-filter: blur(8px) !important;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    }
    .energy-card:hover, [data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-4px) !important;
        border-color: rgba(56, 139, 253, 0.4) !important;
        box-shadow: 0 12px 40px 0 rgba(56, 139, 253, 0.15) !important;
    }
    
    /* Responsive custom metrics inside cards */
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        margin-top: 5px;
        background: linear-gradient(90deg, #58a6ff 0%, #bc8cff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Custom submit button styling */
    .stButton>button {
        background: linear-gradient(90deg, #1f6feb 0%, #388bfd 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 14px rgba(56, 139, 253, 0.4) !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(56, 139, 253, 0.6) !important;
        background: linear-gradient(90deg, #388bfd 0%, #1f6feb 100%) !important;
    }
    
    /* Streamlit input sliders container */
    [data-testid="stSlider"] {
        padding: 10px 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# Language Selector in Sidebar
selected_lang = st.sidebar.selectbox("Language / Тіл", ["Қазақша", "English"])
lang = "kk" if selected_lang == "Қазақша" else "en"
texts = LOCALIZATION[lang]

# Cache status for loading models
models_status = {"solar": False, "wind": False, "lstm": False}

# API Status Indicator in Sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("API Status / Сервер күйі")

try:
    health_response = requests.get(HEALTH_URL, timeout=2)
    if health_response.status_code == 200:
        health_data = health_response.json()
        models_status["solar"] = health_data.get("models_loaded", {}).get("solar", False)
        models_status["wind"] = health_data.get("models_loaded", {}).get("wind", False)
        models_status["lstm"] = health_data.get("models_loaded", {}).get("lstm", False)
        
        if health_data.get("status") == "healthy":
            st.sidebar.markdown("🟢 **Active / Белсенді**")
        else:
            st.sidebar.markdown("🟡 **Degraded / Шектеулі**")
            
        st.sidebar.caption(
            f"Solar model: {'Loaded' if models_status['solar'] else 'Error'}\n"
            f"Wind model: {'Loaded' if models_status['wind'] else 'Error'}\n"
            f"LSTM model: {'Loaded' if models_status['lstm'] else 'Disabled'}"
            if lang == "en" else
            f"Күн моделі: {'Жүктелді' if models_status['solar'] else 'Қате'}\n"
            f"Жел моделі: {'Жүктелді' if models_status['wind'] else 'Қате'}\n"
            f"LSTM моделі: {'Жүктелді' if models_status['lstm'] else 'Сөндірілген'}"
        )
    else:
        st.sidebar.markdown("🔴 **Error / Қателік**")
except Exception:
    st.sidebar.markdown("🔴 **Offline / Қосылмаған**")

# Header Section
st.title(texts["title"])
st.subheader(texts["subtitle"])

def create_session_with_retries():
    """Create requests session with retry logic"""
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# Define Tabs
tab1, tab2, tab3 = st.tabs([texts["tab_predict"], texts["tab_forecast"], texts["tab_chat"]])

# ==================== TAB 1: PREDICT & OPTIMIZE ====================
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            st.markdown(f'<h3>{texts["solar_header"]}</h3>', unsafe_allow_html=True)
            irradiation = st.slider(texts["irradiation"], 0, 1500, 800)
            temp = st.slider(texts["temp"], -10, 60, 30)
            module = st.slider(texts["module_temp"], -10, 80, 35)
            hour = st.slider(texts["hour"], 0, 23, 12)
            day = st.slider(texts["day"], 1, 31, 15)
            month = st.slider(texts["month"], 1, 12, 6)
        
    with col2:
        with st.container(border=True):
            st.markdown(f'<h3>{texts["wind_header"]}</h3>', unsafe_allow_html=True)
            wind_speed = st.slider(texts["wind_speed"], 0, 25, 6)
            direction = st.slider(texts["direction"], 0, 360, 250)
            theoretical = st.slider(texts["theoretical"], 0, 2000, 700)
        
    if st.button(texts["predict_btn"], use_container_width=True):
        params = {
            "irradiation": irradiation,
            "temperature": temp,
            "module": module,
            "hour": hour,
            "day": day,
            "month": month,
            "wind_speed": wind_speed,
            "direction": direction,
            "theoretical": theoretical
        }
        
        try:
            session = create_session_with_retries()
            response = session.post(API_URL, json=params, timeout=10)
            
            if response.status_code != 200:
                try:
                    error_msg = response.json().get("detail", response.text)
                except:
                    error_msg = response.text
                st.error(texts["api_error"].format(code=response.status_code, msg=error_msg))
                st.stop()
                
            data = response.json()
            
            # Extract output values
            solar = float(data["solar_power"])
            wind = float(data["wind_power"])
            total = float(data["total_energy"])
            source = str(data["recommended_source"])
            
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
                
            mapped_source = texts["solar_label"] if source == "Solar" else texts["wind_label"]
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
            st.plotly_chart(fig, use_container_width=True)
            
            # Optimization Details card
            with st.container(border=True):
                st.markdown(f'<h3>{texts["opt_header"]}</h3>', unsafe_allow_html=True)
                st.write(texts["opt_solar"].format(val=round(solar, 2)))
                st.write(texts["opt_wind"].format(val=round(wind, 2)))
                st.write(texts["opt_combined"].format(val=round(total, 2)))
                st.write(texts["opt_better"].format(source=mapped_source, val=round(max(solar, wind), 2)))
            
            # AI advisor explanation via API
            explanation = "..."
            try:
                explain_response = session.post(EXPLAIN_URL, json={"source": source, "lang": lang}, timeout=5)
                if explain_response.status_code == 200:
                    explanation = explain_response.json().get("explanation", "")
            except Exception as e:
                explanation = f"Error: {e}"
                
            with st.container(border=True):
                st.markdown(f'<h3>{texts["advisor_header"]}</h3>', unsafe_allow_html=True)
                st.info(explanation)
            
        except requests.exceptions.Timeout:
            st.error(texts["timeout_error"])
        except requests.exceptions.ConnectionError:
            st.error(texts["conn_error"])
        except Exception as e:
            st.error(texts["unexpected_error"].format(error=str(e)))

# ==================== TAB 2: 24-HOUR FORECASTING ====================
with tab2:
    if not models_status["lstm"]:
        st.warning(texts["fc_no_lstm"])
    else:
        # Load features CSV file
        try:
            df_features = pd.read_csv("data/processed/build_features.csv")
            df_features["DATE_TIME"] = pd.to_datetime(df_features["DATE_TIME"])
            df_features["date_only"] = df_features["DATE_TIME"].dt.date
            
            # Group by dates with enough history (need at least 24 hours preceding the start of date)
            # Find the starting index for each date and select those with first_idx >= 24
            valid_dates = []
            for d in sorted(df_features["date_only"].unique()):
                date_recs = df_features[df_features["date_only"] == d]
                if len(date_recs) > 0 and date_recs.index[0] >= 24:
                    valid_dates.append(d)
                    
            if not valid_dates:
                st.error("No valid dates found in dataset with sufficient preceding history.")
            else:
                with st.container(border=True):
                    selected_date = st.selectbox(texts["select_date"], valid_dates, index=0)
                
                if st.button(texts["forecast_btn"], use_container_width=True):
                    # Extract target date records
                    date_records = df_features[df_features["date_only"] == selected_date]
                    
                    # Prepare sequences batch
                    sequences = []
                    for idx in date_records.index:
                        seq_df = df_features.loc[idx-24:idx-1, [
                            "IRRADIATION",
                            "AMBIENT_TEMPERATURE",
                            "MODULE_TEMPERATURE",
                            "hour",
                            "day",
                            "month"
                        ]]
                        sequences.append(seq_df.values.tolist())
                        
                    # Call Forecast Batch API
                    try:
                        with st.spinner("Running deep learning forecast..."):
                            session = create_session_with_retries()
                            resp = session.post(FORECAST_URL, json={"sequences": sequences}, timeout=15)
                            
                            if resp.status_code == 200:
                                preds = resp.json().get("predictions", [])
                                actuals = date_records["AC_POWER"].values.tolist()
                                hours = pd.to_datetime(date_records["DATE_TIME"]).dt.strftime("%H:%M").tolist()
                                
                                # Make comparison chart
                                fig_fc = go.Figure()
                                fig_fc.add_trace(go.Scatter(
                                    x=hours, y=actuals,
                                    mode='lines+markers',
                                    name=texts["fc_actual"],
                                    line=dict(color='#4CAF50', width=3)
                                ))
                                fig_fc.add_trace(go.Scatter(
                                    x=hours, y=preds,
                                    mode='lines+markers',
                                    name=texts["fc_predicted"],
                                    line=dict(color='#FF9800', width=3, dash='dash')
                                ))
                                fig_fc.update_layout(
                                    title=texts["fc_title"].format(date=selected_date),
                                    xaxis_title="Time" if lang == "en" else "Уақыты",
                                    yaxis_title="Power (kW)" if lang == "en" else "Қуат (кВт)",
                                    plot_bgcolor="rgba(0,0,0,0)",
                                    paper_bgcolor="rgba(0,0,0,0)",
                                    font_color="#c9d1d9",
                                    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
                                )
                                st.plotly_chart(fig_fc, use_container_width=True)
                                
                                # Summary Metrics
                                tot_actual = sum(actuals)
                                tot_pred = sum(preds)
                                mae = np.mean(np.abs(np.array(actuals) - np.array(preds)))
                                peak_hour = hours[np.argmax(preds)]
                                
                                s_col1, s_col2, s_col3, s_col4 = st.columns(4)
                                with s_col1:
                                    st.markdown(f"""
                                    <div class="energy-card">
                                        <div style="font-size:0.85rem;color:#8b949e;">{texts["fc_total_actual"]}</div>
                                        <div class="metric-value">{round(tot_actual, 2)} kW</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                with s_col2:
                                    st.markdown(f"""
                                    <div class="energy-card">
                                        <div style="font-size:0.85rem;color:#8b949e;">{texts["fc_total_pred"]}</div>
                                        <div class="metric-value" style="background: linear-gradient(90deg, #FF9800 0%, #FFB74D 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{round(tot_pred, 2)} kW</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                with s_col3:
                                    st.markdown(f"""
                                    <div class="energy-card">
                                        <div style="font-size:0.85rem;color:#8b949e;">{texts["fc_mae"]}</div>
                                        <div class="metric-value" style="background: linear-gradient(90deg, #f44336 0%, #ef5350 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{round(mae, 2)} kW</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                with s_col4:
                                    st.markdown(f"""
                                    <div class="energy-card">
                                        <div style="font-size:0.85rem;color:#8b949e;">{texts["fc_peak"]}</div>
                                        <div class="metric-value" style="background: linear-gradient(90deg, #00BCD4 0%, #4DD0E1 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{peak_hour}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.error(f"Error calling forecast API: {resp.status_code}")
                    except Exception as e:
                        st.error(f"Forecasting task failed: {e}")
        except Exception as e:
            st.error(f"Could not load feature dataset: {e}")

# ==================== TAB 3: SMART CHATBOT ====================
with tab3:
    st.markdown(f'<h3>{texts["chat_header"]}</h3>', unsafe_allow_html=True)
    
    # Preset Questions as buttons in a neat row
    st.write(texts["chat_preset_title"])
    preset_cols = st.columns(4)
    query_to_submit = ""
    should_submit = False
    
    with preset_cols[0]:
        if st.button(texts["chat_preset_1"], key="p1", use_container_width=True):
            query_to_submit = texts["chat_preset_1"]
            should_submit = True
    with preset_cols[1]:
        if st.button(texts["chat_preset_2"], key="p2", use_container_width=True):
            query_to_submit = texts["chat_preset_2"]
            should_submit = True
    with preset_cols[2]:
        if st.button(texts["chat_preset_3"], key="p3", use_container_width=True):
            query_to_submit = texts["chat_preset_3"]
            should_submit = True
    with preset_cols[3]:
        if st.button(texts["chat_preset_4"], key="p4", use_container_width=True):
            query_to_submit = texts["chat_preset_4"]
            should_submit = True
            
    # Text input for custom query
    if "chat_input_val" not in st.session_state:
        st.session_state.chat_input_val = ""
        
    if should_submit:
        st.session_state.chat_input_val = query_to_submit
        
    user_query = st.text_input(
        texts["chat_placeholder"], 
        value=st.session_state.chat_input_val, 
        key="chat_query_input",
        placeholder=texts["chat_placeholder"]
    )
    
    if st.button(texts["chat_submit"], key="chat_submit_btn"):
        if user_query.strip():
            query_to_submit = user_query
            should_submit = True
        else:
            st.warning("Please type a valid question." if lang == "en" else "Сұрағыңызды енгізіңіз.")
            
    if should_submit and query_to_submit.strip():
        try:
            with st.spinner("Searching knowledge base..."):
                session = create_session_with_retries()
                resp = session.post(CHAT_URL, json={"query": query_to_submit, "lang": lang}, timeout=10)
                
                if resp.status_code == 200:
                    ans = resp.json().get("response", "")
                    
                    with st.container(border=True):
                        st.markdown(f"**Query / Сұрақ:** {query_to_submit}")
                        st.markdown("---")
                        st.markdown(f"**AI Advisor Response / AI Кеңесші жауабы:**")
                        st.write(ans)
                else:
                    st.error(f"Error from Chat API: {resp.status_code}")
        except Exception as e:
            st.error(f"Failed to communicate with Chatbot API: {e}")