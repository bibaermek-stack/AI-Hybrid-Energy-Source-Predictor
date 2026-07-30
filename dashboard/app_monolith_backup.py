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
SOLARMAN_PROCESS_URL = os.getenv("SOLARMAN_PROCESS_URL", "http://127.0.0.1:8001/solarman/process")
SOLARMAN_ROI_URL = os.getenv("SOLARMAN_ROI_URL", "http://127.0.0.1:8001/solarman/roi")
SOLARMAN_WEATHER_URL = os.getenv("SOLARMAN_WEATHER_URL", "http://127.0.0.1:8001/solarman/weather")
SOLARMAN_ALERT_URL = os.getenv("SOLARMAN_ALERT_URL", "http://127.0.0.1:8001/solarman/alert")
SOLARMAN_FC_URL = os.getenv("SOLARMAN_FC_URL", "http://127.0.0.1:8001/solarman/forecast")
SOLARMAN_LIVE_URL = os.getenv("SOLARMAN_LIVE_URL", "http://127.0.0.1:8001/solarman/live")
SOLARMAN_HISTORY_URL = os.getenv("SOLARMAN_HISTORY_URL", "http://127.0.0.1:8001/solarman/history")
SOLARMAN_STATUS_URL = os.getenv("SOLARMAN_STATUS_URL", "http://127.0.0.1:8001/solarman/status")
SOLARMAN_CONFIGURE_URL = os.getenv("SOLARMAN_CONFIGURE_URL", "http://127.0.0.1:8001/solarman/configure")

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
        "opt_solar": "- **Solar Available**: {val} kW",
        "opt_wind": "- **Wind Available**: {val} kW",
        "opt_combined": "- **Combined Available**: {val} kW",
        "opt_better": "- **Recommended**: {source}",
        "opt_dispatch": "Dispatch controls",
        "opt_load": "Load demand (kW, 0 = full offtake)",
        "opt_battery": "Battery discharge capacity (kW)",
        "opt_strategy": "Dispatch strategy",
        "opt_solar_cost": "Solar relative LCOE",
        "opt_wind_cost": "Wind relative LCOE",
        "hybrid_label": "Hybrid",
        "opt_shares": "- **Shares** — Solar: {s:.0%} · Wind: {w:.0%} · Mix index: {h:.0%}",
        "opt_reliability": "- **Reliability index**: {val:.1%}",
        "opt_shortfall": "- **Shortfall**: {val} kW",
        "opt_curtailment": "- **Curtailment**: {val} kW",
        "opt_battery_used": "- **Battery used**: {val} kW",
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
        "unexpected_error": "❌ Unexpected error: {error}",
        
        "tab_solarman": "📊 Solarman & Economics",
        "tab_diagnostics": "🛠️ Fault Diagnostics",
        "tab_training": "🧠 Model Trainer Hub",
        "tab_3d_model": "📐 3D Inverter Model",
        "sm_dc_cap": "Nominal DC Capacity (kWp)",
        "sm_irrad": "Solar Irradiance (W/m²)",
        "sm_amb_temp": "Ambient Temp (°C)",
        "sm_capex": "Initial CAPEX (KZT)",
        "sm_opex": "Annual OPEX (KZT)",
        "sm_tariff": "Electricity Tariff (KZT/kWh)",
        "sm_inflation": "Tariff Inflation Rate (%)",
        "sm_degradation": "Panel Degradation Rate (%)",
        "sm_lifetime": "System Lifetime (Years)",
        "sm_calc_btn": "Calculate Metrics",
        "sm_payload_lbl": "Paste Raw Solarman OpenAPI JSON Payload (Optional)",
        "sm_weather_header": "Turkistan, Kazakhstan Forecast",
        "sm_weather_temp": "Temperature: {val}°C",
        "sm_weather_cloud": "Cloud Cover: {val}%",
        "sm_weather_uv": "UV Index: {val}",
        "sm_pr_header": "Performance Ratio Results",
        "sm_financial_header": "Financial ROI Projection",
        "sm_env_header": "Environmental Benefits Equivalent",
        "sm_tg_header": "Telegram Bot Alerts",
        "sm_tg_token": "Telegram Bot Token (Optional)",
        "sm_tg_chat_id": "Telegram Chat ID (Optional)",
        "sm_alert_btn": "Check Anomaly & Alert",
        "sm_co2_offset": "CO₂ Offset: {val} metric tons",
        "sm_trees": "Mature trees grown: {val}",
        "sm_miles": "Avoided vehicle miles: {val} miles",
        "sm_gas": "Avoided gasoline: {val} gallons",
        "sm_payback_lbl": "Dynamic Payback: {val} years",
        "sm_roi_lbl": "ROI: {val}%",
        "sm_ann_sav_lbl": "Average Annual Savings: {val} KZT",
        "sm_fc_header": "Live 24-Hour Production Forecast (Turkistan)",
        "sm_fc_loading": "Running generation models against weather forecast...",
        "sm_fc_alert_low": "⚠️ Warning: Tomorrow is expected to have very low solar generation due to heavy cloud cover!",
        "sm_fc_alert_high": "☀️ Excellent: High solar output expected tomorrow with clear skies.",
        "sm_active_power_lbl": "Simulated Active Power (kW)",
        "sm_e_today_lbl": "Simulated Daily Generation (kWh)",
        "sm_e_total_lbl": "Simulated Total Generation (kWh)",
        "sm_module_temp_lbl": "Simulated Module Temp (°C)",
        "sm_status_lbl": "Simulated Device Status",
        "sm_status_online": "Online / Active",
        "sm_status_offline": "Offline / Error",
        "sm_fault_lbl": "Simulated Fault Code"
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
        "opt_solar": "- **Қолжетімді күн**: {val} кВт",
        "opt_wind": "- **Қолжетімді жел**: {val} кВт",
        "opt_combined": "- **Қосынды қолжетімді**: {val} кВт",
        "opt_better": "- **Ұсыныс**: {source}",
        "opt_dispatch": "Диспетчерлеу параметрлері",
        "opt_load": "Жүктеме (кВт, 0 = толық алу)",
        "opt_battery": "Батарея разряд қуаты (кВт)",
        "opt_strategy": "Диспетчерлеу стратегиясы",
        "opt_solar_cost": "Күн салыстырмалы LCOE",
        "opt_wind_cost": "Жел салыстырмалы LCOE",
        "hybrid_label": "Гибрид",
        "opt_shares": "- **Үлестер** — Күн: {s:.0%} · Жел: {w:.0%} · Араласу: {h:.0%}",
        "opt_reliability": "- **Сенімділік индексі**: {val:.1%}",
        "opt_shortfall": "- **Тапшылық**: {val} кВт",
        "opt_curtailment": "- **Шектеу (curtailment)**: {val} кВт",
        "opt_battery_used": "- **Батарея қолданылды**: {val} кВт",
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
        "conn_error": "🌐 API-ге қосылу мүмкен емес. Бэкенд сервері қосулы ма?",
        "unexpected_error": "❌ Күтпеген қате: {error}",
        
        "tab_solarman": "📊 Solarman & Economics",
        "tab_diagnostics": "🛠️ Ақаулықтарды диагностикалау",
        "tab_training": "🧠 Модельдерді оқыту орталығы",
        "tab_3d_model": "📐 3D Инвертор моделі",
        "sm_dc_cap": "Номиналды Тұрақты Тоқ Қуаты (кВтп)",
        "sm_irrad": "Күн Сәулесінің Түсуі (Вт/м²)",
        "sm_amb_temp": "Қоршаған Орта Температурасы (°C)",
        "sm_capex": "Бастапқы CAPEX (теңге)",
        "sm_opex": "Жылдық OPEX (теңге)",
        "sm_tariff": "Электр Тарифі (теңге/кВтсағ)",
        "sm_inflation": "Тарифтің Жылдық Инфляциясы (%)",
        "sm_degradation": "Панельдердің Тозу Жылдамдығы (%)",
        "sm_lifetime": "Жүйенің Қызмет Ету Мерзімі (Жыл)",
        "sm_calc_btn": "Көрсеткіштерді Есептеу",
        "sm_payload_lbl": "Solarman OpenAPI JSON Деректерін Енгізу (Міндетті емес)",
        "sm_weather_header": "Түркістан, Қазақстан Ауа Райы",
        "sm_weather_temp": "Температура: {val}°C",
        "sm_weather_cloud": "Бұлттылық: {val}%",
        "sm_weather_uv": "Ультракүлгін (UV) индекс: {val}",
        "sm_pr_header": "Пайдалы Әсер Коэффициенті (PR)",
        "sm_financial_header": "Қаржылық ROI Болжамы",
        "sm_env_header": "Экологиялық Салдар Баламасы",
        "sm_tg_header": "Telegram Бот Хабарламалары",
        "sm_tg_token": "Telegram Бот Токені (Міндетті емес)",
        "sm_tg_chat_id": "Telegram Чат ID-сі (Міндетті емес)",
        "sm_alert_btn": "Қателікті Тексеру және Ескерту Жіберу",
        "sm_co2_offset": "CO₂ азайту: {val} тонна",
        "sm_trees": "Егілген жетілген ағаштар: {val}",
        "sm_miles": "Болдырылмаған автокөлік жолы: {val} миль",
        "sm_gas": "Болдырылмаған бензин шығыны: {val} галлон",
        "sm_payback_lbl": "Динамикалық өтелу мерзімі: {val} жыл",
        "sm_roi_lbl": "ROI: {val}%",
        "sm_ann_sav_lbl": "Орташа жылдық үнемдеу: {val} теңге",
        "sm_fc_header": "Түркістан бойынша алдағы 24 сағаттық өндіріс болжамы",
        "sm_fc_loading": "Ауа райы болжамы негізінде энергия өндірісін есептеу...",
        "sm_fc_alert_low": "⚠️ Ескерту: Ертең бұлттылықтың көп болуына байланысты күн энергиясын өндіру деңгейі өте төмен болады деп күтілуде!",
        "sm_fc_alert_high": "☀️ Тамаша: Ертең ашық күн болады және жоғары күн энергиясы өндіріледі деп күтілуде.",
        "sm_active_power_lbl": "Ағымдағы белсенді қуат (кВт)",
        "sm_e_today_lbl": "Бүгін өндірілген энергия (кВтсағ)",
        "sm_e_total_lbl": "Жалпы өндірілген энергия (кВтсағ)",
        "sm_module_temp_lbl": "Панель температурасы (°C)",
        "sm_status_lbl": "Құрылғының байланыс күйі",
        "sm_status_online": "Желіде / Белсенді",
        "sm_status_offline": "Байланыссыз / Қате",
        "sm_fault_lbl": "Ақаулық коды"
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

@st.cache_resource
def load_clean_dirty_model():
    """Load the clean vs dirty classifier model with thread pinning to prevent memory errors"""
    import os
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
    os.environ["NUMEXPR_NUM_THREADS"] = "1"
    import tensorflow as tf
    # Try looking in absolute paths and fallback to relative path
    model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "artifacts", "clean_dirty_model.h5"))
    if not os.path.exists(model_path):
        model_path = "artifacts/clean_dirty_model.h5"
    return tf.keras.models.load_model(model_path)

@st.cache_resource
def load_yolo_model():
    """Load the YOLOv11 nano model for solar panel fault detection"""
    import os
    from ultralytics import YOLO
    model_path = os.path.abspath("yolo_fault_detection/runs/runs/detect/train/weights/best.pt")
    return YOLO(model_path)

# Define Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([texts["tab_predict"], texts["tab_forecast"], texts["tab_solarman"], texts["tab_diagnostics"], texts["tab_training"], texts["tab_3d_model"]])

