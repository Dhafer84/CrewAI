"""Détermination du niveau ASIL à partir de la cotation S / E / C.

Logique purement déterministe : aucun appel réseau, aucun LLM, aucune
dépendance. C'est ce qui permet à l'interface de réagir instantanément.

⚠️ Démonstration pédagogique. Les libellés ci-dessous sont des reformulations
personnelles destinées à rendre l'outil utilisable ; ils ne reproduisent pas
le texte de l'ISO 26262, qui est un document sous licence. Se référer à la
norme pour toute application réelle.
"""

from dataclasses import dataclass

# Du moins au plus contraignant.
ASIL_ORDER = ["QM", "A", "B", "C", "D"]

# Bornes admises pour chaque axe de cotation.
SEVERITY_RANGE = (0, 3)
EXPOSURE_RANGE = (0, 4)
CONTROLLABILITY_RANGE = (0, 3)

# Somme S+E+C → ASIL. En dessous de 7, la combinaison relève du QM.
_LEVEL_TO_ASIL = {10: "D", 9: "C", 8: "B", 7: "A"}

# Décompositions admises (ISO 26262 Part 9). Chaque couple suppose une
# indépendance suffisante entre les deux éléments — c'est la condition
# lourde de la démarche, pas un détail de notation.
DECOMPOSITIONS: dict[str, list[tuple[str, str]]] = {
    "D": [("D", "QM"), ("C", "A"), ("B", "B")],
    "C": [("C", "QM"), ("B", "A")],
    "B": [("B", "QM"), ("A", "A")],
    "A": [("A", "QM")],
    "QM": [],
}

# Reformulations propres, volontairement courtes.
SEVERITY_LABELS = {
    0: "Aucune blessure",
    1: "Blessures légères à modérées",
    2: "Blessures graves, survie probable",
    3: "Blessures critiques ou mortelles",
}

EXPOSURE_LABELS = {
    0: "Situation invraisemblable",
    1: "Très faible probabilité",
    2: "Faible probabilité",
    3: "Probabilité moyenne",
    4: "Forte probabilité",
}

CONTROLLABILITY_LABELS = {
    0: "Maîtrisable de façon générale",
    1: "Simplement maîtrisable",
    2: "Normalement maîtrisable",
    3: "Difficilement maîtrisable, voire pas du tout",
}


class InvalidRating(ValueError):
    """Cotation hors des bornes admises."""


@dataclass(frozen=True)
class AsilResult:
    """Résultat complet d'une cotation."""

    asil: str
    severity: int
    exposure: int
    controllability: int
    decompositions: list[tuple[str, str]]

    @property
    def is_safety_relevant(self) -> bool:
        """QM signifie que la gestion qualité usuelle suffit."""
        return self.asil != "QM"

    def decomposition_notation(self) -> list[str]:
        """Rend les décompositions dans la notation usuelle, ex. « B(D) + B(D) »."""
        return [
            f"{first}({self.asil}) + {second}({self.asil})"
            for first, second in self.decompositions
        ]


def _check(value: int, bounds: tuple[int, int], axis: str) -> None:
    low, high = bounds
    if not isinstance(value, int) or isinstance(value, bool):
        raise InvalidRating(f"{axis} doit être un entier, reçu {value!r}.")
    if not low <= value <= high:
        raise InvalidRating(f"{axis} doit être compris entre {low} et {high}, reçu {value}.")


def determine_asil(severity: int, exposure: int, controllability: int) -> str:
    """Détermine l'ASIL d'un événement redouté.

    Args:
        severity: sévérité, 0 à 3.
        exposure: exposition, 0 à 4.
        controllability: contrôlabilité, 0 à 3.

    Returns:
        "QM", "A", "B", "C" ou "D".

    Raises:
        InvalidRating: si une cotation sort de ses bornes.
    """
    _check(severity, SEVERITY_RANGE, "La sévérité")
    _check(exposure, EXPOSURE_RANGE, "L'exposition")
    _check(controllability, CONTROLLABILITY_RANGE, "La contrôlabilité")

    # Un zéro sur n'importe quel axe sort l'événement du périmètre ASIL.
    if severity == 0 or exposure == 0 or controllability == 0:
        return "QM"

    return _LEVEL_TO_ASIL.get(severity + exposure + controllability, "QM")


def rate(severity: int, exposure: int, controllability: int) -> AsilResult:
    """Comme determine_asil(), mais rend aussi les décompositions possibles."""
    asil = determine_asil(severity, exposure, controllability)
    return AsilResult(
        asil=asil,
        severity=severity,
        exposure=exposure,
        controllability=controllability,
        decompositions=list(DECOMPOSITIONS[asil]),
    )


def full_matrix() -> dict:
    """Table complète S/E/C → ASIL, plus les libellés et décompositions.

    Sert de **source de vérité unique** : la page web la charge une fois et
    fait ses lookups localement, ce qui rend la cotation instantanée sans
    dupliquer cette logique en JavaScript.

    Les clés de `table` sont de la forme "S{s}E{e}C{c}".
    """
    table = {}
    for s in range(SEVERITY_RANGE[1] + 1):
        for e in range(EXPOSURE_RANGE[1] + 1):
            for c in range(CONTROLLABILITY_RANGE[1] + 1):
                table[f"S{s}E{e}C{c}"] = determine_asil(s, e, c)

    return {
        "table": table,
        "order": ASIL_ORDER,
        "decompositions": {
            asil: [list(pair) for pair in pairs]
            for asil, pairs in DECOMPOSITIONS.items()
        },
        "labels": {
            "severity": SEVERITY_LABELS,
            "exposure": EXPOSURE_LABELS,
            "controllability": CONTROLLABILITY_LABELS,
        },
    }
