"""Tests du rapport markdown de SentinelScan face au texte de tiers.

Exécutable sans pytest :  .venv/bin/python3 -B tests/test_sentinelscan_report.py

Le drapeau `-B` n'est pas décoratif — voir l'en-tête de `tests/test_asil.py`.

⚠️ Audit de sécurité du 22/09/2026 : un fichier d'un dépôt PUBLIC nommé
  a`<img onerror=…>`.env
fermait la balise de code du rapport, et son HTML s'exécutait dans la page de
qui lançait le scan. N'importe qui choisit le nom d'un fichier public, et git
y admet presque tout. Ces tests posent de vraies charges dans chaque champ
qu'un tiers contrôle — chemin, dépôt, adresse, message d'erreur — et vérifient
qu'aucune ne ressort sous une forme qu'un navigateur exécuterait.

Ils ne s'appuient sur aucun rendu JavaScript : la seconde ligne de défense,
côté page, est tenue par `test_routes.py`.
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sentinelscan.report import build_markdown, md_link, md_text  # noqa: E402
from sentinelscan.scanner import Finding, ScanResult  # noqa: E402

# Charges écrites à la main, une par mécanisme réel.
CHEMINS = [
    "config/a`<img src=x onerror=\"alert(1)\">`.env",   # fermeture de la balise de code
    "<script>alert(1)</script>.env",                    # HTML nu
    "a|b|c|d.env",                                      # découpe du tableau
    "x](javascript:alert(1))[y.env",                    # lien forgé
    "a\n| CRITIQUE | faux | faux | faux |\n.env",        # ligne de tableau injectée
]


def _resultat(chemin: str, url: str = "https://github.com/o/r/blob/main/x",
              repo: str = "o/r", erreurs=None) -> ScanResult:
    r = ScanResult(keywords=["dhafer"], started_at=datetime(2026, 9, 22, 12, 0),
                   finished_at=datetime(2026, 9, 22, 12, 1))
    r.findings.append(Finding(criticality="CRITIQUE", detection="Fichier .env exposé",
                              repo=repo, owner="o", path=chemin, url=url, keyword="dhafer"))
    r.errors.extend(erreurs or [])
    return r


def _ligne_du_constat(md: str) -> str:
    lignes = [l for l in md.splitlines() if "Fichier .env" in l]
    assert len(lignes) == 1, f"le constat doit tenir sur UNE ligne de tableau : {lignes}"
    return lignes[0]


def test_no_raw_angle_bracket_survives():
    for chemin in CHEMINS:
        ligne = _ligne_du_constat(build_markdown(_resultat(chemin)))
        assert "<" not in ligne and ">" not in ligne, f"chevron brut pour {chemin!r} : {ligne}"


def test_a_backtick_can_no_longer_close_a_code_span():
    ligne = _ligne_du_constat(build_markdown(_resultat(CHEMINS[0])))
    brut = ligne.replace("\\`", "")
    assert "`" not in brut, f"accent grave non échappé : {ligne}"


def test_the_row_keeps_exactly_four_cells():
    """Une barre verticale ou un saut de ligne ne doit pas fabriquer de cellule."""
    for chemin in CHEMINS:
        ligne = _ligne_du_constat(build_markdown(_resultat(chemin)))
        cellules = [c for c in ligne.replace("\\|", "").split("|")][1:-1]
        assert len(cellules) == 4, f"{chemin!r} → {len(cellules)} cellules : {ligne}"


def test_only_github_links_are_links():
    for url in ("javascript:alert(1)", "data:text/html,<b>x</b>", "http://github.com/o/r",
                "https://github.com.evil.invalid/o/r", "//evil.invalid/x", ""):
        ligne = _ligne_du_constat(build_markdown(_resultat("a.env", url=url)))
        assert "](" not in ligne, f"lien produit vers {url!r} : {ligne}"
    ok = _ligne_du_constat(build_markdown(_resultat("a.env")))
    assert "](https://github.com/o/r/blob/main/x)" in ok, "un vrai lien GitHub doit rester un lien"


def test_a_parenthesis_cannot_escape_the_link():
    lien = md_link("o/r", "https://github.com/o/r/blob/main/a).env")
    cible = lien[lien.index("](") + 2:-1]
    assert ")" not in cible and "(" not in cible, f"parenthèse brute dans l'adresse : {lien}"


def test_error_messages_are_third_party_text_too():
    """Un message d'erreur recopie celui de l'API GitHub."""
    md = build_markdown(_resultat("a.env", erreurs=["<img src=x onerror=alert(1)>"]))
    assert "<img" not in md, "le message d'erreur ressort en HTML brut"


def test_the_text_still_reads_the_same():
    """Échapper n'est pas altérer : entités et barres obliques inverses se
    rendent en texte identique à l'original."""
    import html
    import re
    for valeur in ("config/app.env", "dir with space/x_y*z.env", "a\\b"):
        rendu = html.unescape(re.sub(r"\\(.)", r"\1", md_text(valeur)))
        assert rendu == valeur, f"{valeur!r} relu comme {rendu!r}"


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"  ok    {test.__name__}")
        except AssertionError as exc:
            failures += 1
            print(f"  ÉCHEC {test.__name__} : {exc}")
        except Exception as exc:  # une régression d'échappement lève souvent
            failures += 1
            print(f"  ÉCHEC {test.__name__} : {type(exc).__name__} : {exc}")
    print(f"\n{len(tests) - failures}/{len(tests)} tests passés")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
