"""
Global Application State Manager for EcoPredict AI Mobile.
"""

from typing import Callable, Dict, Any, List
try:
    from mobile.config import DEFAULT_API_BASE, COLORS, get_text
except (ImportError, ModuleNotFoundError):
    from config import DEFAULT_API_BASE, COLORS, get_text  # type: ignore # pyright: ignore[reportMissingImports]


class AppState:
    """Singleton container managing app state and theme preferences."""

    def __init__(self):
        self.lang: str = "kk"
        self.theme_mode: str = "dark"
        self.api_base_url: str = DEFAULT_API_BASE
        self.is_api_online: bool = False
        self.models_loaded: Dict[str, bool] = {"solar": False, "wind": False}
        # Why the last health check failed — shown in Settings so a broken
        # backend is diagnosable from the phone instead of silently 404-ing.
        self.api_status_detail: str = ""

        # Telemetry sliders state
        self.irradiation: float = 900.0
        self.ambient_temp: float = 30.0
        self.module_temp: float = 38.0
        self.hour: int = 12
        self.day: int = 15
        self.month: int = 6
        self.wind_speed: float = 6.5
        self.wind_direction: float = 250.0
        self.theoretical_power: float = 750.0

        # Optimization inputs
        self.load_kw: float = 450.0
        self.battery_kw: float = 200.0
        self.solar_cost: float = 0.08
        self.wind_cost: float = 0.06
        self.strategy: str = "hybrid"

        self.active_tab: str = "overview"
        self._listeners: List[Callable[[], None]] = []

    @property
    def dark_mode(self) -> bool:
        return self.theme_mode == "dark"

    @property
    def colors(self) -> Dict[str, str]:
        return COLORS[self.theme_mode]

    def text(self, key: str, default: str = "") -> str:
        return get_text(self.lang, key, default)

    def toggle_theme(self):
        self.theme_mode = "light" if self.theme_mode == "dark" else "dark"
        self.notify()

    def set_language(self, lang: str):
        if lang in ("kk", "en"):
            self.lang = lang
            self.notify()

    def set_api_url(self, url: str):
        if url and url.strip():
            self.api_base_url = url.strip().rstrip("/")
            self.notify()

    def subscribe(self, callback: Callable[[], None]):
        if callback not in self._listeners:
            self._listeners.append(callback)

    def notify(self):
        for cb in list(self._listeners):
            try:
                cb()
            except Exception as e:
                print(f"Error in state listener: {e}")


state = AppState()
