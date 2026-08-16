"""Cotation du risque cybersécurité : faisabilité d'attaque puis valeur de risque.

Logique purement déterministe : aucun appel réseau, aucun LLM, aucune
dépendance. C'est ce qui permet à l'interface de réagir instantanément — même
parti pris que `safetyscope.asil`.

Deux étapes enchaînées :

1. **Potentiel d'attaque** — cinq paramètres cotés par l'ingénieur, sommés,
   puis ramenés à un niveau de faisabilité. Structurellement identique au
   `S+E+C` de l'ASIL : une somme et des seuils.
2. **Valeur de risque** — croisement de l'impact et de la faisabilité,
   de 1 à 5.

⚠️ Deux précautions qui ne sont pas des détails :

- Le barème de points ci-dessous est une **calibration propre**. Il ne
  reproduit pas celui de l'ISO 18045, qui est un document sous licence.
  Le raisonnement de calibration est explicité dans `_CALIBRATION`.
- La matrice de risque de l'ISO/SAE 21434 est donnée **en exemple** par la
  norme, qui laisse chaque organisation définir sa propre méthode. Celle
  d'ici est donc *une* matrice, pas *la* matrice.
"""

from dataclasses import dataclass

# --------------------------------------------------------------------------
# Potentiel d'attaque
# --------------------------------------------------------------------------

_CALIBRATION = """\
Le temps et l'équipement portent les écarts les plus larges, délibérément :
ce sont les deux facteurs qui discriminent réellement une attaque sur un
véhicule. Une attaque menée avec un dongle radio à 30 € en quelques jours et
une attaque exigeant un banc de laboratoire et six mois de travail ne se
ressemblent en rien, et un barème qui les rapproche ne sert à rien.

La fenêtre d'opportunité suit de près : sur un véhicule, pouvoir agir sur une
voiture en stationnement, en roulage ou immobilisée à l'atelier change tout.

L'expertise et la connaissance de l'item comptent, mais se révèlent plus
binaires en pratique — on a l'information, ou on ne l'a pas.\
"""

# Chaque paramètre : niveau → (libellé, points). Les points croissent avec la
# DIFFICULTÉ de l'attaque : beaucoup de points = attaque peu faisable.
ELAPSED_TIME = {
    0: ("Moins d'une journée", 0),
    1: ("Moins d'une semaine", 2),
    2: ("Moins d'un mois", 5),
    3: ("Moins de six mois", 9),
    4: ("Plus de six mois", 14),
}

EXPERTISE = {
    0: ("Profane", 0),
    1: ("Compétent", 2),
    2: ("Expert", 5),
    3: ("Plusieurs experts de domaines différents", 8),
}

ITEM_KNOWLEDGE = {
    0: ("Publique", 0),
    1: ("Restreinte", 2),
    2: ("Confidentielle", 5),
    3: ("Strictement confidentielle", 8),
}

WINDOW = {
    0: ("Illimitée", 0),
    1: ("Facile à obtenir", 2),
    2: ("Modérée", 5),
    3: ("Difficile à obtenir", 9),
}

EQUIPMENT = {
    0: ("Standard", 0),
    1: ("Spécialisé", 3),
    2: ("Sur mesure", 7),
    3: ("Plusieurs équipements sur mesure", 11),
}

# Ordre d'appel de attack_potential(), et ordre d'affichage dans l'interface.
PARAMETERS = {
    "time": ("Temps nécessaire", ELAPSED_TIME),
    "expertise": ("Expertise requise", EXPERTISE),
    "knowledge": ("Connaissance de l'item", ITEM_KNOWLEDGE),
    "window": ("Fenêtre d'opportunité", WINDOW),
    "equipment": ("Équipement", EQUIPMENT),
}

MAX_POTENTIAL = sum(max(p for _, p in levels.values()) for _, levels in PARAMETERS.values())

# Du moins au plus faisable — un attaquant progresse de gauche à droite.
FEASIBILITY_ORDER = ["Très faible", "Faible", "Moyenne", "Élevée"]

