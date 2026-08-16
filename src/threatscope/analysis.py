"""Objets métier du dossier TARA.

Le tableau saisi dans l'interface est reconstruit ici avant tout export : on
ne fait jamais confiance aux données reçues du navigateur. Les cotations sont
revalidées, et la complétude des traitements est **recalculée** côté serveur —
l'indicateur « complet / à compléter » de la page est une commodité
d'affichage, pas une source de vérité.

Une analyse incomplète n'est pas refusée pour autant : on exporte un travail
en cours en **disant ce qui manque**. Un classeur qui tait ses trous est pire
qu'un classeur qui les liste.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .rating import (
    FEASIBILITY_ORDER,
    IMPACT_CATEGORIES,
    IMPACT_ORDER,
    InvalidRating,
    PARAMETERS,
    attack_potential,
    determine_risk,
    feasibility_from_potential,
    overall_impact,
)
from .treatment import TREATMENTS, check

MAX_DAMAGES = 6
MAX_THREATS_PER_DAMAGE = 4
MAX_ITEM_LENGTH = 120
MAX_TEXT_LENGTH = 300


class InvalidAnalysis(ValueError):
    """Dossier inexploitable — message destiné à l'utilisateur final."""


def analysis_limits() -> dict:
    """Plafonds de la démonstration, servis à l'interface.

    La page ne les réécrit pas : ils vivent ici, comme le barème vit dans
    `rating`. Un plafond décidé à deux endroits finit par diverger.
    """
    return {"damages": MAX_DAMAGES, "threatsPerDamage": MAX_THREATS_PER_DAMAGE}


@dataclass(frozen=True)
class ThreatScenario:
    """Un scénario de menace et son chemin d'attaque, coté en faisabilité."""

    description: str
    path: str
    time: int
    expertise: int
    knowledge: int
    window: int
    equipment: int
    decision: str = ""
    goal: str = ""
    rationale: str = ""

    @property
    def potential(self) -> int:
        return attack_potential(
            self.time, self.expertise, self.knowledge, self.window, self.equipment
        )

    @property
    def feasibility(self) -> int:
        return feasibility_from_potential(self.potential)

    @property
    def feasibility_label(self) -> str:
        return FEASIBILITY_ORDER[self.feasibility]

    @property
    def decision_label(self) -> str:
        return TREATMENTS[self.decision]["label"] if self.decision else ""

    @property
    def written(self) -> str:
        """L'écrit que la décision imposait : objectif ou justification."""
        if not self.decision:
            return ""
        return self.goal if TREATMENTS[self.decision]["requires"] == "goal" else self.rationale


@dataclass(frozen=True)
class DamageScenario:
    """Un scénario de dommage, coté en impact, et les menaces qui le réalisent.

    `origin` porte la traçabilité vers la HARA quand le scénario en est issu.
    ⚠️ Ni l'exposition ni la contrôlabilité n'y figurent : elles ne traversent
    pas le pont (voir `threatscope.bridge`).
    """

    asset: str
    description: str
    safety: int
    financial: int
    operational: int
    privacy: int
    threats: list[ThreatScenario] = field(default_factory=list)
    origin: str = ""
    origin_severity: int = -1
    origin_asil: str = ""

    @property
    def impact(self) -> int:
        return overall_impact(self.safety, self.financial, self.operational, self.privacy)

    @property
    def impact_label(self) -> str:
        return IMPACT_ORDER[self.impact]

    def category_labels(self) -> dict[str, str]:
        return {
            IMPACT_CATEGORIES["safety"]: IMPACT_ORDER[self.safety],
            IMPACT_CATEGORIES["financial"]: IMPACT_ORDER[self.financial],
            IMPACT_CATEGORIES["operational"]: IMPACT_ORDER[self.operational],
            IMPACT_CATEGORIES["privacy"]: IMPACT_ORDER[self.privacy],
        }

    @property
    def traceability(self) -> str:
        """D'où vient ce scénario : reprise de la HARA, ou saisie directe."""
        if not self.origin:
            return "Saisi directement"
        detail = f" (S{self.origin_severity}" if self.origin_severity >= 0 else ""
        if detail and self.origin_asil:
            detail += f", ASIL {self.origin_asil}"
        if detail:
            detail += ")"
        return f"HARA — {self.origin}{detail}"


@dataclass(frozen=True)
class TaraRow:
    """Une ligne du tableau : un chemin d'attaque et tout son contexte résolu."""

    ref: str
    damage: DamageScenario
    threat: ThreatScenario
    risk: int
    problems: list[str]

    @property
    def complete(self) -> bool:
        return not self.problems


@dataclass
class TaraAnalysis:
    item: str
    damages: list[DamageScenario] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def rows(self) -> list[TaraRow]:
        """Aplatit le dossier en lignes de tableau, complétude recalculée."""
        rows: list[TaraRow] = []
        for d_index, damage in enumerate(self.damages, start=1):
            for t_index, threat in enumerate(damage.threats, start=1):
                risk = determine_risk(damage.impact, threat.feasibility)
                rows.append(TaraRow(
                    ref=f"{d_index}.{t_index}",
                    damage=damage,
                    threat=threat,
                    risk=risk,
                    problems=check(risk, threat.decision, threat.goal, threat.rationale),
                ))
        return rows

    @property
    def max_risk(self) -> int:
        rows = self.rows()
        return max((row.risk for row in rows), default=0)

    def count_by_risk(self) -> dict[int, int]:
        counts = {value: 0 for value in range(1, 6)}
        for row in self.rows():
            counts[row.risk] += 1
        return counts

    def goals(self) -> list[TaraRow]:
        """Les lignes qui ont produit une exigence de cybersécurité."""
        return [
            row for row in self.rows()
            if row.threat.decision
            and TREATMENTS[row.threat.decision]["requires"] == "goal"
            and row.threat.goal.strip()
        ]

    def gaps(self) -> list[tuple[str, str]]:
        """Ce qui manque, situé : (référence de la menace, constat)."""
        return [
            (row.ref, problem)
            for row in self.rows()
            for problem in row.problems
        ]

    @property
    def from_hara(self) -> int:
        return sum(1 for damage in self.damages if damage.origin)


