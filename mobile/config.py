"""
Config, themes, colors, and localization dictionaries for EcoPredict AI Mobile.
"""

# Default FastAPI Backend URL (Railway 24/7 TCP Proxy Public URL for Port 8001)
DEFAULT_API_BASE = "http://sakura.proxy.rlwy.net:35462"

# App Colors - Dark & Light Palettes
COLORS = {
    "dark": {
        "bg": "#0F172A",
        "surface": "#1E293B",
        "surface_variant": "#334155",
        "primary": "#3B82F6",
        "primary_container": "#1E3A8A",
        "secondary": "#14B8A6",
        "accent": "#F59E0B",
        "text_primary": "#F8FAFC",
        "text_secondary": "#94A3B8",
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "card_border": "#334155",
    },
    "light": {
        "bg": "#F8FAFC",
        "surface": "#FFFFFF",
        "surface_variant": "#E2E8F0",
        "primary": "#2563EB",
        "primary_container": "#DBEAFE",
        "secondary": "#0D9488",
        "accent": "#D97706",
        "text_primary": "#0F172A",
        "text_secondary": "#64748B",
        "success": "#059669",
        "warning": "#D97706",
        "error": "#DC2626",
        "card_border": "#E2E8F0",
    },
}

# Bilingual Localization Dictionary
LOCALIZATION = {
    "kk": {
        "app_title": "EcoPredict AI Mobile",
        "app_subtitle": "Гибридті ЖЭК үшін ақылды білім беру платформасы",
        "nav_overview": "Басты",
        "nav_forecast": "Болжам",
        "nav_faults": "Ақау",
        "nav_opt": "Оңтайландыру",
        "nav_chat": "AI Кеңесші",
        "nav_live": "Live",
        "nav_settings": "Баптаулар",
        
        # Overview View
        "ov_hero_title": "ЭкоЭнергия AI Басқару Панелі",
        "ov_hero_sub": "Күн мен жел энергиясын AI-мен оңтайландыру, болжау және бақылау",
        "ov_status_online": "🟢 24/7 Онлайн",
        "ov_status_offline": "⚠️ Интернет Жоқ",
        "ov_kpi_solar": "Күн өндірісі",
        "ov_kpi_wind": "Жел өндірісі",
        "ov_kpi_load": "Жүйе жүктемесі",
        "ov_kpi_battery": "Батарея заряды",
        "ov_quick_actions": "Жылдам әрекеттер",
        "ov_btn_predict": "Болжау жасау",
        "ov_btn_fault": "Панельді тексеру",
        "ov_btn_chat": "AI Ассистентке сұрақ",
        
        # Forecast View
        "fc_title": "Энергия өндірісін болжау",
        "fc_solar_params": "Күн параметрлері",
        "fc_wind_params": "Жел параметрлері",
        "fc_irradiation": "Күн радиациясы (Вт/м²)",
        "fc_temp": "Ауа температурасы (°C)",
        "fc_module_temp": "Панель температурасы (°C)",
        "fc_wind_speed": "Жел жылдамдығы (м/с)",
        "fc_wind_dir": "Жел бағыты (°)",
        "fc_theoretical": "Теориялық қуат (кВт/сағ)",
        "fc_btn": "Болжамды есептеу",
        "fc_result_total": "Жалпы болжамды қуат",
        "fc_result_solar": "Күн энергиясы",
        "fc_result_wind": "Жел энергиясы",
        
        # Faults View
        "fl_title": "Күн панельдеріндегі ақауларды анықтау",
        "fl_desc": "Панель суретін жүктеңіз немесе үлгі суреттерді таңдаңыз (YOLO ML Vision)",
        "fl_btn_upload": "Сурет таңдау / Галерея",
        "fl_sample_clean": "Таза панель",
        "fl_sample_dust": "Шаң басқан панель",
        "fl_sample_crack": "Зақымдалған панель",
        "fl_result_class": "Анықталған статус",
        "fl_result_confidence": "Сеніімділік деңгейі",
        "fl_recommendation": "Ұсыныс",
        
        # Optimization View
        "opt_title": "Микрожелілік Dispatch Оңтайландыру",
        "opt_load": "Жүктеме сұранысы (кВт)",
        "opt_battery_cap": "Батарея сыйымдылығы (кВт/сағ)",
        "opt_solar_cost": "Күн нарқы ($/кВт·сағ)",
        "opt_wind_cost": "Жел нарқы ($/кВт·сағ)",
        "opt_strategy": "Оңтайландыру стратегиясы",
        "opt_btn": "Диспетчерлік есептеу",
        "opt_recommendation": "Ұсынылатын көз",
        "opt_saving": "Үнемделген қаражат",
        
        # Chat View
        "chat_title": "AI Energy Advisor",
        "chat_welcome": "Сәлеметсіз бе! Мен ЖЭК және микрожелі бойынша AI кеңесшіңізбін. Қандай сұрағыңыз бар?",
        "chat_placeholder": "Сұрағыңызды жазыңыз...",
        "chat_send": "Жіберу",
        "chat_chip1": "Күн панелін қалай тазалау керек?",
        "chat_chip2": "Энергияны қалай оңтайландырамын?",
        "chat_chip3": "Батарея өмірін ұзарту жолдары",
        
        # Live View
        "live_title": "Solarman Live Бақылау",
        "live_status": "Инвертор Статусы",
        "live_power": "Ағымдағы Қуат",
        "live_daily": "Бүгінгі өндіріс",
        "live_weather": "Ауа райы шарттары",
        "live_alerts": "Белсенді ескертулер",
        
        # Settings View
        "st_title": "Қосымша Баптаулары",
        "st_api_url": "Railway 24/7 Бұлттық AI Сервер",
        "st_status_ok": "🟢 24/7 Бұлттық сервермен байланыс белсенді!",
        "st_status_err": "⚠️ Интернет байланысы жоқ! Ұялы деректерді немесе Wi-Fi-ды тексеріңіз.",
    },
    "en": {
        "app_title": "EcoPredict AI Mobile",
        "app_subtitle": "Smart Educational Platform for Hybrid Renewable Energy",
        "nav_overview": "Overview",
        "nav_forecast": "Forecast",
        "nav_faults": "Diagnostics",
        "nav_opt": "Optimization",
        "nav_chat": "AI Advisor",
        "nav_live": "Live",
        "nav_settings": "Settings",
        
        # Overview View
        "ov_hero_title": "EcoEnergy AI Dashboard",
        "ov_hero_sub": "AI-driven forecasting, fault detection, and microgrid dispatch optimization",
        "ov_status_online": "API Online",
        "ov_status_offline": "API Offline",
        "ov_kpi_solar": "Solar Output",
        "ov_kpi_wind": "Wind Output",
        "ov_kpi_load": "System Load",
        "ov_kpi_battery": "Battery Level",
        "ov_quick_actions": "Quick Actions",
        "ov_btn_predict": "Forecast Energy",
        "ov_btn_fault": "Inspect Panel",
        "ov_btn_chat": "Ask AI Assistant",
        
        # Forecast View
        "fc_title": "Energy Generation Forecast",
        "fc_solar_params": "Solar Parameters",
        "fc_wind_params": "Wind Parameters",
        "fc_irradiation": "Irradiance (W/m²)",
        "fc_temp": "Ambient Temp (°C)",
        "fc_module_temp": "Module Temp (°C)",
        "fc_wind_speed": "Wind Speed (m/s)",
        "fc_wind_dir": "Wind Direction (°)",
        "fc_theoretical": "Theoretical Power (kWh)",
        "fc_btn": "Calculate Forecast",
        "fc_result_total": "Total Predicted Generation",
        "fc_result_solar": "Solar Power",
        "fc_result_wind": "Wind Power",
        
        # Faults View
        "fl_title": "Solar Panel Defect & Dust Diagnostics",
        "fl_desc": "Upload a panel image or pick sample images for instant YOLO ML diagnosis",
        "fl_btn_upload": "Upload Image / Gallery",
        "fl_sample_clean": "Clean Panel",
        "fl_sample_dust": "Dusty Panel",
        "fl_sample_crack": "Damaged Panel",
        "fl_result_class": "Detected Condition",
        "fl_result_confidence": "Confidence Level",
        "fl_recommendation": "Recommendation",
        
        # Optimization View
        "opt_title": "Microgrid Dispatch Optimization",
        "opt_load": "Load Demand (kW)",
        "opt_battery_cap": "Battery Capacity (kWh)",
        "opt_solar_cost": "Solar Cost ($/kWh)",
        "opt_wind_cost": "Wind Cost ($/kWh)",
        "opt_strategy": "Dispatch Strategy",
        "opt_btn": "Run Dispatch Solver",
        "opt_recommendation": "Recommended Source",
        "opt_saving": "Estimated Savings",
        
        # Chat View
        "chat_title": "AI Energy Advisor",
        "chat_welcome": "Hello! I am your AI renewable energy consultant. How can I assist you today?",
        "chat_placeholder": "Ask a question...",
        "chat_send": "Send",
        "chat_chip1": "How to clean solar panels?",
        "chat_chip2": "How to optimize battery life?",
        "chat_chip3": "Microgrid dispatch tips",
        
        # Live View
        "live_title": "Solarman Live Telemetry",
        "live_status": "Inverter Status",
        "live_power": "Current Power",
        "live_daily": "Daily Yield",
        "live_weather": "Weather Conditions",
        "live_alerts": "Active Alerts",
        
        # Settings View
        "st_title": "Application Settings",
        "st_api_url": "FastAPI Backend Base URL",
        "st_btn_test": "Test Connection",
        "st_lang": "Application Language",
        "st_theme": "Theme Mode",
        "st_dark": "Dark Theme",
        "st_light": "Light Theme",
        "st_status_ok": "Connection established successfully!",
        "st_status_err": "Error: Unable to connect to backend server.",
    },
}


def get_text(lang: str, key: str, default: str = "") -> str:
    """Get localized string with fallback."""
    dict_lang = LOCALIZATION.get(lang, LOCALIZATION["kk"])
    return dict_lang.get(key, LOCALIZATION["en"].get(key, default or key))
