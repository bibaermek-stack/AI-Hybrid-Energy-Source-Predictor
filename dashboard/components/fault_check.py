"""
The reliable panel fault check on the site: the same POST /detect the app uses.

The API answers with a diagnosis (src/fault_detection/diagnosis.py) that is
"confirmed" only when two different models agree confidently, and says
"uncertain", "not a panel" or "retake" otherwise. This page shows that answer
as given, with the accuracy the server measured for it; it does not load the
models a second time in the Streamlit process.
"""

from __future__ import annotations

import requests
import streamlit as st

from dashboard.utils.config import DETECT_URL

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


def _t(pair: tuple[str, str], lang: str) -> str:
    return pair[1] if lang == "en" else pair[0]


def _name(label: str | None, lang: str) -> str:
    return _t(CLASS_NAMES[label], lang) if label in CLASS_NAMES else str(label)


def run_fault_check(uploaded_file, lang: str) -> None:
    """POST the file to /detect and show the diagnosis."""
    try:
        resp = requests.post(
            DETECT_URL,
            files={
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type or "image/jpeg",
                )
            },
            timeout=90,
        )
        body = resp.json()
        if not resp.ok:
            raise RuntimeError(body.get("detail") or resp.status_code)
    except Exception as err:
        st.error(("Тексеру орындалмады: " if lang == "kk" else "The check failed: ") + str(err))
        return

    dg = body.get("diagnosis")
    if not dg:
        st.warning(
            (
                "Сенімділік тексерісі серверде қолжетімсіз: "
                if lang == "kk"
                else "The reliability check is unavailable: "
            )
            + str(body.get("diagnosis_error") or "")
        )
        return

    status, label = dg.get("status"), dg.get("label")
    if status == "retake":
        issues = ", ".join(_t(ISSUES[i], lang) for i in dg.get("issues", []) if i in ISSUES)
        st.warning(
            f"**{'Суретті қайта түсіріңіз' if lang == 'kk' else 'Please retake the photo'}:** {issues}. "
            + (
                "Телефонды қозғалтпай, жарық жерде, панельге жақын түсіріңіз."
                if lang == "kk"
                else "Hold the phone still, in good light, close to the panel."
            )
        )
        return
    if status == "not_panel":
        st.error(
            "**Бұл күн панелі емес сияқты.** Кадрды панельмен толтырып, алдынан түсіріңіз."
            if lang == "kk"
            else "**This does not look like a solar panel.** Fill the frame with the panel and shoot it straight on."
        )
        return

    conf = float(dg.get("confidence") or 0) * 100
    expected = dg.get("expected_accuracy")
    measured = (
        f" · {'осындай жауаптың өлшенген дәлдігі' if lang == 'kk' else 'measured accuracy of such answers'} {expected * 100:.1f}%"
        if expected
        else ""
    )
    if status == "confirmed":
        head = f"✓ {'Расталды' if lang == 'kk' else 'Confirmed'}: **{_name(label, lang)}**"
        text = f"{head} ({conf:.0f}%{measured})\n\n{_t(ADVICE.get(label, ('', '')), lang)}"
        (
            st.success
            if label == "Clean"
            else st.error if dg.get("severity") == "repair" else st.warning
        )(text)
    elif status == "likely":
        st.warning(
            f"{'Ықтимал' if lang == 'kk' else 'Likely'}: **{_name(label, lang)}** ({conf:.0f}%{measured})\n\n"
            f"{_t(ADVICE.get(label, ('', '')), lang)} "
            + (
                "Растау үшін жақынырақ қайта түсіріңіз."
                if lang == "kk"
                else "Retake closer to confirm."
            )
        )
    else:
        st.info(
            (
                "**Нақты емес — қайта түсіріңіз.** Модельдер келіспеді, сондықтан жауап берілмейді."
                if lang == "kk"
                else "**Not sure — please retake.** The models disagree, so no verdict is given."
            )
            + (
                f" {'Мүмкін' if lang == 'kk' else 'Candidates'}: "
                + ", ".join(
                    f"{_name(c['label'], lang)} {c['p'] * 100:.0f}%"
                    for c in dg.get("candidates", [])
                )
                if dg.get("candidates")
                else ""
            )
        )

    models = dg.get("models") or {}
    parts = []
    if models.get("classifier"):
        m = models["classifier"]
        parts.append(
            f"YOLO26 {'жіктеуіші' if lang == 'kk' else 'classifier'}: {_name(m['label'], lang)} {m['p'] * 100:.0f}%"
        )
    if models.get("detector"):
        m = models["detector"]
        parts.append(
            f"YOLO11 {'детекторы' if lang == 'kk' else 'detector'}: {_name(m['label'], lang)} {m['p'] * 100:.0f}%"
        )
    if parts:
        st.caption(" · ".join(parts))
