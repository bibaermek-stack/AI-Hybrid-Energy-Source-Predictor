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
# Physical, Snow — (i18n key, colour tone).
RECOMMENDATIONS = {
    "Clean": ("fl_rec_clean", "success"),
    "Dust": ("fl_rec_dust", "warning"),
    "Snow": ("fl_rec_snow", "warning"),
    "Bird": ("fl_rec_bird", "warning"),
    "Electrical": ("fl_rec_electrical", "error"),
    "Physical": ("fl_rec_physical", "error"),
}

# POST /detect rejects anything larger (api/routes.py MAX_UPLOAD_BYTES).
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
# Re-encode picked photos on the device: a phone camera JPEG is often 4–12 MB,
# which is slow over mobile data and can exceed the server limit. YOLO runs at
# 640 px, so this costs the model nothing.
PICK_COMPRESSION_QUALITY = 80

# The camera comes from the flet-camera extension, which is compiled into the
# Android/iOS build only; the desktop and web preview clients do not carry it
# and would draw "Unknown control: Camera".
MOBILE_PLATFORMS = {ft.PagePlatform.ANDROID, ft.PagePlatform.IOS}


def camera_supported(page) -> bool:
    return getattr(page, "platform", None) in MOBILE_PLATFORMS and not getattr(page, "web", False)


