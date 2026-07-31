"""
Glassmorphic Metric Card component for mobile KPI dashboard.
"""

import flet as ft
try:
    from mobile.state import state
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]


from typing import Any

def build_metric_card(
    title: str,
    value: str,
    unit: str = "",
    icon: Any = ft.Icons.BOLT,
    accent_color: str = "#3B82F6",
    subtitle: str = "",
    value_ref: Any = None,
    subtitle_ref: Any = None,
) -> ft.Container:
    """
    Build a metric card control.

    Pass value_ref / subtitle_ref (ft.Ref[ft.Text]) to keep a handle on the
    text controls, so a caller can refresh the figures in place once live data
    arrives instead of rebuilding the whole card.
    """
    c = state.colors

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Icon(icon, color=accent_color, size=20),
                            padding=8,
                            border_radius=10,
                            bgcolor=c["surface_variant"],
                        ),
                        ft.Container(expand=True),
                        ft.Text(
                            title,
                            size=12,
                            weight=ft.FontWeight.W_500,
                            color=c["text_secondary"],
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Row(
                    [
                        ft.Text(
                            value,
                            size=22,
                            weight=ft.FontWeight.BOLD,
                            color=c["text_primary"],
                            ref=value_ref,
                        ),
                        ft.Text(
                            unit,
                            size=12,
                            weight=ft.FontWeight.W_500,
                            color=accent_color,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.BASELINE,
                    spacing=4,
                ),
                ft.Text(
                    subtitle,
                    size=10,
                    color=c["text_secondary"],
                    visible=bool(subtitle),
                    ref=subtitle_ref,
                ) if (subtitle or subtitle_ref) else ft.Container(),
            ],
            spacing=8,
        ),
        padding=14,
        border_radius=14,
        bgcolor=c["surface"],
        border=ft.Border.all(1, c["card_border"]),
    )
