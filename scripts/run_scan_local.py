"""Point d'entrée CLI local pour SentinelScan.

Enveloppe mince autour de sentinelscan.scanner.run_scan().
Ne contient aucune logique métier.

Usage :
    python scripts/run_scan_local.py acme-corp "projet-x"
    python scripts/run_scan_local.py --dry-run acme-corp
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sentinelscan.config import require_github_token  # noqa: E402
from sentinelscan.queries import build_queries, normalize_keywords  # noqa: E402
from sentinelscan.report import build_excel, build_markdown  # noqa: E402
from sentinelscan.scanner import run_scan  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"


def _on_progress(event: dict) -> None:
    if event["type"] == "query_start":
        position = f"[{event['index'] + 1}/{event['total']}]"
        print(f"{position} {event['keyword']} — {event['detection']}…", flush=True)
    elif event["type"] == "query_done":
        print(f"      → {event['found']} nouvelle(s) détection(s)", flush=True)
    elif event["type"] == "query_error":
        print(f"      ! {event['message']}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan de veille SentinelScan.")
    parser.add_argument("keywords", nargs="+", help="Termes à rechercher (3 max).")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Affiche les requêtes sans les exécuter ni consommer de quota.",
    )
    args = parser.parse_args()

    keywords = normalize_keywords(args.keywords)

    if args.dry_run:
        print(f"Mots-clés retenus : {', '.join(keywords)}\n")
        for query in build_queries(keywords):
            print(f"  [{query.criticality:<8}] {query.kind:<4}  {query.expression}")
        print("\n(dry-run — aucune requête envoyée)")
        return

    require_github_token()

    print(f"Mots-clés retenus : {', '.join(keywords)}\n")
    result = run_scan(keywords, progress_callback=_on_progress)

    REPORTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    markdown_path = REPORTS_DIR / f"scan_report_{timestamp}.md"
    markdown_path.write_text(build_markdown(result), encoding="utf-8")

    excel_path = REPORTS_DIR / f"scan_report_{timestamp}.xlsx"
    excel_path.write_bytes(build_excel(result))

    counts = result.count_by_criticality()
    print(
        f"\n{len(result.findings)} détection(s) en {result.duration_seconds:.0f} s "
        f"— CRITIQUE : {counts['CRITIQUE']}, MAJEUR : {counts['MAJEUR']}, "
        f"MINEUR : {counts['MINEUR']}, INFO : {counts['INFO']}"
    )
    print(f"Rapport markdown : {markdown_path}")
    print(f"Rapport Excel    : {excel_path}")


if __name__ == "__main__":
    main()
