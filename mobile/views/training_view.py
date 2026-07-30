import flet as ft
try:
    from mobile.state import state
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]


def build_training_view(page: ft.Page) -> ft.Control:
    """Build ML Training metrics & Feature Importance view."""
    c = state.colors

    # Metrics Cards
    card_r2 = ft.Container(
        content=ft.Column(
            [
                ft.Text("R² Модель Дәлдігі", size=11, color=c["text_secondary"]),
                ft.Text("98.4%", size=20, weight=ft.FontWeight.BOLD, color=c["success"]),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=12,
        border_radius=12,
        bgcolor=c["surface"],
        border=ft.Border.all(1, c["card_border"]),
        expand=True,
    )

    card_rmse = ft.Container(
        content=ft.Column(
            [
                ft.Text("RMSE Қателігі", size=11, color=c["text_secondary"]),
                ft.Text("12.4 kW", size=20, weight=ft.FontWeight.BOLD, color=c["primary"]),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=12,
        border_radius=12,
        bgcolor=c["surface"],
        border=ft.Border.all(1, c["card_border"]),
        expand=True,
    )

    card_mae = ft.Container(
        content=ft.Column(
            [
                ft.Text("MAE Төмендеуі", size=11, color=c["text_secondary"]),
                ft.Text("8.7 kW", size=20, weight=ft.FontWeight.BOLD, color=c["secondary"]),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=12,
        border_radius=12,
        bgcolor=c["surface"],
        border=ft.Border.all(1, c["card_border"]),
        expand=True,
    )

    # Feature Importances list
    features = [
        ("Күн Радиациясы (Solar Irradiance)", 0.42, c["accent"]),
        ("Панель Температурасы (Module Temp)", 0.24, c["primary"]),
        ("Жел Жылдамдығы (Wind Speed)", 0.18, c["secondary"]),
        ("Ауа Температурасы (Ambient Temp)", 0.10, c["warning"]),
        ("Теориялық Қуат (Theoretical kW)", 0.06, c["text_secondary"]),
    ]

    feat_controls = []
    for name, ratio, color in features:
        feat_controls.append(
            ft.Column(
                [
                    ft.Row([ft.Text(name, size=12, weight=ft.FontWeight.W_500), ft.Text(f"{ratio*100:.0f}%", size=12, weight=ft.FontWeight.BOLD, color=color)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(width=ratio * 260, height=8, bgcolor=color, border_radius=4),
                ],
                spacing=2,
            )
        )

    return ft.ListView(
        controls=[
            ft.Text("🎓 ML Модель Оқыту Нәтижелері", size=16, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            ft.Row([card_r2, card_rmse, card_mae], spacing=8),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("📊 Модель Факторларының Маңыздылығы (Feature Importance):", size=13, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
                        ft.Divider(height=1, color=c["card_border"]),
                        *feat_controls,
                    ],
                    spacing=10,
                ),
                padding=14,
                border_radius=14,
                bgcolor=c["surface_variant"],
                border=ft.Border.all(1, c["card_border"]),
            ),
        ],
        spacing=12,
        padding=12,
    )
