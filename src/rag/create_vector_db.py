"""
Build / refresh ChromaDB vector store from knowledge_base/ markdown files.

Usage (from project root EcoPredict AI):
  python -m src.rag.create_vector_db
  python -m src.rag.create_vector_db --reset
"""
from __future__ import annotations

import argparse
import hashlib
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Project root: .../EcoPredict AI
PROJECT_ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge_base"
VECTOR_DIR = PROJECT_ROOT / "vector_db"
COLLECTION_NAME = "ecopredict_knowledge"


def _chunk_text(text: str, max_chars: int = 900, overlap: int = 120) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        # prefer break on paragraph
        if end < len(text):
            br = text.rfind("\n\n", start, end)
            if br > start + max_chars // 3:
                end = br
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def load_knowledge_documents(knowledge_dir: Path = KNOWLEDGE_DIR) -> list[dict]:
    """Load all .md / .txt under knowledge_base into document dicts."""
    docs: list[dict] = []
    if not knowledge_dir.is_dir():
        raise FileNotFoundError(f"knowledge_base not found: {knowledge_dir}")

    for path in sorted(knowledge_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".txt"}:
            continue
        rel = path.relative_to(knowledge_dir)
        category = rel.parts[0] if len(rel.parts) > 1 else "general"
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="ignore")
        for i, chunk in enumerate(_chunk_text(text)):
            doc_id = hashlib.sha1(f"{rel}::{i}::{chunk[:80]}".encode("utf-8")).hexdigest()[:16]
            docs.append(
                {
                    "id": f"{category}_{doc_id}",
                    "text": chunk,
                    "metadata": {
                        "source": str(rel).replace("\\", "/"),
                        "category": category,
                        "chunk": i,
                    },
                }
            )
    return docs


def create_vector_db(reset: bool = False) -> int:
    """
    Index knowledge_base into persistent ChromaDB at vector_db/.
    Returns number of chunks indexed.
    """
    try:
        import chromadb
        from chromadb.config import Settings
    except ImportError as e:
        raise SystemExit(
            "chromadb is not installed. Run: pip install chromadb\n" + str(e)
        ) from e

    VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    docs = load_knowledge_documents()
    if not docs:
        logger.warning("No documents found under %s", KNOWLEDGE_DIR)
        return 0

    client = chromadb.PersistentClient(
        path=str(VECTOR_DIR),
        settings=Settings(anonymized_telemetry=False),
    )

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            logger.info("Deleted existing collection %s", COLLECTION_NAME)
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    # Upsert in batches
    batch = 64
    total = 0
    for i in range(0, len(docs), batch):
        part = docs[i : i + batch]
        collection.upsert(
            ids=[d["id"] for d in part],
            documents=[d["text"] for d in part],
            metadatas=[d["metadata"] for d in part],
        )
        total += len(part)

    logger.info(
        "Indexed %s chunks from %s into %s (collection=%s)",
        total,
        KNOWLEDGE_DIR,
        VECTOR_DIR,
        COLLECTION_NAME,
    )
    print(f"OK: indexed {total} chunks → {VECTOR_DIR} [{COLLECTION_NAME}]")
    return total


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Build EcoPredict ChromaDB knowledge index")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete and recreate the collection before indexing",
    )
    args = parser.parse_args(argv)
    create_vector_db(reset=args.reset)
    return 0


if __name__ == "__main__":
    # Allow `python src/rag/create_vector_db.py` without package install
    root = str(PROJECT_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    raise SystemExit(main())