FEASIBILITY_LABELS = {index: name for index, name in enumerate(FEASIBILITY_ORDER)}

# Seuils de points, bornes hautes incluses. Au-delà du dernier : très faible.
# Chaque palier représente un saut d'investissement de l'attaquant, ancré sur
# un archétype concret (voir les tests, qui les vérifient un par un).
_FEASIBILITY_THRESHOLDS = [
    (13, 3),  # ≤ 13 : quelques jours, matériel courant → faisabilité élevée
    (23, 2),  # ≤ 23 : quelques semaines, matériel spécialisé → moyenne
    (33, 1),  # ≤ 33 : plusieurs mois, sur mesure ou expertise rare → faible
]

# --------------------------------------------------------------------------
# Impact et valeur de risque
# --------------------------------------------------------------------------

IMPACT_ORDER = ["Négligeable", "Modéré", "Majeur", "Sévère"]

IMPACT_LABELS = {index: name for index, name in enumerate(IMPACT_ORDER)}

# Les quatre catégories d'impact cotées séparément par l'ingénieur.
IMPACT_CATEGORIES = {
    "safety": "Sécurité des personnes",
    "financial": "Financier",
    "operational": "Opérationnel",
    "privacy": "Vie privée",
}

# Matrice impact × faisabilité → valeur de risque, de 1 à 5.
# Écrite à plat pour rester lisible : _RISK[impact][faisabilité].
#                     TrèsF  Faible  Moyenne  Élevée
_RISK = {
    0: [1, 1, 1, 1],  # Négligeable — pas de dommage significatif, pas de risque
    1: [1, 2, 2, 3],  # Modéré
    2: [1, 2, 3, 4],  # Majeur
    3: [2, 3, 4, 5],  # Sévère
}

RISK_RANGE = (1, 5)


class InvalidRating(ValueError):
    """Cotation hors des bornes admises."""


@dataclass(frozen=True)
class RiskResult:
    """Résultat complet de la cotation d'un chemin d'attaque."""

    risk: int
    impact: int
    feasibility: int
    potential: int

    @property
    def impact_label(self) -> str:
        return IMPACT_LABELS[self.impact]

    @property
    def feasibility_label(self) -> str:
        return FEASIBILITY_LABELS[self.feasibility]

    @property
    def needs_treatment(self) -> bool:
        """Au-delà de 1, le risque appelle une décision de traitement explicite.

        Un risque de 1 peut être retenu sans autre forme de procès ; tout le
        reste doit être tranché et justifié.
        """
        return self.risk > 1


