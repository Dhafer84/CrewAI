"""Traitement du risque et objectifs de cybersécurité — le bout de la chaîne.

Une TARA ne produit pas un chiffre, elle produit des **exigences**. Une valeur
de risque qui ne débouche sur aucune décision n'a rien décidé.

Quatre traitements possibles, et chacun laisse une trace écrite différente :

- **Éviter** — on supprime la source du risque. Il faut dire ce qu'on retire.
- **Réduire** — on ramène le risque à un niveau acceptable. C'est ici que naît
  l'**objectif de cybersécurité**, la sortie utile de toute la démarche.
- **Partager** — on transfère tout ou partie du risque à un tiers. Il faut dire
  à qui et sur quelle base.
- **Accepter** — on conserve le risque en connaissance de cause. Un risque
  retenu sans argument écrit est un risque oublié : la justification est
  obligatoire.

⚠️ Formulations propres. L'ISO/SAE 21434 est un document sous licence ; on
implémente la démarche, on ne recopie pas son texte.
"""

from i18n import DEFAULT_LANG, t

from .rating import RISK_RANGE, InvalidRating

# Du plus radical au plus permissif.
TREATMENT_ORDER = ["avoid", "reduce", "share", "retain"]

# ⚠️ `requires` est un **IDENTIFIANT, pas un libellé** : il pilote la logique
# (`== "goal"`) et ne se traduit donc jamais. Il désigne le champ que la
# décision oblige à remplir :
#   "goal"      → un objectif de cybersécurité, c'est-à-dire une exigence
#   "rationale" → une justification écrite
_REQUIRES = {
    "avoid": "rationale",
    "reduce": "goal",
    "share": "rationale",
    "retain": "rationale",
}


def requires_field(decision: str) -> str:
    """Le champ qu'une décision oblige à remplir. Sans langue, par nature."""
    return _REQUIRES[decision]


def treatments(lang: str = DEFAULT_LANG) -> dict[str, dict[str, str]]:
    """Les quatre décisions de traitement, libellées."""
    return {
        key: {
            "label": t(f"tara.treatment.{key}.label", lang),
            "hint": t(f"tara.treatment.{key}.hint", lang),
            "requires": _REQUIRES[key],
            "prompt": t(f"tara.treatment.{key}.prompt", lang),
        }
        for key in TREATMENT_ORDER
    }


# Seuil au-delà duquel une décision explicite est exigée. Un risque de 1 peut
# être retenu sans autre forme de procès ; tout le reste doit être tranché.
DECISION_THRESHOLD = 1


def requires_decision(risk: int) -> bool:
    """Ce risque appelle-t-il une décision de traitement explicite ?"""
    low, high = RISK_RANGE
    if not isinstance(risk, int) or isinstance(risk, bool):
        raise InvalidRating(f"Le risque doit être un entier, reçu {risk!r}.")
    if not low <= risk <= high:
        raise InvalidRating(f"Le risque doit être compris entre {low} et {high}, reçu {risk}.")
    return risk > DECISION_THRESHOLD


def check(risk: int, decision: str = "", goal: str = "", rationale: str = "") -> list[str]:
    """Liste ce qui manque pour que le traitement soit complet.

    Rend des constats génériques, sans savoir de quelle menace il s'agit :
    c'est à l'appelant de les situer. Une liste vide signifie « rien à
    redire ».
    """
    decision = (decision or "").strip()

    if not decision:
        return ["aucune décision de traitement"] if requires_decision(risk) else []

    if decision not in _REQUIRES:
        return [f"décision de traitement inconnue ({decision})"]

    besoin = requires_field(decision)
    fourni = (goal if besoin == "goal" else rationale) or ""
    if not fourni.strip():
        manque = "l'objectif de cybersécurité" if besoin == "goal" else "la justification"
        return [f"{manque} manque"]
    return []


def produces_goal(decision: str) -> bool:
    """Seule la réduction du risque produit une exigence de cybersécurité."""
    return _REQUIRES.get((decision or "").strip()) == "goal"


def treatment_scales(lang: str = DEFAULT_LANG) -> dict:
    """Options de traitement, prêtes à sérialiser pour l'interface.

    Même contrat que le barème et la matrice : la page ne réécrit ni les
    libellés, ni ce que chaque décision oblige à remplir — elle les lit.
    """
    return {
        "order": TREATMENT_ORDER,
        "options": treatments(lang),
        "decisionThreshold": DECISION_THRESHOLD,
    }
