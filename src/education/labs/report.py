"""
A student's lab report as one printable HTML file.

The site offers it for download under each lab: who did it, the parameters of
the last run, its results and charts, the practice tasks solved and the test
score, and room for the conclusion and signatures. The file needs nothing but
a browser (print it to PDF), not even the internet: the formulas in the task
prompts are turned into plain HTML (Greek letters, sub- and superscripts).
"""

from __future__ import annotations

import html
import math
import re
from datetime import datetime
from typing import Any, Iterable

from src.education.inverter_lab import SCENARIOS
from src.education.lab_tasks import LAB_TASKS
from src.education.labs.lab_registry import LAB_IDS, LABS
from src.education.labs.lab_tests import PASS_PERCENT, public_test
from src.education.labs.runner import list_params

LAB_3D = "lab_inverter_wiring"
PALETTE = ["#2563eb", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6", "#0891b2"]

_SYMBOLS = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "Delta": "Δ", "eta": "η",
    "theta": "θ", "lambda": "λ", "mu": "μ", "pi": "π", "rho": "ρ", "sigma": "σ",
    "Sigma": "Σ", "sum": "Σ", "tau": "τ", "phi": "φ", "varphi": "φ", "omega": "ω",
    "Omega": "Ω", "times": "×", "cdot": "·", "circ": "°", "propto": "∝", "approx": "≈",
    "le": "≤", "leq": "≤", "ge": "≥", "geq": "≥", "pm": "±", "to": "→", "infty": "∞",
    "max": "max", "min": "min", "ln": "ln", "log": "log", "left": "", "right": "",
}  # fmt: skip
_BRACED = re.compile(r"\\(?:mathrm|text|operatorname|mathbf|mathit)\{([^{}]*)\}")
_FRAC = re.compile(r"\\frac\{([^{}]*)\}\{([^{}]*)\}")
_SCRIPT = re.compile(r"([_^])(\{[^{}]*\}|\\?[^\s{}\\]|\\[A-Za-z]+)")


def _math_to_html(tex: str) -> str:
    # Symbols first, while "\circ\mathrm{C}" still has its backslashes apart.
    out = re.sub(r"\\([A-Za-z]+)", lambda m: _SYMBOLS.get(m.group(1), m.group(0)), tex)
    out = _BRACED.sub(r"\1", out)
    out = _FRAC.sub(r"(\1)/(\2)", out)
    for escape, plain in (
        ("\\,", "\u2009"),
        ("\\;", " "),
        ("\\!", ""),
        ("\\%", "%"),
        ("\\$", "$"),
    ):
        out = out.replace(escape, plain)
    out = re.sub(r"\\([A-Za-z]+)", r"\1", out)  # any other command: its name

    def script(m: re.Match) -> str:
        body = m.group(2).strip("{}")
        if body == "°":
            return "°"
        tag = "sub" if m.group(1) == "_" else "sup"
        return f"<{tag}>{body}</{tag}>"

    out = _SCRIPT.sub(script, out)
    return f"<i>{out.replace('{', '').replace('}', '')}</i>"


def latex_to_html(text: str) -> str:
    """Escaped text whose $…$ formulas are written with Unicode and <sub>/<sup>."""
    parts = re.split(r"(?<!\\)\$(.+?)(?<!\\)\$", html.escape(text, quote=False))
    return "".join(
        _math_to_html(p) if i % 2 else p.replace("\\$", "$") for i, p in enumerate(parts)
    )


