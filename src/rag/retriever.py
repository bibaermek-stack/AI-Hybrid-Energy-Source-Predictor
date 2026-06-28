from src.rag.document_loader import load_documents
import re

def retrieve_context(source, lang="en"):
    knowledge = load_documents()
    lang_knowledge = knowledge.get(lang, knowledge.get("en", {}))
    default_no_knowledge = "No knowledge available." if lang == "en" else "Мәлімет жоқ."
    return lang_knowledge.get(source.lower(), default_no_knowledge)

def search_knowledge(query, lang="en"):
    """
    Search the local RAG knowledge base for the most relevant document based on user query.
    """
    knowledge = load_documents()
    lang_knowledge = knowledge.get(lang, knowledge.get("en", {}))
    
    # Define keywords for each category
    keywords = {
        "solar": ["solar", "sun", "irradiation", "temperature", "temp", "panel", "cell", "kún", "kun", "temp", "panel", "cáwle", "saule", "күн", "температура", "панель", "сәуле"],
        "wind": ["wind", "speed", "direction", "turbine", "theoretical", "blade", "jely", "jel", "jyljydy", "jyldamdyq", "bagyt", "turbina", "жел", "жылдамдық", "бағыт", "турбина"],
        "hybrid": ["hybrid", "combine", "ratio", "grid", "complement", "gibrid", "araqatynas", "qosyndy", "kóp", "kop", "гибрид", "үйлесімділік", "арақатынас"],
        "battery": ["battery", "storage", "charge", "discharge", "capacity", "lithium", "batareya", "akkumulyator", "jinagtaush", "saqta", "батарея", "аккумулятор", "жинақтауыш", "сақтау"],
        "faq": ["how", "why", "what", "question", "faq", "info", "help", "nege", "qalai", "nelikten", "suraq", "kómek", "komek", "сұрақ", "қалай", "неге", "көмек", "жиі"]
    }
    
    query_clean = re.sub(r'[^\w\s]', '', query.lower())
    query_words = set(query_clean.split())
    
    best_match = None
    max_overlap = 0
    
    for category, category_keywords in keywords.items():
        overlap = len(query_words.intersection(set(category_keywords)))
        if overlap > max_overlap:
            max_overlap = overlap
            best_match = category
            
    if best_match and max_overlap > 0:
        return lang_knowledge.get(best_match)
        
    # If no keywords match, let's see if we can find any substring match
    for category in lang_knowledge.keys():
        if category in query_clean:
            return lang_knowledge.get(category)
            
    # Fallback response
    if lang == "en":
        return """I can help you with questions about:
- **Solar Energy** (irradiation, temperature, efficiency)
- **Wind Energy** (wind speed, direction, power curve)
- **Hybrid Systems** (complementarity, ratios, optimization)
- **Battery Storage** (charging, capacity, peak shaving)
- **Frequently Asked Questions (FAQ)**

Please try asking your question with some of these terms!"""
    else:
        return """Мен келесі тақырыптар бойынша сұрақтарға жауап бере аламын:
- **Күн энергиясы** (күн сәулесі, температура, тиімділік)
- **Жел энергиясы** (жел жылдамдығы, бағыты, қуат қисығы)
- **Гибридті жүйелер** (үйлесімділік, арақатынас, оңтайландыру)
- **Батареялар** (зарядтау, сыйымдылық, пиктік реттеу)
- **Жиі қойылатын сұрақтар (FAQ)**

Сұрағыңызда осы сөздерді қолданып көріңіз!"""