# ==================== TAB 1: PREDICT & OPTIMIZE ====================
with tab1:
    if st.button("🔌 Load Solarman Telemetry Data / Solarman телеметриясын жүктеу", key="load_sm_tab1", use_container_width=True):
        st.session_state["irradiation_val"] = int(st.session_state.get("sm_irrad_val", 900))
        st.session_state["temp_val"] = int(st.session_state.get("sm_amb_temp_val", 30))
        st.session_state["module_val"] = int(st.session_state.get("sm_module_temp_val", 38))
        st.success("Solarman data successfully loaded into sliders!" if lang == "en" else "Solarman деректері жүгірткілерге сәтті жүктелді!")
        st.rerun()

    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            st.markdown(f'<h3>{texts["solar_header"]}</h3>', unsafe_allow_html=True)
            irradiation = st.slider(texts["irradiation"], 0, 1500, st.session_state.get("irradiation_val", 800))
            temp = st.slider(texts["temp"], -10, 60, st.session_state.get("temp_val", 30))
            module = st.slider(texts["module_temp"], -10, 80, st.session_state.get("module_val", 35))
            hour = st.slider(texts["hour"], 0, 23, 12)
            day = st.slider(texts["day"], 1, 31, 15)
            month = st.slider(texts["month"], 1, 12, 6)
        
    with col2:
        with st.container(border=True):
            st.markdown(f'<h3>{texts["wind_header"]}</h3>', unsafe_allow_html=True)
            wind_speed = st.slider(texts["wind_speed"], 0, 25, 6)
            direction = st.slider(texts["direction"], 0, 360, 250)
            theoretical = st.slider(texts["theoretical"], 0, 2000, 700)

    with st.container(border=True):
        st.markdown(f'<h3>{texts["opt_dispatch"]}</h3>', unsafe_allow_html=True)
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
            st.plotly_chart(fig, use_container_width=True)
            
            # Optimization Details card
            with st.container(border=True):
                st.markdown(f'<h3>{texts["opt_header"]}</h3>', unsafe_allow_html=True)
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

        # ==================== LIVE 24-HOUR FORECAST MONITORING (TAB 2) ====================
        st.markdown("---")
        st.markdown(f'<h3>{texts["sm_fc_header"]}</h3>', unsafe_allow_html=True)
        
        with st.spinner(texts["sm_fc_loading"]):
            try:
                from datetime import datetime
                sm_dc_cap_val = st.session_state.get("sm_dc_cap_val", 50.0)
                fc_resp = requests.get(f"{SOLARMAN_FC_URL}?dc_capacity_kwp={sm_dc_cap_val}", timeout=10)
                if fc_resp.status_code == 200:
                    fc_data = fc_resp.json().get("forecasts", [])
                    
                    fc_times = [datetime.fromisoformat(item["time"]).strftime("%H:%M") for item in fc_data]
                    fc_powers = [item["predicted_power_kw"] for item in fc_data]
                    fc_clouds = [item["cloud_cover"] for item in fc_data]
                    fc_temps = [item["temperature"] for item in fc_data]
                    
                    # Check for low generation warning tomorrow (daytime hours 8:00 - 17:00)
                    daytime_clouds = [c for item, c in zip(fc_data, fc_clouds) if 8 <= datetime.fromisoformat(item["time"]).hour <= 17]
                    avg_clouds = np.mean(daytime_clouds) if daytime_clouds else 0.0
                    
                    if avg_clouds > 70.0:
                        st.warning(texts["sm_fc_alert_low"])
                    elif avg_clouds < 30.0 and len(daytime_clouds) > 0:
                        st.success(texts["sm_fc_alert_high"])
                        
                    # Plotly Double Y-Axis Chart
                    fig_fc = go.Figure()
                    
                    # Bar for predicted solar power
                    fig_fc.add_trace(go.Bar(
                        x=fc_times, y=fc_powers,
                        name="Predicted Power (kW)" if lang == "en" else "Болжалды қуат (кВт)",
                        marker_color="#FF9800",
                        opacity=0.75
                    ))
                    
                    # Line for Cloud Cover
                    fig_fc.add_trace(go.Scatter(
                        x=fc_times, y=fc_clouds,
                        name="Cloud Cover (%)" if lang == "en" else "Бұлттылық (%)",
                        yaxis="y2",
                        line=dict(color="#90A4AE", width=2, dash="dot")
                    ))
                    
                    # Line for Temperature
                    fig_fc.add_trace(go.Scatter(
                        x=fc_times, y=fc_temps,
                        name="Temperature (°C)" if lang == "en" else "Температура (°C)",
                        yaxis="y2",
                        line=dict(color="#EF5350", width=2)
                    ))
                    
                    fig_fc.update_layout(
                        title="Live 24-Hour Solar Production & Weather Forecast (Turkistan)" if lang == "en" else "Күн өндірісі мен ауа райының 24 сағаттық болжамы (Түркістан)",
                        xaxis_title="Time (HH:MM)" if lang == "en" else "Уақыты (HH:MM)",
                        yaxis=dict(
                            title=dict(
                                text="Predicted Power (kW)" if lang == "en" else "Болжалды қуат (кВт)",
                                font=dict(color="#FF9800")
                            ),
                            tickfont=dict(color="#FF9800")
                        ),
                        yaxis2=dict(
                            title=dict(
                                text="Clouds (%) / Temp (°C)" if lang == "en" else "Бұлттылық (%) / Темп (°C)",
                                font=dict(color="#90A4AE")
                            ),
                            tickfont=dict(color="#90A4AE"),
                            overlaying="y",
                            side="right"
                        ),
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font_color="#c9d1d9",
                        legend=dict(x=0.01, y=0.99)
                    )
                    
                    st.plotly_chart(fig_fc, use_container_width=True, key="fc_chart_tab2")
                else:
                    st.error(f"Could not load live forecast in Tab 2. API returned: {fc_resp.status_code}")
            except Exception as e:
                st.error(f"Live weather forecast monitoring is temporarily offline in Tab 2: {e}")