_TEXT = {
    "report": ("Lab report", "Зертханалық жұмыс есебі"),
    "student": ("Student", "Студент"),
    "group": ("Group", "Тобы"),
    "date": ("Date", "Күні"),
    "lab": ("Lab", "Зертхана"),
    "level": ("Level · time", "Деңгейі · уақыты"),
    "objectives": ("Objectives", "Мақсаты"),
    "params": ("Parameters of the run", "Іске қосу параметрлері"),
    "results": ("Results", "Нәтижелер"),
    "no_run": (
        "The lab was not run in this session.",
        "Бұл сессияда зертхана іске қосылмаған.",
    ),
    "tasks": ("Practice tasks", "Жаттығу тапсырмалары"),
    "tasks_done": ("Solved: {done} of {total}", "Орындалды: {total}-тің {done}-і"),
    "work3d": ("Work in the 3D model", "3D модельдегі жұмыс"),
    "scenarios": ("Fault scenarios fixed", "Түзетілген ақау сценарийлері"),
    "no_scenarios": ("No fault scenario fixed yet.", "Әзірге ақау сценарийі түзетілмеген."),
    "last_check": (
        "Last system check: {s} of {t} items right",
        "Жүйені соңғы тексеру: {t} тармақтың {s}-і дұрыс",
    ),
    "test": ("Test", "Тест"),
    "best": (
        "Best score: {p:.0f} % (pass mark {pm:.0f} %)",
        "Ең жоғары нәтиже: {p:.0f} % (өту шегі {pm:.0f} %)",
    ),
    "no_test": ("The test was not taken yet.", "Тест әлі тапсырылмаған."),
    "last": ("Last attempt: {s} of {t} ({p:.0f} %)", "Соңғы әрекет: {t}-тің {s}-і ({p:.0f} %)"),
    "passed": ("Passed — the lab is completed.", "Өтті — зертхана аяқталды."),
    "failed": ("Not passed yet.", "Әлі өтпеді."),
    "conclusion": ("Conclusion", "Қорытынды"),
    "conclusion_hint": (
        "What did the results show? Compare them with the theory.",
        "Нәтижелер нені көрсетті? Теориямен салыстырыңыз.",
    ),
    "sign_student": ("Student's signature", "Студенттің қолы"),
    "sign_teacher": ("Teacher's signature", "Оқытушының қолы"),
    "print": ("Print or save as PDF: Ctrl+P", "Басып шығару немесе PDF: Ctrl+P"),
    "value": ("Value", "Мәні"),
    "quantity": ("Quantity", "Шама"),
    "parameter": ("Parameter", "Параметр"),
}


def _t(key: str, lang: str, **fmt: Any) -> str:
    en, kk = _TEXT[key]
    text = kk if lang == "kk" else en
    return text.format(**fmt) if fmt else text


def _loc(field: Any, lang: str) -> str:
    if isinstance(field, dict):
        return str(field.get(lang) or field.get("en") or "")
    return str(field or "")


def _e(text: Any) -> str:
    return html.escape(str(text), quote=True)


def lab_number(lab_id: str) -> int:
    return LAB_IDS.index(lab_id) + 1 if lab_id in LAB_IDS else 0


_TRANSLIT = dict(
    pair.split(":")
    for pair in (
        "а:a ә:a б:b в:v г:g ғ:g д:d е:e ё:yo ж:zh з:z и:i й:i к:k қ:q л:l м:m н:n ң:n "
        "о:o ө:o п:p р:r с:s т:t у:u ұ:u ү:u ф:f х:h һ:h ц:ts ч:ch ш:sh щ:shch ъ:- "
        "ы:y і:i ь:- э:e ю:yu я:ya"
    ).split()
)


def report_filename(lab_id: str, student: str = "") -> str:
    """lab03_report_Aigerim_Sadyqova.html. Kazakh/Russian names are written in
    Latin letters: browsers drop a non-ASCII download name (the file arrived as
    "download")."""
    latin = "".join(
        (lambda s: s.capitalize() if ch.isupper() else s)(_TRANSLIT[ch.lower()].strip("-"))
        if ch.lower() in _TRANSLIT
        else ch
        for ch in student.strip()
    )
    name = re.sub(r"[^A-Za-z0-9-]+", "_", latin).strip("_")[:40]
    return f"lab{lab_number(lab_id):02d}_report" + (f"_{name}" if name else "") + ".html"


def _fmt_param(spec: dict[str, Any], value: Any, lang: str) -> str:
    if spec["kind"] == "select":
        labels = {o["id"]: _loc(o["label"], lang) for o in spec.get("options") or []}
        return labels.get(value, str(value))
    step = float(spec.get("step") or 1)
    if all(float(spec[k]).is_integer() for k in ("min", "max", "step")):
        text = f"{int(round(float(value)))}"
    else:
        text = f"{float(value):.{max(0, -math.floor(math.log10(step)))}f}"
    return f"{text} {spec.get('unit') or ''}".strip()


