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

from .rating import RISK_RANGE, InvalidRating

# Du plus radical au plus permissif.
TREATMENT_ORDER = ["avoid", "reduce", "share", "retain"]

# `requires` désigne le champ que la décision oblige à remplir :
#   "goal"      → un objectif de cybersécurité, c'est-à-dire une exigence
#   "rationale" → une justification écrite
TREATMENTS = {
    "avoid": {
        "label": "Éviter le risque",
        "hint": "Supprimer la source du risque : retirer la fonction, l'interface "
                "ou le flux concerné.",
        "requires": "rationale",
        "prompt": "Ce qui est retiré ou remplacé",
    },
    "reduce": {
        "label": "Réduire le risque",
        "hint": "Ramener le risque à un niveau acceptable par des mesures de "
                "cybersécurité. C'est le cas qui produit une exigence.",
        "requires": "goal",
        "prompt": "Objectif de cybersécurité",
    },
    "share": {
        "label": "Partager le risque",
        "hint": "Transférer tout ou partie du risque à un tiers — fournisseur, "
                "contrat, assurance.",
        "requires": "rationale",
        "prompt": "À qui, et sur quelle base",
    },
    "retain": {
        "label": "Accepter le risque",
        "hint": "Conserver le risque en l'état, en connaissance de cause.",
        "requires": "rationale",
        "prompt": "Pourquoi ce risque est acceptable",
    },
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

    if decision not in TREATMENTS:
        return [f"décision de traitement inconnue ({decision})"]

    besoin = TREATMENTS[decision]["requires"]
    fourni = (goal if besoin == "goal" else rationale) or ""
    if not fourni.strip():
        manque = "l'objectif de cybersécurité" if besoin == "goal" else "la justification"
        return [f"{manque} manque"]
    return []


def produces_goal(decision: str) -> bool:
    """Seule la réduction du risque produit une exigence de cybersécurité."""
    return TREATMENTS.get((decision or "").strip(), {}).get("requires") == "goal"


def treatment_scales() -> dict:
    """Options de traitement, prêtes à sérialiser pour l'interface.

    Même contrat que le barème et la matrice : la page ne réécrit ni les
    libellés, ni ce que chaque décision oblige à remplir — elle les lit.
    """
    return {
        "order": TREATMENT_ORDER,
        "options": {key: dict(TREATMENTS[key]) for key in TREATMENT_ORDER},
        "decisionThreshold": DECISION_THRESHOLD,
    }
