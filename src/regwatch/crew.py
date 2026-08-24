"""Crew d'explication — un agent, un seul appel.

**Un agent, pas deux.** SafetyScope et ThreatScope en emploient deux (un qui
balaie, un qui élague) parce qu'il y a une liste à réduire. Ici la liste est
déjà arrêtée par la classification déterministe : il n'y a rien à élaguer,
seulement une phrase à écrire par ligne. Un second agent serait de la mise
en scène.

⚠️ **Un seul appel pour tous les items, jamais un appel par item.** Le quota
quotidien Groq gratuit ne survivrait pas à quinze appels par veille — et la
démonstration doit tenir toute la journée pour un site public.

⚠️ **Le modèle ne reçoit que des métadonnées** : titre, date, norme, palier
et nom de la source. Jamais le corps d'une page — on ne l'a même pas
téléchargé. C'est ce qui rend l'étape défendable face à des normes payantes,
et ça répond aussi au `ai-train=no` d'ISO : rien n'entraîne rien, et la
source est référencée par un lien.
"""

from crewai import Agent, Crew, LLM, Process, Task

from i18n import DEFAULT_LANG
from qualitycrew.config import LLM_MODEL, language_rule, llm_options  # noqa: F401  (charge le .env + le patch litellm)

SEPARATOR = "||"

# Ce que le modèle doit écrire quand le titre ne permet rien d'utile. Une
# phrase inventée serait pire que pas de phrase du tout : elle donnerait
# l'illusion d'une information là où il n'y a qu'un intitulé.
UNKNOWN = "Intitulé trop peu explicite pour se prononcer — voir la source."


def _make_llm() -> LLM:
    return LLM(model=LLM_MODEL, **llm_options())


def _make_agent(llm: LLM) -> Agent:
    return Agent(
        role="Veilleur normatif",
        goal=(
            "Dire en une phrase factuelle pourquoi un signal repéré mérite "
            "l'attention d'une équipe qui applique la norme concernée."
        ),
        backstory=(
            "Tu tiens la veille normative d'un service qualité et sécurité "
            "dans l'automobile, et tu écris **en français** : les documents "
            "que tu suis sont majoritairement en anglais, tes notes ne le "
            "sont jamais. Tes collègues n'ont pas le temps de lire "
            "quinze pages : ils veulent savoir lesquelles ouvrir. Tu écris "
            "donc court, tu restes factuel, et tu dis franchement quand un "
            "intitulé ne permet pas de se prononcer — inventer une "
            "explication serait pire que de ne rien dire."
        ),
        llm=llm,
        verbose=True,
    )


def _output_rule(count: int, lang: str = DEFAULT_LANG) -> str:
    return (
        f"Rends exactement {count} lignes, une par signal, au format :\n"
        f"numéro {SEPARATOR} phrase\n"
        + language_rule(lang) + "\n"
        + "Une seule phrase par ligne, 25 mots au maximum. Aucun titre, aucune "
        "puce, aucun commentaire avant ou après la liste."
    )


def build_crew(block: str, count: int, task_callback=None,
               lang: str = DEFAULT_LANG) -> Crew:
    """Construit le crew pour un lot de signaux déjà retenus.

    Args:
        block: les signaux numérotés, un par ligne, en métadonnées seules.
        count: nombre de lignes attendues en retour.
    """
    llm = _make_llm()
    agent = _make_agent(llm)

    tache = Task(
        description=(
            "Voici des signaux publics repérés autour de normes qualité et "
            "sécurité. Pour chacun, écris en une phrase pourquoi il mérite "
            "l'attention d'une équipe qui applique la norme citée.\n\n"
            "RÈGLES ABSOLUES :\n"
            "- Tu ne disposes que de l'intitulé, de la date et de la source. "
            "Tu n'as PAS lu le document.\n"
            "- N'invente aucun fait qui ne soit pas dans l'intitulé. Pas de "
            "numéro de clause, pas de date d'entrée en vigueur, pas de "
            "contenu de norme.\n"
            "- Ne résume ni ne paraphrase le texte d'une norme : ce sont des "
            "documents sous licence.\n"
            f"- Si l'intitulé ne permet rien d'utile, écris exactement : "
            f"{UNKNOWN}\n"
            "- Un palier « commentaire » est un blog ou un cabinet de "
            "conseil, pas un normalisateur : n'en fais jamais une annonce "
            "officielle.\n\n"
            f"Signaux :\n{block}\n\n"
            f"{_output_rule(count, lang)}"
        ),
        expected_output=_output_rule(count, lang),
        agent=agent,
    )

    return Crew(
        agents=[agent],
        tasks=[tache],
        process=Process.sequential,
        verbose=True,
        task_callback=task_callback,
    )
