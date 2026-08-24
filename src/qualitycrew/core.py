"""Interface stable du moteur QualityCrew.

Ce module est le SEUL point d'entrée que les couches de présentation
(CLI local aujourd'hui, API FastAPI plus tard) doivent appeler.
"""

from i18n import DEFAULT_LANG

from pathlib import Path

from .config import require_llm_key
from .crew import build_crew

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_CHECKLIST = _PROJECT_ROOT / "checklists" / "aspice_iso_checklist.md"


def run_audit(
    documents_dir: Path,
    checklist_path: Path | None = None,
    task_callback=None,
    lang: str = DEFAULT_LANG,
) -> str:
    """Lance l'audit complet sur un dossier de documents projet.

    Args:
        documents_dir: dossier contenant srs.md, test_plan.md, review_report.md.
        checklist_path: checklist à utiliser. Défaut : checklists/aspice_iso_checklist.md.

    Returns:
        Rapport d'audit en markdown.
    """
    require_llm_key()

    checklist_path = checklist_path or _DEFAULT_CHECKLIST

    docs = {
        "srs": (documents_dir / "srs.md").read_text(encoding="utf-8"),
        "test_plan": (documents_dir / "test_plan.md").read_text(encoding="utf-8"),
        "review_report": (documents_dir / "review_report.md").read_text(encoding="utf-8"),
        "checklist": checklist_path.read_text(encoding="utf-8"),
    }

    crew = build_crew(docs, task_callback=task_callback, lang=lang)
    result = crew.kickoff()
    return result.raw