def _check(value: int, high: int, axis: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise InvalidRating(f"{axis} doit être un entier, reçu {value!r}.")
    if not 0 <= value <= high:
        raise InvalidRating(f"{axis} doit être compris entre 0 et {high}, reçu {value}.")


def attack_potential(
    time: int,
    expertise: int,
    knowledge: int,
    window: int,
    equipment: int,
) -> int:
    """Somme les points des cinq paramètres du potentiel d'attaque.

    Args:
        time: temps nécessaire, 0 à 4.
        expertise: expertise requise, 0 à 3.
        knowledge: connaissance de l'item, 0 à 3.
        window: fenêtre d'opportunité, 0 à 3.
        equipment: équipement, 0 à 3.

    Returns:
        Un total de 0 à MAX_POTENTIAL. Plus il est élevé, plus l'attaque est
        coûteuse — donc peu faisable.

    Raises:
        InvalidRating: si une cotation sort de ses bornes.
    """
    values = (time, expertise, knowledge, window, equipment)
    total = 0
    for value, (name, levels) in zip(values, PARAMETERS.values()):
        _check(value, max(levels), name)
        total += levels[value][1]
    return total


def feasibility_from_potential(potential: int) -> int:
    """Ramène un potentiel d'attaque à un niveau de faisabilité (0 à 3)."""
    if not isinstance(potential, int) or isinstance(potential, bool):
        raise InvalidRating(f"Le potentiel doit être un entier, reçu {potential!r}.")
    if not 0 <= potential <= MAX_POTENTIAL:
        raise InvalidRating(
            f"Le potentiel doit être compris entre 0 et {MAX_POTENTIAL}, reçu {potential}."
        )
    for ceiling, level in _FEASIBILITY_THRESHOLDS:
        if potential <= ceiling:
            return level
    return 0


def overall_impact(safety: int, financial: int, operational: int, privacy: int) -> int:
    """Retient l'impact le plus élevé des quatre catégories.

    **Choix de méthode assumé** : la norme n'impose pas d'agrégation. Retenir
    le maximum revient à dire qu'un scénario de dommage est aussi grave que sa
    pire conséquence. Le détail par catégorie reste affiché à côté — il ne
    disparaît pas dans l'agrégation.
    """
    for value, name in (
        (safety, "L'impact sécurité des personnes"),
        (financial, "L'impact financier"),
        (operational, "L'impact opérationnel"),
        (privacy, "L'impact vie privée"),
    ):
        _check(value, len(IMPACT_ORDER) - 1, name)
    return max(safety, financial, operational, privacy)


def determine_risk(impact: int, feasibility: int) -> int:
    """Croise un niveau d'impact et un niveau de faisabilité.

    Args:
        impact: 0 (négligeable) à 3 (sévère).
        feasibility: 0 (très faible) à 3 (élevée).

    Returns:
        La valeur de risque, de 1 à 5.

    Raises:
        InvalidRating: si une cotation sort de ses bornes.
    """
    _check(impact, len(IMPACT_ORDER) - 1, "L'impact")
    _check(feasibility, len(FEASIBILITY_ORDER) - 1, "La faisabilité")
    return _RISK[impact][feasibility]


def rate(
    impact: int,
    time: int,
    expertise: int,
    knowledge: int,
    window: int,
    equipment: int,
) -> RiskResult:
    """Cote un chemin d'attaque de bout en bout : potentiel → faisabilité → risque."""
    potential = attack_potential(time, expertise, knowledge, window, equipment)
    feasibility = feasibility_from_potential(potential)
    return RiskResult(
        risk=determine_risk(impact, feasibility),
        impact=impact,
        feasibility=feasibility,
        potential=potential,
    )


def full_scales() -> dict:
    """Barème et matrice complets, prêts à sérialiser.

    Sert de **source de vérité unique** : la page web les charge une fois et
    fait ses lookups localement, ce qui rend la cotation instantanée sans
    dupliquer cette logique en JavaScript. Même contrat que
    `safetyscope.asil.full_matrix()`.

    Les clés de `risk` sont de la forme "I{impact}F{faisabilité}".
    """
    risk = {}
    for impact in range(len(IMPACT_ORDER)):
        for feasibility in range(len(FEASIBILITY_ORDER)):
            risk[f"I{impact}F{feasibility}"] = determine_risk(impact, feasibility)

    return {
        "parameters": {
            key: {
                "label": name,
                "levels": [
                    {"value": level, "label": label, "points": points}
                    for level, (label, points) in sorted(levels.items())
                ],
            }
            for key, (name, levels) in PARAMETERS.items()
        },
        "maxPotential": MAX_POTENTIAL,
        # Bornes hautes de chaque palier, pour que l'interface puisse expliquer
        # le passage d'un niveau à l'autre au lieu de le subir.
        "feasibilityThresholds": [
            {"upTo": ceiling, "level": level} for ceiling, level in _FEASIBILITY_THRESHOLDS
        ],
        "feasibilityOrder": FEASIBILITY_ORDER,
        "impactOrder": IMPACT_ORDER,
        "impactCategories": IMPACT_CATEGORIES,
        "risk": risk,
        "riskRange": list(RISK_RANGE),
        "calibration": _CALIBRATION,
    }
