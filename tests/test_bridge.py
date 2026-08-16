"""Tests du pont HARA → TARA.

Exécutable sans pytest :  .venv/bin/python3 -B tests/test_bridge.py

Le drapeau `-B` n'est pas décoratif — voir l'en-tête de `tests/test_asil.py`.

Ces tests portent moins sur du calcul que sur une **règle de méthode** : la
sévérité traverse le pont, l'exposition et la contrôlabilité non. C'est le
point le plus facile à casser par mégarde dans six mois, et celui qui porte
toute la valeur de l'outil.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from threatscope.bridge import (  # noqa: E402
    DamageProposal,
    InvalidTransfer,
    bridge_rule,
    propose_damage,
    severity_to_impact,
)

# Correspondance écrite à la main, cran par cran, et non dérivée de l'identité.
# Si les deux échelles cessaient un jour d'avoir la même granularité, c'est ici
# que ça devrait se voir.
EXPECTED_MAPPING = {
    0: 0,  # aucune blessure          → négligeable
    1: 1,  # blessures légères        → modéré
    2: 2,  # blessures graves         → majeur
    3: 3,  # blessures critiques      → sévère
}


def test_severity_mapping_reference():
    for severity, expected in EXPECTED_MAPPING.items():
        got = severity_to_impact(severity)
        assert got == expected, f"S{severity} : attendu {expected}, obtenu {got}"


def test_exposure_and_controllability_have_no_field():
    """La garantie est structurelle : ce qui n'a pas de champ ne peut pas fuir.

    Si quelqu'un ajoutait un jour un champ d'exposition ou de contrôlabilité à
    la proposition, ce test tomberait — et c'est exactement le moment où il
    faut se demander pourquoi, pas ajuster le test.
    """
    noms = set(DamageProposal.__dataclass_fields__)
    for interdit in ("exposure", "controllability", "asil_decomposition"):
        assert interdit not in noms, f"« {interdit} » n'a rien à faire dans le pont"

    # Et la règle servie à l'interface doit dire la même chose.
    regle = bridge_rule()
    assert regle["transfers"] == ["severity"]
    assert set(regle["doesNotTransfer"]) == {"exposure", "controllability"}
    for interdit in regle["doesNotTransfer"]:
        assert interdit not in regle["carriedFields"]


def test_proposal_rates_only_safety_impact():
    """Le pont ne cote que la sécurité des personnes.

    Financier, opérationnel et vie privée n'ont aucun équivalent en HARA :
    les proposer serait inventer une cotation.
    """
    proposal = propose_damage(
        malfunction="Perte inattendue du couple de freinage",
        situation="Descente sur autoroute, chaussée mouillée",
        severity=3,
        asil="D",
        origin="Événement redouté 2",
    )
    assert proposal.safety_impact == 3
    noms = set(DamageProposal.__dataclass_fields__)
    for categorie in ("financial", "operational", "privacy"):
        assert categorie not in noms, f"le pont ne doit rien proposer pour « {categorie} »"


def test_proposal_keeps_its_origin():
    """Sans traçabilité, une reprise devient indiscernable d'une saisie manuelle."""
    proposal = propose_damage("Malfonction", "Situation", 2, asil="B", origin="Événement 5")
    assert proposal.origin == "Événement 5"
    assert proposal.severity == 2
    assert proposal.asil == "B"


def test_text_joins_malfunction_and_situation():
    assert propose_damage("Malfonction", "Situation", 1).text == "Malfonction — Situation"
    # Une situation vide ne doit pas laisser un tiret orphelin.
    assert propose_damage("Malfonction", "", 1).text == "Malfonction"
    assert propose_damage("", "Situation", 1).text == "Situation"
    assert propose_damage("  ", "  ", 1).text == ""


def test_out_of_range_is_rejected():
    for bad in (4, -1, 99):
        try:
            severity_to_impact(bad)
        except InvalidTransfer:
            continue
        raise AssertionError(f"S{bad} aurait dû être refusé")


def test_booleans_are_rejected():
    """True vaut 1 en Python — accepter un booléen masquerait une erreur d'appel."""
    try:
        severity_to_impact(True)
    except InvalidTransfer:
        return
    raise AssertionError("un booléen aurait dû être refusé")


def test_rule_carries_its_own_justification():
    """La page doit pouvoir expliquer la règle sans la réécrire elle-même."""
    why = bridge_rule()["why"]
    for cle in ("severity", "exposure", "controllability", "replacement"):
        assert why.get(cle), f"la justification de « {cle} » manque"

    served = bridge_rule()["severityToImpact"]
    assert served == [EXPECTED_MAPPING[s] for s in sorted(EXPECTED_MAPPING)]


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
