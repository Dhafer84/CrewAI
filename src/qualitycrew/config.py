"""Chargement centralisé de la configuration et des secrets.

Toute clé API ou paramètre sensible transite par ce module et par le
fichier .env local (jamais committé — voir .gitignore et .env.example).
Ne jamais coder une clé en dur ailleurs dans le projet.
"""

import os

import litellm
from dotenv import load_dotenv

load_dotenv()

# Bug CrewAI 1.15.x : strip_cache_breakpoint n'est pas appelé pour les
# providers LiteLLM (Groq, etc.), donc le champ "cache_breakpoint" atterrit
# dans les messages et Groq le rejette. On patch litellm.completion pour
# le retirer avant l'envoi.
_original_litellm_completion = litellm.completion
_RATE_LIMIT_NAMES = ("ratelimiterror", "rate_limit_exceeded", "rate limit")


def _completion_strip_cache_breakpoint(**kwargs):
    for msg in kwargs.get("messages", []):
        if isinstance(msg, dict):
            msg.pop("cache_breakpoint", None)

    # Backoff exponentiel sur rate limit (free tier Groq : 12k TPM)
    delay = 2.0
    for attempt in range(7):
        try:
            return _original_litellm_completion(**kwargs)
        except Exception as exc:
            name = type(exc).__name__.lower() + str(exc).lower()
            if any(k in name for k in _RATE_LIMIT_NAMES) and attempt < 6:
                import time
                time.sleep(delay)
                delay = min(delay * 2, 60)
            else:
                raise


litellm.completion = _completion_strip_cache_breakpoint

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
