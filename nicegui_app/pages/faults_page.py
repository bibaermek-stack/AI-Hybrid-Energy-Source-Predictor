"""
Solar Panel Fault & Dust Diagnostics Page for NiceGUI.

Sends the photo to POST /detect and shows its diagnosis as given: "confirmed"
only when two models agree confidently, otherwise "likely", "uncertain", "not
a panel" or "retake" (src/fault_detection/texts.py has the words). This page
used to print fixed verdicts ("93.1% — Dust detected") for any upload and for
three sample buttons, without running a model.
"""

from nicegui import ui

from nicegui_app.api_client import api_client
from nicegui_app.state import state
from src.fault_detection.texts import WORDS, describe, t

TONE_CLASSES = {
    "success": "text-emerald-500",
    "warning": "text-amber-500",
    "error": "text-red-500",
    "info": "text-gray-500",
}


def render_faults_page():
    """Render solar panel fault detection page."""
    with ui.column().classes("w-full gap-6 p-4"):
        ui.label("🔍 " + state.text("fl_title")).classes("text-xl font-bold text-gray-800 dark:text-white")

        with ui.card().classes("w-full p-5 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-slate-900 shadow-sm"):
            ui.label(state.text("fl_upload_hint")).classes("text-sm text-gray-500 mb-3")

            lbl_class = ui.label("—").classes("text-lg font-bold text-gray-800 dark:text-white")
            lbl_conf = ui.label("").classes("text-sm font-semibold text-blue-500")
            lbl_rec = ui.label("").classes("text-xs text-gray-500 mt-2")
            lbl_details = ui.label("").classes("text-xs text-gray-400")

            def show(headline: str, confidence: str, advice: str, details: str, tone: str) -> None:
                lbl_class.set_text(headline)
                lbl_class.classes(replace=f"text-lg font-bold {TONE_CLASSES.get(tone, '')}")
                lbl_conf.set_text(confidence)
                lbl_rec.set_text(advice)
                lbl_details.set_text(details)

            async def handle_upload(e):
                if hasattr(e, "file"):  # NiceGUI 3
                    content, name, ctype = await e.file.read(), e.file.name, e.file.content_type
                else:  # NiceGUI 1-2
                    content, name, ctype = e.content.read(), e.name, e.type
                show("…", "", "", "", "info")
                try:
                    body = await api_client.detect(content, name or "panel.jpg", ctype)
                except Exception as err:
                    show(state.text("fl_failed"), "", str(err), "", "error")
                    return
                dg = body.get("diagnosis")
                if not dg:
                    show(t(WORDS["unavailable"], state.lang), "", str(body.get("diagnosis_error") or ""), "", "warning")
                    return
                d = describe(dg, state.lang)
                show(d["headline"], d["confidence"] or "", d["advice"], "\n".join(d["details"]), d["tone"])

            ui.upload(on_upload=handle_upload, auto_upload=True).props("accept=image/*").classes("w-full mt-2")
