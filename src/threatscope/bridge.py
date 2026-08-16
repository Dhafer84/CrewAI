"""Pont HARA → TARA : ce qui passe d'une analyse de sûreté à une analyse de sécurité.

Logique pure, sans dépendance — y compris envers `safetyscope`. Les deux
moteurs restent indépendants ; seule la **règle de transfert** vit ici.

⚠️ La règle centrale, et la raison d'être de ce module :

    La sévérité traverse le pont. L'exposition et la contrôlabilité, non.

Un événement redouté n'est pas un scénario de dommage. Reprendre une ligne de
HARA telle quelle serait faux :

- **Sévérité** — la gravité physique des conséquences ne dépend pas de leur
  cause. Un freinage perdu à 90 km/h blesse autant, que l'origine soit une
  panne ou une attaque. Elle se transfère.
- **Exposition** — elle mesure la probabilité de se trouver dans la situation
  dangereuse. Un attaquant *choisit son moment* : il frappe précisément quand
  ça fait mal. La notion s'effondre, elle ne se transfère pas.
- **Contrôlabilité** — elle suppose un conducteur en mesure de réagir. Un
  attaquant peut neutraliser délibérément ce recours, voire l'attaquer en
  premier. Elle ne se transfère pas non plus.

Côté sécurité, ces deux axes sont remplacés par la faisabilité de l'attaque,
qui joue le rôle inverse : elle décrit ce que l'attaque coûte, pas ce que la
situation impose.

Le transfert est une **proposition**, jamais un report automatique : c'est
l'ingénieur qui confirme.
"""

from dataclasses import dataclass, fields

# S0 à S3 côté HARA, quatre niveaux d'impact côté TARA. Les deux échelles ont
# quatre crans et décrivent la même chose — la gravité des conséquences —, la
# correspondance est donc directe.
SEVERITY_LEVELS = 4

_WHY = {
    "severity": (
        "La gravité physique des conséquences ne dépend pas de leur cause. "
        "Un freinage perdu blesse autant, que l'origine soit une panne ou une attaque."
    ),
    "exposure": (
        "L'exposition mesure la probabilité de se trouver dans la situation dangereuse. "
        "Un attaquant choisit son moment : il frappe quand ça fait mal. La notion s'effondre."
    ),
    "controllability": (
        "La contrôlabilité suppose un conducteur en mesure de réagir. Un attaquant peut "
        "neutraliser ce recours, voire l'attaquer en premier."
    ),
    "replacement": (
        "Côté sécurité, l'exposition et la contrôlabilité sont remplacées par la "
        "faisabilité de l'attaque, qui décrit ce que l'attaque coûte."
    ),
}


class InvalidTransfer(ValueError):
    """Cotation de sévérité hors des bornes admises."""


@dataclass(frozen=True)
class DamageProposal:
    """Scénario de dommage proposé à partir d'un événement redouté.

    ⚠️ Cette classe n'a **volontairement aucun champ** pour l'exposition ni la
    contrôlabilité. Ce n'est pas un oubli : ce qui n'a pas de champ ne peut pas
    traverser le pont par mégarde. Même discipline que `sentinelscan.Hit`, qui
    n'a aucun champ de contenu.

    `severity` et `asil` ne sont conservés que pour la **traçabilité** — dire
    d'où vient la proposition —, jamais pour alimenter une cotation TARA.
    """

    malfunction: str
    situation: str
    severity: int
    safety_impact: int
    asil: str
    origin: str

    @property
    def text(self) -> str:
        """Amorce de description du dommage, à retravailler par l'ingénieur."""
        parts = [part.strip() for part in (self.malfunction, self.situation) if part.strip()]
        return " — ".join(parts)


def severity_to_impact(severity: int) -> int:
    """Traduit une sévérité HARA en impact « sécurité des personnes » TARA.

    Args:
        severity: sévérité HARA, 0 à 3.

    Returns:
        Le niveau d'impact correspondant, 0 à 3.

    Raises:
        InvalidTransfer: si la sévérité sort de ses bornes.
    """
    if not isinstance(severity, int) or isinstance(severity, bool):
        raise InvalidTransfer(f"La sévérité doit être un entier, reçu {severity!r}.")
    if not 0 <= severity < SEVERITY_LEVELS:
        raise InvalidTransfer(
            f"La sévérité doit être comprise entre 0 et {SEVERITY_LEVELS - 1}, reçu {severity}."
        )
    return severity


def propose_damage(
    malfunction: str,
    situation: str,
    severity: int,
    asil: str = "",
    origin: str = "",
) -> DamageProposal:
    """Construit une proposition de scénario de dommage.

    Ne cote que l'impact « sécurité des personnes ». Les trois autres
    catégories — financier, opérationnel, vie privée — n'ont pas d'équivalent
    en HARA et restent à la main de l'ingénieur.
    """
    return DamageProposal(
        malfunction=malfunction,
        situation=situation,
        severity=severity,
        safety_impact=severity_to_impact(severity),
        asil=asil,
        origin=origin,
    )


def bridge_rule() -> dict:
    """Règle de transfert, prête à sérialiser pour l'interface.

    Sert de **source de vérité unique** : la page n'écrit nulle part que S se
    transfère et que E et C ne se transfèrent pas, elle lit cette règle et
    l'affiche. Même contrat que la matrice ASIL et le barème de faisabilité.
    """
    return {
        "severityToImpact": [severity_to_impact(s) for s in range(SEVERITY_LEVELS)],
        "transfers": ["severity"],
        "doesNotTransfer": ["exposure", "controllability"],
        # Les champs que le pont accepte de transporter. Ce qui n'y figure pas
        # n'a pas de place dans une proposition — voir DamageProposal.
        "carriedFields": [field.name for field in fields(DamageProposal)],
        "why": _WHY,
    }
