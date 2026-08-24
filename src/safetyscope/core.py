"""Interface stable de la proposition d'événements redoutés.

Seul point d'entrée destiné aux couches de présentation.
"""

from i18n import DEFAULT_LANG

import re
from dataclasses import dataclass

from .analysis import MAX_EVENTS, MAX_TEXT_LENGTH
from .crew import MAX_SUGGESTIONS, SEPARATOR, build_crew

# Puces et numérotations que le modèle ajoute malgré la consigne.
_LEADING_NOISE = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s*")


@dataclass(frozen=True)
class HazardSuggestion:
    """Un événement redouté proposé. Jamais coté : S/E/C restent vides."""

    malfunction: str
    situation: str


def parse_suggestions(raw: str) -> list[HazardSuggestion]:
    """Extrait les événements d'une sortie de crew.

    Tolérant : le modèle ajoute volontiers des puces, des numéros ou une
    phrase d'introduction. Toute ligne sans séparateur est ignorée plutôt
    que de faire échouer la proposition entière.
    """
    suggestions: list[HazardSuggestion] = []
    seen: set[tuple[str, str]] = set()

    for line in (raw or "").splitlines():
        if SEPARATOR not in line:
            continue

        left, _, right = line.partition(SEPARATOR)
        malfunction = _LEADING_NOISE.sub("", left).strip(" *_`").strip()
        situation = right.strip(" *_`").strip()

        if not malfunction or not situation:
            continue

        key = (malfunction.lower(), situation.lower())
        if key in seen:
            continue
        seen.add(key)

        suggestions.append(
            HazardSuggestion(
                malfunction=malfunction[:MAX_TEXT_LENGTH],
                situation=situation[:MAX_TEXT_LENGTH],
            )
        )

        if len(suggestions) >= min(MAX_SUGGESTIONS, MAX_EVENTS):
            break

    return suggestions


def suggest_hazards(item: str, task_callback=None,
                    lang: str = DEFAULT_LANG) -> list[HazardSuggestion]:
    """Propose des événements redoutés pour un item donné.

    Args:
        item: intitulé de la fonction véhicule étudiée.
        task_callback: appelé à la fin de chaque tâche du crew.

    Returns:
        Liste d'événements **non cotés** — la cotation S/E/C reste au
        jugement de l'ingénieur.
    """
    item = (item or "").strip()
    if not item:
        raise ValueError("Aucun item à analyser.")

    crew = build_crew(item, task_callback=task_callback, lang=lang)
    result = crew.kickoff()
    return parse_suggestions(result.raw)
