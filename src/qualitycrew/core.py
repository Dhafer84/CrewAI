"""Interface stable du moteur QualityCrew.

Ce module est le SEUL point d'entrée que les couches de présentation
(CLI local aujourd'hui, API FastAPI plus tard) doivent appeler.

Ni cette fonction ni rien dans src/qualitycrew/ ne doit connaître
l'existence d'un CLI, d'un serveur web ou d'une route HTTP.
Ce découplage est ce qui permet de passer de l'Option A (site statique)
à l'Option B (démo live) sans réécrire le moteur.

À implémenter en Phase 2, après agents.py / tasks.py / crew.py.
"""

from pathlib import Path


def run_audit(documents_dir: Path) -> str:
    """Lance l'audit complet sur un dossier de documents projet.

    Args:
        documents_dir: chemin vers un dossier contenant les documents
            fictifs (srs.md, test_plan.md, review_report.md).

    Returns:
        Le rapport final en markdown, tel que produit par l'agent
        "Rédacteur de synthèse".
    """
    raise NotImplementedError("À implémenter en Phase 2.")
