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

from i18n import DEFAULT_LANG, t

from dataclasses import dataclass

# --------------------------------------------------------------------------
# Potentiel d'attaque
# --------------------------------------------------------------------------

# ⚠️ **Les points sont le barème ; les libellés sont de la présentation.**
# Séparer les deux est ce qui permet de traduire sans toucher à la
# calibration — et de vérifier que la traduction ne l'a pas touchée.
# Les points croissent avec la DIFFICULTÉ : beaucoup de points = attaque peu
# faisable.
_POINTS: dict[str, tuple[int, ...]] = {
    "time": (0, 2, 5, 9, 14),
    "expertise": (0, 2, 5, 8),
    "knowledge": (0, 2, 5, 8),
    "window": (0, 2, 5, 9),
    "equipment": (0, 3, 7, 11),
}

# Ordre d'appel de attack_potential(), et ordre d'affichage dans l'interface.
PARAMETER_ORDER = ("time", "expertise", "knowledge", "window", "equipment")


def parameter_levels(key: str, lang: str = DEFAULT_LANG) -> dict[int, tuple[str, int]]:
    """Niveaux d'un paramètre : niveau → (libellé, points)."""
    return {
        niveau: (t(f"tara.{key}.{niveau}", lang), points)
        for niveau, points in enumerate(_POINTS[key])
    }


def parameters(lang: str = DEFAULT_LANG) -> dict[str, tuple[str, dict]]:
    """Les cinq paramètres : clé → (libellé, niveaux)."""
    return {
        key: (t(f"tara.param.{key}", lang), parameter_levels(key, lang))
        for key in PARAMETER_ORDER
    }


def feasibility_order(lang: str = DEFAULT_LANG) -> list[str]:
    """Du moins au plus faisable — un attaquant progresse de gauche à droite."""
    return [t(f"tara.feasibility.{n}", lang) for n in range(4)]


def impact_order(lang: str = DEFAULT_LANG) -> list[str]:
    return [t(f"tara.impact.{n}", lang) for n in range(4)]


def impact_categories(lang: str = DEFAULT_LANG) -> dict[str, str]:
    """Les quatre catégories d'impact cotées séparément par l'ingénieur."""
    return {cle: t(f"tara.category.{cle}", lang)
            for cle in ("safety", "financial", "operational", "privacy")}


MAX_POTENTIAL = sum(max(points) for points in _POINTS.values())

FEASIBILITY_LEVELS = 4

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

IMPACT_LEVELS = 4

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
        return impact_order()[self.impact]

    @property
    def feasibility_label(self) -> str:
        return feasibility_order()[self.feasibility]

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
    # ⚠️ La cotation s'appuie sur `_POINTS` seul : le barème ne doit dépendre
    # d'aucun libellé, donc d'aucune langue. Le message d'erreur, lui, nomme
    # le paramètre dans la langue par défaut — il s'adresse au développeur,
    # pas au visiteur (l'interface valide avant d'appeler).
    values = (time, expertise, knowledge, window, equipment)
    total = 0
    for value, key in zip(values, PARAMETER_ORDER):
        points = _POINTS[key]
        _check(value, len(points) - 1, t(f"tara.param.{key}"))
        total += points[value]
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
        _check(value, IMPACT_LEVELS - 1, name)
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
    _check(impact, IMPACT_LEVELS - 1, "L'impact")
    _check(feasibility, FEASIBILITY_LEVELS - 1, "La faisabilité")
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


def full_scales(lang: str = DEFAULT_LANG) -> dict:
    """Barème et matrice complets, prêts à sérialiser.

    Sert de **source de vérité unique** : la page web les charge une fois et
    fait ses lookups localement, ce qui rend la cotation instantanée sans
    dupliquer cette logique en JavaScript. Même contrat que
    `safetyscope.asil.full_matrix()`.

    Les clés de `risk` sont de la forme "I{impact}F{faisabilité}".
    """
    risk = {}
    for impact in range(IMPACT_LEVELS):
        for feasibility in range(FEASIBILITY_LEVELS):
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
            for key, (name, levels) in parameters(lang).items()
        },
        "maxPotential": MAX_POTENTIAL,
        # Table complète potentiel → faisabilité, un cran par point. L'interface
        # y fait un simple lookup : les seuils ne sont **jamais** réécrits en
        # JavaScript, ils ne vivent qu'ici.
        "feasibilityByPotential": [
            feasibility_from_potential(points) for points in range(MAX_POTENTIAL + 1)
        ],
        # Bornes hautes de chaque palier, pour que l'interface puisse expliquer
        # le passage d'un niveau à l'autre au lieu de le subir.
        "feasibilityThresholds": [
            {"upTo": ceiling, "level": level} for ceiling, level in _FEASIBILITY_THRESHOLDS
        ],
        "feasibilityOrder": feasibility_order(lang),
        "impactOrder": impact_order(lang),
        "impactCategories": impact_categories(lang),
        "risk": risk,
        "riskRange": list(RISK_RANGE),
        "calibration": t("tara.calibration", lang),
    }
