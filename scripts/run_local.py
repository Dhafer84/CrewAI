"""Point d'entrée CLI local — Option A.

Enveloppe mince autour de qualitycrew.core.run_audit().
Ne contient aucune logique métier : lit un dossier de documents,
appelle le moteur, écrit le rapport sur disque.

À implémenter en Phase 3, une fois le moteur (Phase 2) fonctionnel.
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from qualitycrew.config import require_llm_key  # noqa: E402
from qualitycrew.core import run_audit  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = PROJECT_ROOT / "data" / "sample_project"
REPORTS_DIR = PROJECT_ROOT / "reports"


def main() -> None:
    require_llm_key()

    REPORTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = REPORTS_DIR / f"audit_report_{timestamp}.md"

    report = run_audit(DOCUMENTS_DIR)
    output_path.write_text(report, encoding="utf-8")

    print(f"Rapport généré : {output_path}")


if __name__ == "__main__":
    main()
