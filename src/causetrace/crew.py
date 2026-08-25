"""Crew de relecture — un agent, un appel par discipline.

**Un agent, pas deux.** SafetyScope et ThreatScope en emploient deux (un qui
balaie, un qui élague) parce qu'il y a une liste à réduire. Ici il n'y a rien
à élaguer : l'ingénieur a écrit un texte, il s'agit de le resserrer et de dire
ce qui manque. Un second agent serait de la mise en scène — même raison que
dans RegWatch.

⚠️ **Un appel par DISCIPLINE, jamais par champ.** Un guide continu à raison
d'un appel par frappe brûlerait l'enveloppe Groq en un visiteur. L'ingénieur
remplit un D, demande sa relecture : environ cinq appels pour un 8D entier.

## ⚠️ Le danger de cette fonction : le fait inventé

Un modèle qui « améliore » une description ajoute spontanément une date, un
nombre de pièces, un numéro de lot. Dans un document qui part chez le client,
un fait inventé est catastrophique — bien pire qu'une phrase mal écrite.

D'où le geste central : **l'IA ne complète pas, elle réclame.** Tout ce
qu'elle voudrait ajouter mais ne peut pas savoir devient une **demande**, pas
une valeur. C'est le même esprit que le « je ne peux pas me prononcer » de
RegWatch, qui est reconnu et non stocké.

Trois autres verrous, portés par le prompt et vérifiés par les tests :

- **Elle ne juge jamais.** Dire si un 8D est complet appartient au moteur
  déterministe ; un modèle qui s'en mêlerait rendrait le verdict irreproductible.
- **Elle ne remplit pas un champ vide.** Seuls les champs déjà écrits lui sont
  soumis. Un champ vide relève du moteur, qui le signale déjà.
- **Elle se tait sur ce qui va bien.** Reformuler une phrase déjà précise ne
  produit que du bruit et de la défiance.

⚠️ **Elle interroge le fond, sans jamais le juger.** Quand un pourquoi met en
cause une personne, la consigne lui demande de poser la question suivante —
« qu'est-ce qui, dans l'organisation, a rendu ce geste possible ? » — et non
de déclarer la chaîne fautive. Ce verdict-là appartient à `whychain`, qui le
rend de façon déterministe.

⚠️ **L'effet de cette consigne n'est pas établi.** Deux runs réels le
25/08/2026, un sans et un avec : dans les deux cas le modèle a réclamé des
faits (valeur de couple, référence de consigne) et jamais la question
systémique. Le plafond de quatre demandes l'évince probablement. Un run avant
et un run après ne mesurent rien ; la consigne est gardée parce qu'elle est
juste, pas parce qu'elle est prouvée. Ne pas la retoucher sur une seule
observation — c'est exactement le surapprentissage écarté à l'étape B4.
"""

from crewai import Agent, Crew, LLM, Process, Task

from i18n import DEFAULT_LANG
from qualitycrew.config import LLM_MODEL, language_rule, llm_options  # noqa: F401  (charge le .env + le patch litellm)

SEPARATOR = "||"

# ⚠️ Marqueur d'une demande : un point d'interrogation, PAS un mot.
# Le prompt est en français mais la sortie suit la langue du visiteur : un
# marqueur lexical comme « MANQUE » se ferait traduire en « MISSING » et le
# parseur ne le reconnaîtrait plus. Un « ? » ne se traduit pas — et il dit
# exactement ce que la ligne fait : elle demande.
DEMAND_MARK = "?"


def _make_llm() -> LLM:
    return LLM(model=LLM_MODEL, **llm_options())


def _make_agent(llm: LLM) -> Agent:
    return Agent(
        role="Relecteur de 8D",
        goal=(
            "Resserrer la rédaction d'un 8D sans jamais y ajouter un fait, et "
            "réclamer par écrit ce qui manque pour qu'il soit exploitable."
        ),
        backstory=(
            "Tu relis les 8D qu'un fournisseur envoie à son client. Tu sais "
            "qu'un 8D se juge sur sa précision : « plusieurs pièces » ne "
            "permet ni de trier, ni de comparer, ni de borner. Tu resserres "
            "donc ce qui est écrit — et quand il manque un chiffre, une date "
            "ou un périmètre, tu **poses la question** au lieu de l'inventer. "
            "Un fait que tu ajouterais partirait chez le client sous la "
            "signature de quelqu'un d'autre. Tu ne dis jamais si le dossier "
            "est complet : ce n'est pas ton rôle."
        ),
        llm=llm,
        verbose=True,
    )


