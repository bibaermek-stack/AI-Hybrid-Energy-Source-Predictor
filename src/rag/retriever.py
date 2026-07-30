"""
RAG retriever: ChromaDB vector search with keyword fallback.

vector_db/ is created by: python -m src.rag.create_vector_db
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
VECTOR_DIR = PROJECT_ROOT / "vector_db"
COLLECTION_NAME = "ecopredict_knowledge"

_collection = None
_chroma_failed = False


def _get_collection():
    """Lazy open persistent Chroma collection (None if missing / not installed)."""
    global _collection, _chroma_failed
    if _chroma_failed:
        return None
    if _collection is not None:
        return _collection
    try:
        import chromadb
        from chromadb.config import Settings

        if not VECTOR_DIR.is_dir():
            logger.info("vector_db missing — run create_vector_db.py")
            _chroma_failed = True
            return None
        client = chromadb.PersistentClient(
            path=str(VECTOR_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
        names = [c.name for c in client.list_collections()]
        if COLLECTION_NAME not in names:
            logger.info("Collection %s not found — run create_vector_db.py", COLLECTION_NAME)
            _chroma_failed = True
            return None
        _collection = client.get_collection(COLLECTION_NAME)
        return _collection
    except Exception as e:
        logger.warning("ChromaDB unavailable (%s) — using keyword fallback", e)
        _chroma_failed = True
        return None


def retrieve_from_vector_db(query: str, top_k: int = 4) -> list[dict]:
    """Return list of {text, source, category, distance} hits."""
    col = _get_collection()
    if col is None or not query or not str(query).strip():
        return []
    try:
        res = col.query(query_texts=[str(query).strip()], n_results=max(1, top_k))
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        out = []
        for i, text in enumerate(docs):
            meta = metas[i] if i < len(metas) else {}
            dist = dists[i] if i < len(dists) else None
            out.append(
                {
                    "text": text,
                    "source": (meta or {}).get("source", ""),
                    "category": (meta or {}).get("category", ""),
                    "distance": dist,
                }
            )
        return out
    except Exception as e:
        logger.error("Vector query failed: %s", e, exc_info=True)
        return []


def retrieve_context(source: str, lang: str = "en") -> str:
    """
    Context for energy source recommendation (solar / wind / hybrid).
    Uses vector search + legacy in-memory knowledge.
    """
    source_key = (source or "").strip().lower()
    query_map = {
        "solar": "solar panel irradiation temperature efficiency generation",
        "wind": "wind turbine speed direction power curve",
        "hybrid": "hybrid solar wind complementarity optimization",
    }
    query = query_map.get(source_key, source_key or "hybrid energy")
    hits = retrieve_from_vector_db(query, top_k=3)
    if hits:
        return "\n\n".join(h["text"] for h in hits)

    # Fallback: original document_loader dict
    try:
        from src.rag.document_loader import load_documents

        knowledge = load_documents()
        lang_knowledge = knowledge.get(lang, knowledge.get("en", {}))
        default = "No knowledge available." if lang == "en" else "Мәлімет жоқ."
        return lang_knowledge.get(source_key, default)
    except Exception:
        return "No knowledge available." if lang == "en" else "Мәлімет жоқ."


def search_knowledge(query: str, lang: str = "en") -> str:
    """
    Answer-style RAG: retrieve top chunks, or keyword fallback over legacy KB.
    """
    if not isinstance(query, str) or not query.strip():
        return "Please type a valid question." if lang == "en" else "Сұрағыңызды енгізіңіз."

    hits = retrieve_from_vector_db(query, top_k=4)
    if hits:
        parts = []
        for h in hits:
            src = h.get("source") or h.get("category") or "kb"
            parts.append(f"[{src}]\n{h['text']}")
        body = "\n\n---\n\n".join(parts)
        if lang == "kk":
            return f"Білім базасынан табылған мәлімет:\n\n{body}"
        return f"From knowledge base:\n\n{body}"

    # Keyword fallback (legacy)
    try:
        from src.rag.document_loader import load_documents

        knowledge = load_documents()
        lang_knowledge = knowledge.get(lang, knowledge.get("en", {}))
    except Exception:
        lang_knowledge = {}

    keywords = {
        "solar": [
            "solar", "sun", "irradiation", "temperature", "panel", "күн", "панель", "сәуле",
        ],
        "wind": ["wind", "turbine", "speed", "жел", "турбина", "жылдамдық"],
        "hybrid": ["hybrid", "гибрид", "combine", "grid"],
        "battery": ["battery", "storage", "батарея", "аккумулятор"],
        "faq": ["how", "why", "what", "неге", "қалай", "сұрақ"],
        "cleaning": ["clean", "dust", "soiling", "таза", "шаң"],
        "fault": ["fault", "error", "hotspot", "ақау", "қате"],
    }

    query_clean = re.sub(r"[^\w\s]", "", query.lower())
    query_words = set(query_clean.split())
    best_match = None
    max_overlap = 0
    for category, category_keywords in keywords.items():
        overlap = len(query_words.intersection(set(category_keywords)))
        if overlap > max_overlap:
            max_overlap = overlap
            best_match = category

    # Map extra categories to closest legacy keys
    legacy_key = {
        "cleaning": "solar",
        "fault": "solar",
        "faq": "faq",
    }.get(best_match, best_match)

    if legacy_key and max_overlap > 0 and legacy_key in lang_knowledge:
        return lang_knowledge[legacy_key]

    if lang == "kk":
        return """Мен келесі тақырыптар бойынша көмектесе аламын:
- Күн панелі ақаулары · тазалау · ауа райы әсері
- Қазақстан / Түркістан · ұсыныстар · жалпы EcoPredict

`python -m src.rag.create_vector_db` арқылы vector_db жаңартыңыз."""
    return """I can help with:
- Panel faults · cleaning · weather impact
- Kazakhstan / Turkistan · recommendations · EcoPredict overview

Rebuild the index with: `python -m src.rag.create_vector_db`"""
