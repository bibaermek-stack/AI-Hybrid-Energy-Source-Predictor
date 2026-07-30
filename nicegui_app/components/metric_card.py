"""
NiceGUI Glassmorphic Metric Card component.
"""

from nicegui import ui


def build_metric_card(title: str, value: str, unit: str = "", icon: str = "bolt", color: str = "text-blue-500", subtitle: str = ""):
    """Build a KPI metric card."""
    with ui.card().classes("p-4 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm w-full bg-white dark:bg-slate-900"):
        with ui.row().classes("w-full items-center justify-between"):
            ui.icon(icon, size="sm").classes(f"{color} p-2 rounded-lg bg-gray-100 dark:bg-slate-800")
            ui.label(title).classes("text-xs font-semibold text-gray-500 dark:text-gray-400")

        with ui.row().classes("items-baseline gap-1 mt-2"):
            ui.label(value).classes("text-2xl font-bold text-gray-900 dark:text-white")
            if unit:
                ui.label(unit).classes(f"text-xs font-semibold {color}")

        if subtitle:
            ui.label(subtitle).classes("text-xs text-gray-400 mt-1")
