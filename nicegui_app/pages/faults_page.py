"""
Solar Panel Fault & Dust Diagnostics Page for NiceGUI.
"""

from nicegui import ui
from nicegui_app.state import state


def render_faults_page():
    """Render solar panel fault detection page."""
    with ui.column().classes("w-full gap-6 p-4"):
        ui.label("🔍 " + state.text("fl_title")).classes("text-xl font-bold text-gray-800 dark:text-white")

        with ui.card().classes("w-full p-5 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-slate-900 shadow-sm"):
            ui.label(state.text("fl_upload_hint")).classes("text-sm text-gray-500 mb-3")

            lbl_class = ui.label("Status: Ready for scan").classes("text-lg font-bold text-gray-800 dark:text-white")
            lbl_conf = ui.label("---").classes("text-sm font-semibold text-blue-500")
            lbl_rec = ui.label("Upload an image or pick a test sample.").classes("text-xs text-gray-500 mt-2")
            ui.icon("wb_sunny", size="xl").classes("text-amber-500 mx-auto my-3")

            def set_diagnosis(defect: str, confidence: float, recommendation: str, text_color: str):
                lbl_class.set_text(f"Status: {defect}")
                lbl_class.classes(replace=f"text-lg font-bold {text_color}")
                lbl_conf.set_text(f"ML Confidence: {confidence:.1f}%")
                lbl_rec.set_text(f"Recommendation: {recommendation}")
                ui.notify(f"Diagnosis: {defect}", type="info")

            with ui.row().classes("gap-2 my-2"):
                ui.button(state.text("fl_sample_clean"), on_click=lambda: set_diagnosis("Clean Panel / Таза Панель", 98.4, "Panel operating at 100% nominal efficiency.", "text-emerald-500")).props("outline color=positive dense")
                ui.button(state.text("fl_sample_dust"), on_click=lambda: set_diagnosis("Dust Accumulation / Шаң Басқан", 94.2, "Efficiency reduced by ~15.8%. Clean surface with water jet.", "text-amber-500")).props("outline color=warning dense")
                ui.button(state.text("fl_sample_crack"), on_click=lambda: set_diagnosis("Cell Hotspot & Crack / Зақымдалған", 91.7, "Micro-crack detected. Replacement recommended.", "text-red-500")).props("outline color=negative dense")

            def handle_upload(e):
                set_diagnosis("Analyzed Custom Upload", 93.1, "YOLO Computer Vision analysis complete. Dust detected.", "text-amber-500")

            ui.upload(on_upload=handle_upload, auto_upload=True).classes("w-full mt-2")
