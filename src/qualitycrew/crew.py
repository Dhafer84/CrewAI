"""Assemblage du crew : agents + tâches + process séquentiel."""

from i18n import DEFAULT_LANG

from crewai import Crew, Process

from .agents import make_agents, make_llm
from .tasks import make_tasks, make_visitor_tasks


def build_crew(docs: dict[str, str], task_callback=None,
               lang: str = DEFAULT_LANG, visitor: bool = False) -> Crew:
    """`visitor=True` : documents d'un visiteur — consignes génériques
    (`visitor.py`) et AUCUN affichage console (rien des documents dans les
    journaux). Sinon : la démo, consignes ciblées sur l'exemple, inchangée."""
    llm = make_llm()
    agents = make_agents(llm, verbose=not visitor)
    tasks = (make_visitor_tasks if visitor else make_tasks)(agents, docs, lang)

    return Crew(
        agents=list(agents.values()),
        tasks=tasks,
        process=Process.sequential,
        verbose=not visitor,
        task_callback=task_callback,
    )
