"""Crew de proposition d'événements redoutés.

Deux agents suffisent : un qui balaie, un qui élague. Un crew de quatre
serait de la mise en scène — la valeur est dans le balayage systématique
des mots-guides, pas dans le nombre d'intervenants.

Les agents ne cotent jamais S, E ni C. La cotation est le jugement de
l'ingénieur ; la déléguer viderait la démarche de son sens.
"""

from crewai import Agent, Crew, LLM, Process, Task

from i18n import DEFAULT_LANG
from qualitycrew.config import LLM_MODEL, language_rule, llm_options  # noqa: F401  (charge le .env + le patch litellm)

from .hazards import guide_words_block, situations_block

SEPARATOR = "||"
MAX_SUGGESTIONS = 10


def _make_llm() -> LLM:
    return LLM(model=LLM_MODEL, **llm_options())


def _make_agents(llm: LLM) -> dict[str, Agent]:
    analyste = Agent(
        role="Ingénieur sûreté de fonctionnement",
        goal=(
            "Balayer systématiquement les mots-guides et les situations de "
            "conduite pour proposer les événements redoutés d'un item véhicule."
        ),
        backstory=(
            "Tu prépares des analyses de risques pour des systèmes embarqués "
            "automobiles. Tu sais qu'un événement redouté n'est pas un "
            "dysfonctionnement isolé : c'est un dysfonctionnement placé dans "
            "une situation de conduite où il produit un dommage. Tu procèdes "
            "par balayage méthodique, jamais par inspiration."
        ),
        llm=llm,
        verbose=True,
    )

    relecteur = Agent(
        role="Relecteur d'analyse de risques",
        goal=(
            "Élaguer la liste proposée : retirer les doublons et les "
            "formulations creuses, et garantir que chaque ligne associe bien "
            "un dysfonctionnement précis à une situation concrète."
        ),
        backstory=(
            "Tu relis des HARA avant leur revue. Tu élimines sans état d'âme "
            "les lignes qui n'apportent rien, et tu reformules celles qui "
            "restent vagues. Tu préfères huit événements exploitables à vingt "
            "approximatifs."
        ),
        llm=llm,
        verbose=True,
    )

    return {"analyste": analyste, "relecteur": relecteur}


def _make_tasks(agents: dict[str, Agent], item: str,
                lang: str = DEFAULT_LANG) -> list[Task]:
    output_rule = (
        language_rule(lang) + "\n"
        f"Une ligne par événement, au format exact :\n"
        f"dysfonctionnement {SEPARATOR} situation de conduite\n"
        f"Aucune numérotation, aucun titre, aucun commentaire, "
        f"aucune cotation S/E/C. {MAX_SUGGESTIONS} lignes au maximum."
    )

    proposition = Task(
        description=(
            f"Item étudié : « {item} »\n\n"
            "Pour chaque mot-guide ci-dessous, demande-toi si le "
            "dysfonctionnement correspondant est plausible pour cet item. "
            "S'il l'est, associe-le à la situation de conduite qui le rend "
            "le plus dangereux.\n\n"
            f"Mots-guides :\n{guide_words_block()}\n\n"
            f"Situations de conduite typiques :\n{situations_block()}\n\n"
            "Tu peux proposer une situation hors de cette liste si elle est "
            "plus pertinente pour l'item. Ne code aucune cotation.\n\n"
            f"{output_rule}"
        ),
        expected_output=output_rule,
        agent=agents["analyste"],
    )

    relecture = Task(
        description=(
            "Relis la liste proposée. Retire les doublons et toute ligne dont "
            "le dysfonctionnement ou la situation reste vague. Reformule ce "
            "qui peut l'être en une phrase courte et concrète. Conserve "
            "l'ordre de gravité perçue, du plus grave au moins grave.\n\n"
            f"{output_rule}"
        ),
        expected_output=output_rule,
        agent=agents["relecteur"],
    )

    return [proposition, relecture]


def build_crew(item: str, task_callback=None, lang: str = DEFAULT_LANG) -> Crew:
    llm = _make_llm()
    agents = _make_agents(llm)
    return Crew(
        agents=list(agents.values()),
        tasks=_make_tasks(agents, item, lang),
        process=Process.sequential,
        verbose=True,
        task_callback=task_callback,
    )
