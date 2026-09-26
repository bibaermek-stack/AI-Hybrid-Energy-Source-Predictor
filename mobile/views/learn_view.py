import flet as ft
try:
    from mobile.state import state
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]


def build_learn_view(page: ft.Page) -> ft.Control:
    """Build educational interactive microgrid learning view."""
    c = state.colors
    t = state.text

    # (title key, body key, colour)
    topics = [
        ("learn_pv_title", "learn_pv_body", c["accent"]),
        ("learn_wind_title", "learn_wind_body", c["secondary"]),
        ("learn_bess_title", "learn_bess_body", c["success"]),
        ("learn_dispatch_title", "learn_dispatch_body", c["primary"]),
    ]

    cards = []
    for title_key, body_key, color in topics:
        cards.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row([ft.Icon(ft.Icons.SCHOOL, color=color, size=20), ft.Text(t(title_key), size=13, weight=ft.FontWeight.BOLD, color=c["text_primary"])]),
                        ft.Text(t(body_key), size=12, color=c["text_secondary"]),
                    ],
                    spacing=6,
                ),
                padding=12,
                border_radius=14,
                bgcolor=c["surface"],
                border=ft.Border.all(1, color),
            )
        )

    return ft.ListView(
        controls=[
            ft.Text(t("learn_title"), size=16, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            *cards,
        ],
        spacing=12,
        padding=12,
        expand=True,
    )
