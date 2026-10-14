"""Assemblage du crew : agents + tâches + process séquentiel."""

from i18n import DEFAULT_LANG

from crewai import Crew, Process

from .agents import make_agents, make_llm
from .tasks import make_tasks


def build_crew(docs: dict[str, str], task_callback=None,
               lang: str = DEFAULT_LANG, visitor: bool = False) -> Crew:
    """Mêmes consignes pour la démo et le visiteur (`tasks.py`). `visitor=True` :
    AUCUN affichage console — rien des documents d'un visiteur dans les journaux.
    La démo, elle, garde l'affichage (documents fictifs et publics)."""
    llm = make_llm()
    agents = make_agents(llm, verbose=not visitor)
    tasks = make_tasks(agents, docs, lang)

    return Crew(
        agents=list(agents.values()),
        tasks=tasks,
        process=Process.sequential,
        verbose=not visitor,
        task_callback=task_callback,
    )
