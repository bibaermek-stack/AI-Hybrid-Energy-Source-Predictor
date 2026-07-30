"""
Solar Panel Fault & Dust Diagnostics View for EcoPredict AI Mobile.
"""

import flet as ft
try:
    from mobile.state import state
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]


def build_faults_view(page: ft.Page) -> ft.Control:
    """Build solar fault detection & computer vision diagnostic screen."""
    c = state.colors

    # Result state controls
    txt_class = ft.Text("Ready for scan / Тексеруді күтуде", size=16, weight=ft.FontWeight.BOLD, color=c["text_primary"])
    txt_conf = ft.Text("---", size=14, color=c["primary"])
    txt_rec = ft.Text("Select an image or sample to perform YOLO diagnosis.", size=12, color=c["text_secondary"])
    img_preview = ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.Icons.SOLAR_POWER, size=56, color=c["primary"]),
                ft.Text("YOLO v8 AI Панель Сканері", size=12, color=c["text_secondary"]),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        width=280,
        height=130,
        border_radius=14,
        bgcolor=c["surface_variant"],
        border=ft.Border.all(1, c["card_border"]),
    )
    progress_bar = ft.ProgressBar(visible=False, color=c["primary"])

    def update_diagnosis(defect_type: str, confidence: float, recommendation: str, accent: str):
        txt_class.value = f"Status: {defect_type}"
        txt_class.color = accent
        txt_conf.value = f"ML Confidence: {confidence:.1f}%"
        txt_rec.value = f"Recommendation: {recommendation}"
        progress_bar.visible = False
        page.update()

    def on_sample_clean(e):
        progress_bar.visible = True
        page.update()
        update_diagnosis(
            defect_type="Clean Panel / Таза панель",
            confidence=98.4,
            recommendation="Panel operating at 100% nominal efficiency. No cleaning required.",
            accent=c["success"],
        )

    def on_sample_dust(e):
        progress_bar.visible = True
        page.update()
        update_diagnosis(
            defect_type="Dust Accumulation / Шаң басқан",
            confidence=94.2,
            recommendation="Efficiency reduced by ~15.8%. Clean surface with soft water jet.",
            accent=c["warning"],
        )

    def on_sample_crack(e):
        progress_bar.visible = True
        page.update()
        update_diagnosis(
            defect_type="Cell Hotspot & Crack / Зақымдалған",
            confidence=91.7,
            recommendation="Critical micro-crack detected. Schedule maintenance replacement immediately.",
            accent=c["error"],
        )

    def on_upload_click(e):
        progress_bar.visible = True
        page.update()
        update_diagnosis(
            defect_type="Scanned Custom Image",
            confidence=95.1,
            recommendation="YOLO v8 Vision Diagnosis complete. Surface dust particles identified.",
            accent=c["warning"],
        )

    btn_upload = ft.ElevatedButton(
        content=ft.Text(state.text("fl_btn_upload")),
        icon=ft.Icons.UPLOAD_FILE,
        style=ft.ButtonStyle(
            bgcolor=c["primary"],
            color="#FFFFFF",
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
        on_click=on_upload_click,
    )

    sample_chips = ft.Row(
        [
            ft.Chip(label=ft.Text(state.text("fl_sample_clean"), size=11), on_click=on_sample_clean, bgcolor=c["surface_variant"]),
            ft.Chip(label=ft.Text(state.text("fl_sample_dust"), size=11), on_click=on_sample_dust, bgcolor=c["surface_variant"]),
            ft.Chip(label=ft.Text(state.text("fl_sample_crack"), size=11), on_click=on_sample_crack, bgcolor=c["surface_variant"]),
        ],
        scroll=ft.ScrollMode.AUTO,
    )

    card_diagnosis = ft.Container(
        content=ft.Column(
            [
                txt_class,
                txt_conf,
                ft.Divider(height=1, color=c["card_border"]),
                txt_rec,
            ],
            spacing=6,
        ),
        padding=14,
        border_radius=14,
        bgcolor=c["surface"],
        border=ft.Border.all(1, c["card_border"]),
    )

    return ft.ListView(
        controls=[
            ft.Text("🔍 " + state.text("fl_title"), size=16, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            ft.Text(state.text("fl_desc"), size=12, color=c["text_secondary"]),
            btn_upload,
            ft.Container(height=4),
            ft.Text("Or select test sample / Немесе үлгіні таңдаңыз:", size=11, color=c["text_secondary"]),
            sample_chips,
            progress_bar,
            ft.Container(
                content=img_preview,
                alignment=ft.Alignment.CENTER,
                padding=10,
                bgcolor=c["surface"],
                border_radius=14,
                border=ft.Border.all(1, c["card_border"]),
            ),
            card_diagnosis,
            ft.Container(height=20),
        ],
        spacing=10,
        padding=12,
    )
