import flet as ft
try:
    from mobile.state import state
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]


def build_sustainability_view(page: ft.Page) -> ft.Control:
    """Build sustainability metrics and CO2 reduction calculator view."""
    c = state.colors

    # Sustainability stats
    card_co2 = ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.Icons.CO2, color=c["success"], size=28),
                ft.Text("Қолайсыз CO2 Төмендеуі", size=11, color=c["text_secondary"]),
                ft.Text("412.8 Тонна", size=18, weight=ft.FontWeight.BOLD, color=c["success"]),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=14,
        border_radius=14,
        bgcolor=c["surface"],
        border=ft.Border.all(1, c["success"]),
        expand=True,
    )

    card_trees = ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.Icons.PARK, color=c["accent"], size=28),
                ft.Text("Балама Тігілген Ағаштар", size=11, color=c["text_secondary"]),
                ft.Text("18,650 Ағаш", size=18, weight=ft.FontWeight.BOLD, color=c["accent"]),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=14,
        border_radius=14,
        bgcolor=c["surface"],
        border=ft.Border.all(1, c["accent"]),
        expand=True,
    )

    card_coal = ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.Icons.LOCAL_FIRE_DEPARTMENT, color=c["warning"], size=28),
                ft.Text("Үнемделген Көмір Тоннасы", size=11, color=c["text_secondary"]),
                ft.Text("245.0 Тонна", size=18, weight=ft.FontWeight.BOLD, color=c["warning"]),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=14,
        border_radius=14,
        bgcolor=c["surface"],
        border=ft.Border.all(1, c["warning"]),
        expand=True,
    )

    return ft.ListView(
        controls=[
            ft.Text("🌱 Экологиялық Тұрақтылық Мониторы", size=16, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            ft.Row([card_co2, card_trees]),
            card_coal,
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("💚 Жасыл Энергия Үлесі (Green Ratio):", size=13, weight=ft.FontWeight.BOLD),
                        ft.ProgressBar(value=0.88, color=c["success"], bgcolor="rgba(255,255,255,0.1)", height=12),
                        ft.Row([ft.Text("Микрожелі Жасыл Энергиясы: 88.4%"), ft.Text("Максимум", color=c["success"])], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ],
                    spacing=6,
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