def _fmt_metric(m: dict[str, Any]) -> str:
    if m.get("value") is None:
        return "—"
    value = f"{m['value']:,.{int(m.get('digits', 1))}f}".replace(",", " ")
    return f"{value} {m.get('unit', '')}".strip()


def _tick(v: float, span: float) -> str:
    digits = 0 if span >= 20 else 1 if span >= 2 else 2 if span >= 0.2 else 3
    return f"{v:,.{digits}f}".replace(",", " ")


def svg_chart(chart: dict[str, Any], lang: str, width: int = 680, height: int = 240) -> str:
    """One line chart of a lab result as inline SVG (no script, prints as is)."""
    xs = [float(x) for x in chart.get("x") or []]
    series = [s for s in chart.get("series") or [] if s.get("values")]
    limits = chart.get("limits") or []
    ys = [float(v) for s in series for v in s["values"] if v is not None]
    ys += [float(lim["value"]) for lim in limits]
    if len(xs) < 2 or not ys:
        return ""
    y0, y1 = min(ys), max(ys)
    if y1 - y0 < 1e-9:
        y0, y1 = y0 - 1, y1 + 1
    pad = (y1 - y0) * 0.06
    y0, y1 = y0 - pad, y1 + pad
    x0, x1 = xs[0], xs[-1]
    if x1 == x0:
        x1 = x0 + 1
    left, right, top, bottom = 56, 12, 10, 30
    w, h = width - left - right, height - top - bottom

    def px(x: float) -> float:
        return left + (x - x0) / (x1 - x0) * w

    def py(y: float) -> float:
        return top + (1 - (y - y0) / (y1 - y0)) * h

    out = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" role="img" '
        f'aria-label="{_e(_loc(chart.get("title"), lang))}" font-size="10" '
        'font-family="system-ui, sans-serif">'
    ]
    for k in range(5):
        yv = y0 + (y1 - y0) * k / 4
        out.append(
            f'<line x1="{left}" x2="{left + w}" y1="{py(yv):.1f}" y2="{py(yv):.1f}" stroke="#e5e7eb"/>'
            f'<text x="{left - 6}" y="{py(yv) + 3:.1f}" text-anchor="end" fill="#6b7280">'
            f"{_tick(yv, y1 - y0)}</text>"
        )
    for xv, anchor in ((x0, "start"), ((x0 + x1) / 2, "middle"), (x1, "end")):
        out.append(
            f'<text x="{px(xv):.1f}" y="{top + h + 14}" text-anchor="{anchor}" fill="#6b7280">'
            f"{_tick(xv, x1 - x0)}</text>"
        )
    out.append(
        f'<text x="{left + w / 2:.1f}" y="{height - 2}" text-anchor="middle" fill="#374151">'
        f"{_e(_loc(chart.get('x_label'), lang))}</text>"
        f'<text x="12" y="{top + h / 2:.1f}" text-anchor="middle" fill="#374151" '
        f'transform="rotate(-90 12 {top + h / 2:.1f})">{_e(chart.get("y_label") or "")}</text>'
    )
    for lim in limits:
        y = py(float(lim["value"]))
        out.append(
            f'<line x1="{left}" x2="{left + w}" y1="{y:.1f}" y2="{y:.1f}" stroke="#dc2626" '
            'stroke-dasharray="5 4"/>'
            f'<text x="{left + 4}" y="{y - 3:.1f}" fill="#dc2626">{_e(_loc(lim["label"], lang))}</text>'
        )
    for i, s in enumerate(series):
        # A gap (None) in the data breaks the line instead of joining across it.
        runs: list[list[str]] = [[]]
        for x, v in zip(xs, s["values"]):
            if v is None:
                runs.append([])
            else:
                runs[-1].append(f"{px(x):.1f},{py(float(v)):.1f}")
        for pts in runs:
            if len(pts) > 1:
                out.append(
                    f'<polyline fill="none" stroke="{PALETTE[i % len(PALETTE)]}" '
                    f'stroke-width="2" points="{" ".join(pts)}"/>'
                )
    out.append("</svg>")
    legend = " ".join(
        f'<span class="key"><i style="background:{PALETTE[i % len(PALETTE)]}"></i>'
        f"{_e(_loc(s['name'], lang))}</span>"
        for i, s in enumerate(series)
    )
    return f'<figure><figcaption>{_e(_loc(chart.get("title"), lang))}</figcaption>{"".join(out)}<div class="legend">{legend}</div></figure>'


