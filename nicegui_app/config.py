"""
Configuration, themes, styling tokens, and localization for EcoPredict AI NiceGUI App.
"""

DEFAULT_API_BASE = "http://127.0.0.1:8001"

LOCALIZATION = {
    "kk": {
        "app_title": "EcoPredict AI Web",
        "app_subtitle": "Жаңартылатын Энергия Жүйелерін AI-мен Оңтайландыру және Дашборд",
        "nav_overview": "Басты Дашборд",
        "nav_forecast": "Энергия Болжамы",
        "nav_faults": "Ақау Анықтау (Vision)",
        "nav_opt": "Микрожелі Оңтайландыру",
        "nav_chat": "AI Кеңесші",
        "nav_live": "Solarman Live",
        "nav_settings": "Баптаулар",

        # Overview Page
        "ov_title": "ЭкоЭнергия AI Басқару Панелі",
        "ov_subtitle": "Күн және жел генерациясы, жүктеме мен батарея диспетчеризациясы",
        "ov_kpi_solar": "Күн Өндірісі",
        "ov_kpi_wind": "Жел Өндірісі",
        "ov_kpi_load": "Жүйе Жүктемесі",
        "ov_kpi_battery": "Батарея Статусы",
        "ov_status_online": "API Белсенді",
        "ov_status_offline": "API Офлайн",

        # Forecast Page
        "fc_title": "Энергия өндірісін болжау",
        "fc_solar_params": "Күн Параметрлері",
        "fc_wind_params": "Жел Параметрлері",
        "fc_btn": "Болжамды Есептеу",
        "fc_total": "Жалпы Болжамды Қуат",
        "fc_solar": "Күн Энергиясы",
        "fc_wind": "Жел Энергиясы",

        # Faults Page
        "fl_title": "Күн Панельдеріндегі Ақауларды Анықтау (YOLO ML Vision)",
        "fl_upload_hint": "Панель суретін осы жерге жүктеңіз немесе үлгіні таңдаңыз",
        "fl_sample_clean": "Таза Панель",
        "fl_sample_dust": "Шаң Басқан Панель",
        "fl_sample_crack": "Зақымдалған Панель",

        # Optimization Page
        "opt_title": "Микрожелі Диспетчеризациясын Оңтайландыру",
        "opt_load": "Жүктеме сұранысы (кВт)",
        "opt_battery": "Батарея сыйымдылығы (кВт/сағ)",
        "opt_solar_cost": "Күн нарқы ($/кВт·сағ)",
        "opt_wind_cost": "Жел нарқы ($/кВт·сағ)",
        "opt_btn": "Оңтайлы Сценарийді Есептеу",

        # Chat Page
        "chat_title": "AI Energy Advisor (RAG Assistant)",
        "chat_placeholder": "ЖЭК және микрожелі бойынша сұрағыңызды жазыңыз...",
        "chat_send": "Жіберу",

        # Live Page
        "live_title": "Solarman Инвертор Бақылау",
        "live_power": "Ағымдағы Қуат",
        "live_yield": "Бүгінгі Өндіріс",

        # Settings Page
        "st_title": "Сервер мен Интерфейс Баптаулары",
        "st_api_url": "FastAPI Backend Base URL",
        "st_btn_test": "Байланысты Тексеру",
        "st_lang": "Интерфейс Тілі",
    },
    "en": {
        "app_title": "EcoPredict AI Web",
        "app_subtitle": "AI-Driven Renewable Energy Optimization Dashboard",
        "nav_overview": "Overview Dashboard",
        "nav_forecast": "Energy Forecasting",
        "nav_faults": "Fault Diagnostics",
        "nav_opt": "Microgrid Optimization",
        "nav_chat": "AI Advisor",
        "nav_live": "Solarman Live",
        "nav_settings": "Settings",

        # Overview Page
        "ov_title": "EcoEnergy AI Dashboard",
        "ov_subtitle": "Solar & Wind generation, load demand, and battery microgrid dispatch",
        "ov_kpi_solar": "Solar Yield",
        "ov_kpi_wind": "Wind Yield",
        "ov_kpi_load": "System Load",
        "ov_kpi_battery": "Battery Charge",
        "ov_status_online": "API Online",
        "ov_status_offline": "API Offline",

        # Forecast Page
        "fc_title": "Generation Forecast & Prediction",
        "fc_solar_params": "Solar Input Parameters",
        "fc_wind_params": "Wind Input Parameters",
        "fc_btn": "Calculate Forecast",
        "fc_total": "Total Predicted Output",
        "fc_solar": "Solar Output",
        "fc_wind": "Wind Output",

        # Faults Page
        "fl_title": "Solar Panel Defect & Dust Diagnostics",
        "fl_upload_hint": "Upload panel image or click preset test samples",
        "fl_sample_clean": "Clean Panel",
        "fl_sample_dust": "Dusty Panel",
        "fl_sample_crack": "Damaged Panel",

        # Optimization Page
        "opt_title": "Microgrid Dispatch Optimization",
        "opt_load": "Load Demand (kW)",
        "opt_battery": "Battery Capacity (kWh)",
        "opt_solar_cost": "Solar Cost ($/kWh)",
        "opt_wind_cost": "Wind Cost ($/kWh)",
        "opt_btn": "Run Dispatch Optimization",

        # Chat Page
        "chat_title": "AI Energy Advisor (RAG Assistant)",
        "chat_placeholder": "Ask a question about renewable energy or microgrid...",
        "chat_send": "Send",

        # Live Page
        "live_title": "Solarman Live Telemetry",
        "live_power": "Current Power",
        "live_yield": "Daily Production",

        # Settings Page
        "st_title": "Backend Connection & Settings",
        "st_api_url": "FastAPI Backend Base URL",
        "st_btn_test": "Test Connection",
        "st_lang": "Language",
    },
}


def get_text(lang: str, key: str, default: str = "") -> str:
    """Get localized text string."""
    d = LOCALIZATION.get(lang, LOCALIZATION["kk"])
    return d.get(key, LOCALIZATION["en"].get(key, default or key))