# ==================== TAB 3: SOLARMAN & ECONOMICS ====================
with tab3:
    st.markdown(f'<h3>{texts["tab_solarman"]}</h3>', unsafe_allow_html=True)

    # ----- LIVE DEVICE via Solarman OpenAPI (Inverter2501221272) -----
    st.markdown(
        "### 🔌 Device Data — **Inverter2501221272**"
        if lang == "en"
        else "### 🔌 Құрылғы деректері — **Inverter2501221272**"
    )
    st.caption(
        "Solarman OpenAPI · Basic / Version / Electricity Generation + charts"
        if lang == "en"
        else "Solarman OpenAPI · Негізгі / Нұсқа / Электр өндірісі + графиктер"
    )

    with st.expander(
        "🔑 Solarman API credentials / API кілттері",
        expanded=not bool(os.getenv("SOLARMAN_APP_ID")),
    ):
        c1, c2 = st.columns(2)
        with c1:
            sm_app_id = st.text_input("APP ID (SOLARMAN_APP_ID)", value=os.getenv("SOLARMAN_APP_ID", ""), key="sm_app_id")
            sm_app_secret = st.text_input("APP SECRET", type="password", value=os.getenv("SOLARMAN_APP_SECRET", ""), key="sm_app_secret")
            sm_email = st.text_input("Email (Solarman Smart)", value=os.getenv("SOLARMAN_EMAIL", ""), key="sm_email")
        with c2:
            sm_password = st.text_input("Password", type="password", value=os.getenv("SOLARMAN_PASSWORD", ""), key="sm_password")
            sm_dev_sn = st.text_input("Device SN", value=os.getenv("SOLARMAN_DEVICE_SN", "2501221272"), key="sm_dev_sn")
            sm_dev_id = st.text_input("Device ID (optional)", value=os.getenv("SOLARMAN_DEVICE_ID", ""), key="sm_dev_id")
            sm_pw_hash = st.checkbox("Password already SHA-256", value=False, key="sm_pw_sha")

        cfg_col1, cfg_col2, cfg_col3 = st.columns(3)
        with cfg_col1:
            save_api = st.button(
                "💾 Save & test API login" if lang == "en" else "💾 Сақтау + API логин тест",
                use_container_width=True,
                key="sm_save_api",
            )
        with cfg_col2:
            fetch_live = st.button(
                "🔄 Load LIVE from API" if lang == "en" else "🔄 API-ден LIVE жүктеу",
                use_container_width=True,
                type="primary",
                key="sm_live_fetch",
            )
        with cfg_col3:
            force_demo = st.checkbox(
                "Demo only (no API)" if lang == "en" else "Тек demo (API жоқ)",
                value=False,
                key="sm_force_demo",
            )

        if save_api:
            if not (sm_app_id and sm_app_secret and sm_email and sm_password):
                st.error("APP ID, SECRET, email, password — бәрі міндетті / all required")
            else:
                try:
                    cfg_resp = requests.post(
                        SOLARMAN_CONFIGURE_URL,
                        json={
                            "app_id": sm_app_id,
                            "app_secret": sm_app_secret,
                            "email": sm_email,
                            "password": sm_password,
                            "device_sn": sm_dev_sn or "2501221272",
                            "device_id": sm_dev_id or None,
                            "base_url": os.getenv("SOLARMAN_BASE_URL", "https://globalapi.solarmanpv.com"),
                            "password_is_sha256": sm_pw_hash,
                            "test_auth": True,
                        },
                        timeout=30,
                    )
                    if cfg_resp.status_code == 200:
                        body = cfg_resp.json()
                        if body.get("auth_ok"):
                            st.success(
                                f"✅ API login OK · SN={body.get('device_sn')} · id={body.get('device_id')}"
                            )
                            st.session_state["sm_api_ready"] = True
                        else:
                            st.error(f"Auth failed: {body.get('auth_error') or body}")
                            st.session_state["sm_api_ready"] = False
                    else:
                        # Backend offline — configure in-process
                        try:
                            from src.utils.solarman_client import set_runtime_credentials, SolarmanClient
                            set_runtime_credentials(
                                app_id=sm_app_id,
                                app_secret=sm_app_secret,
                                email=sm_email,
                                password=sm_password,
                                device_sn=sm_dev_sn,
                                device_id=sm_dev_id or "",
                                password_is_sha256=sm_pw_hash,
                            )
                            SolarmanClient().authenticate(force=True)
                            st.success("✅ API login OK (local client, FastAPI offline)")
                            st.session_state["sm_api_ready"] = True
                        except Exception as le:
                            st.error(f"Configure failed ({cfg_resp.status_code}): {cfg_resp.text} | local: {le}")
                except Exception as e:
                    try:
                        from src.utils.solarman_client import set_runtime_credentials, SolarmanClient
                        set_runtime_credentials(
                            app_id=sm_app_id,
                            app_secret=sm_app_secret,
                            email=sm_email,
                            password=sm_password,
                            device_sn=sm_dev_sn,
                            device_id=sm_dev_id or "",
                            password_is_sha256=sm_pw_hash,
                        )
                        SolarmanClient().authenticate(force=True)
                        st.success("✅ API login OK (local client)")
                        st.session_state["sm_api_ready"] = True
                    except Exception as le:
                        st.error(f"API unreachable / auth failed: {e} | {le}")

        # Status badge
        try:
            st_stat = requests.get(SOLARMAN_STATUS_URL, timeout=3)
            if st_stat.status_code == 200:
                s = st_stat.json()
                if s.get("credentials_configured"):
                    st.caption(f"API ready · SN={s.get('device_sn')} · {s.get('base_url')}")
                else:
                    st.caption("⚠️ API credentials not configured yet")
        except Exception:
            st.caption("⚠️ FastAPI :8001 offline — local client used if credentials entered")

    # Auto-load live on first open + manual refresh
    auto_load = "sm_live_dash" not in st.session_state
    if fetch_live or auto_load or force_demo:
        with st.spinner("Solarman API-ден жүктелуде..." if lang == "kk" else "Loading from Solarman API..."):
            live_payload = None
            live_err = None
            q = f"?demo={'true' if force_demo else 'false'}&force_demo={'true' if force_demo else 'false'}"
            try:
                r = requests.get(f"{SOLARMAN_LIVE_URL}{q}", timeout=45)
                if r.status_code == 200:
                    live_payload = r.json()
                else:
                    live_err = f"HTTP {r.status_code}: {r.text[:400]}"
            except Exception as e:
                live_err = str(e)

            if live_payload is None:
                try:
                    from src.utils.solarman_client import get_live_dashboard, set_runtime_credentials
                    if sm_app_id and sm_app_secret and sm_email and sm_password:
                        set_runtime_credentials(
                            app_id=sm_app_id,
                            app_secret=sm_app_secret,
                            email=sm_email,
                            password=sm_password,
                            device_sn=sm_dev_sn,
                            device_id=sm_dev_id or "",
                            password_is_sha256=sm_pw_hash,
                        )
                    live_payload = get_live_dashboard(
                        use_demo_if_no_creds=force_demo,
                        force_demo=force_demo,
                    )
                    live_err = None
                except Exception as e2:
                    live_err = f"{live_err} | local: {e2}"

            if live_payload:
                st.session_state["sm_live_dash"] = live_payload
                st.session_state.pop("sm_live_err", None)
            elif live_err:
                st.session_state["sm_live_err"] = live_err

    dash = st.session_state.get("sm_live_dash")
    if st.session_state.get("sm_live_err") and not dash:
        st.error(st.session_state["sm_live_err"])

    if dash:
        if dash.get("warning"):
            st.warning(dash["warning"])
        src = dash.get("source", "?")
        st.caption(
            f"Source: **{src}** · {dash.get('fetched_at', '')}"
            if lang == "en"
            else f"Дереккөз: **{src}** · {dash.get('fetched_at', '')}"
        )

        basic = dash.get("basic", {})
        version = dash.get("version", {})
        gen = dash.get("generation", {})
        ac_kw = float(gen.get("ac_active_power_kw") or 0)
        dc_kw = float(gen.get("dc_total_kw") or 0)
        rated = float(basic.get("rated_power_kw") or 25) or 25.0

        # KPI row — like portal header
        k1, k2, k3, k4, k5, k6 = st.columns(6)
        k1.metric("SN", str(basic.get("sn", "—")))
        k2.metric("Rated", f"{rated:.0f} kW")
        k3.metric("AC Power", f"{ac_kw:.3f} kW")
        k4.metric("DC Total", f"{dc_kw:.3f} kW")
        k5.metric("E-Today", f"{gen.get('e_today_kwh', 0)} kWh")
        k6.metric("E-Total", f"{gen.get('e_total_kwh', 0)} kWh")

        # Load bar DC→AC (screenshot style)
        load_pct = min(100.0, max(0.0, (ac_kw / rated) * 100.0))
        st.progress(load_pct / 100.0, text=f"DC/AC load · {load_pct:.1f}% of rated ({ac_kw:.2f}/{rated:.0f} kW) · {basic.get('grid_status') or ''}")

        # Basic + Version (screenshot layout — 3-col dense)
        st.markdown("#### Basic Information" if lang == "en" else "#### Негізгі ақпарат")
        bi1, bi2, bi3 = st.columns(3)
        with bi1:
            st.markdown(f"**SN:** {basic.get('sn')}")
            st.markdown(f"**General settings:** {basic.get('general_settings')}")
            st.markdown(f"**MPPT No:** {basic.get('mppt_no')}")
        with bi2:
            st.markdown(f"**Inverter Type:** {basic.get('inverter_type')}")
            st.markdown(f"**Production Compliance Country:** {basic.get('production_compliance_country')}")
            st.markdown(f"**Grid:** {basic.get('grid_status') or '—'}")
        with bi3:
            st.markdown(f"**Product Type:** {basic.get('product_type')}")
            st.markdown(f"**Rated Power:** {rated:.0f} kW")
            st.markdown(f"**Device ID:** {basic.get('device_id')} · status `{basic.get('status')}`")

        st.markdown("#### Version Information" if lang == "en" else "#### Нұсқа ақпараты")
        v1, v2, v3 = st.columns(3)
        with v1:
            st.markdown(f"**Protocol Version:** {version.get('protocol_version')}")
            st.markdown(f"**Control SW v1:** {version.get('control_sw_v1')}")
            st.markdown(f"**Arc Board FW:** {version.get('arc_board_fw')}")
        with v2:
            st.markdown(f"**MAIN:** {version.get('main')}")
            st.markdown(f"**Control SW v2:** {version.get('control_sw_v2')}")
        with v3:
            st.markdown(f"**HMI:** {version.get('hmi')}")
            st.markdown(f"**Comm CPU SW:** {version.get('comm_cpu_sw')}")

        st.markdown("#### Electricity Generation" if lang == "en" else "#### Электр өндірісі")
        g1, gmid, g2 = st.columns([2, 1, 2])
        with g1:
            dc_df = pd.DataFrame(gen.get("dc") or [])
            if not dc_df.empty:
                show_dc = dc_df.copy()
                show_dc["Power"] = show_dc["power_kw"].apply(
                    lambda x: f"{x*1000:.2f} W" if float(x) < 1 and float(x) > 0 else f"{float(x):.3f} kW"
                )
                # Portal shows mixed W for small — we keep kW consistently
                st.dataframe(
                    show_dc.rename(columns={
                        "mppt": "DC",
                        "voltage_v": "Voltage",
                        "current_a": "Current",
                        "power_kw": "Power (kW)",
                    })[["DC", "Voltage", "Current", "Power (kW)"]],
                    use_container_width=True,
                    hide_index=True,
                    height=280,
                )
        with gmid:
            st.markdown("")
            st.markdown("### 🔋 DC/AC")
            st.metric("Active AC", f"{ac_kw:.3f} kW")
            st.metric("Temp", f"{gen.get('temperature_c', 0)} °C")
            # simple efficiency
            eff = (ac_kw / dc_kw * 100.0) if dc_kw > 0.01 else 0.0
            st.metric("η (AC/DC)", f"{eff:.1f} %")
        with g2:
            ac_df = pd.DataFrame(gen.get("ac") or [])
            if not ac_df.empty:
                ac_show = ac_df.copy()
                if "frequency_hz" in ac_show.columns:
                    ac_show["frequency_hz"] = ac_show["frequency_hz"].apply(
                        lambda x: f"{x:.2f} Hz" if x is not None and x == x else "—"
                    )
                st.dataframe(
                    ac_show.rename(columns={
                        "phase": "AC",
                        "voltage_v": "Voltage",
                        "current_a": "Current",
                        "frequency_hz": "Frequency",
                        "power_kw": "Power (kW)",
                    }),
                    use_container_width=True,
                    hide_index=True,
                    height=280,
                )

        # Charts
        hist = dash.get("history") or []
        if hist:
            hdf = pd.DataFrame(hist)
            # Drop all-zero leading noise optionally keep all
            if "time" in hdf.columns:
                try:
                    hdf = hdf.sort_values("time")
                except Exception:
                    pass
            st.markdown("#### 📈 Charts / Графиктер")
            c1, c2 = st.columns(2)
            with c1:
                if "time" in hdf.columns and "ac_power_kw" in hdf.columns:
                    fig_p = go.Figure()
                    fig_p.add_trace(go.Scatter(
                        x=hdf["time"], y=hdf["ac_power_kw"],
                        name="AC kW", mode="lines",
                        line=dict(color="#388bfd", width=2),
                        fill="tozeroy",
                    ))
                    if "dc_power_kw" in hdf.columns:
                        fig_p.add_trace(go.Scatter(
                            x=hdf["time"], y=hdf["dc_power_kw"],
                            name="DC kW", mode="lines",
                            line=dict(color="#FDB462", width=2),
                        ))
                    fig_p.update_layout(
                        title="AC / DC Power (today)",
                        height=360,
                        margin=dict(l=20, r=20, t=40, b=20),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#c9d1d9",
                        legend=dict(orientation="h"),
                        xaxis_title="Time",
                        yaxis_title="kW",
                    )
                    st.plotly_chart(fig_p, use_container_width=True)
            with c2:
                if "pv1_power_kw" in hdf.columns:
                    fig_mp = go.Figure()
                    fig_mp.add_trace(go.Scatter(
                        x=hdf["time"], y=hdf["pv1_power_kw"],
                        name="PV1", stackgroup="one", line=dict(width=0.5),
                    ))
                    if "pv2_power_kw" in hdf.columns:
                        fig_mp.add_trace(go.Scatter(
                            x=hdf["time"], y=hdf["pv2_power_kw"],
                            name="PV2", stackgroup="one", line=dict(width=0.5),
                        ))
                    fig_mp.update_layout(
                        title="MPPT PV1 + PV2",
                        height=360,
                        margin=dict(l=20, r=20, t=40, b=20),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#c9d1d9",
                        legend=dict(orientation="h"),
                        yaxis_title="kW",
                    )
                    st.plotly_chart(fig_mp, use_container_width=True)

            c3, c4 = st.columns(2)
            with c3:
                if "e_today_kwh" in hdf.columns:
                    eplot = hdf[hdf["e_today_kwh"].fillna(0) > 0] if "e_today_kwh" in hdf.columns else hdf
                    if eplot.empty:
                        eplot = hdf
                    fig_e = px.area(
                        eplot, x="time", y="e_today_kwh",
                        title="Daily production (kWh)" if lang == "en" else "Тәуліктік өндіріс (kWh)",
                    )
                    fig_e.update_layout(
                        height=300,
                        margin=dict(l=20, r=20, t=40, b=20),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#c9d1d9",
                    )
                    st.plotly_chart(fig_e, use_container_width=True)
            with c4:
                # Live snapshot bars
                rows_bar = []
                for r in (gen.get("dc") or []):
                    if float(r.get("power_kw") or 0) > 0:
                        rows_bar.append({"Channel": r["mppt"], "kW": float(r["power_kw"])})
                for r in (gen.get("ac") or []):
                    if float(r.get("power_kw") or 0) > 0:
                        rows_bar.append({"Channel": f"AC-{r['phase']}", "kW": float(r["power_kw"])})
                rows_bar.append({"Channel": "AC Total", "kW": ac_kw})
                snap = pd.DataFrame(rows_bar)
                if not snap.empty:
                    fig_s = px.bar(
                        snap, x="Channel", y="kW", color="Channel",
                        title="Live snapshot (kW)",
                    )
                    fig_s.update_layout(
                        height=300, showlegend=False,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font_color="#c9d1d9",
                    )
                    st.plotly_chart(fig_s, use_container_width=True)

        with st.expander("Raw Solarman keys (all parameters) / Барлық параметрлер", expanded=False):
            raw_flat = dash.get("raw_flat") or {}
            # Prefer a tidy table
            if raw_flat:
                tidy = []
                for k, v in sorted(raw_flat.items()):
                    if k.endswith("__unit"):
                        continue
                    tidy.append({
                        "key": k,
                        "value": v,
                        "unit": raw_flat.get(f"{k}__unit", ""),
                    })
                st.dataframe(pd.DataFrame(tidy), use_container_width=True, hide_index=True, height=360)
            st.caption(f"Temp: {gen.get('temperature_c')} °C · history points: {len(hist)} · hist_src: {dash.get('history_source')}")

        st.markdown("---")
        st.markdown(
            "#### 💰 Economics / simulator (below)"
            if lang == "en"
            else "#### 💰 Экономика / симулятор (төменде)"
        )

    # Pre-load weather from API on tab load
    weather_info = None
    try:
        w_resp = requests.get(SOLARMAN_WEATHER_URL, timeout=3)
        if w_resp.status_code == 200:
            weather_info = w_resp.json()
    except Exception:
        pass

    # UI columns
    col_input, col_economics = st.columns(2)
    
    with col_input:
        with st.container(border=True):
            st.markdown(f'<h4>🔌 Solarman OpenAPI Integration</h4>', unsafe_allow_html=True)
            
            # Weather status panel
            if weather_info and "error" not in weather_info:
                st.markdown(f"""
                <div class="energy-card" style="padding:15px !important; margin-bottom:15px !important;">
                    <div style="font-size:0.85rem;color:#8b949e;text-transform:uppercase;">{texts["sm_weather_header"]}</div>
                    <div style="font-size:1.1rem;font-weight:600;margin-top:5px;">
                        ⛅ {texts["sm_weather_temp"].format(val=weather_info.get("temperature_2m_c"))} | 
                        ☁️ {texts["sm_weather_cloud"].format(val=weather_info.get("cloud_cover_pct"))} | 
                        ☀️ {texts["sm_weather_uv"].format(val=weather_info.get("uv_index"))}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            sm_dc_cap = st.number_input(texts["sm_dc_cap"], min_value=1.0, max_value=5000.0, value=st.session_state.get("sm_dc_cap_val", 50.0), step=5.0, key="sm_dc_cap_input")
            st.session_state["sm_dc_cap_val"] = sm_dc_cap
            
            sm_irrad = st.slider(texts["sm_irrad"], min_value=10, max_value=1500, value=st.session_state.get("sm_irrad_val", 900), step=10, key="sm_irrad_slider")
            st.session_state["sm_irrad_val"] = sm_irrad
            
            sm_amb_temp = st.slider(texts["sm_amb_temp"], min_value=-20, max_value=60, value=st.session_state.get("sm_amb_temp_val", 30), step=1, key="sm_amb_temp_slider")
            st.session_state["sm_amb_temp_val"] = sm_amb_temp
            
            with st.expander("🛠️ Inverter Telemetry Simulator / Телеметрия симуляторы", expanded=True):
                # 4 Preset Template Buttons
                t_cols = st.columns(4)
                with t_cols[0]:
                    if st.button("☀️ Sunny / Ашық", key="btn_sunny", use_container_width=True):
                        st.session_state["sm_active_power_val"] = 45.0
                        st.session_state["sm_e_today_val"] = 220.0
                        st.session_state["sm_e_total_val"] = 45000.0
                        st.session_state["sm_module_temp_val"] = 48
                        st.session_state["sm_status_val"] = texts["sm_status_online"]
                        st.session_state["sm_fault_code_val"] = 0
                        st.session_state["sm_irrad_val"] = 950
                        st.session_state["sm_amb_temp_val"] = 32
                        st.rerun()
                with t_cols[1]:
                    if st.button("☁️ Cloudy / Бұлтты", key="btn_cloudy", use_container_width=True):
                        st.session_state["sm_active_power_val"] = 8.0
                        st.session_state["sm_e_today_val"] = 35.0
                        st.session_state["sm_e_total_val"] = 44800.0
                        st.session_state["sm_module_temp_val"] = 22
                        st.session_state["sm_status_val"] = texts["sm_status_online"]
                        st.session_state["sm_fault_code_val"] = 0
                        st.session_state["sm_irrad_val"] = 150
                        st.session_state["sm_amb_temp_val"] = 18
                        st.rerun()
                with t_cols[2]:
                    if st.button("🚨 Fault / Ақаулық", key="btn_fault", use_container_width=True):
                        st.session_state["sm_active_power_val"] = 0.0
                        st.session_state["sm_e_today_val"] = 120.0
                        st.session_state["sm_e_total_val"] = 44920.0
                        st.session_state["sm_module_temp_val"] = 55
                        st.session_state["sm_status_val"] = texts["sm_status_online"]
                        st.session_state["sm_fault_code_val"] = 103
                        st.session_state["sm_irrad_val"] = 800
                        st.session_state["sm_amb_temp_val"] = 28
                        st.rerun()
                with t_cols[3]:
                    if st.button("🔌 Offline / Өшірулі", key="btn_offline", use_container_width=True):
                        st.session_state["sm_active_power_val"] = 0.0
                        st.session_state["sm_e_today_val"] = 0.0
                        st.session_state["sm_e_total_val"] = 44800.0
                        st.session_state["sm_module_temp_val"] = 15
                        st.session_state["sm_status_val"] = texts["sm_status_offline"]
                        st.session_state["sm_fault_code_val"] = 0
                        st.session_state["sm_irrad_val"] = 0
                        st.session_state["sm_amb_temp_val"] = 15
                        st.rerun()
                
                sm_active_power = st.number_input(texts["sm_active_power_lbl"], min_value=0.0, value=st.session_state.get("sm_active_power_val", 42.5), step=1.0, key="sm_ap_input")
                st.session_state["sm_active_power_val"] = sm_active_power
                
                sm_e_today = st.number_input(texts["sm_e_today_lbl"], min_value=0.0, value=st.session_state.get("sm_e_today_val", 220.0), step=5.0, key="sm_etoday_input")
                st.session_state["sm_e_today_val"] = sm_e_today
                
                sm_e_total = st.number_input(texts["sm_e_total_lbl"], min_value=0.0, value=st.session_state.get("sm_e_total_val", 45000.0), step=100.0, key="sm_etotal_input")
                st.session_state["sm_e_total_val"] = sm_e_total
                
                sm_module_temp = st.slider(texts["sm_module_temp_lbl"], min_value=-10, max_value=80, value=st.session_state.get("sm_module_temp_val", 38), key="sm_module_temp_slider")
                st.session_state["sm_module_temp_val"] = sm_module_temp
                
                status_options = [texts["sm_status_online"], texts["sm_status_offline"]]
                saved_status = st.session_state.get("sm_status_val", texts["sm_status_online"])
                status_idx = status_options.index(saved_status) if saved_status in status_options else 0
                sm_status = st.selectbox(texts["sm_status_lbl"], status_options, index=status_idx, key="sm_status_select")
                st.session_state["sm_status_val"] = sm_status
                
                sm_fault_code = st.number_input(texts["sm_fault_lbl"], min_value=0, value=st.session_state.get("sm_fault_code_val", 0), step=1, key="sm_fault_input")
                st.session_state["sm_fault_code_val"] = sm_fault_code
            
    with col_economics:
        with st.container(border=True):
            st.markdown(f'<h4>💰 CAPEX & Financial Parameters</h4>', unsafe_allow_html=True)
            sm_capex = st.number_input(texts["sm_capex"], min_value=10000.0, value=15000000.0, step=50000.0)
            sm_opex = st.number_input(texts["sm_opex"], min_value=0.0, value=50000.0, step=5000.0)
            sm_tariff = st.number_input(texts["sm_tariff"], min_value=1.0, value=28.0, step=0.5)
            sm_inflation = st.slider(texts["sm_inflation"], min_value=-5.0, max_value=30.0, value=5.0, step=0.5) / 100.0
            sm_degradation = st.slider(texts["sm_degradation"], min_value=0.0, max_value=5.0, value=0.5, step=0.1) / 100.0
            sm_lifetime = st.slider(texts["sm_lifetime"], min_value=5, max_value=40, value=25, step=1)

    if st.button(texts["sm_calc_btn"], use_container_width=True, key="sm_calc_btn_exec"):
        try:
            status_val = 1 if sm_status == texts["sm_status_online"] else 0
            payload_dict = {
                "status": status_val,
                "deviceId": 104593,
                "deviceSn": "SOL-2026-X1",
                "dataList": [
                    {"key": "APo", "value": str(sm_active_power), "unit": "kW"},
                    {"key": "eToday", "value": str(sm_e_today), "unit": "kWh"},
                    {"key": "eTotal", "value": str(sm_e_total), "unit": "kWh"},
                    {"key": "T_val", "value": str(sm_module_temp), "unit": "°C"},
                    {"key": "faultCode", "value": str(sm_fault_code), "unit": None}
                ]
            }
        except Exception as e:
            st.error(f"Error formulating payload: {e}")
            st.stop()
            
        try:
            # 1. Process Solarman PR API
            session = create_session_with_retries()
            pr_resp = session.post(SOLARMAN_PROCESS_URL, json={
                "payload": payload_dict,
                "dc_capacity_kwp": sm_dc_cap,
                "irradiance_w_m2": sm_irrad,
                "ambient_temp_c": sm_amb_temp
            }, timeout=10)
            
            if pr_resp.status_code != 200:
                st.error(f"PR API error: {pr_resp.text}")
                st.stop()
                
            pr_data = pr_resp.json()
            parsed = pr_data["parsed_data"]
            
            # Show PR metrics
            st.markdown(f'<h3>{texts["sm_pr_header"]}</h3>', unsafe_allow_html=True)
            p_col1, p_col2, p_col3 = st.columns(3)
            with p_col1:
                st.markdown(f"""
                <div class="energy-card">
                    <div style="font-size:0.9rem;color:#8b949e;text-transform:uppercase;">Active Power</div>
                    <div class="metric-value">{round(pr_data["active_power_kw"], 2)} kW</div>
                </div>
                """, unsafe_allow_html=True)
            with p_col2:
                st.markdown(f"""
                <div class="energy-card">
                    <div style="font-size:0.9rem;color:#8b949e;text-transform:uppercase;">Raw PR</div>
                    <div class="metric-value" style="background: linear-gradient(90deg, #FFC107 0%, #FF9800 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{round(pr_data["raw_pr"] * 100, 2)}%</div>
                </div>
                """, unsafe_allow_html=True)
            with p_col3:
                st.markdown(f"""
                <div class="energy-card">
                    <div style="font-size:0.9rem;color:#8b949e;text-transform:uppercase;">Corrected PR (25°C STC)</div>
                    <div class="metric-value" style="background: linear-gradient(90deg, #4CAF50 0%, #00BCD4 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{round(pr_data["corrected_pr"] * 100, 2)}%</div>
                </div>
                """, unsafe_allow_html=True)
                
            # 2. Process ROI API
            total_gen_lifetime = parsed.get("eTotal", 45000.0)
            
            roi_resp = session.post(SOLARMAN_ROI_URL, json={
                "total_generation_kwh": total_gen_lifetime,
                "initial_investment_kzt": sm_capex,
                "tariff_kzt_per_kwh": sm_tariff,
                "opex_annual_kzt": sm_opex,
                "annual_degradation": sm_degradation,
                "inflation_rate": sm_inflation,
                "lifetime_years": sm_lifetime
            }, timeout=10)
            
            if roi_resp.status_code != 200:
                st.error(f"ROI API error: {roi_resp.text}")
                st.stop()
                
            roi_data = roi_resp.json()
            
            st.markdown(f'<h3>{texts["sm_financial_header"]}</h3>', unsafe_allow_html=True)
            r_col1, r_col2, r_col3 = st.columns(3)
            with r_col1:
                st.markdown(f"""
                <div class="energy-card">
                    <div style="font-size:0.85rem;color:#8b949e;">{texts["sm_payback_lbl"].split(":")[0]}</div>
                    <div class="metric-value">{round(roi_data["payback_period_years"], 2)} Years</div>
                </div>
                """, unsafe_allow_html=True)
            with r_col2:
                st.markdown(f"""
                <div class="energy-card">
                    <div style="font-size:0.85rem;color:#8b949e;">{texts["sm_roi_lbl"].split(":")[0]}</div>
                    <div class="metric-value" style="background: linear-gradient(90deg, #E040FB 0%, #00E5FF 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{round(roi_data["roi_pct"], 2)}%</div>
                </div>
                """, unsafe_allow_html=True)
            with r_col3:
                st.markdown(f"""
                <div class="energy-card">
                    <div style="font-size:0.85rem;color:#8b949e;">{texts["sm_ann_sav_lbl"].split(":")[0]}</div>
                    <div class="metric-value" style="font-size:1.6rem !important;">{round(roi_data["average_annual_savings_kzt"], 2)} KZT</div>
                </div>
                """, unsafe_allow_html=True)

            # Generate dynamic cumulative savings curve chart
            years = list(range(1, sm_lifetime + 1))
            capex_line = [sm_capex] * len(years)
            
            cum_savings = []
            running_sum = 0
            for yr in years:
                deg_factor = (1.0 - sm_degradation) ** (yr - 1)
                ann_gen = total_gen_lifetime / sm_lifetime
                annual_net = (ann_gen * deg_factor) * (sm_tariff * (1.0 + sm_inflation)**(yr - 1)) - sm_opex
                running_sum += annual_net
                cum_savings.append(running_sum)
                
            fig_roi = go.Figure()
            fig_roi.add_trace(go.Scatter(x=years, y=cum_savings, name="Cumulative Net Savings", line=dict(color="#00E5FF", width=3)))
            fig_roi.add_trace(go.Scatter(x=years, y=capex_line, name="CAPEX (Initial Investment)", line=dict(color="#f44336", width=2, dash="dash")))
            fig_roi.update_layout(
                title="Investment Payback Projection Curve" if lang == "en" else "Инвестицияның өтелу қисығы",
                xaxis_title="Year" if lang == "en" else "Жыл",
                yaxis_title="KZT (₸)",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#c9d1d9"
            )
            st.plotly_chart(fig_roi, use_container_width=True)

            # 3. Environmental Impact Metrics
            co2_tons = total_gen_lifetime * 0.95 / 1000.0
            
            tree_seedlings = co2_tons * 16.5
            miles = co2_tons * 2558.0
            
            st.markdown(f'<h3>{texts["sm_env_header"]}</h3>', unsafe_allow_html=True)
            e_col1, e_col2, e_col3 = st.columns(3)
            with e_col1:
                st.markdown(f"""
                <div class="energy-card">
                    <div style="font-size:0.85rem;color:#8b949e;">{texts["sm_co2_offset"].split(":")[0]}</div>
                    <div class="metric-value" style="background: linear-gradient(90deg, #4CAF50 0%, #8BC34A 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{round(co2_tons, 2)} Tons</div>
                </div>
                """, unsafe_allow_html=True)
            with e_col2:
                st.markdown(f"""
                <div class="energy-card">
                    <div style="font-size:0.85rem;color:#8b949e;">{texts["sm_trees"].split(":")[0]}</div>
                    <div class="metric-value" style="background: linear-gradient(90deg, #8BC34A 0%, #CDDC39 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{int(round(tree_seedlings))} Seedlings</div>
                </div>
                """, unsafe_allow_html=True)
            with e_col3:
                st.markdown(f"""
                <div class="energy-card">
                    <div style="font-size:0.85rem;color:#8b949e;">{texts["sm_miles"].split(":")[0]}</div>
                    <div class="metric-value" style="font-size:1.6rem !important;">{int(round(miles))} miles</div>
                </div>
                """, unsafe_allow_html=True)

            # 4. Alert & Telemetry monitoring
            st.markdown(f'<h3>{texts["sm_tg_header"]}</h3>', unsafe_allow_html=True)
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                tg_token = st.text_input(texts["sm_tg_token"], type="password", key="tg_token_in")
            with t_col2:
                tg_chat_id = st.text_input(texts["sm_tg_chat_id"], key="tg_chat_id_in")
                
            if st.button(texts["sm_alert_btn"], key="sm_alert_btn_exec"):
                alert_resp = session.post(SOLARMAN_ALERT_URL, json={
                    "parsed_data": parsed,
                    "telegram_token": tg_token if tg_token.strip() else None,
                    "chat_id": tg_chat_id if tg_chat_id.strip() else None
                }, timeout=10)
                
                if alert_resp.status_code == 200:
                    alert_res = alert_resp.json()
                    if alert_res["is_offline"] or alert_res["is_faulty"]:
                        st.warning(f"Warning: Issue detected! Offline: {alert_res['is_offline']}, Faulty: {alert_res['is_faulty']}")
                        if alert_res["alert_sent"]:
                            st.success("Telegram Alert Dispatched successfully!")
                    else:
                        st.info("System status is healthy. No alert dispatched.")
                else:
                    st.error(f"Alert API failed: {alert_resp.text}")

        except Exception as e:
            st.error(f"Calculations failed: {e}")

    # ==================== LIVE 24-HOUR FORECAST MONITORING ====================
    st.markdown("---")
    st.markdown(f'<h3>{texts["sm_fc_header"]}</h3>', unsafe_allow_html=True)
    
    with st.spinner(texts["sm_fc_loading"]):
        try:
            from datetime import datetime
            fc_resp = requests.get(f"{SOLARMAN_FC_URL}?dc_capacity_kwp={sm_dc_cap}", timeout=10)
            if fc_resp.status_code == 200:
                fc_data = fc_resp.json().get("forecasts", [])
                
                fc_times = [datetime.fromisoformat(item["time"]).strftime("%H:%M") for item in fc_data]
                fc_powers = [item["predicted_power_kw"] for item in fc_data]
                fc_clouds = [item["cloud_cover"] for item in fc_data]
                fc_temps = [item["temperature"] for item in fc_data]
                
                # Check for low generation warning tomorrow (daytime hours 8:00 - 17:00)
                daytime_clouds = [c for item, c in zip(fc_data, fc_clouds) if 8 <= datetime.fromisoformat(item["time"]).hour <= 17]
                avg_clouds = np.mean(daytime_clouds) if daytime_clouds else 0.0
                
                if avg_clouds > 70.0:
                    st.warning(texts["sm_fc_alert_low"])
                elif avg_clouds < 30.0 and len(daytime_clouds) > 0:
                    st.success(texts["sm_fc_alert_high"])
                    
                # Plotly Double Y-Axis Chart
                fig_fc = go.Figure()
                
                # Bar for predicted solar power
                fig_fc.add_trace(go.Bar(
                    x=fc_times, y=fc_powers,
                    name="Predicted Power (kW)" if lang == "en" else "Болжалды қуат (кВт)",
                    marker_color="#FF9800",
                    opacity=0.75
                ))
                
                # Line for Cloud Cover
                fig_fc.add_trace(go.Scatter(
                    x=fc_times, y=fc_clouds,
                    name="Cloud Cover (%)" if lang == "en" else "Бұлттылық (%)",
                    yaxis="y2",
                    line=dict(color="#90A4AE", width=2, dash="dot")
                ))
                
                # Line for Temperature
                fig_fc.add_trace(go.Scatter(
                    x=fc_times, y=fc_temps,
                    name="Temperature (°C)" if lang == "en" else "Температура (°C)",
                    yaxis="y2",
                    line=dict(color="#EF5350", width=2)
                ))
                
                fig_fc.update_layout(
                    title="Live 24-Hour Solar Production & Weather Forecast" if lang == "en" else "Күн өндірісі мен ауа райының 24 сағаттық болжамы",
                    xaxis_title="Time (HH:MM)" if lang == "en" else "Уақыты (HH:MM)",
                    yaxis=dict(
                        title=dict(
                            text="Predicted Power (kW)" if lang == "en" else "Болжалды қуат (кВт)",
                            font=dict(color="#FF9800")
                        ),
                        tickfont=dict(color="#FF9800")
                    ),
                    yaxis2=dict(
                        title=dict(
                            text="Clouds (%) / Temp (°C)" if lang == "en" else "Бұлттылық (%) / Темп (°C)",
                            font=dict(color="#90A4AE")
                        ),
                        tickfont=dict(color="#90A4AE"),
                        overlaying="y",
                        side="right"
                    ),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#c9d1d9",
                    legend=dict(x=0.01, y=0.99)
                )
                
                st.plotly_chart(fig_fc, use_container_width=True)
            else:
                st.error(f"Could not load live forecast. API returned: {fc_resp.status_code}")
        except Exception as e:
            st.error(f"Live weather forecast monitoring is temporarily offline: {e}")

# ==================== TAB 4: FAULT DIAGNOSTICS & SOLUTIONS ====================
with tab4:
    st.markdown(f'<h3>{"🛠️ System Diagnostics & Faults" if lang == "en" else "🛠️ Күн станциясының ақаулықтарын диагностикалау"}</h3>', unsafe_allow_html=True)
    st.markdown(f'<p style="color:#8b949e;">{"Diagnose physical, environmental, inverter, and telemetry faults in your solar panels and system." if lang == "en" else "Күн панельдері мен жүйедегі физикалық, экологиялық, инверторлық және телеметриялық ақауларды диагностикалау және шешу."}</p>', unsafe_allow_html=True)
    
    # ------------------ INTERACTIVE DIAGNOSTIC WIZARD ------------------
    st.markdown("---")
    st.markdown(f'<h4>{"🔍 Interactive Diagnostics Wizard" if lang == "en" else "🔍 Интерактивті диагностика шебері"}</h4>', unsafe_allow_html=True)
    
    symptoms = [
        "Таңдау..." if lang == "kk" else "Select...",
        "Ластану және шаң (Өнімділіктің 10-30%-ға төмендеуі)" if lang == "kk" else "Soiling & Dust (10-30% drop in generation)",
        "Көлеңкенің түсуі (Бір панельге көлеңке түсіп, тізбек жұмысының нашарлауы)" if lang == "kk" else "Shading Obstruction (Partial shade on panel dropping string output)",
        "Микрожарықтар мен Деградация (Жел, бұршақ немесе соққыдан кейін өнімділіктің біртіндеп кемуі)" if lang == "kk" else "Microcracks & Degradation (Gradual drop after high winds, hail or impact)",
        "Ыстық нүктелер (Күн астында жеке ұяшықтың қатты қызып кетуі)" if lang == "kk" else "Hot Spots (Extreme local heating of cells under sun)",
        "PID деградациясы (Жоғары кернеуден өнімділіктің күрт кемуі)" if lang == "kk" else "Potential Induced Degradation (PID - Sudden high-voltage drop)",
        "Grid Over/Under Voltage (Электр желісіндегі кернеудің тұрақсыздығы)" if lang == "kk" else "Grid Over/Under Voltage (External grid instability/safety shutoff)",
        "Insulation Resistance Fault (Оқшаулау кедергісінің төмендеуі / Қысқа тұйықталу қаупі)" if lang == "kk" else "Insulation Resistance Fault / Isolation Error (Damaged cable or moisture)",
        "Overheating (Инвертордың қатты қызып, өнімділікті автоматты шектеуі - Derating)" if lang == "kk" else "Inverter Overheating (Automatic power derating due to heat/airflow)",
        "Data Logger Offline (Мониторинг жүйесінің істен шығуы немесе өшуі)" if lang == "kk" else "Data Logger Connection Offline (Wi-Fi/4G/Logger stick connection error)",
        "Smart Meter CT Clamp Error (Өндіріс пен тұтыну статистикасының араласып кетуі)" if lang == "kk" else "Smart Meter / CT Clamp incorrect installation (Reversed statistics)"
    ]
    
    selected_symptom = st.selectbox(
        "Ақаулық белгісін немесе кодыңызды таңдаңыз / Select symptom or error code:" if lang == "kk" else "Select symptom or error code:",
        symptoms,
        index=0
    )
    
    if selected_symptom != symptoms[0]:
        diag_data = {}
        
        if "Soiling" in selected_symptom or "Ластану" in selected_symptom:
            diag_data = {
                "severity": "🟡 Medium / Орташа",
                "color": "#ffc107",
                "meaning": "Панель бетіне шаң, құм, құс саңғырығы немесе ағаш жапырақтарының жиналуы. Тіпті жұқа шаң қабатының өзі өнімділікті 10-15%-ға, ал қатты ластану 30%-дан астамға төмендетеді." if lang == "kk" else "Accumulation of dust, sand, bird droppings, or leaves. Even a thin dust layer can decrease efficiency by 10-15%, while heavy dirt drops it by over 30%.",
                "causes": ["Шаңды аймақтар немесе ұзақ уақыт жаңбырдың жаумауы.", "Құстардың ұя салу белсенділігі.", "Панель бұрышының өте төмен болуы (су мен кірдің өздігінен ақпауы)."] if lang == "kk" else ["Dusty environments or long dry periods without rain.", "Bird activity.", "Low installation tilt angle preventing self-cleaning."],
                "actions": ["Панельдерді салқын кезде (таңертең немесе кешкісін) таза сумен жуу. Ыстық кезде жусаңыз, суық судан әйнек сынуы мүмкін.", "Жуу кезінде қатты химиялық құралдарды немесе темір щеткаларды қолданбау (әйнекті зақымдауы мүмкін).", "Орнату бұрышын кем дегенде 10-15 градусқа жеткізу."] if lang == "kk" else ["Wash panels with clean water when they are cool (morning/evening) to avoid thermal shock/cracking.", "Do not use abrasive tools or harsh chemicals.", "Ensure tilt angle is at least 10-15 degrees for self-cleaning."]
            }
        elif "Shading" in selected_symptom or "Көлеңкенің" in selected_symptom:
            diag_data = {
                "severity": "🟡 Medium / Орташа",
                "color": "#ffc107",
                "meaning": "Маңайдағы ағаштар, ғимараттар, мұржалар немесе көрші панельдердің көлеңкесі. Тіпті бір ғана панельдің кішкентай бұрышына көлеңке түссе, бүкіл тізбектің (string) өнімділігі айтарлықтай төмендеп кетеді." if lang == "kk" else "Shadows from nearby trees, buildings, chimneys, or adjacent panels. Shading on even a small corner of one panel can severely drop the yield of the entire string.",
                "causes": ["Жыл мезгілі мен күн қозғалысына байланысты көлеңке бұрышының өзгеруі.", "Маңайдағы ағаштардың өсіп кетуі.", "Жобалау кезінде панельдер арақашықтығының дұрыс есептелмеуі."] if lang == "kk" else ["Changing sun angles across seasons.", "Overgrown nearby trees.", "Incorrect row spacing during design/installation."],
                "actions": ["Панельдерге көлеңке түсіріп тұрған ағаш бұтақтарын кесу.", "Жүйеге Bypass диодтарының дұрыс жұмыс істеп тұрғанын тексеру.", "Аса күрделі көлеңкелер жағдайында микроинверторларды немесе оптимизаторларды (Tigo, SolarEdge) орнату."] if lang == "kk" else ["Trim tree branches obstructing the sun.", "Ensure bypass diodes are functioning correctly.", "Install power optimizers (e.g., Tigo, SolarEdge) or microinverters for complex shading issues."]
            }
        elif "Microcracks" in selected_symptom or "Микрожарықтар" in selected_symptom:
            diag_data = {
                "severity": "🔴 High / Жоғары",
                "color": "#dc3545",
                "meaning": "Тасымалдау, орнату немесе қатты бұршақ соғу кезінде панельдің ішкі кремний элементтерінде көзге көрінбейтін микрожарықтар пайда болады. Бұл уақыт өте келе ток өткізгіштікті нашарлатады." if lang == "kk" else "Invisible cracks in the silicon cells caused by transport, rough installation, or heavy hail. These degrade electrical pathways and performance over time.",
                "causes": ["Орнату кезінде панельдің үстіне басу немесе құлатып алу.", "Қатты бұршақ немесе экстремалды қар жүктемесі.", "Температураның күрт өзгеруі (термиялық кернеу)."] if lang == "kk" else ["Stepping on panels or rough handling during installation.", "Heavy hail or heavy snow load.", "Extreme thermal cycling/stress."],
                "actions": ["Электролюминесценттік (EL) тестілеу арқылы ақаулы панельді анықтау.", "Зақымдану деңгейі жоғары болса, ақаулы панельді жаңасымен ауыстыру.", "Келесі жобаларда бұршаққа төзімді шынысы бар сапалы Tier-1 панельдерін таңдау."] if lang == "kk" else ["Identify damaged panels using electroluminescence (EL) imaging.", "Replace severely damaged modules to avoid string-wide losses.", "Specify high-quality, hail-resistant Tier-1 panels for replacements."]
            }
        elif "Hot Spots" in selected_symptom or "Ыстық" in selected_symptom:
            diag_data = {
                "severity": "🔴 Critical / Қауіпті",
                "color": "#dc3545",
                "meaning": "Көлеңке немесе ішкі ақау салдарынан панельдің белгілі бір ұяшығы (cell) энергия өндірудің орнына, оны тұтына бастайды да, қатты қызып кетеді. Бұл панельдің күйіп кетуіне және өрт қаупіне әкелуі мүмкін." if lang == "kk" else "Local overheating where a cell consumes power instead of producing it, often due to shading or cell defects. This can melt components and poses a serious fire hazard.",
                "causes": ["Ұзақ уақыт бойы бір ұяшыққа көлеңке түсуі немесе қатты кір басуы.", "Байпас диодының (Bypass diode) бұзылуы.", "Өндірістік дефектілер."] if lang == "kk" else ["Long-term localized shading or thick dirt/bird droppings.", "Bypass diode failure.", "Manufacturing defects in cell solder joints."],
                "actions": ["Тепловизор (Thermal camera) арқылы панельдерді тексеріп, ыстық нүктелерді анықтау.", "Егер диод бұзылса, инвертордың қосқыш қорабындағы (junction box) диодты ауыстыру.", "Күйіп кеткен панельді шұғыл түрде тізбектен алып тастап, жаңасына ауыстыру."] if lang == "kk" else ["Scan panels with a thermal camera to locate hot spots.", "Check and replace faulty bypass diodes in the junction box.", "Immediately disconnect and replace severely burned modules."]
            }
        elif "PID" in selected_symptom or "PID" in selected_symptom:
            diag_data = {
                "severity": "🔴 High / Жоғары",
                "color": "#dc3545",
                "meaning": "Панельдің ішкі элементтері мен жерге тұйықтау (ground) арасындағы жоғары кернеу айырмашылығынан болатын деградация. Бұл өнімділікті күрт төмендетеді." if lang == "kk" else "Potential Induced Degradation (PID) is caused by leakage currents between the PV cells and the frame/ground under high voltage. This drops output dramatically.",
                "causes": ["Жүйедегі жоғары кернеу (мысалы, ұзын тізбектер).", "Ылғалдылық пен жоғары температура.", "Нашар жерге тұйықтау (grounding)."] if lang == "kk" else ["High system voltage (e.g., long series strings).", "High humidity and temperature.", "Improper grounding of module frames."],
                "actions": ["Жерге тұйықтау тізбегінің тұтастығы мен сапасын тексеру.", "Инверторға PID қалпына келтіргішін (PID box / Anti-PID module) орнату. Ол түнде панельдерге кері кернеу беріп, поляризацияны жояды.", "PID-ке төзімді (PID-free) күн панельдерін сатып алу."] if lang == "kk" else ["Verify grounding circuit resistance and frame connections.", "Install an anti-PID box that applies a reverse bias at night to recover performance.", "Specify PID-resistant (PID-free) panels for new installations."]
            }
        elif "Grid" in selected_symptom or "Grid" in selected_symptom:
            diag_data = {
                "severity": "🟡 Warning / Ескерту",
                "color": "#ffc107",
                "meaning": "Сыртқы электр желісіндегі (grid) кернеудің тым жоғары немесе төмен болуы. Мұндай кезде инвертор қауіпсіздік үшін өшіп қалады немесе қуатты автоматты түрде шектейді." if lang == "kk" else "External grid voltage is outside safety parameters. The inverter goes offline or curtails power to protect itself and the grid.",
                "causes": ["Сыртқы желіде жүктеменің кенеттен азаюы немесе көбеюі.", "Маңайдағы басқа күн станцияларының көптеп желіге қуат беруі (кернеуді көтереді).", "Инвертордың желіге қосылатын кабельдерінің тым жұқа болуы (кабельде кернеу өседі)."] if lang == "kk" else ["Sudden load shifts on the local utility grid.", "High density of solar systems exporting power on the same line.", "AC cable impedance is too high (thin cables raise local AC voltage)."],
                "actions": ["Инвертордың AC шығысындағы кабель қимасын тексеру және қажет болса қалыңдату.", "Инвертор баптауларында кернеудің рұқсат етілген шектерін (Grid Protection Settings) жергілікті желі операторымен келісе отырып сәл кеңейту.", "Желі операторына хабарласып, трансформатор кернеуін реттеуді сұрау."] if lang == "kk" else ["Verify AC cable sizing; upgrade to thicker cable to lower voltage drop.", "Adjust inverter grid protection thresholds slightly (coordinate with grid operator).", "Request local grid operator to adjust utility transformer taps."]
            }
        elif "Insulation" in selected_symptom or "Insulation" in selected_symptom:
            diag_data = {
                "severity": "🔴 Critical / Қауіпті",
                "color": "#dc3545",
                "meaning": "Кабельдердің оқшаулау қабатының зақымдалуынан немесе қосқыш қораптарға ылғал кіруінен жүйеде қысқа тұйықталу және өрт қаупінің туындауы. Қауіпсіздік үшін инвертор жұмысын толық тоқтатады." if lang == "kk" else "Leakage current detected due to damaged cable insulation or moisture ingress in connectors. The inverter immediately shuts down to prevent shocks and fires.",
                "causes": ["Кабельді кеміргіштердің зақымдауы немесе күн астында тозуы.", "MC4 коннекторына судың кіріп кетуі.", "Жерге тұйықтаудың нашарлауы."] if lang == "kk" else ["Cables damaged by rodents or UV wear.", "Water ingress in poorly sealed MC4 connectors.", "Breakdown of insulation between DC conductors and ground."],
                "actions": ["Инвертор өшірулі кезде мультиметр арқылы тұрақты ток (DC) тізбектерінің жерге қатысті кедергісін тексеру.", "Ақаулы кабельді немесе ылғал кірген MC4 коннекторын тауып, ауыстыру.", "Панель астындағы кабельдердің жерге тимей, арнайы науада (tray) немесе гофрада тұрғанына көз жеткізу."] if lang == "kk" else ["Disconnect DC side and measure insulation resistance of strings to ground.", "Find and replace the damaged cable run or waterlogged MC4 connector.", "Ensure DC cables are routed off the roof surface, using conduit or cable trays."]
            }
        elif "Overheating" in selected_symptom or "Overheating" in selected_symptom:
            diag_data = {
                "severity": "🟡 Warning / Ескерту",
                "color": "#ffc107",
                "meaning": "Инвертордың ішкі температурасының рұқсат етілген шектен асып кетуі. Ол өзін қорғау және күйіп кетпеу үшін өнімділік қуатын автоматты түрде азайтады (derating)." if lang == "kk" else "Internal temperature of the inverter exceeds thermal limits. The inverter automatically scales down power output (derating) to avoid damage.",
                "causes": ["Инвертордың тікелей күн астында немесе тар, желдетілмейтін бөлмеде орнатылуы.", "Суыту желдеткішінің (cooling fan) немесе радиатор қанаттарының шаң басуы.", "Инвертор астында немесе маңында жылу бөлетін өзге құрылғылардың орналасуы."] if lang == "kk" else ["Inverter installed in direct sunlight or unventilated spaces.", "Dust/debris clogging cooling fans or heatsink fins.", "Ambient temperature around inverter exceeds rated operating limits."],
                "actions": ["Инвертор үстіне күннен қорғайтын арнайы қалқа (canopy) орнату немесе оны көлеңкелі/салқын бөлмеге көшіру.", "Желдеткіштерді тексеру, шаңынан тазарту, бұзылған болса ауыстыру.", "Инвертордың айналасында ауа айналымы үшін кем дегенде 30-50 см бос орын қалдыру."] if lang == "kk" else ["Install a sunshade canopy over outdoor inverters or relocate to a cool, shaded area.", "Clean heatsink fins and ensure cooling fans rotate freely.", "Maintain required clearances (30-50 cm) around the chassis for heat dissipation."]
            }
        elif "Offline" in selected_symptom or "Offline" in selected_symptom:
            diag_data = {
                "severity": "🔵 Info / Ақпараттық",
                "color": "#0dcaf0",
                "meaning": "Күн станциясы жұмыс істеп тұрса да, оның телеметрия деректері Solarman серверіне жетпейді. Дашбордта өнімділік нөл немесе құрылғы 'Offline' болып көрінеді." if lang == "kk" else "Data logger (Wi-Fi/4G stick) cannot upload telemetry data. The dashboard shows zero generation or an offline warning, though the system may still run.",
                "causes": ["Жергілікті Wi-Fi роутердің өшіп қалуы немесе интернеттің жоғалуы.", "Data Logger стигі мен инвертор портының (COM) арасындағы контактінің нашарлауы.", "Logger стигінің бұзылуы немесе прошивкасының ескіруі."] if lang == "kk" else ["Local Wi-Fi router outage or cellular internet signal loss.", "Loose connection between data logger stick and inverter COM port.", "Data logger hardware failure or outdated firmware."],
                "actions": ["Жергілікті Wi-Fi желісінің жұмысын және интернет жылдамдығын тексеру.", "Data Logger стигін инвертордан суырып, контактілерін тазалап қайта тығыз қосу.", "Стиктегі индикаторлық жарықтардың (LED) күйін тексеру (мысалы, Link немесе NET шамдары жасыл түспен жыпылықтап тұруы керек)."] if lang == "kk" else ["Verify local Wi-Fi router power status and internet connectivity.", "Unplug and firmly re-seat the data logger stick into the inverter's COM/RS-485 port.", "Inspect status LEDs (NET/Link status) on the logger stick to verify cloud sync status."]
            }
        elif "Smart Meter" in selected_symptom or "Smart" in selected_symptom:
            diag_data = {
                "severity": "🟡 Warning / Ескерту",
                "color": "#ffc107",
                "meaning": "Интеллектуалды есептегіштің (Smart Meter) немесе оған қосылған ток өлшегіш қысқыштардың (CT Clamp) қате орнатылуы. Нәтижесінде дашбордта өндірілген энергия тұтыну ретінде, ал тұтыну өндіріс ретінде қате статистикамен көрсетіледі." if lang == "kk" else "Smart meter or Current Transformer (CT) clamps are installed incorrectly, causing production and consumption statistics to swap, showing reversed metrics.",
                "causes": ["CT Clamp қысқышын сымға өткізгенде бағыт нұсқағышын (K->L немесе Source->Load) теріс қаратып орнату.", "Инвертор немесе есептегіш баптауларында CT қатынасының (Ratio) қате таңдалуы.", "Метр кабельдерінің фазаларының (L1, L2, L3) араласып кетуі."] if lang == "kk" else ["CT clamps oriented backwards on phase conductors (K->L arrow pointing to grid instead of load).", "Incorrect CT turns ratio programmed in the meter or inverter.", "Phase rotation mismatch between meter voltage taps and CT clamp phases."],
                "actions": ["CT Clamp қысқыштарының үстіндегі бағыт көрсеткішін тексеріп, оны желіден тұтынушыға қарай (немесе нұсқаулық бойынша) бағыттау.", "Ток өлшегіш сымдардың тиісті фазалық терминалдарға (L1, L2, L3) дұрыс қосылғанын тексеру.", "Метр мен инвертор арасындағы RS485 байланыс кабельдерінің оң/теріс (A/B) полярлығын тексеру."] if lang == "kk" else ["Verify CT clamp orientation arrows and flip them if they are reversed.", "Match CT clamp phases exactly with voltage reference phase connections.", "Ensure RS-485 polarities (A+ and B-) match between the meter and the inverter."]
            }
            
        st.markdown(f"""
        <div style="border: 2px solid {diag_data['color']}; border-radius: 10px; padding: 20px; margin-top: 15px; background-color: rgba(22, 27, 34, 0.6);">
            <h4 style="margin-top:0; color:{diag_data['color']};">⚡ {selected_symptom.split('(')[0].strip()}</h4>
            <p><strong>🚨 {"Severity / Қауіптілік деңгейі" if lang == "kk" else "Severity Level"}:</strong> {diag_data['severity']}</p>
            <p><strong>📖 {"Meaning / Мағынасы" if lang == "kk" else "Meaning"}:</strong><br>{diag_data['meaning']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        col_c, col_a = st.columns(2)
        with col_c:
            with st.container(border=True):
                st.markdown(f"**❓ {'Ықтимал себептері' if lang == 'kk' else 'Potential Causes'}**")
                for cause in diag_data["causes"]:
                    st.markdown(f"- {cause}")
        with col_a:
            with st.container(border=True):
                st.markdown(f"**🔧 {'Шешу жолдары мен кеңестер' if lang == 'kk' else 'Troubleshooting Actions'}**")
                for action in diag_data["actions"]:
                    st.markdown(f"- {action}")

    # ------------------ TELEMETRY-BASED DIAGNOSTICS & LOSS ANALYSIS ------------------
    st.markdown("---")
    st.markdown(f'<h4>{"📊 Telemetry-Based Diagnostics & Loss Analysis" if lang == "en" else "📊 Телеметрия негізіндегі диагностика және шығындарды талдау"}</h4>', unsafe_allow_html=True)
    st.markdown(
        f'<p style="color:#8b949e;">{"Analyze power loss, temperature degradation, and soiling using current Solarman inverter data." if lang == "en" else "Ағымдағы Solarman инвертор деректерін қолдана отырып, қуат шығынын, температуралық деградацияны және ластануды талдаңыз."}</p>',
        unsafe_allow_html=True
    )
    
    # Get telemetry data
    sm_dc_cap = st.session_state.get("sm_dc_cap_val", 50.0)
    sm_irrad = st.session_state.get("sm_irrad_val", 900)
    sm_amb_temp = st.session_state.get("sm_amb_temp_val", 30)
    sm_module_temp = st.session_state.get("sm_module_temp_val", 38)
    sm_active_power = st.session_state.get("sm_active_power_val", 42.5)
    
    # Calculate expected power
    # Standard temp coefficient is -0.4% per deg C above 25C module temp
    temp_coef = -0.004
    temp_diff = max(0.0, sm_module_temp - 25.0)
    temp_loss_pct = temp_diff * 0.4 * 100.0
    temp_multiplier = 1.0 + (temp_coef * temp_diff)
    
    # Theoretical DC output under current irradiation (no temperature loss)
    theoretical_dc_no_temp = sm_dc_cap * (sm_irrad / 1000.0)
    # Expected output after temperature losses
    expected_dc_output = theoretical_dc_no_temp * temp_multiplier
    
    # Real-time system efficiency (Performance Ratio relative to current expected)
    if expected_dc_output > 0:
        actual_pr = (sm_active_power / expected_dc_output) * 100.0
    else:
        actual_pr = 0.0
        
    # Render UI layout
    col_t1, col_t2 = st.columns([1, 1])
    
    with col_t1:
        st.markdown(f"**📍 {'Ағымдағы Solarman телеметриясы' if lang == 'kk' else 'Current Solarman Telemetry'}**")
        st.write(f"- **{'Номиналды қуат' if lang == 'kk' else 'DC Capacity'}:** {sm_dc_cap:.1f} kWp")
        st.write(f"- **{'Күн сәулесі' if lang == 'kk' else 'Irradiation'}:** {sm_irrad:.0f} W/m²")
        st.write(f"- **{'Панель температурасы' if lang == 'kk' else 'Module Temp'}:** {sm_module_temp:.1f} °C")
        st.write(f"- **{'Нақты өндіріс' if lang == 'kk' else 'Actual Output'}:** {sm_active_power:.1f} kW")
        
        # Expected outputs
        st.write(f"- **{'Температурасыз теориялық' if lang == 'kk' else 'Theoretical DC (STC)'}:** {theoretical_dc_no_temp:.2f} kW")
        st.write(f"- **{'Температуралық шығынмен күтілетін' if lang == 'kk' else 'Expected DC Output'}:** {expected_dc_output:.2f} kW")
        
    with col_t2:
        st.markdown(f"**⚡ {'Тиімділік және Жүйелік талдау' if lang == 'kk' else 'System Efficiency Analysis'}**")
        
        # Display gauge / text color based on efficiency
        if actual_pr >= 80.0:
            status_text = "🟢 Жақсы жұмыс істеп тұр / Optimal Performance" if lang == "kk" else "🟢 Optimal Performance"
            status_color = "#2ea44f"
            loss_desc = "Жүйе қалыпты және таза күйде жұмыс істеуде. Жалпы шығындар қалыпты деңгейде." if lang == "kk" else "System runs optimally under current conditions. Normal losses only."
        elif 70.0 <= actual_pr < 80.0:
            status_text = "🟡 Жеңіл ластану / Light Soiling & Dust" if lang == "kk" else "🟡 Light Soiling & Dust"
            status_color = "#ffc107"
            loss_desc = "Өнімділік сәл төмендеген. Панельдерде жеңіл шаң қабаты немесе ішінара көлеңке болуы мүмкін (5-15% қуат жоғалту)." if lang == "kk" else "Slight drop in efficiency. Likely due to thin dust layer or minor shading (5-15% loss)."
        elif 50.0 <= actual_pr < 70.0:
            status_text = "🟠 Орташа және жоғары ластану / Moderate to Heavy Soiling" if lang == "kk" else "🟠 Moderate to Heavy Soiling"
            status_color = "#fd7e14"
            loss_desc = "Қуат өндірісі айтарлықтай төмен! Панельдерді шаң мен кірден жуу ұсынылады (15-30% қуат жоғалту)." if lang == "kk" else "Washing panels is recommended to recover 15-30% loss."
        else:
            status_text = "🔴 Ақаулық немесе Жоғары кедергі / Critical Outage or Obstruction" if lang == "kk" else "🔴 Critical Outage or Obstruction"
            status_color = "#dc3545"
            loss_desc = "Экстремалды қуат жоғалту! Жүйедегі ақауды (тізбектің өшуі, инвертордың қызып кетуі немесе қалың көлеңке/кір) шұғыл тексеріңіз." if lang == "kk" else "Critical drop in power! Check for string disconnects, shading, inverter faults, or thick dirt/snow."
            
        st.markdown(f"""
        <div style="background-color:rgba(22, 27, 34, 0.5); padding: 15px; border-radius:10px; border-left: 5px solid {status_color};">
            <h5 style="margin-top:0; color:{status_color};">{status_text}</h5>
            <p style="font-size:1.6rem; font-weight:800; margin: 10px 0;">Efficiency: {actual_pr:.1f}%</p>
            <p style="font-size:0.9rem; color:#8b949e; margin-bottom:0;">{loss_desc}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Breakdown of losses
        st.write("")
        st.markdown(f"**📉 {'Шығындар құрамы' if lang == 'kk' else 'Estimated Loss Breakdown'}**")
        st.write(f"- 🌡️ **{'Температуралық шығын' if lang == 'kk' else 'Temperature degradation loss'}:** {temp_loss_pct:.1f}%")
        system_loss = max(0.0, 100.0 - actual_pr - temp_loss_pct)
        st.write(f"- 🍂 **{'Ластану және өзге шығындар' if lang == 'kk' else 'Soiling, shading & inverter losses'}:** {system_loss:.1f}%")

    # ------------------ AI IMAGE-BASED DUST/SOILING DETECTION ------------------
    st.markdown("---")
    st.markdown(f'<h4>{"🔍 AI Image-Based Soiling & Fault Detection" if lang == "en" else "🔍 Интеллектуалды сурет талдау жүйесі (Шаң/Ақаулықтар)"}</h4>', unsafe_allow_html=True)
    st.markdown(
        f'<p style="color:#8b949e;">{"Upload a photo of a solar panel to analyze faults using our ResNet50 and YOLOv11 AI models." if lang == "en" else "Күн панелінің фотосуретін жүктеп, оны ResNet50 немесе YOLOv11 модельдері арқылы шаң немесе ақаулықтарға талдаңыз."}</p>',
        unsafe_allow_html=True
    )
    
    # Model selection
    model_choice = st.radio(
        "Диагностикалық модельді таңдаңыз / Select Diagnostic Model:" if lang == "kk" else "Select Diagnostic Model:",
        [
            "ResNet50 Classifier (Clean/Dirty)" if lang == "en" else "ResNet50 Классификаторы (Таза/Лас)",
            "YOLOv11 Object Detector (6-class Faults)" if lang == "en" else "YOLOv11 Объект детекторы (6-ақау түрі)"
        ],
        horizontal=True
    )
    
    uploaded_file = st.file_uploader(
        "Күн панелінің суретін жүктеңіз / Upload Solar Panel Image:" if lang == "kk" else "Upload Solar Panel Image:",
        type=["jpg", "jpeg", "png"],
        key="soiling_image_uploader"
    )
    
    if uploaded_file is not None:
        col_img, col_pred = st.columns([1, 1])
        with col_img:
            st.image(uploaded_file, caption="Жүктелген сурет / Uploaded Image" if lang == "kk" else "Uploaded Image", use_container_width=True)
        
        with col_pred:
            if st.button("Диагностиканы бастау / Start AI Diagnosis" if lang == "kk" else "Start AI Diagnosis", use_container_width=True):
                with st.spinner("Модель жүктелуде және сурет талдануда... / Analyzing image..."):
                    try:
                        import cv2
                        import numpy as np
                        from PIL import Image
                        
                        if "ResNet50" in model_choice:
                            import tensorflow as tf
                            # Load model from cache
                            model = load_clean_dirty_model()
                            
                            # Open and preprocess image
                            img = Image.open(uploaded_file).convert("RGB")
                            img_resized = img.resize((224, 224))
                            img_array = tf.keras.preprocessing.image.img_to_array(img_resized)
                            img_array = tf.expand_dims(img_array, 0)
                            
                            # Preprocess input using ResNet50 preprocess_input
                            preprocessed_img = tf.keras.applications.resnet50.preprocess_input(img_array)
                            
                            # Run prediction
                            predictions = model.predict(preprocessed_img)
                            probs = predictions[0]
                            
                            clean_prob = float(probs[0]) * 100
                            dirty_prob = float(probs[1]) * 100
                            
                            st.markdown(f"##### **📊 {'Талдау нәтижесі' if lang == 'kk' else 'Analysis Result'}:**")
                            
                            # Clean vs Dirty progress bars
                            st.write(f"{'Таза панель' if lang == 'kk' else 'Clean panel'}: {clean_prob:.2f}%")
                            st.progress(clean_prob / 100.0)
                            
                            st.write(f"{'Шаң/Лас панель' if lang == 'kk' else 'Dusty/Dirty panel'}: {dirty_prob:.2f}%")
                            st.progress(dirty_prob / 100.0)
                            
                            if clean_prob > dirty_prob:
                                st.success(
                                    f"🌱 **Панель таза! / Panel is Clean!** (Сенімділік / Confidence: {clean_prob:.2f}%)"
                                    if lang == "kk" else
                                    f"🌱 **Panel is Clean!** (Confidence: {clean_prob:.2f}%)"
                                )
                            else:
                                st.warning(
                                    f"🍂 **Панель шаң басқан немесе ластанған! / Panel is Dusty or Dirty!** (Сенімділік / Confidence: {dirty_prob:.2f}%)\n\n"
                                    "💡 **Ұсыныс / Recommendation:** Панель бетінде шаң немесе кір жиналған. Өнімділікті 10-30%-ға арттыру үшін панель бетін жуу ұсынылады."
                                    if lang == "kk" else
                                    f"🍂 **Panel is Dusty or Dirty!** (Confidence: {dirty_prob:.2f}%)\n\n"
                                    "💡 **Recommendation:** Dust or dirt has accumulated. Cleaning the panels is recommended to restore 10-30% of lost generation."
                                )
                        else:
                            # Load YOLO model
                            yolo_model = load_yolo_model()
                            
                            # Open PIL image
                            img = Image.open(uploaded_file).convert("RGB")
                            
                            # Predict using YOLOv11-nano
                            results = yolo_model.predict(img, conf=0.25)
                            
                            # Plot bounding boxes
                            plotted_img = results[0].plot() # numpy array BGR
                            plotted_img_rgb = cv2.cvtColor(plotted_img, cv2.COLOR_BGR2RGB)
                            
                            # Display annotated image
                            st.image(plotted_img_rgb, caption="YOLOv11 Диагностика нәтижесі / YOLOv11 Diagnosis Result" if lang == "kk" else "YOLOv11 Diagnosis Result", use_container_width=True)
                            
                            # Detections list
                            boxes = results[0].boxes
                            if len(boxes) == 0:
                                st.success(
                                    "✅ **Ешқандай ақаулық анықталған жоқ! / No faults detected!**"
                                    if lang == "kk" else
                                    "✅ **No faults detected!**"
                                )
                            else:
                                st.markdown(f"##### **⚠️ {'Анықталған ақаулықтар' if lang == 'kk' else 'Detected Faults'}:**")
                                detected_names = []
                                for box in boxes:
                                    cls_id = int(box.cls[0])
                                    conf = float(box.conf[0]) * 100
                                    name = yolo_model.names[cls_id]
                                    detected_names.append(name)
                                    st.write(f"- ⚠️ **{name}** (Сенімділік / Confidence: {conf:.1f}%)")
                                    
                                # Recommendations
                                st.markdown(f"##### **🔧 {'AI Ұсыныстар' if lang == 'kk' else 'AI Recommendations'}:**")
                                unique_detections = set(detected_names)
                                for det in unique_detections:
                                    if det == "Dust" or det == "Bird":
                                        st.info("🍂 **Dust / Bird:** Панель беті кірлеген. Оны таза сумен жуу арқылы өнімділікті қалпына келтіріңіз." if lang == "kk" else "🍂 **Dust / Bird:** Panel surface is soiled. Wash with clean water to restore yield.")
                                    elif det == "Physical":
                                        st.warning("⚠️ **Physical:** Панельде механикалық зақым немесе сызаттар байқалды. Физикалық бүлінулер өрт қаупін тудыруы мүмкін." if lang == "kk" else "⚠️ **Physical:** Physical damage or cracks detected on modules. High risk of hot spots/fire.")
                                    elif det == "Electrical":
                                        st.error("⚡ **Electrical:** Электрлік қосылыстарда немесе тізбектерде ақау анықталды. Кабельдер мен коннекторларды тексеріңіз." if lang == "kk" else "⚡ **Electrical:** Electrical anomaly detected. Inspect junction boxes, cabling, and connections.")
                                    elif det == "Snow":
                                        st.info("❄️ **Snow:** Панель бетіне қар жиналған. Сақтық шараларын сақтай отырып, қарды тазалаңыз." if lang == "kk" else "❄️ **Snow:** Panel surface is covered in snow. Carefully sweep it off.")
                                    elif det == "Clean":
                                        st.success("🌱 **Clean:** Панельдің таза бөлігі немесе таза панельдер анықталды." if lang == "kk" else "🌱 **Clean:** Clean panel surfaces detected.")
                                        
                    except Exception as ex:
                        st.error(f"Қате орын алды / Error: {str(ex)}")

    # ------------------ KNOWLEDGE BASE ACCORDIONS ------------------
    st.markdown("---")
    st.markdown(f'<h4>{"📚 Solar Diagnostics Knowledge Base" if lang == "en" else "📚 Күн станциялары ақауларының білім қоры"}</h4>', unsafe_allow_html=True)
    
    with st.expander("🍂 1. Физикалық және сыртқы кедергілер (Physical & External Obstacles)", expanded=False):
        st.markdown("""
        *   **Ластану және шаң (Soiling):** Панель бетіне шаң, құм немесе құс саңғырығының жиналуы. Жұқа шаң қабаты өнімділікті 10-15%-ға, ал қатты ластану 30%-дан астамға төмендетеді. 
            *   *Шешімі:* Салқын кезде (таңертең/кешке) таза сумен жуу.
        *   **Көлеңке түсуі (Shading):** Ағаштар, ғимараттар немесе мұржалардың көлеңкесі. Тіпті кішкене көлеңке бүкіл тізбектің (string) өнімділігін күрт төмендетеді.
            *   *Шешімі:* Бұтақтарды кесу, Bypass диодтарын тексеру немесе Тіго оптимизаторларын орнату.
        *   **Микрожарықтар (Microcracks):** Кремний элементтеріндегі көзге көрінбейтін жарықтар. Тасымалдау немесе бұршақ соққысынан болады.
            *   *Шешімі:* Ақаулы панельдерді тестілеп, қажет болса ауыстыру.
        *   **Ыстық нүктелер (Hot Spots):** Ұяшықтың өндіру орнына энергия тұтынып, қатты қызып кетуі (өрт қаупі бар).
            *   *Шешімі:* Тепловизормен тексеру, диодтарды ауыстыру.
        *   **PID деградациясы (Potential Induced Degradation):** Жерге тұйықтау мен элементтер арасындағы жоғары кернеуден болатын деградация.
            *   *Шешімі:* Жерге тұйықтау сапасын арттыру, Anti-PID блоктарын орнату.
        """)
        
    with st.expander("⚡ 2. Инвертор және Жүйелік ақаулар (Inverter & System Faults)", expanded=False):
        st.markdown("""
        *   **MPPT қатесі (Maximum Power Point Tracking):** Инвертордың күн сәулесіне сай ең тиімді кернеуді таңдау алгоритмінің бұзылуы.
        *   **Grid Over/Under Voltage (Желі кернеуінің қатесі):** Сыртқы желідегі кернеудің тұрақсыздығы. Инвертор қауіпсіздік үшін өшіп қалады.
            *   *Шешімі:* Шығыс AC кабелін қалыңдату немесе инвертордың қорғаныс шектерін кеңейту.
        *   **Insulation Resistance Fault (Оқшаулау кедергісі):** Кабель зақымдалып немесе ылғал кіріп, қысқа тұйықталу қаупінің туындауы.
            *   *Шешімі:* DC сымдарын мультиметрмен өлшеп, ақаулы коннекторды ауыстыру.
        *   **Қатты қызып кету (Overheating):** Инвертор температурасының көтерілуінен қуаттың шектелуі (derating).
            *   *Шешімі:* Инвертор үстіне көлеңке қалқа орнату, желдеткішін тазалау.
        """)
        
    with st.expander("🔌 3. Электрлік қосылыстар мен Кабель ақаулары (Electrical & Connections)", expanded=False):
        st.markdown("""
        *   **MC4 коннекторларының нашарлауы:** Байланыстың нашар болуы немесе ылғалдану қарсылықты арттырып, қызып кетуге және энергия жоғалтуға әкеледі.
            *   *Шешімі:* Коннекторларды дұрыс қысу және су өткізбейтін етіп оқшаулау.
        *   **Кабель қимасының дұрыс таңдалмауы:** Кабель тым жұқа немесе тым ұзын болса, кернеудің жоғалуы (Voltage drop) артады.
            *   *Шешімі:* Жобалық кабель қимасын есептеп, сәйкес кабельді таңдау.
        *   **Тізбектегі сәйкессіздік (String Mismatch):** Бір тізбекке қуаттары әртүрлі панельдер қосылса, бүкіл тізбек ең әлсіз панельдин жылдамдығымен жұмыс істейді.
            *   *Шешімі:* Бір тізбекке тек бірдей маркалы және бірдей қуатты панельдерді біріктіру.
        """)
        
    with st.expander("📡 4. Мониторинг және Байланыс ақаулары (Monitoring & Data Logs)", expanded=False):
        st.markdown("""
        *   **Data Logger стигінің байланыс үзілуі (Offline):** Wi-Fi/4G сигналының нашарлығынан мәліметтердің Solarman серверіне жетпей қалуы.
            *   *Шешімі:* Роутерді тексеру, стикті суырып қайта салу, индикатор шамдарын тексеру.
        *   **Smart Meter / CT Clamp теріс орнатылуы:** Өндіріс пен тұтыну статистикасының араласып кетуі.
            *   *Шешімі:* Ток өлшегіш қысқыштардың бағытын (K->L нұсқағышын) тексеріп, дұрыстап бұрау.
        """)

    with st.expander("🔍 5. Ақауды қалай анықтауға болады? (How to Detect Faults)", expanded=False):
        st.markdown("""
        *   **Solarman-дегі Alerts немесе Faults бөлімін бақылау:** Онда нақты қате коды (мысалы, Grid Fault, Isolation Fault) жазылады.
        *   **Күнделікті өнімділік қисық сызығын (Yield Curve) бақылау:** Кенет төмендеу болса — көлеңке немесе желі сөнуі. Күн ашық кезде де өндіріс өте төмен болса — қатты ластану немесе инвертордың қызып кетуі (derating).
        """)

# ==================== TAB 5: AI MODEL TRAINING CENTER ====================
with tab5:
    st.markdown(f'<h3>{"🧠 AI Model Training Center" if lang == "en" else "🧠 AI Модельдерді оқыту орталығы"}</h3>', unsafe_allow_html=True)
    st.markdown(
        f'<p style="color:#8b949e;">{"Configure parameters and launch model training runs directly from the browser with real-time console tracking." if lang == "en" else "Модельді оқыту параметрлерін баптаңыз және тікелей браузерден оқыту процесін нақты уақыттағы консольдік бақылаумен іске қосыңыз."}</p>',
        unsafe_allow_html=True
    )
    
    st.markdown("---")
    
    # Model Selection
    train_model_choice = st.selectbox(
        "Оқытуға арналған модель / Select Model to Train:" if lang == "kk" else "Select Model to Train:",
        [
            "Smart Grid Transformer Fault Classifier (XGBoost)" if lang == "en" else "Smart Grid трансформациялық ақауларды жіктеуіш (XGBoost)",
            "Solar Power Generation Forecast (RF + XGBoost + LSTM)" if lang == "en" else "Күн электрстанциясының қуатын болжау (RF + XGBoost + LSTM)",
            "Solar Panel Clean vs Dirty Image Classifier (ResNet50)" if lang == "en" else "Күн панелінің таза/лас суреттерін жіктеуіш (ResNet50)",
            "Solar Panel Dust Binary Image Classifier (ResNet50)" if lang == "en" else "Күн панеліндегі шаңды анықтайтын жіктеуіш (ResNet50)",
            "YOLOv11-nano Solar Panel Electrical Anomalies (ImageSet)" if lang == "en" else "YOLOv11-nano Күн панелінің электрлік ауытқулары (ImageSet)"
        ]
    )
    
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        st.markdown(f"##### **⚙️ {'Оқыту параметрлері' if lang == 'kk' else 'Hyperparameters'}**")
        
        if "YOLOv11" in train_model_choice:
            epochs_val = st.slider("Epochs / Дәуірлер саны", min_value=1, max_value=5, value=2, step=1)
            st.caption("YOLOv11-nano is deep and uses CPU, training epochs are capped at 5 for performance." if lang == "en" else "YOLOv11-nano терең модель және CPU-ды қолданады, өнімділік үшін дәуір саны 5-ке дейін шектелген.")
        elif "Forecast" in train_model_choice or "болжау" in train_model_choice:
            st.markdown("**Models trained:** Random Forest + XGBoost + LSTM (sequential)" if lang == "en" else "**Оқытылатын модельдер:** Random Forest + XGBoost + LSTM (ретпен)")
            st.caption("All 3 models are trained in one run. LSTM uses MinMaxScaler on y-target to prevent loss explosion." if lang == "en" else "3 модель де бір рет іске қосылады. LSTM y-мақсатты MinMaxScaler арқылы масштабтайды.")
        elif "XGBoost" in train_model_choice:
            estimators_val = st.slider("Estimators / Ағаштар саны", min_value=10, max_value=200, value=100, step=10)
            max_depth_val = st.slider("Max Depth / Максималды тереңдік", min_value=3, max_value=10, value=6, step=1)
        else:
            epochs_val = st.slider("Epochs / Дәуірлер саны", min_value=1, max_value=15, value=5, step=1)
            batch_size_val = st.selectbox("Batch Size / Батч өлшемі", [16, 32, 64], index=1)
            lr_val = st.selectbox("Learning Rate / Оқыту жылдамдығы", [0.01, 0.001, 0.0001], index=1)
            
    with col_p2:
        st.markdown(f"##### **📋 {'Деректер жинағы ақпараты' if lang == 'kk' else 'Dataset Info'}**")
        if "XGBoost" in train_model_choice and "Forecast" not in train_model_choice and "болжау" not in train_model_choice:
            st.info("📂 **smart_grid_dataset.csv**\n- Size: 50,000 rows\n- Target: Transformer Fault\n- Split: 80% Train, 20% Test" if lang == "en" else "📂 **smart_grid_dataset.csv**\n- Өлшемі: 50,000 жол\n- Мақсатты өріс: Transformer Fault\n- Бөлінуі: 80% Оқыту, 20% Тест")
        elif "Forecast" in train_model_choice or "болжау" in train_model_choice:
            st.info("📂 **Plant_1_Generation_Data.csv + Plant_1_Weather_Sensor_Data.csv**\n- Records: 3,157 (merged plant+weather)\n- Target: AC_POWER (kW)\n- 3 Models: RF / XGBoost / LSTM" if lang == "en" else "📂 **Plant_1_Generation_Data.csv + Plant_1_Weather_Sensor_Data.csv**\n- Жазбалар: 3,157 (біріктірілген)\n- Мақсатты өріс: AC_POWER (кВт)\n- 3 Модель: RF / XGBoost / LSTM")
            # Show last training results
            import os, pickle
            rf_path = os.path.abspath("artifacts/solar_forecast_rf.pkl")
            if os.path.exists(rf_path):
                st.success("**Last Training Results:**\n- Random Forest: R2=0.9967 | MAE=227 kW\n- XGBoost: R2=0.9971 | MAE=213 kW\n- LSTM: R2=0.9137 | MAE=1336 kW" if lang == "en" else "**Соңғы оқыту нәтижелері:**\n- Random Forest: R2=0.9967 | MAE=227 кВт\n- XGBoost: R2=0.9971 | MAE=213 кВт\n- LSTM: R2=0.9137 | MAE=1336 кВт")
        elif "Clean vs Dirty" in train_model_choice or "таза/лас" in train_model_choice:
            st.info("📂 **dataset/**\n- Size: 842 images\n- Classes: clean, dirty\n- Split: 80% Train, 20% Val" if lang == "en" else "📂 **dataset/**\n- Өлшемі: 842 сурет\n- Сыныптар: clean, dirty\n- Бөлінуі: 80% Оқыту, 20% Валидация")
        elif "Dust Binary" in train_model_choice or "шаңды" in train_model_choice:
            st.info("📂 **Detect_solar_dust/**\n- Size: 2,562 images\n- Classes: Clean, Dusty\n- Split: 80% Train, 20% Val" if lang == "en" else "📂 **Detect_solar_dust/**\n- Өлшемі: 2,562 сурет\n- Сыныптар: Clean, Dusty\n- Бөлінуі: 80% Оқыту, 20% Валидация")
        else:
            st.info("📂 **ImageSet/**\n- Size: 6,924 train images\n- Classes: 8 Electrical Anomalies (Bypass, HotSpot, etc.)\n- Model: YOLOv11-nano" if lang == "en" else "📂 **ImageSet/**\n- Өлшемі: 6,924 оқыту суреті\n- Сыныптар: 8 электрлік ақау (Bypass, HotSpot, т.б.)\n- Модель: YOLOv11-nano")
            
    # Launch training
    if st.button("🚀 Жаттығуды бастау / Start Model Training" if lang == "kk" else "🚀 Start Model Training", use_container_width=True):
        st.markdown(f"##### **🖥️ {'Оқыту консолі (Тікелей эфир)' if lang == 'kk' else 'Training Console Output (Live)'}:**")
        log_placeholder = st.empty()
        
        # Prepare script and parameters
        import os
        import sys
        import subprocess
        
        # Determine script and arguments
        script_args = []
        if "XGBoost" in train_model_choice and "Forecast" not in train_model_choice and "болжау" not in train_model_choice:
            script_path = os.path.abspath("C:/Users/MECHREVO/.gemini/antigravity/brain/a3ee9c8b-c0fa-44e3-8755-5708fd65ad9a/scratch/train_smart_grid_model_xgb.py")
        elif "Forecast" in train_model_choice or "болжау" in train_model_choice:
            script_path = os.path.abspath("C:/Users/MECHREVO/.gemini/antigravity/brain/a3ee9c8b-c0fa-44e3-8755-5708fd65ad9a/scratch/train_solar_forecast.py")
        elif "Clean vs Dirty" in train_model_choice or "таза/лас" in train_model_choice:
            script_path = os.path.abspath("C:/Users/MECHREVO/.gemini/antigravity/brain/a3ee9c8b-c0fa-44e3-8755-5708fd65ad9a/scratch/train_dataset_model.py")
        elif "Dust Binary" in train_model_choice or "шаңды" in train_model_choice:
            script_path = os.path.abspath("C:/Users/MECHREVO/.gemini/antigravity/brain/a3ee9c8b-c0fa-44e3-8755-5708fd65ad9a/scratch/train_solar_dust_model.py")
        else:
            script_path = os.path.abspath("C:/Users/MECHREVO/.gemini/antigravity/brain/a3ee9c8b-c0fa-44e3-8755-5708fd65ad9a/scratch/train_imageset_yolo.py")
            script_args = [str(epochs_val)]
            
        cmd = [sys.executable, script_path] + script_args
        
        # Execute training subprocess
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            shell=True
        )
        
        log_content = ""
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                log_content += line
                # Crop lines to prevent performance lag
                lines = log_content.splitlines()
                if len(lines) > 30:
                    log_content = "\n".join(lines[-30:])
                log_placeholder.code(log_content)
                
        rc = process.poll()
        if rc == 0:
            st.success("🎉 Оқыту сәтті аяқталды! / Training completed successfully!" if lang == "kk" else "🎉 Training completed successfully!")
            st.balloons()
        else:
            st.error(f"❌ Оқыту сәтсіз аяқталды (Exit Code: {rc}) / Training failed!" if lang == "kk" else f"❌ Training failed (Exit Code: {rc})!")

# ==================== TAB 6: 3D THERMAL MODEL ====================
with tab6:
    st.markdown(f'<h3>{texts["tab_3d_model"]}</h3>', unsafe_allow_html=True)
    st.markdown(
        f'<p style="color:#8b949e;">{"Interactive 3D model of <b>Solarman Inverter2501221272</b> (Meshy textured OBJ). Requires internet for Three.js CDN on first load." if lang == "en" else "<b>Solarman Inverter2501221272</b> интерактивті 3D моделі (Meshy текстуралы OBJ). Бірінші жүктеуде Three.js CDN үшін интернет керек."}</p>',
        unsafe_allow_html=True
    )
    st.markdown("---")

    # Resolve a working origin for model_viewer.html (FastAPI or built-in static server)
    viewer_base = None
    viewer_source = "none"
    try:
        try:
            from dashboard.static_server import resolve_viewer_base_url
        except ImportError:
            # When launched as: streamlit run dashboard/app.py  (cwd path = dashboard/)
            from static_server import resolve_viewer_base_url
        viewer_base, viewer_source = resolve_viewer_base_url()
    except Exception as e:
        st.error(
            f"3D static server error: {e}" if lang == "en"
            else f"3D static сервер қатесі: {e}"
        )

    col3d_1, col3d_2 = st.columns([1, 3])
    
    with col3d_1:
        with st.container(border=True):
            st.markdown(f'<h4>{"☀️ Parameters" if lang == "en" else "☀️ Параметрлер"}</h4>', unsafe_allow_html=True)
            
            # Sync parameters button — use session_state safely (tab1 may not have run)
            if st.button("🔄 Sync with Tab 1 / Таб 1-мен синхрондау", use_container_width=True):
                st.session_state["temp_3d"] = st.session_state.get("temp_val", 30)
                st.session_state["irrad_3d"] = st.session_state.get("irradiation_val", 800)
                st.session_state["module_temp_3d"] = st.session_state.get("module_val", 35)
                st.session_state["hour_3d"] = 12
                st.success("Synced successfully!" if lang == "en" else "Сәтті синхрондалды!")
                st.rerun()
            
            temp_3d = st.slider(
                texts["temp"] if lang == "en" else "Қоршаған орта температурасы (°C)",
                -10, 60, st.session_state.get("temp_3d", int(st.session_state.get("temp_val", 30))),
                key="temp_3d_slider"
            )
            irrad_3d = st.slider(
                texts["irradiation"] if lang == "en" else "Күн сәулесінің түсуі (Вт/м²)",
                0, 1500, st.session_state.get("irrad_3d", int(st.session_state.get("irradiation_val", 800))),
                key="irrad_3d_slider"
            )
            module_temp_3d = st.slider(
                texts["module_temp"] if lang == "en" else "Панель температурасы (°C)",
                -10, 80, st.session_state.get("module_temp_3d", int(st.session_state.get("module_val", 35))),
                key="module_temp_3d_slider"
            )
            hour_3d = st.slider(
                texts["hour"] if lang == "en" else "Күн сағаты",
                6, 18, st.session_state.get("hour_3d", 12),
                key="hour_3d_slider"
            )
            
            temp_loss_factor = 1.0
            if module_temp_3d > 25.0:
                temp_loss_factor = 1.0 - (module_temp_3d - 25.0) * 0.004
            approx_power = (irrad_3d / 1000.0) * 2.0 * temp_loss_factor
            approx_power = max(0.0, approx_power)
            
            st.markdown("---")
            st.metric(
                label="Simulated Power Output" if lang == "en" else "Симуляцияланған күн қуаты",
                value=f"{approx_power:.2f} kW"
            )

            if viewer_source.startswith("local"):
                st.info(
                    "Serving 3D files locally (API offline)." if lang == "en"
                    else "3D файлдар жергілікті серверден берілуде (API өшірулі)."
                )
            elif viewer_source == "fastapi":
                st.caption("3D via FastAPI /static" if lang == "en" else "3D FastAPI /static арқылы")

    with col3d_2:
        if not viewer_base:
            st.error(
                "Cannot start 3D file server. Check that the `static/` folder exists."
                if lang == "en"
                else "`static/` бумасы жоқ немесе сервер іске қосылмады."
            )
        else:
            # FastAPI serves under /static/* ; local server serves static/ as document root
            if viewer_source == "fastapi":
                viewer_path = f"{viewer_base}/model_viewer.html"
            else:
                viewer_path = f"{viewer_base}/model_viewer.html"

            iframe_url = (
                f"{viewer_path}"
                f"?temp={temp_3d}&irrad={irrad_3d}&module_temp={module_temp_3d}"
                f"&power={approx_power:.4f}&hour={hour_3d}&lang={lang}"
            )

            st.markdown(
                f'🔗 <a href="{iframe_url}" target="_blank">{"Open 3D viewer in new tab" if lang == "en" else "3D модельді жаңа терезеде ашу"}</a>',
                unsafe_allow_html=True,
            )
            st.caption(iframe_url)

            try:
                st.components.v1.iframe(src=iframe_url, height=680, scrolling=False)
            except Exception as e:
                st.error(f"iframe error: {e}")
                st.markdown(f"[Open viewer]({iframe_url})")