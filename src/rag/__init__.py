"""EcoPredict RAG: knowledge_base → vector_db (Chroma) → retriever / advisor."""

from src.rag.energy_advisor import chat_advisor, explain_energy
from src.rag.retriever import retrieve_context, retrieve_from_vector_db, search_knowledge

__all__ = [
    "explain_energy",
    "chat_advisor",
    "retrieve_context",
    "search_knowledge",
    "retrieve_from_vector_db",
]
