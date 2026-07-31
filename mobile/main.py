"""
EcoPredict AI Cross-Platform Mobile Application Shell.
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
    from mobile.state import state
    from mobile.api_client import api_client
    from mobile.components.header import build_app_header
    from mobile.components.nav_bar import build_bottom_nav

    from mobile.views.overview_view import build_overview_view
    from mobile.views.predictions_view import build_predictions_view
    from mobile.views.forecast_view import build_forecast_view
    from mobile.views.faults_view import build_faults_view
    from mobile.views.training_view import build_training_view
    from mobile.views.learn_view import build_learn_view
    from mobile.views.optimization_view import build_optimization_view
    from mobile.views.sustainability_view import build_sustainability_view
    from mobile.views.labs_view import build_labs_view
    from mobile.views.chat_view import build_chat_view
    from mobile.views.live_view import build_live_view
    from mobile.views.settings_view import build_settings_view
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]
    from api_client import api_client  # type: ignore # pyright: ignore[reportMissingImports]
    from components.header import build_app_header  # type: ignore # pyright: ignore[reportMissingImports]
    from components.nav_bar import build_bottom_nav  # type: ignore # pyright: ignore[reportMissingImports]

    from views.overview_view import build_overview_view  # type: ignore # pyright: ignore[reportMissingImports]
    from views.predictions_view import build_predictions_view  # type: ignore # pyright: ignore[reportMissingImports]
    from views.forecast_view import build_forecast_view  # type: ignore # pyright: ignore[reportMissingImports]
    from views.faults_view import build_faults_view  # type: ignore # pyright: ignore[reportMissingImports]
    from views.training_view import build_training_view  # type: ignore # pyright: ignore[reportMissingImports]
    from views.learn_view import build_learn_view  # type: ignore # pyright: ignore[reportMissingImports]
    from views.optimization_view import build_optimization_view  # type: ignore # pyright: ignore[reportMissingImports]
    from views.sustainability_view import build_sustainability_view  # type: ignore # pyright: ignore[reportMissingImports]
    from views.labs_view import build_labs_view  # type: ignore # pyright: ignore[reportMissingImports]
    from views.chat_view import build_chat_view  # type: ignore # pyright: ignore[reportMissingImports]
    from views.live_view import build_live_view  # type: ignore # pyright: ignore[reportMissingImports]
    from views.settings_view import build_settings_view  # type: ignore # pyright: ignore[reportMissingImports]


async def main(page: ft.Page):
    """Main Flet mobile application entry point with Splash Screen."""
    page.title = "EcoPredict AI Mobile"
    page.padding = 0
    page.spacing = 0

    # Dynamic theme mode
    page.theme_mode = ft.ThemeMode.DARK if state.dark_mode else ft.ThemeMode.LIGHT

    # Dynamic Splash Loading Controls
    txt_loading_status = ft.Text(
        "AI модельдері дайындалуда...",
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

    # 1. Fullscreen Splash Loading Page
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
                ft.Text(
                    "EcoPredict AI",
                    size=30,
                    weight=ft.FontWeight.BOLD,
                    color="#FFFFFF",
                ),
                ft.Text(
                    "Гибридті ЖЭК үшін ақылды білім беру платформасы",
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

    view_container = ft.Container(
        content=splash_screen,
        expand=True,
    )

    # Render Loading Page instantly on startup
    page.add(view_container)
    page.update()

    # Refresh UI helper
    def refresh_ui():
        page.theme_mode = ft.ThemeMode.DARK if state.dark_mode else ft.ThemeMode.LIGHT
        page.appbar = build_app_header(page, refresh_ui)
        page.update()

    view_keys = ["overview", "predictions", "forecast", "faults", "training", "opt", "sustainability", "labs", "chat", "live", "settings"]

    def on_nav_change(view_key: str):
        if view_key in views:
            state.active_tab = view_key
            target = views[view_key]
            view_container.content = target
            if view_key in view_keys and page.navigation_bar:
                page.navigation_bar.selected_index = view_keys.index(view_key)
            page.update()
            # Views are built once and cached, so a screen showing live figures
            # would otherwise keep whatever it loaded at startup. A view opts in
            # by leaving an async reload callable in .data.
            reload_fn = getattr(target, "data", None)
            if callable(reload_fn):
                page.run_task(reload_fn)

    # Views Registry
    views = {
        "overview": build_overview_view(page, on_nav_change),
        "predictions": build_predictions_view(page),
        "forecast": build_forecast_view(page),
        "faults": build_faults_view(page),
        "training": build_training_view(page),
        "learn": build_learn_view(page),
        "opt": build_optimization_view(page),
        "sustainability": build_sustainability_view(page),
        "labs": build_labs_view(page),
        "chat": build_chat_view(page),
        "live": build_live_view(page),
        "settings": build_settings_view(page, refresh_ui),
    }

    # Dynamic Step-by-Step Loading Animation
    health_task = asyncio.create_task(api_client.check_health())

    progress_bar.value = 0.60
    txt_loading_status.value = "Solar & Wind ML модельдері жүктелуде..."
    page.update()

    try:
        # shield so a slow backend does not get the health check cancelled —
        # wait_for kills the task on timeout, which left the app permanently
        # "offline" whenever the container took more than 2s to wake up.
        await asyncio.wait_for(asyncio.shield(health_task), timeout=2.0)
    except Exception:
        pass  # still running; it updates the header when it lands

    progress_bar.value = 1.0
    txt_loading_status.value = "Жүйе сәтті іске қосылды! 🚀"
    page.update()
    await asyncio.sleep(0.1)

    # Transition from Loading Page to Main Dashboard
    view_container.content = views["overview"]
    view_container.padding = 12
    page.appbar = build_app_header(page, refresh_ui)
    page.navigation_bar = build_bottom_nav(0, lambda e: on_nav_change(view_keys[e.control.selected_index] if e.control.selected_index < len(view_keys) else "overview"))
    page.update()

    # Only now that the dashboard is mounted is it safe to fetch live figures.
    overview_reload = getattr(views["overview"], "data", None)
    if callable(overview_reload):
        page.run_task(overview_reload)


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

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    _FASTAPI_AVAILABLE = True
except ImportError:  # running inside the APK — no server, nothing to do
    _FASTAPI_AVAILABLE = False

app = None

if _FASTAPI_AVAILABLE:
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