def _output_rule(count: int, lang: str = DEFAULT_LANG) -> str:
    return (
        "Format de réponse, une information par ligne :\n"
        f"  numéro {SEPARATOR} la reformulation de ce champ\n"
        f"  {DEMAND_MARK} {SEPARATOR} une information qui manque, formulée en question\n"
        f"Au plus une ligne numérotée par champ. Ne rends une ligne numérotée "
        f"que si tu améliores VRAIMENT la formulation ; sinon, n'écris pas de "
        f"ligne pour ce champ.\n"
        + language_rule(lang) + "\n"
        + "Aucun titre, aucune puce, aucun commentaire avant ou après."
    )


def build_crew(discipline: str, block: str, count: int,
               task_callback=None, lang: str = DEFAULT_LANG) -> Crew:
    """Construit le crew de relecture d'une discipline.

    Args:
        discipline: le nom lisible de la discipline relue.
        block: les champs renseignés, numérotés, un par ligne.
        count: nombre de champs soumis.
    """
    llm = _make_llm()
    agent = _make_agent(llm)

    tache = Task(
        description=(
            f"Voici les champs déjà renseignés de la discipline « {discipline} » "
            "d'un rapport 8D. Relis-les.\n\n"
            "RÈGLES ABSOLUES :\n"
            "- **N'ajoute AUCUN fait.** Pas de date, pas de quantité, pas de "
            "numéro de lot, pas de nom qui ne soit pas déjà écrit. Si une "
            "information manque, elle va sur une ligne de demande, jamais "
            "dans une reformulation.\n"
            "- Une reformulation dit la MÊME chose, plus précisément et plus "
            "court. Elle ne conclut rien et n'ajoute pas de cause.\n"
            "- Ne dis jamais si le dossier est complet, conforme ou "
            "acceptable : ce n'est pas ton rôle.\n"
            "- Ne reformule pas un champ déjà clair : passe-le sous silence.\n"
            "- Réclame en priorité ce qui rend un 8D inexploitable : une "
            "quantité qui n'est pas chiffrée, une date qui n'en est pas une, "
            "un périmètre qu'on ne peut pas borner.\n"
            "- **Si un pourquoi met en cause une personne**, demande ce qui, "
            "dans l'organisation, a rendu ce geste possible — une consigne "
            "ambiguë, un outil qui ne contrôle rien, une formation absente. "
            "Ne dis PAS que la chaîne est fautive : pose la question "
            "suivante, c'est elle qui manque.\n"
            "- Au plus 4 demandes, les plus utiles.\n\n"
            f"Champs :\n{block}\n\n"
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


# --------------------------------------------------------------------------
# Proposition de contenu — Ishikawa 5M et questions discriminantes
#
# ⚠️ **Étape distincte de la relecture.** La relecture porte sur ce que
# l'ingénieur a ÉCRIT ; ici l'IA propose ce qu'il n'a PAS écrit. C'est le même
# usage que dans SafetyScope et ThreatScope — dérouler les cinq familles d'un
# Ishikawa est long, répétitif, et un modèle y est réellement bon.
#
# ⚠️ **Les familles et les axes sont NUMÉROTÉS dans le prompt**, jamais nommés
# en retour. Le prompt est en français mais la sortie suit la langue du
# visiteur : « Méthode » reviendrait en « Method » et l'appariement serait
# perdu. Même raison que le marqueur « ? » de la relecture.
# --------------------------------------------------------------------------


def _make_proposer(llm: LLM) -> Agent:
    return Agent(
        role="Animateur d'analyse causale",
        goal=(
            "Ouvrir des pistes de cause qu'une équipe n'aurait pas explorées, "
            "sans jamais désigner laquelle est la bonne."
        ),
        backstory=(
            "Tu animes des groupes de résolution de problème dans l'industrie "
            "automobile. Ton rôle est de faire émerger des hypothèses, pas de "
            "trancher : c'est l'équipe qui investigue et qui conclut. Tu sais "
            "qu'une piste énoncée trop vaguement — « problème de qualité », "
            "« manque de rigueur » — ne se vérifie pas, donc tu formules des "
            "hypothèses que l'on peut aller CONTRÔLER sur le terrain."
        ),
        llm=llm,
        verbose=True,
    )


def _proposal_rule(lang: str = DEFAULT_LANG) -> str:
    return (
        f"Format de réponse, une proposition par ligne :\n"
        f"  numéro {SEPARATOR} la proposition\n"
        "Le numéro est celui de la liste ci-dessus. Plusieurs lignes peuvent "
        "porter le même numéro.\n"
        + language_rule(lang) + "\n"
        + "Aucun titre, aucune puce, aucun commentaire avant ou après."
    )


def build_ishikawa_crew(problem: str, families: str, per_family: int,
                        task_callback=None, lang: str = DEFAULT_LANG) -> Crew:
    """Propose des hypothèses de cause, famille par famille.

    Args:
        problem: la description du problème telle que saisie.
        families: les cinq familles, numérotées, une par ligne.
        per_family: nombre maximal d'hypothèses par famille.
    """
    llm = _make_llm()
    agent = _make_proposer(llm)

    tache = Task(
        description=(
            "Voici un problème constaté sur un produit automobile. Propose des "
            "hypothèses de cause, en balayant les cinq familles ci-dessous.\n\n"
            "RÈGLES ABSOLUES :\n"
            "- Ce sont des HYPOTHÈSES à vérifier, pas des conclusions. Ne dis "
            "jamais laquelle est la cause racine, ne les classe pas, ne les "
            "note pas.\n"
            "- Chaque hypothèse doit être **contrôlable sur le terrain** : on "
            "doit pouvoir aller la confirmer ou l'infirmer. « Problème de "
            "qualité » n'en est pas une ; « couple de serrage non contrôlé au "
            "poste » en est une.\n"
            "- N'invente aucun fait sur ce cas précis : tu proposes des pistes "
            "génériques adaptées au problème décrit, pas des constats.\n"
            f"- Au plus {per_family} hypothèses par famille. Une famille sans "
            "piste crédible n'est pas remplie de force.\n"
            "- Ne qualifie pas la nature d'une hypothèse : c'est l'ingénieur "
            "qui le fera.\n\n"
            f"Problème :\n{problem}\n\n"
            f"Familles :\n{families}\n\n"
            f"{_proposal_rule(lang)}"
        ),
        expected_output=_proposal_rule(lang),
        agent=agent,
    )

    return Crew(agents=[agent], tasks=[tache], process=Process.sequential,
                verbose=True, task_callback=task_callback)


def build_questions_crew(problem: str, axes: str, task_callback=None,
                         lang: str = DEFAULT_LANG) -> Crew:
    """Propose les questions discriminantes « est / n'est pas ».

    ⚠️ Distinct de la relecture, qui demande de préciser ce qui est écrit.
    Ici on cherche la **comparaison qui n'a pas été faite** : ce qui aurait pu
    être touché et ne l'est pas est ce qui resserre le périmètre d'une cause.
    """
    llm = _make_llm()
    agent = _make_proposer(llm)

    tache = Task(
        description=(
            "Voici la description d'un problème. Pour chaque axe ci-dessous, "
            "écris LA question qui ferait apparaître ce qui aurait pu être "
            "touché et ne l'est pas.\n\n"
            "RÈGLES ABSOLUES :\n"
            "- Une seule question par axe, fermée et vérifiable.\n"
            "- Cherche le CONTRASTE : un lot voisin indemne, un poste "
            "identique sans défaut, une période sans occurrence. C'est ce "
            "contraste qui resserre le périmètre d'une cause.\n"
            "- Ne réponds pas aux questions, ne suppose aucune réponse.\n"
            "- N'invente aucun fait sur ce cas.\n\n"
            f"Problème :\n{problem}\n\n"
            f"Axes :\n{axes}\n\n"
            f"{_proposal_rule(lang)}"
        ),
        expected_output=_proposal_rule(lang),
        agent=agent,
    )

    return Crew(agents=[agent], tasks=[tache], process=Process.sequential,
                verbose=True, task_callback=task_callback)
