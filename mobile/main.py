"""
EcoPredict AI Cross-Platform Mobile Application Shell.

Navigation: five destinations (nav_bar.TABS) — a bottom bar on phones, a
rail from RAIL_BREAKPOINT px. Secondary screens open from the "More" tab with
a back arrow. Screens are built on first visit and cached; a language or
theme change clears the cache so every screen is rebuilt in the new language
and colours (they read state.colors / state.text when built).
"""

import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
_DIR = Path(__file__).resolve().parent
_ROOT = _DIR.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import flet as ft

try:
    from mobile.api_client import api_client
    from mobile.components.header import build_app_header
    from mobile.components.nav_bar import (
        MORE_KEYS,
        RAIL_BREAKPOINT,
        TAB_KEYS,
        back_target,
        build_bottom_nav,
        build_nav_rail,
        tab_index,
    )
    from mobile.state import state
    from mobile.views.chat_view import build_chat_view
    from mobile.views.faults_view import build_faults_view
    from mobile.views.forecast_hub_view import build_forecast_hub
    from mobile.views.labs_view import build_labs_view
    from mobile.views.learn_view import build_learn_view
    from mobile.views.live_view import build_live_view
    from mobile.views.more_view import TITLE_KEYS, build_more_view
    from mobile.views.optimization_view import build_optimization_view
    from mobile.views.overview_view import build_overview_view
    from mobile.views.settings_view import build_settings_view
    from mobile.views.sustainability_view import build_sustainability_view
    from mobile.views.training_view import build_training_view
except (ImportError, ModuleNotFoundError):
    from api_client import api_client  # type: ignore # pyright: ignore[reportMissingImports]
    from components.header import (
        build_app_header,  # type: ignore # pyright: ignore[reportMissingImports]
    )
    from components.nav_bar import (  # type: ignore # pyright: ignore[reportMissingImports]
        MORE_KEYS,
        RAIL_BREAKPOINT,
        TAB_KEYS,
        back_target,
        build_bottom_nav,
        build_nav_rail,
        tab_index,
    )
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]
    from views.chat_view import (
        build_chat_view,  # type: ignore # pyright: ignore[reportMissingImports]
    )
    from views.faults_view import (
        build_faults_view,  # type: ignore # pyright: ignore[reportMissingImports]
    )
    from views.forecast_hub_view import (
        build_forecast_hub,  # type: ignore # pyright: ignore[reportMissingImports]
    )
    from views.labs_view import (
        build_labs_view,  # type: ignore # pyright: ignore[reportMissingImports]
    )
    from views.learn_view import (
        build_learn_view,  # type: ignore # pyright: ignore[reportMissingImports]
    )
    from views.live_view import (
        build_live_view,  # type: ignore # pyright: ignore[reportMissingImports]
    )
    from views.more_view import (  # type: ignore # pyright: ignore[reportMissingImports]
        TITLE_KEYS,
        build_more_view,
    )
    from views.optimization_view import (
        build_optimization_view,  # type: ignore # pyright: ignore[reportMissingImports]
    )
    from views.overview_view import (
        build_overview_view,  # type: ignore # pyright: ignore[reportMissingImports]
    )
    from views.settings_view import (
        build_settings_view,  # type: ignore # pyright: ignore[reportMissingImports]
    )
    from views.sustainability_view import (
        build_sustainability_view,  # type: ignore # pyright: ignore[reportMissingImports]
    )
    from views.training_view import (
        build_training_view,  # type: ignore # pyright: ignore[reportMissingImports]
    )


PREF_LANG = "ecopredict.lang"
PREF_THEME = "ecopredict.theme"
DESKTOP_PLATFORMS = {ft.PagePlatform.WINDOWS, ft.PagePlatform.MACOS, ft.PagePlatform.LINUX}


