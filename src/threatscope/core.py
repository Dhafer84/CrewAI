"""Interface stable de la proposition de scénarios de menace.

Seul point d'entrée destiné aux couches de présentation.
"""

import re
from dataclasses import dataclass

from .analysis import MAX_TEXT_LENGTH, MAX_THREATS_PER_DAMAGE
from .crew import MAX_SUGGESTIONS, SEPARATOR, build_crew

# Puces et numérotations que le modèle ajoute malgré la consigne.
_LEADING_NOISE = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s*")


@dataclass(frozen=True)
class ThreatSuggestion:
    """Une menace proposée.

    ⚠️ Jamais cotée : les cinq paramètres de faisabilité et la décision de
    traitement restent vides. C'est le cœur du positionnement de l'outil.
    """

    threat: str
    path: str


def parse_suggestions(raw: str) -> list[ThreatSuggestion]:
    """Extrait les menaces d'une sortie de crew.

    Tolérant : le modèle ajoute volontiers des puces, des numéros, du gras ou
    une phrase d'introduction. Toute ligne sans séparateur est ignorée plutôt
    que de faire échouer la proposition entière — une sortie imparfaite vaut
    mieux qu'un écran d'erreur.
    """
    suggestions: list[ThreatSuggestion] = []
    seen: set[tuple[str, str]] = set()

    for line in (raw or "").splitlines():
        if SEPARATOR not in line:
            continue

        left, _, right = line.partition(SEPARATOR)
        threat = _LEADING_NOISE.sub("", left).strip(" *_`").strip()
        path = right.strip(" *_`").strip()

        if not threat or not path:
            continue

        key = (threat.lower(), path.lower())
        if key in seen:
            continue
        seen.add(key)

        suggestions.append(
            ThreatSuggestion(
                threat=threat[:MAX_TEXT_LENGTH],
                path=path[:MAX_TEXT_LENGTH],
            )
        )

        if len(suggestions) >= min(MAX_SUGGESTIONS, MAX_THREATS_PER_DAMAGE):
            break

    return suggestions


def suggest_threats(item: str, asset: str, damage: str, task_callback=None):
    """Propose des scénarios de menace pour un scénario de dommage donné.

    La proposition est **contextuelle** : elle porte sur un actif et une
    conséquence redoutée précis, pas sur l'item entier. Un balayage STRIDE
    hors contexte produit des généralités.

    Args:
        item: intitulé de l'item étudié.
        asset: actif concerné par le scénario de dommage.
        damage: conséquence redoutée à réaliser.
        task_callback: appelé à la fin de chaque tâche du crew.

    Returns:
        Liste de menaces **non cotées** — faisabilité et traitement restent
        au jugement de l'ingénieur.
    """
    item = (item or "").strip()
    damage = (damage or "").strip()
    asset = (asset or "").strip()

    # L'actif seul suffit à cadrer : une conséquence redoutée est utile mais
    # pas indispensable pour amorcer un balayage.
    if not asset and not damage:
        raise ValueError("Décrivez l'actif ou la conséquence redoutée.")

    crew = build_crew(
        item or "Système embarqué non nommé",
        asset or "Actif non nommé",
        damage or "Conséquence non décrite",
        task_callback=task_callback,
    )
    result = crew.kickoff()
    return parse_suggestions(result.raw)
