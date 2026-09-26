"""
"Forecast" tab for EcoPredict AI Mobile: the instant ML prediction and the
24 h weather-driven forecast, switched with a segmented button. They were two
separate bottom-bar destinations before the bar was cut to five.
"""

import asyncio
import flet as ft
from typing import Callable, Tuple
try:
    from mobile.state import state
    from mobile.views.predictions_view import build_predictions_view
    from mobile.views.forecast_view import build_forecast_view
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]
    from views.predictions_view import build_predictions_view  # type: ignore # pyright: ignore[reportMissingImports]
    from views.forecast_view import build_forecast_view  # type: ignore # pyright: ignore[reportMissingImports]

SEGMENTS = ("ml", "24h")


def build_forecast_hub(page: ft.Page) -> Tuple[ft.Control, Callable[[str], None]]:
    """
    Returns the hub control and a select(segment) function for main.py.

    The hub's .data reloads whichever panel is showing, so on_nav_change keeps
    refreshing it on each visit like any other screen.
    """
    c = state.colors
    t = state.text

    panels = {"ml": build_predictions_view(page), "24h": build_forecast_view(page)}
    if state.forecast_segment not in panels:
        state.forecast_segment = "ml"
    content = ft.Container(content=panels[state.forecast_segment], expand=True)

    def reload_current() -> None:
        fn = getattr(panels[state.forecast_segment], "data", None)
        if not callable(fn):
            return

        async def run():
            res = fn()
            if asyncio.iscoroutine(res):
                await res

        page.run_task(run)

    def select(segment: str) -> None:
        if segment not in panels:
            return
        changed = segment != state.forecast_segment
        state.forecast_segment = segment
        segmented.selected = [segment]
        content.content = panels[segment]
        page.update()
        if changed:
            reload_current()

    segmented = ft.SegmentedButton(
        segments=[
            ft.Segment(value="ml", label=ft.Text(t("hub_ml")), icon=ft.Icon(ft.Icons.AUTO_AWESOME)),
            ft.Segment(value="24h", label=ft.Text(t("hub_24h")), icon=ft.Icon(ft.Icons.SHOW_CHART)),
        ],
        selected=[state.forecast_segment],
        on_change=lambda e: select((e.control.selected or [state.forecast_segment])[0]),
        show_selected_icon=False,
    )

    hub = ft.Column(
        [
            ft.Container(content=segmented, padding=ft.Padding.only(left=12, right=12, top=10), alignment=ft.Alignment.CENTER),
            content,
        ],
        spacing=0,
        expand=True,
    )
    hub.data = reload_current
    return hub, select
