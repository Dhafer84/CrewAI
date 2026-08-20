"""Crew de proposition de scénarios de menace.

Deux agents suffisent : un qui balaie STRIDE, un qui élague. Un crew de quatre
serait de la mise en scène — la valeur est dans le balayage systématique des
catégories, pas dans le nombre d'intervenants.

⚠️ **Les agents ne cotent jamais.** Ni l'impact, ni les cinq paramètres de
faisabilité, ni la décision de traitement. Dérouler STRIDE est long et
répétitif : un LLM y est utile. Décider qu'une attaque demande trois semaines
et un banc de laboratoire est un jugement d'ingénieur ; le déléguer viderait
la démarche de son sens.
"""

from crewai import LLM, Agent, Crew, Process, Task

from qualitycrew.config import LLM_MODEL, llm_options  # noqa: F401  (charge le .env + le patch litellm)

from .threats import guide_words_block, surfaces_block

SEPARATOR = "||"
# Aligné sur le plafond de menaces par scénario de dommage : proposer plus
# que ce que la page peut accueillir ne ferait que jeter du travail.
MAX_SUGGESTIONS = 4


def _make_llm() -> LLM:
    return LLM(model=LLM_MODEL, **llm_options())


def _make_agents(llm: LLM) -> dict[str, Agent]:
    analyste = Agent(
        role="Analyste en cybersécurité automobile",
        goal=(
            "Balayer systématiquement les catégories de menace et les surfaces "
            "d'attaque d'un véhicule pour proposer les scénarios de menace qui "
            "réalisent un scénario de dommage donné."
        ),
        backstory=(
            "Tu prépares des analyses de menaces pour des calculateurs "
            "embarqués automobiles. Tu sais qu'un scénario de menace n'est pas "
            "une inquiétude générale : c'est une propriété de sécurité attaquée "
            "sur un actif précis, réalisable par un chemin qu'on peut décrire "
            "étape par étape. Tu procèdes par balayage méthodique, jamais par "
            "inspiration."
        ),
        llm=llm,
        verbose=True,
    )

    relecteur = Agent(
        role="Relecteur d'analyse de menaces",
        goal=(
            "Élaguer la liste proposée : retirer les doublons et les menaces "
            "génériques, et garantir que chaque ligne décrit un chemin "
            "d'attaque concret plutôt qu'une crainte abstraite."
        ),
        backstory=(
            "Tu relis des TARA avant leur revue. Tu élimines sans état d'âme "
            "les lignes qui pourraient s'appliquer à n'importe quel système, et "
            "tu exiges que le chemin d'attaque cite la surface par laquelle "
            "l'attaquant entre. Tu préfères trois menaces exploitables à dix "
            "approximatives."
        ),
        llm=llm,
        verbose=True,
    )

    return {"analyste": analyste, "relecteur": relecteur}


def _make_tasks(agents: dict[str, Agent], item: str, asset: str, damage: str) -> list[Task]:
    # Le modèle a spontanément tendance à recopier le nom de la catégorie
    # comme intitulé de menace. « Usurpation d'identité » ne dit ni ce qui est
    # usurpé ni auprès de qui : c'est inexploitable dans un tableau TARA.
    output_rule = (
        f"Une ligne par menace, au format exact :\n"
        f"scénario de menace {SEPARATOR} chemin d'attaque\n"
        f"Le scénario de menace doit nommer **ce qui est attaqué et auprès de qui**, "
        f"jamais se réduire au nom de la catégorie. "
        f"Trop générique : « Usurpation d'identité ». "
        f"Exploitable : « Usurpation du calculateur de freinage auprès de la passerelle ». "
        f"Aucune numérotation, aucun titre, aucun commentaire. "
        f"**Aucune cotation** : ni impact, ni faisabilité, ni traitement. "
        f"{MAX_SUGGESTIONS} lignes au maximum."
    )

    contexte = (
        f"Item étudié : « {item} »\n"
        f"Actif concerné : « {asset} »\n"
        f"Scénario de dommage à réaliser : « {damage} »\n\n"
    )

    proposition = Task(
        description=(
            contexte
            + "Pour chaque catégorie de menace ci-dessous, demande-toi si elle "
            "permettrait d'aboutir à ce scénario de dommage sur cet actif. Si "
            "oui, décris le chemin d'attaque : par quelle surface l'attaquant "
            "entre, puis les étapes jusqu'au dommage.\n\n"
            f"Catégories de menace :\n{guide_words_block()}\n\n"
            f"Surfaces d'attaque typiques :\n{surfaces_block()}\n\n"
            "Tu peux citer une surface hors de cette liste si elle est plus "
            "pertinente. N'invente aucune cotation : le temps nécessaire, "
            "l'expertise et l'équipement seront évalués par l'ingénieur.\n\n"
            f"{output_rule}"
        ),
        expected_output=output_rule,
        agent=agents["analyste"],
    )

    relecture = Task(
        description=(
            "Relis la liste proposée. Retire les doublons et toute menace qui "
            "s'appliquerait telle quelle à n'importe quel système.\n\n"
            "**Reformule systématiquement tout intitulé qui se réduit au nom "
            "d'une catégorie** (« Altération », « Déni de service »…) : il doit "
            "nommer l'actif visé et la propriété attaquée. Vérifie que chaque "
            "chemin d'attaque nomme la surface d'entrée et enchaîne des étapes "
            "concrètes. Classe du plus plausible au moins plausible.\n\n"
            f"{output_rule}"
        ),
        expected_output=output_rule,
        agent=agents["relecteur"],
    )

    return [proposition, relecture]


def build_crew(item: str, asset: str, damage: str, task_callback=None) -> Crew:
    llm = _make_llm()
    agents = _make_agents(llm)
    return Crew(
        agents=list(agents.values()),
        tasks=_make_tasks(agents, item, asset, damage),
        process=Process.sequential,
        verbose=True,
        task_callback=task_callback,
    )
