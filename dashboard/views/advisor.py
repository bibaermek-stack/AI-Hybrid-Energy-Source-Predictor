"""Streamlit UI: Kazakh/English AI Energy Advisor (RAG)."""

from __future__ import annotations

import streamlit as st


def _t(lang: str, en: str, kk: str) -> str:
    return kk if lang == "kk" else en


def render(lang: str, texts: dict | None = None, models_status: dict | None = None) -> None:
    lang = "kk" if lang == "kk" else "en"
    st.caption(
        _t(
            lang,
            "RAG knowledge base (panel faults, cleaning, Kazakhstan context)",
            "RAG білім қоры (ақаулар, тазалау, ҚР контексті)",
        )
    )

    if "advisor_history" not in st.session_state:
        st.session_state["advisor_history"] = []

    col_q, col_ex = st.columns([2, 1])
    with col_ex:
        st.markdown(_t(lang, "**Example questions**", "**Мысал сұрақтар**"))
        examples = (
            [
                "Why is solar output low after dust storms?",
                "How often should panels be cleaned in Turkistan?",
                "What is a hot spot on a PV panel?",
            ]
            if lang != "kk"
            else [
                "Шаңнан кейін генерация неге төмендейді?",
                "Түркістанда панельді қаншалықты жиі тазалау керек?",
                "PV панелінде hot spot деген не?",
            ]
        )
        for ex in examples:
            if st.button(ex, key=f"ex_{hash(ex)}"):
                st.session_state["advisor_prefill"] = ex

    with col_q:
        default = st.session_state.pop("advisor_prefill", "")
        question = st.text_area(
            _t(lang, "Your question", "Сұрағыңыз"),
            value=default,
            height=120,
            placeholder=_t(
                lang,
                "Ask about faults, cleaning, weather, Kazakhstan PV…",
                "Ақау, тазалау, ауа райы, ҚР PV туралы сұраңыз…",
            ),
        )
        use_rag = st.checkbox(_t(lang, "Use vector knowledge base", "Векторлық білім қорын қолдану"), True)

    if st.button(_t(lang, "Ask advisor", "Кеңесшіге сұрау"), type="primary") and question.strip():
        with st.spinner(_t(lang, "Thinking…", "Ойлануда…")):
            try:
                from src.rag.energy_advisor import chat_advisor

                answer = chat_advisor(question.strip(), lang=lang)
            except Exception:
                try:
                    from src.llm_agent.energy_advisor import chat_advisor

                    answer = chat_advisor(question.strip(), lang=lang)
                except Exception as e:
                    answer = (
                        f"Advisor error: {e}"
                        if lang != "kk"
                        else f"Кеңесші қатесі: {e}"
                    )
        st.session_state["advisor_history"].append(
            {"q": question.strip(), "a": answer, "rag": use_rag}
        )

    for turn in reversed(st.session_state["advisor_history"][-8:]):
        st.markdown(f"**Q:** {turn['q']}")
        a = turn["a"]
        if isinstance(a, dict):
            st.info(a.get("answer") or a.get("response") or str(a))
            if a.get("sources"):
                with st.expander(_t(lang, "Sources", "Дереккөздер")):
                    st.write(a["sources"])
        else:
            st.info(str(a))
        st.markdown("---")
