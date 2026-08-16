"""Objets métier de l'analyse HARA.

Le tableau saisi dans l'interface est reconstruit ici avant tout export : on
ne fait jamais confiance aux données reçues du navigateur.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .asil import ASIL_ORDER, DECOMPOSITIONS, InvalidRating, determine_asil

MAX_EVENTS = 10
MAX_ITEM_LENGTH = 120
MAX_TEXT_LENGTH = 300


class InvalidAnalysis(ValueError):
    """Analyse inexploitable — message destiné à l'utilisateur final."""


@dataclass(frozen=True)
class HazardousEvent:
    """Un événement redouté coté."""

    malfunction: str
    situation: str
    severity: int
    exposure: int
    controllability: int

    @property
    def asil(self) -> str:
        return determine_asil(self.severity, self.exposure, self.controllability)

    @property
    def rating(self) -> str:
        return f"S{self.severity} E{self.exposure} C{self.controllability}"


@dataclass
class HaraAnalysis:
    item: str
    events: list[HazardousEvent] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def max_asil(self) -> str:
        """ASIL le plus contraignant de l'analyse. QM si rien n'est coté."""
        if not self.events:
            return "QM"
        return max(
            (event.asil for event in self.events),
            key=ASIL_ORDER.index,
        )

    def count_by_asil(self) -> dict[str, int]:
        counts = {level: 0 for level in ASIL_ORDER}
        for event in self.events:
            counts[event.asil] += 1
        return counts

    @property
    def decompositions(self) -> list[tuple[str, str]]:
        return list(DECOMPOSITIONS[self.max_asil])


def _clean_text(value, limit: int, label: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise InvalidAnalysis(f"{label} doit être du texte.")
    return value.strip()[:limit]


def build_analysis(item, raw_events) -> HaraAnalysis:
    """Reconstruit une analyse à partir de données brutes, en la validant.

    Args:
        item: intitulé de l'item étudié.
        raw_events: séquence d'objets exposant malfunction, situation,
            severity, exposure et controllability.

    Raises:
        InvalidAnalysis: si l'analyse est vide, trop longue, ou si une
            cotation sort de ses bornes.
    """
    if raw_events is None:
        raise InvalidAnalysis("Aucun événement redouté fourni.")

    raw_events = list(raw_events)
    if not raw_events:
        raise InvalidAnalysis(
            "Aucun événement redouté coté — il n'y a rien à exporter."
        )
    if len(raw_events) > MAX_EVENTS:
        raise InvalidAnalysis(
            f"{MAX_EVENTS} événements au maximum pour cette démonstration."
        )

    events: list[HazardousEvent] = []
    for index, raw in enumerate(raw_events, start=1):
        try:
            event = HazardousEvent(
                malfunction=_clean_text(
                    getattr(raw, "malfunction", None), MAX_TEXT_LENGTH,
                    f"Le dysfonctionnement de l'événement {index}",
                ),
                situation=_clean_text(
                    getattr(raw, "situation", None), MAX_TEXT_LENGTH,
                    f"La situation de l'événement {index}",
                ),
                severity=getattr(raw, "severity"),
                exposure=getattr(raw, "exposure"),
                controllability=getattr(raw, "controllability"),
            )
            # Force l'évaluation : une cotation hors bornes doit échouer ici,
            # pas au moment de l'écriture du classeur.
            _ = event.asil
        except InvalidRating as exc:
            raise InvalidAnalysis(f"Événement {index} — {exc}") from exc
        except AttributeError as exc:
            raise InvalidAnalysis(f"Événement {index} incomplet.") from exc

        events.append(event)

    return HaraAnalysis(
        item=_clean_text(item, MAX_ITEM_LENGTH, "L'item") or "Item non nommé",
        events=events,
    )
