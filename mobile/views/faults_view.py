"""
Solar Panel Fault & Dust Diagnostics View for EcoPredict AI Mobile.

Sends the chosen image to POST /detect, which runs the trained YOLO11n model.
Previously this screen ran no detection at all: the upload button and the three
sample chips just printed fixed verdicts ("95.1% — surface dust identified")
without an image ever leaving the device.
"""

import mimetypes
import flet as ft
try:
    from mobile.state import state
    from mobile.api_client import api_client
    from mobile import api_client as api_client_module
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]
    from api_client import api_client  # type: ignore # pyright: ignore[reportMissingImports]
    import api_client as api_client_module  # type: ignore # pyright: ignore[reportMissingImports]

# Advice per class the model was trained on: Clean, Dust, Bird, Electrical,
# Physical, Snow.
RECOMMENDATIONS = {
    "Clean": ("Панель таза. Әрекет қажет емес.", "success"),
    "Dust": ("Шаң басқан. Жуу жоспарлаңыз — өнімділік 10-25% төмендейді.", "warning"),
    "Snow": ("Қар жабыны. Тазартылмайынша өндіріс іс жүзінде нөлге тең.", "warning"),
    "Bird": ("Құс саңғырығы. Жергілікті қызып кету қаупі, тезірек тазалаңыз.", "warning"),
    "Electrical": ("Электрлік ақау белгісі. Инвертор мен қосылымдарды тексеріңіз.", "error"),
    "Physical": ("Физикалық зақым (жарық/сынық). Панельді ауыстыру қажет.", "error"),
}


def build_faults_view(page: ft.Page) -> ft.Control:
    """Solar fault detection screen backed by the real YOLO endpoint."""
    c = state.colors

    txt_class = ft.Text("Тексеруді күтуде", size=16, weight=ft.FontWeight.BOLD, color=c["text_primary"])
    txt_conf = ft.Text("—", size=14, color=c["primary"])
    txt_rec = ft.Text("Панель суретін таңдаңыз — YOLO моделі диагноз қояды.", size=12, color=c["text_secondary"])
    txt_all = ft.Text("", size=11, color=c["text_secondary"], visible=False)

    img_preview = ft.Image(src="", visible=False, width=280, height=160, fit=ft.BoxFit.CONTAIN, border_radius=14)
    placeholder = ft.Column(
        [
            ft.Icon(ft.Icons.SOLAR_POWER, size=56, color=c["primary"]),
            ft.Text("YOLO11 AI Панель Сканері", size=12, color=c["text_secondary"]),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
    )
    preview_box = ft.Container(
        content=placeholder,
        width=280,
        height=160,
        border_radius=14,
        bgcolor=c["surface_variant"],
        border=ft.Border.all(1, c["card_border"]),
        alignment=ft.Alignment.CENTER,
    )
    progress_bar = ft.ProgressBar(visible=False, color=c["primary"])

    def show(status: str, confidence: str, advice: str, accent: str) -> None:
        txt_class.value = status
        txt_class.color = accent
        txt_conf.value = confidence
        txt_rec.value = advice
        progress_bar.visible = False
        page.update()

    async def run_detection(content: bytes, filename: str) -> None:
        progress_bar.visible = True
        txt_class.value = "Талдау жүріп жатыр…"
        txt_class.color = c["text_primary"]
        txt_conf.value = "—"
        txt_rec.value = f"{filename} серверге жіберілді"
        txt_all.visible = False
        page.update()

        content_type = mimetypes.guess_type(filename)[0] or "image/jpeg"
        result = await api_client.detect_fault(content, filename, content_type)

        if result is None:
            # Read through the module: last_http_error is rebound on each failure.
            reason = getattr(api_client_module, "last_http_error", "") or "себебі белгісіз"
            show("Диагноз орындалмады", "—", f"Сервер жауап бермеді. {reason}", c["error"])
            return

        primary = result.get("primary")
        if not primary:
            show(
                "Ақау табылмады",
                "Модель ешнәрсе анықтамады",
                "Суретте таныған нысан жоқ. Панель толық түскен, анығырақ сурет жіберіп көріңіз.",
                c["text_secondary"],
            )
            return

        cls = str(primary.get("class_name", "?"))
        conf = float(primary.get("confidence", 0.0)) * 100
        advice, tone = RECOMMENDATIONS.get(cls, ("Белгісіз класс — қолмен тексеріңіз.", "warning"))
        show(f"Анықталды: {cls}", f"Сенімділік: {conf:.1f}%", advice, c[tone])

        others = result.get("detections") or []
        if len(others) > 1:
            txt_all.value = "Қосымша: " + ", ".join(
                f"{d['class_name']} {float(d['confidence']) * 100:.0f}%" for d in others[1:5]
            )
            txt_all.visible = True
        page.update()

    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    async def on_upload_click(e) -> None:
        # flet 0.86: pick_files is awaitable and returns the files directly;
        # with_data gives the bytes without touching the filesystem, which
        # matters on Android where the picked path is often not readable.
        files = await file_picker.pick_files(
            dialog_title="Панель суретін таңдаңыз",
            allow_multiple=False,
            file_type=ft.FilePickerFileType.IMAGE,
            allowed_extensions=["jpg", "jpeg", "png", "webp", "bmp"],
            with_data=True,
        )
        if not files:
            return
        picked = files[0]

        content = getattr(picked, "bytes", None)
        if not content and picked.path:
            try:
                with open(picked.path, "rb") as fh:
                    content = fh.read()
            except Exception as err:
                show("Файл оқылмады", "—", str(err), c["error"])
                return
        if not content:
            show("Файл оқылмады", "—", "Сурет мазмұны алынбады.", c["error"])
            return

        # flet 0.86 Image.src takes str | bytes, so the picked image renders
        # straight from memory.
        img_preview.src = content
        img_preview.visible = True
        preview_box.content = img_preview
        await run_detection(content, picked.name or "panel.jpg")

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

    card_diagnosis = ft.Container(
        content=ft.Column([txt_class, txt_conf, ft.Divider(height=1, color=c["card_border"]), txt_rec, txt_all], spacing=6),
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
            progress_bar,
            ft.Container(content=preview_box, alignment=ft.Alignment.CENTER, padding=10, bgcolor=c["surface"], border_radius=14, border=ft.Border.all(1, c["card_border"])),
            card_diagnosis,
            ft.Container(height=20),
        ],
        spacing=10,
        padding=12,
        expand=True,
    )
