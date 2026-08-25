"""Jeux d'essai déterministes pour les cinq exports Excel.

Partagés par `test_i18n.py` (instantané de non-régression, puis comparaison
FR/EN) et disponibles pour toute suite qui aurait besoin d'un classeur
reproductible. Les valeurs sont figées : aucune date « maintenant », aucun
identifiant aléatoire, sinon l'instantané changerait à chaque exécution.
"""

import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

_QUAND = datetime(2026, 8, 24, 9, 30, tzinfo=timezone.utc)


@dataclass
class _Evenement:
    malfunction: str
    situation: str
    severity: int
    exposure: int
    controllability: int


@dataclass
class _Menace:
    description: str = "Usurpation du calculateur de freinage"
    path: str = "Injection de trames forgées sur le bus"
    time: int = 1
    expertise: int = 2
    knowledge: int = 1
    window: int = 1
    equipment: int = 1
    decision: str = "reduce"
    goal: str = "Authentifier les trames de freinage"
    rationale: str = ""


@dataclass
class _Dommage:
    asset: str = "Passerelle télématique"
    description: str = "Freinage commandé à distance"
    safety: int = 3
    financial: int = 2
    operational: int = 2
    privacy: int = 1
    threats: list = None
    origin: str = "Événement redouté 1"
    origin_severity: int = 3
    origin_asil: str = "D"

    def __post_init__(self):
        if self.threats is None:
            self.threats = [_Menace()]


def _figer(analyse):
    """Fige l'horodatage d'une analyse.

    ⚠️ `created_at` vaut `datetime.now()` par défaut, et la Synthèse
    l'imprime à la minute près : sans ce gel, l'instantané de
    non-régression se mettrait à échouer tout seul au prochain changement
    de minute. Même raison que la couture `today` de `run_watch`.
    """
    try:
        analyse.created_at = _QUAND
    except (AttributeError, TypeError):
        object.__setattr__(analyse, "created_at", _QUAND)
    return analyse


def hara_analysis():
    from safetyscope.analysis import build_analysis
    return _figer(build_analysis("Freinage électrique", [
        _Evenement("Absence de freinage", "Descente, trafic dense", 3, 4, 3),
        _Evenement("Freinage intempestif", "Autoroute, vitesse stabilisée", 2, 3, 2),
    ]))


def tara_analysis():
    from threatscope.analysis import build_analysis as build_tara
    return _figer(build_tara("Passerelle télématique", [_Dommage()]))


def scan_result():
    from sentinelscan.scanner import Finding, ScanResult
    return ScanResult(
        keywords=["acme-corp"],
        started_at=_QUAND,
        finished_at=_QUAND + timedelta(seconds=90),
        findings=[Finding("CRITIQUE", "Fichier .env exposé", "acme/site",
                          "acme", "config/.env", "https://github.test/a", "acme-corp")],
        errors=["Dépôt — quota atteint"],
        incomplete_queries=["Fichier de configuration"],
        queries_run=5, queries_total=5,
    )


def watch_result():
    from regwatch.core import WatchItem, WatchResult
    return WatchResult(
        norms=["iso9001"], lookback_days=90,
        started_at=_QUAND, finished_at=_QUAND + timedelta(seconds=7),
        # ⚠️ Le signal est un IDENTIFIANT depuis le 25/08/2026, plus un libellé
        # français : le libellé se rend à l'affichage via `signal_label()`.
        items=[WatchItem("iso9001", "ISO 9001", "publication",
                         "ISO 9001 revision update", date(2026, 8, 7),
                         "iso_tc176sc2", "ISO/TC 176/SC 2", "officiel",
                         "https://committee.iso.test/x.html", "Parce que.")],
        unreachable=["iso_tc176"],
        undated=[("vda_spice", "Guidelines 2nd Edition 2025")],
        errors=["ISO/TC 176 — injoignable"],
        sources_read=2, sources_total=2,
    )


def workbooks(lang: str = "fr") -> dict[str, bytes]:
    """Les quatre classeurs, construits dans la langue demandée."""
    from causetrace.report import build_excel as causetrace_excel
    from regwatch.report import build_excel as regwatch_excel
    from safetyscope.report import build_excel as hara_excel
    from sentinelscan.report import build_excel as scan_excel
    from threatscope.report import build_excel as tara_excel

    def appeler(fonction, donnees):
        try:
            return fonction(donnees, lang)
        except TypeError:
            # Tant que l'export n'est pas extrait, il ne prend pas la langue.
            return fonction(donnees)

    return {
        "hara": appeler(hara_excel, hara_analysis()),
        "tara": appeler(tara_excel, tara_analysis()),
        "sentinelscan": appeler(scan_excel, scan_result()),
        "regwatch": appeler(regwatch_excel, watch_result()),
        "causetrace": causetrace_excel(causetrace_dossier(), lang, _QUAND),
    }


def causetrace_dossier():
    """Un 8D figé — délibérément incomplet, comme un vrai brouillon.

    ⚠️ Aucune date « maintenant » : `build_excel` reçoit `_QUAND`. Le piège
    s'est déjà refermé sur l'export HARA, dont la Synthèse imprimait
    `datetime.now()` à la minute près — l'instantané aurait échoué tout seul
    au changement de minute suivant.
    """
    from causetrace.model import build_dossier

    return build_dossier({
        "reference": "8D-2026-014",
        "title": "Perte intermittente du signal de vitesse roue",
        "d1": {"owner": "A. Mercier", "members": ["Atelier montage"]},
        "d2": {"what": "Le capteur avant gauche perd son signal",
               "where": "Fin de ligne", "since": "2026-05-12",
               "how_many": "7 pièces sur 1 240", "is_not": "Roue avant droite indemne"},
        "d3": {"action": "Tri à 100 % des lots en stock", "due_date": "2026-06-30"},
        "d4": {"occurrence": "Serrage du connecteur hors tolérance",
               "escape": "",
               "occurrence_chain": [
                   {"statement": "Le connecteur perd le contact", "nature": "technical"},
                   {"statement": "Le couple appliqué est sous la spécification",
                    "nature": "technical"},
                   {"statement": "La visseuse n'est pas asservie au couple",
                    "nature": "process"},
               ]},
        "d7": {"lessons": "Sensibilisation de l'équipe"},
        "d8": {"claimed_closed": True, "closed_on": "2026-06-20"},
    })


def cell_values(data: bytes) -> dict[str, list[str]]:
    """Toutes les chaînes d'un classeur, onglet par onglet."""
    from io import BytesIO

    import openpyxl

    classeur = openpyxl.load_workbook(BytesIO(data))
    return {
        onglet.title: [
            str(cellule.value)
            for ligne in onglet.iter_rows() for cellule in ligne
            if isinstance(cellule.value, str) and cellule.value.strip()
        ]
        for onglet in classeur.worksheets
    }