def build_report_html(
    lab_id: str,
    lang: str = "kk",
    *,
    student: str = "",
    group: str = "",
    run_result: dict[str, Any] | None = None,
    test_result: dict[str, Any] | None = None,
    best_test_percent: float | None = None,
    tasks_done: Iterable[str] = (),
    last_3d_check: dict[str, Any] | None = None,
    generated_at: datetime | None = None,
) -> str:
    """The report page. Everything the student typed is escaped.

    Lab 12 is done in the 3D model rather than by a simulation run: its report
    lists the fault scenarios fixed there and the last system check instead.
    """
    lang = "kk" if lang == "kk" else "en"
    lab = LABS[lab_id]
    when = (generated_at or datetime.now()).strftime("%d.%m.%Y %H:%M")
    done = set(tasks_done)
    title = f"{lab_number(lab_id)}. {_loc(lab['title'], lang)}"
    blank = "&nbsp;" * 40

    info = [
        (_t("student", lang), _e(student) or blank),
        (_t("group", lang), _e(group) or blank),
        (_t("date", lang), _e(when)),
        (_t("lab", lang), _e(title)),
        (
            _t("level", lang),
            _e(f"{_loc(lab['level'], lang)} · {lab['minutes']} {'мин' if lang == 'kk' else 'min'}"),
        ),
    ]
    parts = [
        f"<header><p class='brand'>EcoPredict AI</p><h1>{_t('report', lang)}</h1>"
        f"<p class='muted print-hint'>{_t('print', lang)}</p></header>",
        "<table class='info'>"
        + "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in info)
        + "</table>",
        f"<h2>{_t('objectives', lang)}</h2><p>{_e(_loc(lab['objectives'], lang))}</p>",
    ]

    number = iter(range(1, 10))

    def h2(key: str) -> str:
        return f"<h2>{next(number)}. {_t(key, lang)}</h2>"

    scenarios = sorted(d.removeprefix("scenario_") for d in done if d.startswith("scenario_"))
    if lab_id == LAB_3D:
        parts.append(h2("work3d"))
        if scenarios:
            names = sorted(_loc(SCENARIOS.get(sc, {}).get("title"), lang) or sc for sc in scenarios)
            parts.append(
                f"<p>{_t('scenarios', lang)}:</p><ul>"
                + "".join(f"<li>✓ {_e(n)}</li>" for n in names)
                + "</ul>"
            )
        else:
            parts.append(f"<p class='muted'>{_t('no_scenarios', lang)}</p>")
        if last_3d_check:
            parts.append(
                "<p>"
                + _t("last_check", lang, s=last_3d_check["score"], t=last_3d_check["total"])
                + "</p>"
            )
        run_result, specs = None, {}
    else:
        specs = {s["key"]: s for s in list_params(lab_id)}

    # the last run
    if specs:
        parts.append(h2("params"))
    if run_result and specs:
        rows = "".join(
            f"<tr><td>{_e(_loc(spec['label'], lang))}</td>"
            f"<td>{_e(_fmt_param(spec, run_result['params'].get(key, spec['default']), lang))}</td></tr>"
            for key, spec in specs.items()
        )
        parts.append(
            f"<table><tr><th>{_t('parameter', lang)}</th><th>{_t('value', lang)}</th></tr>{rows}</table>"
        )
    elif specs:
        parts.append(f"<p class='muted'>{_t('no_run', lang)}</p>")
    if specs:
        parts.append(h2("results"))
    if run_result:
        rows = "".join(
            f"<tr><td>{_e(_loc(m['label'], lang))}</td><td>{_e(_fmt_metric(m))}</td></tr>"
            for m in run_result.get("metrics") or []
        )
        parts.append(
            f"<table><tr><th>{_t('quantity', lang)}</th><th>{_t('value', lang)}</th></tr>{rows}</table>"
        )
        parts += [f"<p class='note'>{_e(_loc(n, lang))}</p>" for n in run_result.get("notes") or []]
        parts += [svg_chart(ch, lang) for ch in run_result.get("charts") or []]
    elif specs:
        parts.append(f"<p class='muted'>{_t('no_run', lang)}</p>")

    # practice tasks
    tasks = LAB_TASKS.get(lab_id, [])
    parts.append(h2("tasks"))
    solved = [t for t in tasks if t["id"] in done]
    parts.append(
        f"<p>{_t('tasks_done', lang, done=len(solved), total=len(tasks))}</p><ol class='tasks'>"
    )
    for task in tasks:
        mark = "✓" if task["id"] in done else "—"
        parts.append(f"<li><b>{mark}</b> {latex_to_html(_loc(task['prompt'], lang))}</li>")
    parts.append("</ol>")

    # test
    parts.append(h2("test"))
    best = best_test_percent
    if test_result is not None:
        best = max(float(best or 0), float(test_result["percent"]))
    if best is None:
        parts.append(f"<p class='muted'>{_t('no_test', lang)}</p>")
    else:
        passed = best >= PASS_PERCENT
        parts.append(
            f"<p><b>{_t('best', lang, p=best, pm=PASS_PERCENT)}</b> — "
            f"<span class='{'ok' if passed else 'bad'}'>{_t('passed' if passed else 'failed', lang)}</span></p>"
        )
    if test_result is not None:
        parts.append(
            "<p>"
            + _t(
                "last",
                lang,
                s=test_result["score"],
                t=test_result["total"],
                p=float(test_result["percent"]),
            )
            + "</p><ol class='tasks'>"
        )
        prompts = {q["id"]: q["prompt"] for q in public_test(lab_id, lang)["questions"]}
        for d in test_result.get("details") or []:
            mark = "✓" if d.get("correct") else "✗"
            parts.append(f"<li><b>{mark}</b> {_e(prompts.get(d['id'], d['id']))}</li>")
        parts.append("</ol>")

    # conclusion
    parts.append(
        h2("conclusion")
        + f"<p class='muted'>{_t('conclusion_hint', lang)}</p>"
        + "<div class='line'></div>" * 6
        + f"<div class='signs'><span>{_t('sign_student', lang)}: ________________</span>"
        f"<span>{_t('sign_teacher', lang)}: ________________</span></div>"
    )

    return f"""<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_e(_t("report", lang))} · {_e(title)} · {_e(student)}</title>
<style>
  body {{ font: 14px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; color: #111827;
         background: #fff; max-width: 780px; margin: 24px auto; padding: 0 16px; }}
  header {{ border-bottom: 2px solid #111827; margin-bottom: 12px; }}
  .brand {{ margin: 0; color: #2563eb; font-weight: 600; }}
  h1 {{ margin: 2px 0 4px; font-size: 22px; }}
  h2 {{ font-size: 16px; margin: 20px 0 6px; border-bottom: 1px solid #d1d5db; padding-bottom: 2px; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #d1d5db; padding: 4px 8px; text-align: left; vertical-align: top; }}
  th {{ background: #f3f4f6; font-weight: 600; }}
  table.info th {{ width: 30%; }}
  .muted {{ color: #6b7280; }}
  .note {{ background: #fef3c7; padding: 6px 8px; border-radius: 4px; }}
  .ok {{ color: #047857; font-weight: 600; }} .bad {{ color: #b91c1c; font-weight: 600; }}
  figure {{ margin: 12px 0; break-inside: avoid; }}
  figcaption {{ font-weight: 600; margin-bottom: 2px; }}
  .legend {{ font-size: 12px; }} .key {{ margin-right: 14px; }}
  .key i {{ display: inline-block; width: 14px; height: 3px; margin-right: 4px; vertical-align: middle; }}
  ol.tasks li {{ margin: 4px 0; }}
  .line {{ border-bottom: 1px solid #9ca3af; height: 26px; }}
  .signs {{ display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap; margin-top: 28px; }}
  @media print {{ .print-hint {{ display: none; }} body {{ margin: 0 auto; }} }}
</style></head>
<body>
{"".join(parts)}
</body></html>
"""
