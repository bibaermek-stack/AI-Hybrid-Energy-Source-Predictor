import flet as ft
try:
    from mobile.state import state
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]


def build_learn_view(page: ft.Page) -> ft.Control:
    """Build educational interactive microgrid learning view."""
    c = state.colors

    topics = [
        ("☀️ Күн Фотовольтаикасы (Solar PV Physics)", "Күн радиациясын P-N өткелі арқылы тікелей тұрақты токқа (DC) айналдыру физикалық негіздері. Панель тиімділігі температураның әр 1°C көтерілуіне ~0.4%-ға төмендейді.", c["accent"]),
        ("💨 Жел Турбиналары (Wind Aerodynamics)", "Жел ағынының кинетикалық энергиясын турбина қалақшалары арқылы айналмалы механикалық қуатқа және генератор арқылы айнымалы токқа (AC) түрлендіру.", c["secondary"]),
        ("🔋 Батарея Жүйелері (BESS Energy Storage)", "Литий-иондық батареялар арқылы пиктік жүктемені тегістеу және энергияны оңтайлы сақтау. Батареяның зарядталу деңгейі (SOC) микрожелі тұрақтылығын сақтайды.", c["success"]),
        ("⚡ Оңтайлы Диспетчерлеу (Microgrid Dispatch)", "LCOE (Энергияның келтірілген құны) негізінде ең арзан және экологиялық таза генерация көзін таңдайтын алгоритмдік диспетчерлік оңтайландыру.", c["primary"]),
    ]

    cards = []
    for title, desc, color in topics:
        cards.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row([ft.Icon(ft.Icons.SCHOOL, color=color, size=20), ft.Text(title, size=13, weight=ft.FontWeight.BOLD, color=c["text_primary"])]),
                        ft.Text(desc, size=12, color=c["text_secondary"]),
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
            ft.Text("📚 ЖЭК және Микрожелі Оқыту Модулі", size=16, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            *cards,
        ],
        spacing=12,
        padding=12,
    )
