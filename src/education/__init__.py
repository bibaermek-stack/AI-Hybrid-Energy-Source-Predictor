"""
EcoPredict AI — Educational platform package.

Modules
-------
lessons          Theory content (EN/KK) for interactive lessons
exercises        Hands-on labs (forecast params, battery, image concepts)
explainable_ai   Feature-importance / rule-based model explanations
quiz             Quizzes with scoring helpers
progress         Session-based learning progress (Streamlit session_state)

Streamlit entry: ``dashboard/views/learn.py`` + page ``6_Learn_Explore.py``.
Static markdown labs: ``src/education/content/``.
"""

from src.education.lessons import LESSON_IDS, get_lesson, list_lessons
from src.education.progress import ProgressTracker
from src.education.quiz import QUIZ_BANK, grade_quiz

__all__ = [
    "LESSON_IDS",
    "list_lessons",
    "get_lesson",
    "QUIZ_BANK",
    "grade_quiz",
    "ProgressTracker",
]
