"""Chargement centralisé de la configuration et des secrets.

Toute clé API ou paramètre sensible transite par ce module et par le
fichier .env local (jamais committé — voir .gitignore et .env.example).
Ne jamais coder une clé en dur ailleurs dans le projet.
"""

import os

from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

LLM_MODEL = os.getenv("LLM_MODEL", "groq/llama-3.3-70b-versatile")


def require_llm_key() -> None:
    """Vérifie qu'au moins une clé LLM est configurée avant de lancer un audit.

    Lève une erreur explicite plutôt que de laisser CrewAI échouer plus loin
    avec un message moins clair.
    """
    if not any([GROQ_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY]):
        raise RuntimeError(
            "Aucune clé API LLM trouvée. "
            "Copier .env.example en .env et renseigner au moins une clé "
            "(GROQ_API_KEY recommandé pour démarrer, c'est le free tier)."
        )