def build_faults_view(page: ft.Page) -> ft.Control:
    """Solar fault detection screen backed by the real YOLO endpoint."""
    c = state.colors
    t = state.text

    txt_class = ft.Text(t("fl_waiting"), size=16, weight=ft.FontWeight.BOLD, color=c["text_primary"])
    txt_conf = ft.Text("—", size=14, color=c["primary"])
    txt_rec = ft.Text(t("fl_hint"), size=12, color=c["text_secondary"])
    txt_all = ft.Text("", size=11, color=c["text_secondary"], visible=False)

    img_preview = ft.Image(src="", visible=False, width=280, height=160, fit=ft.BoxFit.CONTAIN, border_radius=14)
    placeholder = ft.Column(
        [
            ft.Icon(ft.Icons.SOLAR_POWER, size=56, color=c["primary"]),
            ft.Text(t("fl_scanner"), size=12, color=c["text_secondary"]),
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
        txt_class.value = t("fl_analyzing")
        txt_class.color = c["text_primary"]
        txt_conf.value = "—"
        txt_rec.value = t("fl_sent", filename=filename)
        txt_all.visible = False
        page.update()

        content_type = mimetypes.guess_type(filename)[0] or "image/jpeg"
        result = await api_client.detect_fault(content, filename, content_type)

        if result is None:
            # Read through the module: last_http_error is rebound on each failure.
            reason = getattr(api_client_module, "last_http_error", "") or t("reason_unknown")
            show(t("fl_failed"), "—", t("fl_err_server", reason=reason), c["error"])
            return

        primary = result.get("primary")
        if not primary:
            show(t("fl_none_found"), t("fl_none_conf"), t("fl_none_advice"), c["text_secondary"])
            return

        cls = str(primary.get("class_name", "?"))
        conf = float(primary.get("confidence", 0.0)) * 100
        advice_key, tone = RECOMMENDATIONS.get(cls, ("fl_rec_unknown", "warning"))
        show(t("fl_detected", cls=cls), t("fl_confidence", pct=conf), t(advice_key), c[tone])

        others = result.get("detections") or []
        if len(others) > 1:
            txt_all.value = t("fl_also") + ", ".join(
                f"{d['class_name']} {float(d['confidence']) * 100:.0f}%" for d in others[1:5]
            )
            txt_all.visible = True
        page.update()

    file_picker = ft.FilePicker()
    # FilePicker subclasses Service, not Control, in flet 0.86+. Putting it in
    # page.overlay made Flutter render a full-height red "Unknown control:
    # FilePicker" banner over every screen.
    page.services.append(file_picker)

    async def analyze_image(content: bytes, filename: str) -> None:
        """Size check, preview, then YOLO — shared by the gallery and the camera."""
        if len(content) > MAX_UPLOAD_BYTES:
            # Say so here rather than uploading megabytes to get a 413 back.
            show(
                t("fl_too_large"),
                "—",
                t("fl_too_large_advice", mb=len(content) / 1024 / 1024, limit=MAX_UPLOAD_BYTES // 1024 // 1024),
                c["error"],
            )
            return
        # Image.src takes str | bytes, so the picked image renders from memory.
        img_preview.src = content
        img_preview.visible = True
        preview_box.content = img_preview
        await run_detection(content, filename)

    # ---- camera (Android / iOS) -------------------------------------------
    camera_holder = ft.Container(height=360, border_radius=14, bgcolor="#000000", clip_behavior=ft.ClipBehavior.HARD_EDGE)
    camera_status = ft.Text("", size=12, color=c["text_secondary"])
    camera_ref: dict = {}

    def close_camera() -> None:
        # Dropping the control from the tree disposes the native controller.
        camera_ref.clear()
        camera_holder.content = None
        camera_panel.visible = False
        page.update()

    async def on_camera_click(e) -> None:
        import flet_camera as fc  # only present in the mobile build

        cam = fc.Camera(expand=True, preview_enabled=True)
        camera_holder.content = cam
        camera_panel.visible = True
        camera_status.value = t("fl_cam_starting")
        btn_capture.disabled = True
        page.update()
        try:
            cameras = await cam.get_available_cameras()
            if not cameras:
                raise RuntimeError(t("fl_cam_none"))
            back = next((d for d in cameras if d.lens_direction == fc.CameraLensDirection.BACK), cameras[0])
            # 720p is plenty for a 640 px model; no audio, so no microphone prompt.
            await cam.initialize(back, fc.ResolutionPreset.HIGH, enable_audio=False)
        except Exception as err:
            close_camera()
            show(t("fl_cam_failed"), "—", t("fl_cam_failed_advice", reason=str(err) or type(err).__name__), c["error"])
            return
        camera_ref["cam"] = cam
        camera_status.value = t("fl_cam_ready")
        btn_capture.disabled = False
        page.update()

    async def on_capture_click(e) -> None:
        cam = camera_ref.get("cam")
        if cam is None:
            return
        btn_capture.disabled = True
        camera_status.value = t("fl_cam_capturing")
        page.update()
        try:
            content = await cam.take_picture()
        except Exception as err:
            close_camera()
            show(t("fl_cam_failed"), "—", t("fl_cam_failed_advice", reason=str(err) or type(err).__name__), c["error"])
            return
        close_camera()
        if not content:
            show(t("fl_read_failed"), "—", t("fl_read_empty"), c["error"])
            return
        await analyze_image(bytes(content), "camera.jpg")

    btn_capture = ft.Button(
        content=ft.Text(t("fl_cam_capture")),
        icon=ft.Icons.CAMERA,
        style=ft.ButtonStyle(bgcolor=c["primary"], color="#FFFFFF", shape=ft.RoundedRectangleBorder(radius=12)),
        on_click=on_capture_click,
        disabled=True,
        expand=True,
    )
    camera_panel = ft.Column(
        [
            camera_holder,
            camera_status,
            ft.Row(
                [
                    btn_capture,
                    ft.OutlinedButton(
                        content=ft.Text(t("fl_cam_cancel")),
                        on_click=lambda e: close_camera(),
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                    ),
                ],
                spacing=10,
            ),
        ],
        spacing=8,
        visible=False,
    )

    async def on_upload_click(e) -> None:
        # pick_files is awaitable and returns the files directly; with_data gives
        # the bytes without touching the filesystem, which matters on Android
        # where the picked path is often not readable.
        files = await file_picker.pick_files(
            dialog_title=t("fl_pick_title"),
            allow_multiple=False,
            file_type=ft.FilePickerFileType.IMAGE,
            allowed_extensions=["jpg", "jpeg", "png", "webp", "bmp"],
            with_data=True,
            compression_quality=PICK_COMPRESSION_QUALITY,
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
                show(t("fl_read_failed"), "—", str(err), c["error"])
                return
        if not content:
            show(t("fl_read_failed"), "—", t("fl_read_empty"), c["error"])
            return
        await analyze_image(content, picked.name or "panel.jpg")

    btn_upload = ft.Button(
        content=ft.Text(t("fl_btn_upload")),
        icon=ft.Icons.UPLOAD_FILE,
        style=ft.ButtonStyle(
            bgcolor=c["primary"],
            color="#FFFFFF",
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
        on_click=on_upload_click,
        expand=True,
    )
    buttons = [btn_upload]
    if camera_supported(page):
        buttons.append(
            ft.Button(
                content=ft.Text(t("fl_btn_camera")),
                icon=ft.Icons.PHOTO_CAMERA,
                style=ft.ButtonStyle(bgcolor=c["secondary"], color="#FFFFFF", shape=ft.RoundedRectangleBorder(radius=12)),
                on_click=on_camera_click,
                expand=True,
            )
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
            ft.Text("🔍 " + t("fl_title"), size=16, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            ft.Text(t("fl_desc"), size=12, color=c["text_secondary"]),
            ft.Row(buttons, spacing=10),
            camera_panel,
            progress_bar,
            ft.Container(content=preview_box, alignment=ft.Alignment.CENTER, padding=10, bgcolor=c["surface"], border_radius=14, border=ft.Border.all(1, c["card_border"])),
            card_diagnosis,
            ft.Container(height=20),
        ],
        spacing=10,
        padding=12,
        expand=True,
    )
