"""Définition des 4 tâches du crew, une par agent.

Un seul jeu de consignes, GÉNÉRIQUE (`visitor.py`), pour la démo comme pour les
documents d'un visiteur (14/10/2026, étape 5 du « 12/12 réel »). Avant, la démo
avait des consignes ciblées sur l'exemple (« module BTM », « SRS-014 et
SRS-015 », « contacteur < 50 ms ») : elles lui donnaient la réponse, et le
« 12/12 » affiché ne disait rien d'un document inconnu. Le score affiché est
désormais celui de CES consignes, mesuré (voir CLAUDE.md).
"""

from i18n import DEFAULT_LANG

from .config import language_rule
from .visitor import descriptions

from crewai import Agent, Task


def make_tasks(agents: dict[str, Agent], docs: dict[str, str],
               lang: str = DEFAULT_LANG) -> list[Task]:
    return [
        Task(description=description, expected_output=expected, agent=agents[agent])
        for agent, description, expected in descriptions(docs, language_rule(lang))
    ]