async def main(page: ft.Page):
    """Main Flet mobile application entry point with Splash Screen."""
    page.title = "EcoPredict AI"
    page.padding = 0
    page.spacing = 0

    # iPhone 16 frame (393 x 852) for the desktop preview only; on a phone
    # the OS owns the window.
    if not page.web and page.platform in DESKTOP_PLATFORMS:
        try:
            page.window.width = 393
            page.window.height = 852
            page.window.min_width = 360
            page.window.min_height = 700
        except Exception:
            pass

    # ---- saved preferences (language, theme) ----------------------------
    prefs = ft.SharedPreferences()
    page.services.append(prefs)
    page.update()
    try:
        saved_lang = await asyncio.wait_for(prefs.get(PREF_LANG), timeout=3)
        saved_theme = await asyncio.wait_for(prefs.get(PREF_THEME), timeout=3)
        if saved_lang in ("kk", "en"):
            state.lang = saved_lang
        if saved_theme in ("dark", "light"):
            state.theme_mode = saved_theme
    except Exception as err:  # first launch, or storage unavailable
        print(f"Preferences not loaded: {err}")

    async def save_prefs():
        try:
            await prefs.set(PREF_LANG, state.lang)
            await prefs.set(PREF_THEME, state.theme_mode)
        except Exception as err:
            print(f"Preferences not saved: {err}")

    page.theme_mode = ft.ThemeMode.DARK if state.dark_mode else ft.ThemeMode.LIGHT
    t = state.text

    # ---- splash ----------------------------------------------------------
    txt_loading_status = ft.Text(
        t("splash_preparing"),
        size=12,
        weight=ft.FontWeight.W_500,
        color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
    )
    progress_bar = ft.ProgressBar(
        value=0.2,
        width=240,
        color="#3B82F6",
        bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
        border_radius=6,
    )
    splash_screen = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Icon(ft.Icons.ENERGY_SAVINGS_LEAF, color="#3B82F6", size=72),
                    padding=24,
                    border_radius=40,
                    bgcolor=ft.Colors.with_opacity(0.15, "#3B82F6"),
                    border=ft.Border.all(1, ft.Colors.with_opacity(0.3, "#3B82F6")),
                ),
                ft.Container(height=20),
                ft.Text("EcoPredict AI", size=30, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                ft.Text(
                    t("app_subtitle"),
                    size=12,
                    color=ft.Colors.with_opacity(0.75, ft.Colors.WHITE),
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=40),
                progress_bar,
                ft.Container(height=14),
                txt_loading_status,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        expand=True,
        alignment=ft.Alignment.CENTER,
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_CENTER,
            end=ft.Alignment.BOTTOM_CENTER,
            colors=["#0B132B", "#1C2541", "#0B132B"],
        ),
    )

    view_container = ft.Container(content=splash_screen, expand=True)
    page.add(view_container)
    page.update()

    # ---- screens ---------------------------------------------------------
    nav = {"screen": "overview", "wide": None}
    cache: dict = {}
    hub_select: dict = {}
    # A screen with its own inner page (a lab opened from the labs list)
    # registers what Back should do there; see go_back().
    inner_back: dict = {}

    def set_inner_back(screen: str):
        def setter(handler) -> None:
            if handler is None:
                inner_back.pop(screen, None)
            else:
                inner_back[screen] = handler
        return setter

    def build_hub():
        control, select = build_forecast_hub(page)
        hub_select["fn"] = select
        return control

    builders = {
        "overview": lambda: build_overview_view(page, navigate),
        "forecast": build_hub,
        "live": lambda: build_live_view(page),
        "chat": lambda: build_chat_view(page),
        "more": lambda: build_more_view(page, navigate),
        "faults": lambda: build_faults_view(page),
        "opt": lambda: build_optimization_view(page),
        "sustainability": lambda: build_sustainability_view(page),
        "labs": lambda: build_labs_view(page, set_inner_back("labs"), prefs),
        "training": lambda: build_training_view(page),
        "learn": lambda: build_learn_view(page),
        "settings": lambda: build_settings_view(page, refresh_chrome),
    }

    def get_view(key: str) -> ft.Control:
        if key not in cache:
            cache[key] = builders[key]()
        return cache[key]

    def run_reload(view: ft.Control) -> None:
        # Views are cached, so a screen showing live figures would otherwise
        # keep whatever it loaded first. A view opts in by leaving a reload
        # callable (sync or async) in .data.
        reload_fn = getattr(view, "data", None)
        if not callable(reload_fn):
            return

        async def _run():
            res = reload_fn()
            if asyncio.iscoroutine(res):
                await res

        page.run_task(_run)

    # ---- chrome: app bar + navigation ----------------------------------
    def build_header() -> ft.AppBar:
        screen = nav["screen"]

        def on_recheck() -> None:
            page.run_task(recheck)

        if screen in MORE_KEYS:
            return build_app_header(page, on_recheck, on_back=go_back, title=t(TITLE_KEYS[screen]))
        return build_app_header(page, on_recheck)

    def on_tab_change(e) -> None:
        index = e.control.selected_index or 0
        show(TAB_KEYS[index] if index < len(TAB_KEYS) else "overview")

    def apply_layout() -> None:
        """Bottom bar on phones, rail on wide screens; rebuilds nav labels too."""
        wide = (page.width or 0) >= RAIL_BREAKPOINT
        nav["wide"] = wide
        index = tab_index(nav["screen"])
        page.controls.clear()
        if wide:
            page.navigation_bar = None
            page.controls.append(
                ft.Row(
                    [build_nav_rail(index, on_tab_change), ft.VerticalDivider(width=1), view_container],
                    expand=True,
                    spacing=0,
                )
            )
        else:
            page.navigation_bar = build_bottom_nav(index, on_tab_change)
            page.controls.append(view_container)

    def refresh_chrome() -> None:
        """Redraw the app bar (status pill) without touching the screens."""
        page.appbar = build_header()
        page.update()

    def show(key: str, segment: str = "", reload: bool = True) -> None:
        if key not in builders:
            key = "overview"
        nav["screen"] = key
        state.active_tab = key
        if key == "forecast" and segment:
            state.forecast_segment = segment
        view = get_view(key)
        if key == "forecast" and segment and "fn" in hub_select:
            hub_select["fn"](segment)
        view_container.content = view

        index = tab_index(key)
        if page.navigation_bar is not None:
            page.navigation_bar.selected_index = index
        for control in page.controls:
            if isinstance(control, ft.Row) and control.controls and isinstance(control.controls[0], ft.NavigationRail):
                control.controls[0].selected_index = index
        page.appbar = build_header()
        root_view.can_pop = back_target(key) is None
        page.update()
        if reload:
            run_reload(view)

    def navigate(target: str) -> None:
        """Screen key, optionally "forecast:ml" / "forecast:24h"."""
        key, _, segment = target.partition(":")
        show(key, segment)

    def on_state_changed() -> None:
        """Language or theme changed: rebuild every screen, then persist."""
        page.theme_mode = ft.ThemeMode.DARK if state.dark_mode else ft.ThemeMode.LIGHT
        cache.clear()
        inner_back.clear()
        hub_select.clear()
        apply_layout()
        show(nav["screen"])
        page.run_task(save_prefs)

    state.subscribe(on_state_changed)

    # ---- system Back button (Android) ------------------------------------
    # Everything lives in one Flet view, so Back used to pop that view and
    # close the app from any screen. can_pop=False makes Flutter ask first
    # (on_confirm_pop); we refuse the pop and navigate instead. On Home it
    # stays True and Back exits normally.
    root_view = page.views[0]

    def go_back() -> bool:
        """Back inside the current screen first, then to its parent screen.
        False when there is nowhere to go (Home), so the app may close."""
        handler = inner_back.get(nav["screen"])
        if handler is not None and handler():
            return True
        target = back_target(nav["screen"])
        if target is None:
            return False
        show(target)
        return True

    async def on_confirm_pop(e) -> None:
        # Decide before answering Flutter: confirm_pop(True) closes the app.
        handled = go_back()
        await root_view.confirm_pop(not handled)

    root_view.on_confirm_pop = on_confirm_pop

    def on_resize(e) -> None:
        wide = (page.width or 0) >= RAIL_BREAKPOINT
        if wide != nav["wide"]:
            apply_layout()
            page.update()

    page.on_resize = on_resize

    async def recheck() -> None:
        await api_client.check_health()
        refresh_chrome()

    # ---- start-up --------------------------------------------------------
    health_task = asyncio.create_task(api_client.check_health())

    progress_bar.value = 0.60
    txt_loading_status.value = t("splash_loading_models")
    page.update()

    try:
        # shield so a slow backend does not get the health check cancelled —
        # wait_for kills the task on timeout, which left the app permanently
        # "offline" whenever the container took more than 2s to wake up.
        await asyncio.wait_for(asyncio.shield(health_task), timeout=2.0)
    except Exception:
        pass  # still running; watch_health updates the header when it lands

    progress_bar.value = 1.0
    txt_loading_status.value = t("splash_ready")
    page.update()
    await asyncio.sleep(0.1)

    # Transition from the splash to the dashboard.
    apply_layout()
    show("overview")

    async def watch_health() -> None:
        # The header is drawn once; without this a check that finished after
        # the 2 s splash window left it saying "offline" until the next rebuild.
        await health_task
        refresh_chrome()

    if not health_task.done():
        page.run_task(watch_health)


