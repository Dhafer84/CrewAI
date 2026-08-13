"""Assemblage du crew : agents + tâches + process séquentiel."""

from crewai import Crew, Process

from .agents import make_agents, make_llm
from .tasks import make_tasks


def build_crew(docs: dict[str, str]) -> Crew:
    llm = make_llm()
    agents = make_agents(llm)
    tasks = make_tasks(agents, docs)

    return Crew(
        agents=list(agents.values()),
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )
