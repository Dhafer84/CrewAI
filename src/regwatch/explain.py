"""Étape 3 du pipeline : une phrase « pourquoi ça compte », par l'IA.

⚠️ **L'IA arrive en dernier, et ne filtre jamais.** Ce qui est retenu a été
décidé par `classify`, de façon déterministe, reproductible et testée hors
ligne. Ce module ne fait qu'ajouter une phrase à des lignes **déjà retenues** :
il ne peut ni en écarter une, ni en ajouter une, ni changer son niveau de
signal. `explain_items` rend exactement autant d'items qu'il en reçoit, dans
le même ordre — et un test le verrouille.

L'outil doit rester complet et utile sans cette étape. Si l'appel échoue, le
tableau est déjà là : on perd une commodité, pas le résultat.
"""

from i18n import DEFAULT_LANG

import re
from dataclasses import replace

from .core import WatchItem
from .crew import SEPARATOR, UNKNOWN, build_crew

# Plafond de signaux expliqués en un appel. Deux raisons, dans cet ordre :
# le quota quotidien Groq gratuit, et la qualité — au-delà, le modèle
# expédie les dernières lignes.
MAX_EXPLAINED = 12

MAX_SENTENCE_LENGTH = 220

# Puces et numérotations que le modèle ajoute malgré la consigne.
_LEADING_NOISE = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s*")


def _rank(item: WatchItem, signal_order: tuple[str, ...]) -> tuple[int, str]:
    try:
        strength = signal_order.index(item.signal)
    except ValueError:
        strength = len(signal_order)
    # Signal le plus fort d'abord ; à force égale, le plus récent.
    return (strength, item.published.isoformat())


def select(items: list[WatchItem]) -> list[int]:
    """Indices des signaux à expliquer, les plus forts d'abord.

    Quand il y a plus de signaux que le plafond, on explique les
    **publications et amendements** avant les simples informations : c'est
    la question que pose l'outil. Les indices rendus sont ceux de la liste
    d'origine, dont l'ordre n'est jamais modifié.
    """
    from .classify import SIGNAL_ORDER

    classement = sorted(
        range(len(items)),
        key=lambda index: _rank(items[index], SIGNAL_ORDER),
    )
    return sorted(classement[:MAX_EXPLAINED])


def build_block(items: list[WatchItem], indices: list[int]) -> str:
    """Le lot envoyé au modèle — métadonnées seules, jamais de contenu."""
    lignes = []
    for numero, index in enumerate(indices, start=1):
        item = items[index]
        lignes.append(
            f"{numero}. [{item.norm_label} · {item.signal} · "
            f"{item.published.isoformat()} · {item.source_label} "
            f"({item.source_tier})] {item.title}"
        )
    return "\n".join(lignes)


def parse_explanations(raw: str, count: int) -> list[str]:
    """Extrait les phrases d'une sortie de crew, indexées de 0 à count-1.

    Tolérant, comme les parseurs de SafetyScope et ThreatScope : le modèle
    ajoute des puces, du gras, une phrase d'introduction. Une ligne
    illisible laisse sa place **vide** plutôt que de décaler toutes les
    suivantes — un décalage attribuerait une explication au mauvais signal,
    ce qui est bien pire qu'une case vide.
    """
    phrases = [""] * count

    for ligne in (raw or "").splitlines():
        if SEPARATOR not in ligne:
            continue

        gauche, _, droite = ligne.partition(SEPARATOR)
        numero = re.search(r"\d+", _LEADING_NOISE.sub("", gauche).strip(" *_`#"))
        if not numero:
            continue

        position = int(numero.group(0)) - 1
        if not 0 <= position < count:
            continue

        phrase = droite.strip(" *_`").strip()
        if not phrase:
            continue

        # Premier arrivé, premier servi : si le modèle répète un numéro, on
        # garde sa première réponse plutôt que d'écraser au hasard.
        if not phrases[position]:
            phrases[position] = phrase[:MAX_SENTENCE_LENGTH]

    return phrases


def explain_items(items: list[WatchItem], task_callback=None,
                  lang: str = DEFAULT_LANG) -> list[WatchItem]:
    """Ajoute une phrase à des signaux **déjà retenus**.

    Args:
        items: les signaux d'un `WatchResult`, dans leur ordre d'affichage.
        task_callback: appelé à la fin de la tâche du crew.

    Returns:
        La **même liste, dans le même ordre, de la même longueur** — seul le
        champ `why` change. Rien n'est écarté, rien n'est réordonné : ce
        n'est pas à un modèle de décider de la pertinence.

    Raises:
        ValueError: aucun signal à expliquer.
    """
    if not items:
        raise ValueError("Aucun signal à expliquer.")

    indices = select(items)
    crew = build_crew(build_block(items, indices), len(indices),
                      task_callback=task_callback, lang=lang)
    phrases = parse_explanations(crew.kickoff().raw, len(indices))

    explique = list(items)
    for position, index in enumerate(indices):
        phrase = phrases[position]
        if phrase and phrase != UNKNOWN:
            explique[index] = replace(items[index], why=phrase)
    return explique
