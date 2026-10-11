"""Interface stable du moteur QualityCrew.

Ce module est le SEUL point d'entrée que les couches de présentation
(CLI local aujourd'hui, API FastAPI plus tard) doivent appeler.
"""

from i18n import DEFAULT_LANG, t

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
    docs = {
        name: (documents_dir / f"{name}.md").read_text(encoding="utf-8")
        for name in ("srs", "test_plan", "review_report")
    }
    return run_audit_docs(docs, checklist_path, task_callback, lang)


def run_audit_docs(
    docs: dict[str, str],
    checklist_path: Path | None = None,
    task_callback=None,
    lang: str = DEFAULT_LANG,
    visitor: bool = False,
) -> str:
    """Lance l'audit sur des documents déjà lus. `run_audit` y passe aussi :
    un seul chemin vers `build_crew`.

    Args:
        docs: srs, test_plan, review_report (textes).
        visitor: documents d'un VISITEUR (vérifiés par `documents.check_documents`) :
            consignes génériques, aucun affichage console, et le rapport commence
            par l'avertissement « brouillon, aucune référence » (décision D6) —
            ajouté ici, pas demandé au modèle : il ne peut pas l'oublier.

    Returns:
        Rapport d'audit en markdown.
    """
    require_llm_key()
    checklist_path = checklist_path or _DEFAULT_CHECKLIST
    docs = {**docs, "checklist": checklist_path.read_text(encoding="utf-8")}

    crew = build_crew(docs, task_callback=task_callback, lang=lang, visitor=visitor)
    report = crew.kickoff().raw
    if visitor:
        report = "> " + t("qc.docs.report_banner", lang) + "\n\n" + report
    return report
