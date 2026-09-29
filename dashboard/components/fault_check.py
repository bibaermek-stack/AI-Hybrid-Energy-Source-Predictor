"""
The panel fault check on the site: the same POST /detect the app uses.

The API answers with a diagnosis (src/fault_detection/diagnosis.py) that is
"confirmed" only when two different models agree confidently, and says
"uncertain", "not a panel" or "retake" otherwise. This page shows that answer
as given, with the accuracy the server measured for it, and draws the
detector's boxes on the photo; it does not load the models a second time in
the Streamlit process.
"""

from __future__ import annotations

import io

import requests
import streamlit as st

from dashboard.utils.config import DETECT_URL
from src.fault_detection.texts import WORDS, class_name, describe, t

TONES = {"success": st.success, "warning": st.warning, "error": st.error, "info": st.info}


def post_detect(filename: str, content: bytes, content_type: str) -> dict:
    resp = requests.post(
        DETECT_URL,
        files={"file": (filename, content, content_type or "image/jpeg")},
        timeout=90,
    )
    try:
        body = resp.json()
    except ValueError:
        body = {"detail": resp.text[:200]}
    if not resp.ok:
        raise RuntimeError(body.get("detail") or resp.status_code)
    return body


def boxed_image(content: bytes, detections: list, lang: str):
    """The photo with the detector's boxes, or None if there are none."""
    from PIL import Image, ImageDraw

    if not detections:
        return None
    img = Image.open(io.BytesIO(content)).convert("RGB")
    draw = ImageDraw.Draw(img)
    width = max(2, round(max(img.size) / 300))
    for d in detections:
        box = d.get("box") or []
        if len(box) != 4:
            continue
        draw.rectangle(box, outline=(245, 158, 11), width=width)
        draw.text(
            (box[0] + width, box[1] + width),
            f"{class_name(d.get('class_name'), lang)} {float(d.get('confidence') or 0) * 100:.0f}%",
            fill=(245, 158, 11),
        )
    return img


def run_fault_check(uploaded_file, lang: str) -> None:
    """POST the file to /detect and show the diagnosis."""
    content = uploaded_file.getvalue()
    try:
        body = post_detect(uploaded_file.name, content, uploaded_file.type)
    except Exception as err:
        st.error(("Тексеру орындалмады: " if lang == "kk" else "The check failed: ") + str(err))
        return

    dg = body.get("diagnosis")
    if not dg:
        st.warning(f"{t(WORDS['unavailable'], lang)}: {body.get('diagnosis_error') or ''}")
        return

    d = describe(dg, lang)
    text = f"**{d['headline']}**"
    if d["confidence"]:
        text += f"  \n{d['confidence']}"
    text += f"\n\n{d['advice']}"
    TONES[d["tone"]](text)
    for line in d["details"]:
        st.caption(line)

    if dg.get("status") in ("confirmed", "likely", "uncertain"):
        img = boxed_image(content, body.get("detections") or [], lang)
        if img is not None:
            st.image(
                img,
                caption=(
                    "YOLO11 детекторының аймақтары" if lang == "kk" else "YOLO11 detector boxes"
                ),
                width="stretch",
            )
