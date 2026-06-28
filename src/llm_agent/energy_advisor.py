from src.rag.retriever import retrieve_context, search_knowledge
import logging

logger = logging.getLogger(__name__)


def explain_energy(source, lang="en"):
    """
    Generate explanation for energy recommendation in English or Kazakh.
    """
    try:
        # Validate source type
        if not isinstance(source, str):
            logger.warning(f"Invalid source type: {type(source).__name__}, expected str")
            return "Unable to generate explanation: Invalid source format." if lang == "en" else "Түсіндірме беру мүмкін емес: пішім қате."
        
        # Retrieve knowledge context
        context = retrieve_context(source, lang=lang)
        
        if lang == "kk":
            source_mapped = "Күн" if source.lower() == "solar" else "Жел"
            explanation = f"""Ұсынылатын энергия көзі: {source_mapped}

Түсіндірме:
{context}"""
        else:
            explanation = f"""Recommended energy source: {source}

Explanation:
{context}"""
            
        return explanation
        
    except Exception as e:
        logger.error(f"Error generating explanation for source '{source}': {e}", exc_info=True)
        return f"Unable to generate explanation for {source} at this time." if lang == "en" else f"{source} үшін түсіндірме дайындау сәтсіз аяқталды."

def chat_advisor(query, lang="en"):
    """
    RAG-based chat advisor that answers user queries on hybrid energy topics.
    """
    try:
        if not isinstance(query, str) or not query.strip():
            return "Please type a valid question." if lang == "en" else "Сұрағыңызды енгізіңіз."
        return search_knowledge(query, lang=lang)
    except Exception as e:
        logger.error(f"Error in chat advisor for query '{query}': {e}", exc_info=True)
        return "An error occurred while answering your question." if lang == "en" else "Сұраққа жауап беру кезінде қате орын алды."