if __name__ == "__main__":
    ft.run(main)

# ============================================================
# Optional FastAPI backend, for deployments that point at this directory.
#
# NOTE: with Railway "Root Directory = mobile", the api/ and src/ packages of
# the repo are outside the deployment, so `from api.routes import router` can
# only ever raise ModuleNotFoundError — leaving a service that answers /health
# but 404s /predict, /chat and every /solarman/* route. Serving the real API
# requires deploying from the repository root instead.
#
# These imports are guarded because this module is also the Flet mobile entry
# point: the APK bundles flet only, so an unguarded `import fastapi` here would
# crash the app on launch.
# ============================================================
import logging
import os

logger = logging.getLogger("mobile-backend")

FastAPI = None  # type: ignore
CORSMiddleware = None  # type: ignore

try:
    from fastapi import FastAPI  # type: ignore
    from fastapi.middleware.cors import CORSMiddleware  # type: ignore

    _FASTAPI_AVAILABLE = True
except ImportError:  # running inside the APK — no server, nothing to do
    _FASTAPI_AVAILABLE = False

app = None

if _FASTAPI_AVAILABLE and FastAPI is not None and CORSMiddleware is not None:
    DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    db_status = "disconnected"

    if DATABASE_URL:
        try:
            import sqlalchemy  # type: ignore # pyright: ignore[reportMissingImports]

            engine = sqlalchemy.create_engine(DATABASE_URL, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(sqlalchemy.text("SELECT 1"))
            db_status = "connected"
            logger.info("PostgreSQL Database connected successfully in mobile backend!")
        except Exception as exc:
            logger.warning("Database connection failed in mobile backend: %s", str(exc))
            db_status = "error_fallback"

    app = FastAPI(
        title="EcoPredict AI Mobile Service",
        description="FastAPI Backend for EcoPredict AI Mobile App & Railway deployment",
        version="2.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount the feature routes first so their /health wins when available.
    api_router_loaded = False
    api_router_error = None
    try:
        from api.routes import router as api_router

        app.include_router(api_router)
        api_router_loaded = True
        logger.info("API router included — feature routes available.")
    except Exception as err:
        api_router_error = f"{type(err).__name__}: {err}"
        logger.error(
            "API router NOT included — /predict, /chat and /solarman/* will return "
            "404. This deployment cannot see the repo's api/ package; deploy from "
            "the repository root instead of mobile/. Cause: %s",
            err,
            exc_info=True,
        )

    @app.get("/")
    async def root_status():
        return {
            "status": "online",
            "service": "EcoPredict AI Mobile Backend",
            "database_url_configured": bool(DATABASE_URL),
            "database_status": db_status,
            "api_router_loaded": api_router_loaded,
            "version": "2.0.0",
        }

    @app.get("/health")
    async def health_check():
        """
        Degraded-mode reply; the router's own /health takes precedence when it
        loads. `api` tells clients whether the feature routes are really mounted
        — reporting "full" without them is what made a broken deployment look
        healthy to the mobile app.
        """
        return {
            "status": "healthy" if api_router_loaded else "degraded",
            "api": "full" if api_router_loaded else "stub",
            "database": db_status,
            "models_loaded": {"solar": api_router_loaded, "wind": api_router_loaded},
            "api_router_error": api_router_error,
        }

    try:
        import flet_fastapi  # type: ignore # pyright: ignore[reportMissingImports]

        app.mount("/app", flet_fastapi.app(main))
    except Exception as err:
        logger.info("flet_fastapi web view not mounted: %s", err)
