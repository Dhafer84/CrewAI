"""Point d'entrée CLI local pour RegWatch.

Enveloppe mince autour de regwatch.core.run_watch(). Aucune logique métier.

Usage :
    python scripts/run_watch_local.py aspice iso9001
    python scripts/run_watch_local.py --all
    python scripts/run_watch_local.py --dry-run --all
    python scripts/run_watch_local.py --check-sources

⚠️ `--check-sources` est **l'outil de maintenance de la veille**. Une fixture
prouve qu'un parseur lit un balisage donné ; elle ne prouve pas que la source
a encore cette forme. Ce mode-là va voir en vrai, et c'est le seul endroit du
projet qui le fasse — jamais un test.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from regwatch import fetch  # noqa: E402
from regwatch.classify import SIGNAL_ORDER  # noqa: E402
from regwatch.config import LOOKBACK_DAYS  # noqa: E402
from regwatch.core import _read, run_watch  # noqa: E402
from regwatch.norms import NORM_ORDER, NORMS, parse_selection  # noqa: E402
from regwatch.sources import SOURCES, sources_for  # noqa: E402


def _on_progress(event: dict) -> None:
    position = f"[{event['index'] + 1}/{event['total']}]"
    if event["type"] == "source_start":
        print(f"{position} {event['source']} ({event['tier']})…", flush=True)
    elif event["type"] == "source_done":
        etat = " ⚠ DÉGRADÉE" if event["state"] == "degraded" else ""
        print(f"      → {event['found']} signal(aux) retenu(s){etat}", flush=True)
    elif event["type"] == "source_error":
        print(f"      ! {event['message']}", flush=True)


def _check_sources() -> int:
    """Interroge chaque source et dit ce qu'on en tire réellement."""
    print(f"Vérification des {len(SOURCES)} sources du catalogue.\n")
    fetch.clear_cache()
    en_panne = 0

    for source in SOURCES:
        print(f"  {source.label}")
        print(f"    {source.url}")
        try:
            body = fetch.get_text(source.url)
        except fetch.FetchError as exc:
            print(f"    ✗ INJOIGNABLE — {exc}\n")
            en_panne += 1
            continue

        try:
            items = _read(source, body)
        except Exception as exc:  # noqa: BLE001
            print(f"    ✗ PARSEUR EN ÉCHEC — {type(exc).__name__}: {exc}\n")
            en_panne += 1
            continue

        dates = [item.published for item in items if item.published]
        recent = max(dates).isoformat() if dates else "—"
        marque = "✓" if items else "✗ AUCUN ITEM"
        print(f"    {marque} {len(items)} item(s), {len(body) // 1024} Ko, "
              f"plus récent : {recent}")
        for item in items[:2]:
            print(f"        · {item.published} {item.title[:66]}")
        print()
        if not items:
            en_panne += 1

    if en_panne:
        print(f"⚠ {en_panne} source(s) à revoir sur {len(SOURCES)}.")
    else:
        print(f"Les {len(SOURCES)} sources répondent et livrent des items.")
    return 1 if en_panne else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Veille normative RegWatch.")
    parser.add_argument("norms", nargs="*", help=f"Clés parmi : {', '.join(NORM_ORDER)}")
    parser.add_argument("--all", action="store_true", help="Surveiller les 5 normes.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Affiche les sources qui seraient lues, sans réseau.")
    parser.add_argument("--check-sources", action="store_true",
                        help="Interroge chaque source du catalogue et rend son état.")
    args = parser.parse_args()

    if args.check_sources:
        return _check_sources()

    keys = list(NORM_ORDER) if args.all else args.norms
    if not keys:
        parser.error("Indiquer au moins une norme, ou --all.")

    normes = parse_selection(keys)
    sources = sources_for(normes)

    print(f"Normes surveillées : {', '.join(n.label for n in normes)}")
    print(f"Fenêtre : {LOOKBACK_DAYS} jours\n")

    if args.dry_run:
        for source in sources:
            print(f"  [{source.tier:<11}] {source.kind:<4} {source.label}")
            print(f"                      {source.url}")
        print(f"\n(dry-run — {len(sources)} source(s), aucune requête envoyée)")
        return 0

    result = run_watch(normes, progress_callback=_on_progress)

    print(f"\n{len(result.items)} signal(aux) en {result.duration_seconds:.0f} s")

    if result.coverage_is_incomplete:
        print("\n⚠ COUVERTURE INCOMPLÈTE — une absence de signal ne prouve rien :")
        for label in result.unreachable:
            print(f"    injoignable : {label}")
        for label in result.degraded:
            print(f"    dégradée    : {label}")
    if result.undated:
        print(f"\n{len(result.undated)} item(s) pertinent(s) écarté(s), faute de date :")
        for ligne in result.undated:
            print(f"    {ligne[:96]}")

    for key in result.norms:
        retenus = [item for item in result.items if item.norm_key == key]
        print(f"\n=== {NORMS[key].label} — {len(retenus)} signal(aux)")
        for signal in SIGNAL_ORDER:
            for item in [i for i in retenus if i.signal == signal]:
                print(f"  {item.published}  [{item.signal}]")
                print(f"              {item.title[:84]}")
                print(f"              {item.source_label} ({item.source_tier})")
                print(f"              {item.url[:88]}")

    for message in result.errors:
        print(f"\n  ! {message}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
