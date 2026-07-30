"""
RAG energy advisor (explanations + chat) using vector_db / knowledge_base.

Public API used by FastAPI and Streamlit:
  - explain_energy(source, lang)
  - chat_advisor(query, lang)
"""
from __future__ import annotations

import logging

from src.rag.retriever import retrieve_context, search_knowledge

logger = logging.getLogger(__name__)


def explain_energy(source, lang: str = "en") -> str:
    """Generate explanation for energy recommendation (Solar / Wind / Hybrid)."""
    try:
        if not isinstance(source, str):
            logger.warning("Invalid source type: %s", type(source).__name__)
            return (
                "Unable to generate explanation: Invalid source format."
                if lang == "en"
                else "Түсіндірме беру мүмкін емес: пішім қате."
            )

        source_key = source.strip().lower()
        if source_key in ("hybrid", "mixed", "both"):
            source_key = "hybrid"
        elif source_key.startswith("sol"):
            source_key = "solar"
        elif source_key.startswith("win"):
            source_key = "wind"

        context = retrieve_context(source_key, lang=lang)

        if lang == "kk":
            labels = {"solar": "Күн", "wind": "Жел", "hybrid": "Гибрид"}
            source_mapped = labels.get(source_key, source)
            return f"""Ұсынылатын энергия көзі: {source_mapped}

Түсіндірме:
{context}"""

        labels = {"solar": "Solar", "wind": "Wind", "hybrid": "Hybrid"}
        source_mapped = labels.get(source_key, source)
        return f"""Recommended energy source: {source_mapped}

Explanation:
{context}"""
    except Exception as e:
        logger.error("Error generating explanation for '%s': %s", source, e, exc_info=True)
        return (
            f"Unable to generate explanation for {source} at this time."
            if lang == "en"
            else f"{source} үшін түсіндірме дайындау сәтсіз аяқталды."
        )


def chat_advisor(query, lang: str = "en") -> str:
    """RAG chat: retrieve knowledge_base / ChromaDB chunks for the user query."""
    try:
        if not isinstance(query, str) or not query.strip():
            return "Please type a valid question." if lang == "en" else "Сұрағыңызды енгізіңіз."
        return search_knowledge(query, lang=lang)
    except Exception as e:
        logger.error("Error in chat advisor for query '%s': %s", query, e, exc_info=True)
        return (
            "An error occurred while answering your question."
            if lang == "en"
            else "Сұраққа жауап беру кезінде қате орын алды."
        )