def _clean_text(value, limit: int, label: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise InvalidAnalysis(f"{label} doit être du texte.")
    return value.strip()[:limit]


def _decision(value, label: str) -> str:
    value = _clean_text(value, 32, label)
    if value and value not in TREATMENTS:
        raise InvalidAnalysis(f"{label} : décision de traitement inconnue.")
    return value


def build_analysis(item, raw_damages) -> TaraAnalysis:
    """Reconstruit un dossier TARA à partir de données brutes, en le validant.

    Args:
        item: intitulé de l'item étudié.
        raw_damages: séquence d'objets exposant les champs d'un scénario de
            dommage, dont `threats`.

    Raises:
        InvalidAnalysis: dossier vide, plafonds dépassés, cotation hors bornes
            ou décision de traitement inconnue.
    """
    if raw_damages is None:
        raise InvalidAnalysis("Aucun scénario de dommage fourni.")

    raw_damages = list(raw_damages)
    if not raw_damages:
        raise InvalidAnalysis("Aucun scénario de dommage coté — il n'y a rien à exporter.")
    if len(raw_damages) > MAX_DAMAGES:
        raise InvalidAnalysis(
            f"{MAX_DAMAGES} scénarios de dommage au maximum pour cette démonstration."
        )

    damages: list[DamageScenario] = []
    for d_index, raw in enumerate(raw_damages, start=1):
        raw_threats = list(getattr(raw, "threats", None) or [])
        if not raw_threats:
            raise InvalidAnalysis(
                f"Scénario de dommage {d_index} — aucun chemin d'attaque coté."
            )
        if len(raw_threats) > MAX_THREATS_PER_DAMAGE:
            raise InvalidAnalysis(
                f"Scénario de dommage {d_index} — "
                f"{MAX_THREATS_PER_DAMAGE} menaces au maximum."
            )

        threats: list[ThreatScenario] = []
        for t_index, raw_threat in enumerate(raw_threats, start=1):
            situe = f"Menace {d_index}.{t_index}"
            try:
                threat = ThreatScenario(
                    description=_clean_text(
                        getattr(raw_threat, "description", None), MAX_TEXT_LENGTH,
                        f"{situe} — l'intitulé"),
                    path=_clean_text(
                        getattr(raw_threat, "path", None), MAX_TEXT_LENGTH,
                        f"{situe} — le chemin d'attaque"),
                    time=getattr(raw_threat, "time"),
                    expertise=getattr(raw_threat, "expertise"),
                    knowledge=getattr(raw_threat, "knowledge"),
                    window=getattr(raw_threat, "window"),
                    equipment=getattr(raw_threat, "equipment"),
                    decision=_decision(getattr(raw_threat, "decision", ""), situe),
                    goal=_clean_text(getattr(raw_threat, "goal", None),
                                     MAX_TEXT_LENGTH, f"{situe} — l'objectif"),
                    rationale=_clean_text(getattr(raw_threat, "rationale", None),
                                          MAX_TEXT_LENGTH, f"{situe} — la justification"),
                )
                # Force l'évaluation : une cotation hors bornes doit échouer
                # ici, pas au moment d'écrire le classeur.
                _ = threat.feasibility
            except InvalidRating as exc:
                raise InvalidAnalysis(f"{situe} — {exc}") from exc
            except AttributeError as exc:
                raise InvalidAnalysis(f"{situe} incomplète.") from exc
            threats.append(threat)

        situe = f"Scénario de dommage {d_index}"
        try:
            damage = DamageScenario(
                asset=_clean_text(getattr(raw, "asset", None), MAX_TEXT_LENGTH,
                                  f"{situe} — l'actif"),
                description=_clean_text(getattr(raw, "description", None),
                                        MAX_TEXT_LENGTH, f"{situe} — la description"),
                safety=getattr(raw, "safety"),
                financial=getattr(raw, "financial"),
                operational=getattr(raw, "operational"),
                privacy=getattr(raw, "privacy"),
                threats=threats,
                origin=_clean_text(getattr(raw, "origin", None), 120,
                                   f"{situe} — l'origine"),
                origin_severity=getattr(raw, "origin_severity", -1),
                origin_asil=_clean_text(getattr(raw, "origin_asil", None), 8,
                                        f"{situe} — l'ASIL d'origine"),
            )
            _ = damage.impact
        except InvalidRating as exc:
            raise InvalidAnalysis(f"{situe} — {exc}") from exc
        except AttributeError as exc:
            raise InvalidAnalysis(f"{situe} incomplet.") from exc

        damages.append(damage)

    return TaraAnalysis(
        item=_clean_text(item, MAX_ITEM_LENGTH, "L'item") or "Item non nommé",
        damages=damages,
    )


# Réexporté pour que `report` n'ait pas à connaître `rating`.
PARAMETER_LABELS = {key: label for key, (label, _levels) in PARAMETERS.items()}
