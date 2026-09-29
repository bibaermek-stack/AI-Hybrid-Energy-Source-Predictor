"""
What a /detect diagnosis says to a person, in Kazakh or English.

The site (Streamlit) and the NiceGUI app show the same words; the phone app
has the same texts in mobile/i18n.py. An "uncertain" answer gets no verdict,
only what each model said: the two models disagree and the measured accuracy
of such answers is about a coin toss.
"""

from __future__ import annotations

from typing import Any

CLASS_NAMES = {
    "Bird": ("Құс саңғырығы", "Bird droppings"),
    "Clean": ("Таза панель", "Clean panel"),
    "Dust": ("Шаң", "Dust"),
    "Electrical": ("Электрлік ақау", "Electrical damage"),
    "Physical": ("Физикалық зақым", "Physical damage"),
    "Snow": ("Қар", "Snow"),
}
ADVICE = {
    "Clean": ("Панель таза. Әрекет қажет емес.", "The panel is clean. No action needed."),
    "Dust": (
        "Шаң басқан. Жуу жоспарлаңыз — өнімділік 10–25% төмендейді.",
        "Dusty. Schedule cleaning — output drops 10–25%.",
    ),
    "Bird": (
        "Құс саңғырығы. Жергілікті қызып кету қаупі, тезірек тазалаңыз.",
        "Bird droppings. Risk of hot spots — clean soon.",
    ),
    "Snow": (
        "Қар жабыны. Тазартылмайынша өндіріс іс жүзінде нөлге тең.",
        "Snow cover. Output is practically zero until cleared.",
    ),
    "Electrical": (
        "Электрлік ақау белгісі. Инвертор мен қосылымдарды тексеріңіз.",
        "Signs of an electrical fault. Check the inverter and connections.",
    ),
    "Physical": (
        "Физикалық зақым (жарық/сынық). Панельді ауыстыру қажет.",
        "Physical damage (crack/break). The panel needs replacing.",
    ),
}
ISSUES = {
    "blurry": ("сурет бұлыңғыр", "the photo is blurred"),
    "too_dark": ("сурет тым қараңғы", "the photo is too dark"),
    "overexposed": ("сурет тым жарық (шағылысу)", "the photo is overexposed (glare)"),
    "too_small": ("сурет тым кішкентай", "the image is too small"),
}
WORDS = {
    "confirmed": ("✓ Расталды", "✓ Confirmed"),
    "likely": ("Ықтимал", "Likely"),
    "uncertain": ("Нақты емес — қайта түсіріңіз", "Not sure — please retake"),
    "not_panel": ("Бұл күн панелі емес сияқты", "This does not look like a solar panel"),
    "retake": ("Суретті қайта түсіріңіз", "Please retake the photo"),
    "confidence": ("Сенімділік", "Confidence"),
    "measured": ("осындай жауаптың өлшенген дәлдігі", "measured accuracy of such answers"),
    "likely_advice": (
        "Екі модель келісті, бірақ сенімділік төмен. Растау үшін жақынырақ қайта түсіріңіз.",
        "Both models agree, with less confidence. Retake closer to confirm.",
    ),
    "uncertain_advice": (
        "Модельдер келіспеді, сондықтан жауап берілмейді. Панельді алдынан, жақыннан, "
        "көлеңкесіз қайта түсіріңіз немесе қолмен тексеріңіз.",
        "The models disagree, so no verdict is given. Retake the panel straight on, "
        "close up, without shadows, or inspect it by hand.",
    ),
    "not_panel_advice": (
        "Кадрды панельмен толтырып, алдынан түсіріңіз. Бұл панель болса, жақынырақ қайта түсіріңіз.",
        "Fill the frame with the panel and shoot it straight on. If it is a panel, retake closer.",
    ),
    "retake_advice": (
        "Телефонды қозғалтпай, жарық жерде, панельге жақын түсіріңіз.",
        "Hold the phone still, in good light, close to the panel.",
    ),
    "classifier": ("YOLO26 жіктеуіші", "YOLO26 classifier"),
    "detector": ("YOLO11 детекторы", "YOLO11 detector"),
    "candidates": ("Нұсқалар", "Candidates"),
    "unavailable": (
        "Сенімділік тексерісі серверде қолжетімсіз",
        "The reliability check is unavailable on the server",
    ),
}


def t(pair: tuple[str, str], lang: str) -> str:
    return pair[1] if lang == "en" else pair[0]


def class_name(label: Any, lang: str) -> str:
    return t(CLASS_NAMES[label], lang) if label in CLASS_NAMES else str(label)


def describe(dg: dict[str, Any], lang: str = "kk") -> dict[str, Any]:
    """
    tone (success / warning / error / info), headline, confidence line (or
    None), advice and detail lines for one diagnosis.
    """
    status, label = dg.get("status"), dg.get("label")
    out: dict[str, Any] = {
        "status": status,
        "tone": "warning",
        "headline": "",
        "confidence": None,
        "advice": "",
        "details": [],
    }
    if status == "retake":
        issues = [t(ISSUES[i], lang) for i in dg.get("issues") or [] if i in ISSUES]
        out["headline"] = t(WORDS["retake"], lang)
        out["advice"] = (", ".join(issues).capitalize() + ". " if issues else "") + t(
            WORDS["retake_advice"], lang
        )
        return out
    if status == "not_panel":
        out.update(
            tone="error",
            headline=t(WORDS["not_panel"], lang),
            advice=t(WORDS["not_panel_advice"], lang),
        )
        return out

    conf = f"{t(WORDS['confidence'], lang)}: {float(dg.get('confidence') or 0) * 100:.0f}%"
    if dg.get("expected_accuracy"):
        conf += f" · {t(WORDS['measured'], lang)} {float(dg['expected_accuracy']) * 100:.1f}%"
    advice = t(ADVICE[label], lang) if label in ADVICE else ""
    if status == "confirmed":
        tone = (
            "success"
            if label == "Clean"
            else "error" if dg.get("severity") == "repair" else "warning"
        )
        out.update(
            tone=tone,
            headline=f"{t(WORDS['confirmed'], lang)}: {class_name(label, lang)}",
            confidence=conf,
            advice=advice,
        )
    elif status == "likely":
        out.update(
            headline=f"{t(WORDS['likely'], lang)}: {class_name(label, lang)}",
            confidence=conf,
            advice=f"{advice} {t(WORDS['likely_advice'], lang)}".strip(),
        )
    else:
        out.update(
            tone="info",
            headline=t(WORDS["uncertain"], lang),
            advice=t(WORDS["uncertain_advice"], lang),
        )

    models = dg.get("models") or {}
    parts = [
        f"{t(WORDS[key], lang)}: {class_name(m.get('label'), lang)} {float(m.get('p') or 0) * 100:.0f}%"
        for key in ("classifier", "detector")
        if (m := models.get(key))
    ]
    if parts:
        out["details"].append(" · ".join(parts))
    if status == "uncertain" and dg.get("candidates"):
        out["details"].append(
            f"{t(WORDS['candidates'], lang)}: "
            + ", ".join(
                f"{class_name(c.get('label'), lang)} {float(c.get('p') or 0) * 100:.0f}%"
                for c in dg["candidates"]
            )
        )
    return out
