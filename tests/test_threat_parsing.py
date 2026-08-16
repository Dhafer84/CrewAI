"""Tests du parseur de propositions de menaces.

Exécutable sans pytest :  .venv/bin/python3 -B tests/test_threat_parsing.py

Le drapeau `-B` n'est pas décoratif — voir l'en-tête de `tests/test_asil.py`.

⚠️ **Aucun appel au LLM ici.** On teste le parseur sur des sorties réalistes,
pas le modèle. Une suite de tests qui dépend d'un fournisseur externe ne se
lance plus le jour où on en a besoin — et consommerait le quota gratuit.

Le parseur doit être **tolérant** : le modèle ajoute des puces, du gras, des
phrases d'introduction. Une ligne mal formée s'ignore, elle ne fait pas
échouer la proposition entière. Un écran d'erreur serait pire qu'une liste
imparfaite que l'ingénieur corrige.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from threatscope.core import parse_suggestions  # noqa: E402
from threatscope.crew import MAX_SUGGESTIONS  # noqa: E402


def test_clean_output_is_parsed():
    brut = (
        "Élévation de privilèges via le diagnostic || Accès au port OBD, puis "
        "contournement de l'authentification UDS\n"
        "Altération du logiciel || Interception de la mise à jour, injection d'un binaire modifié"
    )
    resultat = parse_suggestions(brut)
    assert len(resultat) == 2
    assert resultat[0].threat == "Élévation de privilèges via le diagnostic"
    assert resultat[0].path.startswith("Accès au port OBD")


def test_noise_the_model_adds_anyway():
    """Puces, numéros, gras, phrase d'introduction, ligne de séparation."""
    brut = (
        "Voici les scénarios de menace identifiés :\n"
        "\n"
        "1. **Usurpation d'identité du calculateur** || Injection de trames forgées sur le bus\n"
        "- Déni de service || Saturation du bus par des trames à haute priorité\n"
        "* `Divulgation de données` || Lecture de la mémoire après revente du véhicule\n"
        "---\n"
        "En espérant que cette analyse vous soit utile."
    )
    resultat = parse_suggestions(brut)
    assert len(resultat) == 3
    assert resultat[0].threat == "Usurpation d'identité du calculateur"
    assert resultat[2].threat == "Divulgation de données"


def test_malformed_lines_are_skipped_not_fatal():
    """Une ligne bancale ne doit pas emporter les bonnes."""
    brut = (
        "Menace sans séparateur ni chemin\n"
        "Bonne menace || Bon chemin d'attaque\n"
        "|| chemin orphelin sans menace\n"
        "menace orpheline sans chemin ||\n"
        "   ||   \n"
        "Autre bonne menace || Autre bon chemin"
    )
    resultat = parse_suggestions(brut)
    assert [s.threat for s in resultat] == ["Bonne menace", "Autre bonne menace"]


def test_duplicates_are_removed_case_insensitively():
    brut = (
        "Altération du logiciel || Via la mise à jour\n"
        "ALTÉRATION DU LOGICIEL || VIA LA MISE À JOUR\n"
        "Altération du logiciel || Via le port de diagnostic"
    )
    resultat = parse_suggestions(brut)
    assert len(resultat) == 2, "seul le doublon exact devait disparaître"


def test_output_is_capped():
    brut = "\n".join(f"Menace {i} || Chemin {i}" for i in range(20))
    assert len(parse_suggestions(brut)) == MAX_SUGGESTIONS


def test_empty_and_garbage_inputs_are_survivable():
    for brut in ("", None, "   ", "Aucune menace identifiée.", "\n\n\n", "||"):
        assert parse_suggestions(brut) == [], f"{brut!r} aurait dû rendre une liste vide"


def test_long_fields_are_truncated():
    brut = "M" * 900 + " || " + "C" * 900
    resultat = parse_suggestions(brut)
    assert len(resultat) == 1
    assert len(resultat[0].threat) <= 300
    assert len(resultat[0].path) <= 300


def test_a_suggestion_carries_no_rating():
    """Le cœur du positionnement : l'IA propose, elle ne cote jamais.

    Si quelqu'un ajoutait un jour un champ de cotation à la suggestion, ce
    test tomberait — et c'est le moment de se demander pourquoi, pas
    d'ajuster le test.
    """
    from threatscope.core import ThreatSuggestion

    champs = set(ThreatSuggestion.__dataclass_fields__)
    assert champs == {"threat", "path"}, f"champs inattendus : {champs}"
    for interdit in ("time", "expertise", "knowledge", "window", "equipment",
                     "decision", "risk", "feasibility", "impact"):
        assert interdit not in champs, f"« {interdit} » n'a rien à faire dans une proposition"


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
    print(f"\n{len(tests) - failures}/{len(tests)} tests passés")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
