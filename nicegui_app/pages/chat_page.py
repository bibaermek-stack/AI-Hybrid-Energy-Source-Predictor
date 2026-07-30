"""
AI Energy Advisor Chat Page for NiceGUI.
"""

from nicegui import ui
from nicegui_app.state import state
from nicegui_app.api_client import api_client


def render_chat_page():
    """Render AI Advisor chat page."""
    with ui.column().classes("w-full gap-4 p-4"):
        ui.label("💬 " + state.text("chat_title")).classes("text-xl font-bold text-gray-800 dark:text-white")

        with ui.card().classes("w-full p-4 h-96 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-slate-900 shadow-sm overflow-y-auto") as chat_box:
            ui.chat_message(state.text("chat_welcome"), name="EcoPredict AI", sent=False).classes("text-sm")

        async def send_msg(text: str):
            if not text.strip():
                return
            with chat_box:
                ui.chat_message(text, name="User", sent=True).classes("text-sm")
            inp_text.set_value("")

            spinner = ui.spinner(size="sm")
            reply = await api_client.chat(text)
            spinner.delete()

            with chat_box:
                ui.chat_message(reply, name="EcoPredict AI", sent=False).classes("text-sm")

        with ui.row().classes("w-full gap-2 items-center"):
            inp_text = ui.input(placeholder=state.text("chat_placeholder")).classes("flex-grow")
            ui.button(icon="send", on_click=lambda: send_msg(inp_text.value or "")).props("flat color=primary round")

        with ui.row().classes("gap-2 mt-1"):
            ui.chip("Күн панелін тазалау?", on_click=lambda: send_msg("Күн панелін тазалау ұсыныстары?")).props("outline dense")
            ui.chip("Энергия оңтайландыру?", on_click=lambda: send_msg("Микрожеліде энергияны қалай оңтайландырамын?")).props("outline dense")
            ui.chip("Батарея сыйымдылығы?", on_click=lambda: send_msg("Батарея зарядын сақтау жолдары")).props("outline dense")
