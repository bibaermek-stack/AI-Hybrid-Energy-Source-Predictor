"""
Line chart drawn on a Flet Canvas, for the lab results.

Takes one chart from the labs API (see src/education/labs/runner.py):
{title, x, x_label, y_label, series: [{name, values}], limits: [{value, label}]}.
Flet's own charts live in a separate extension package; three polylines on a
canvas do not justify another native dependency in the APK.
"""

from typing import Any, Dict, List

import flet as ft
import flet.canvas as cv

try:
    from mobile.state import state
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]

PALETTE = ["#38BDF8", "#F59E0B", "#10B981", "#EF4444", "#A78BFA", "#F472B6"]
HEIGHT = 180
PAD_L, PAD_R, PAD_T, PAD_B = 40, 8, 8, 18


def _loc(field: Any) -> str:
    if isinstance(field, dict):
        return str(field.get(state.lang) or field.get("en") or "")
    return str(field or "")


def _tick(v: float, step: float) -> str:
    """Axis label with as many decimals as the tick spacing needs."""
    if float(v).is_integer() and step >= 1:
        decimals = 0
    elif step >= 10:
        decimals = 0
    elif step >= 1:
        decimals = 1
    elif step >= 0.01:
        decimals = 2
    else:
        decimals = 3
    return f"{v:,.{decimals}f}".replace(",", " ")


def _shapes(chart: Dict[str, Any], width: float, height: float) -> List[cv.Shape]:
    c = state.colors
    xs = [float(x) for x in chart.get("x") or []]
    series = [s for s in chart.get("series") or [] if s.get("values")]
    limits = chart.get("limits") or []
    ys = [v for s in series for v in s["values"] if v is not None] + [
        float(l["value"]) for l in limits
    ]
    if len(xs) < 2 or not ys:
        return []
    y_min, y_max = min(ys), max(ys)
    if y_max - y_min < 1e-9:
        y_min, y_max = y_min - 1, y_max + 1
    pad = (y_max - y_min) * 0.06
    y_min, y_max = y_min - pad, y_max + pad
    x_min, x_max = xs[0], xs[-1]
    if x_max == x_min:
        x_max = x_min + 1
    w = max(width - PAD_L - PAD_R, 10)
    h = max(height - PAD_T - PAD_B, 10)

    def px(x: float) -> float:
        return PAD_L + (x - x_min) / (x_max - x_min) * w

    def py(y: float) -> float:
        return PAD_T + (1 - (y - y_min) / (y_max - y_min)) * h

    grid = ft.Paint(color=ft.Colors.with_opacity(0.18, c["text_secondary"]), stroke_width=1)
    label = ft.TextStyle(size=9, color=c["text_secondary"])
    shapes: List[cv.Shape] = []
    y_step = (y_max - y_min) / 3
    for k in range(4):
        yv = y_min + y_step * k
        shapes.append(cv.Line(PAD_L, py(yv), PAD_L + w, py(yv), paint=grid))
        shapes.append(cv.Text(2, py(yv) - 6, _tick(yv, y_step), style=label))
    x_step = (x_max - x_min) / 2
    for xv in (x_min, x_min + x_step, x_max):
        shapes.append(cv.Text(px(xv) - 8, PAD_T + h + 3, _tick(xv, x_step), style=label))
    for lim in limits:
        yv = float(lim["value"])
        shapes.append(
            cv.Line(
                PAD_L,
                py(yv),
                PAD_L + w,
                py(yv),
                paint=ft.Paint(color=c["error"], stroke_width=1.2, stroke_dash_pattern=[5, 4]),
            )
        )
    for i, s in enumerate(series):
        pts = [(px(x), py(v)) for x, v in zip(xs, s["values"]) if v is not None]
        if len(pts) < 2:
            continue
        elements = [cv.Path.MoveTo(*pts[0])] + [cv.Path.LineTo(*p) for p in pts[1:]]
        shapes.append(
            cv.Path(
                elements,
                paint=ft.Paint(
                    color=PALETTE[i % len(PALETTE)], stroke_width=2, style=ft.PaintingStyle.STROKE
                ),
            )
        )
    return shapes


def build_line_chart(chart: Dict[str, Any]) -> ft.Container:
    c = state.colors

    def on_resize(e: cv.CanvasResizeEvent) -> None:
        e.control.shapes = _shapes(chart, e.width, e.height)
        e.control.update()

    canvas = cv.Canvas(shapes=[], height=HEIGHT, expand=True, on_resize=on_resize)
    legend = [
        ft.Row(
            [
                ft.Container(
                    width=10, height=10, border_radius=5, bgcolor=PALETTE[i % len(PALETTE)]
                ),
                ft.Text(_loc(s.get("name")), size=10, color=c["text_secondary"]),
            ],
            spacing=4,
            tight=True,
        )
        for i, s in enumerate(chart.get("series") or [])
    ]
    for lim in chart.get("limits") or []:
        legend.append(
            ft.Row(
                [
                    ft.Container(width=12, height=2, bgcolor=c["error"]),
                    ft.Text(_loc(lim.get("label")), size=10, color=c["text_secondary"]),
                ],
                spacing=4,
                tight=True,
            )
        )
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    _loc(chart.get("title")),
                    size=13,
                    weight=ft.FontWeight.BOLD,
                    color=c["text_primary"],
                ),
                ft.Text(
                    f"{_loc(chart.get('x_label'))} · {chart.get('y_label', '')}",
                    size=10,
                    color=c["text_secondary"],
                ),
                ft.Row([canvas]),
                ft.Row(legend, wrap=True, spacing=10, run_spacing=4),
            ],
            spacing=6,
        ),
        padding=12,
        border_radius=14,
        bgcolor=c["surface"],
        border=ft.Border.all(1, c["card_border"]),
    )
