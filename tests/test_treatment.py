"""Tests du traitement du risque et des objectifs de cybersécurité.

Exécutable sans pytest :  .venv/bin/python3 -B tests/test_treatment.py

Le drapeau `-B` n'est pas décoratif — voir l'en-tête de `tests/test_asil.py`.

Ce qui est vérifié ici tient en une phrase : **une valeur de risque qui ne
débouche sur rien n'a rien décidé.** Un risque au-dessus de 1 sans décision,
une réduction sans objectif, une acceptation sans justification — chacun de
ces trous doit être signalé, pas toléré.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from threatscope.rating import InvalidRating  # noqa: E402
from threatscope.treatment import (  # noqa: E402
    TREATMENT_ORDER,
    check,
    produces_goal,
    requires_decision,
    treatment_scales,
)

# Écrit à la main : quel risque exige une décision explicite.
EXPECTED_REQUIRES = {1: False, 2: True, 3: True, 4: True, 5: True}


def test_decision_threshold_reference():
    for risk, expected in EXPECTED_REQUIRES.items():
        got = requires_decision(risk)
        assert got == expected, f"risque {risk} : attendu {expected}, obtenu {got}"


def test_risk_one_may_be_left_alone():
    """Un risque de 1 peut être retenu sans autre forme de procès."""
    assert check(1) == []
    assert check(1, decision="") == []


def test_risk_above_one_demands_a_decision():
    for risk in (2, 3, 4, 5):
        problemes = check(risk)
        assert problemes == ["aucune décision de traitement"], f"risque {risk} laissé passer"


def test_reduction_without_a_goal_is_incomplete():
    """C'est le cas qui produit une exigence — sans objectif, il ne produit rien."""
    assert check(4, decision="reduce") == ["l'objectif de cybersécurité manque"]
    assert check(4, decision="reduce", goal="   ") == ["l'objectif de cybersécurité manque"]
    assert check(4, decision="reduce", goal="Authentifier les requêtes de diagnostic") == []
    # Une justification ne remplace pas un objectif.
    assert check(4, decision="reduce", rationale="on verra plus tard") != []


def test_retention_without_justification_is_incomplete():
    """Un risque accepté sans argument écrit est un risque oublié."""
    assert check(5, decision="retain") == ["la justification manque"]
    assert check(5, decision="retain", rationale="Hors périmètre du véhicule") == []
    # Un objectif ne remplace pas une justification.
    assert check(5, decision="retain", goal="Authentifier") != []


def test_every_option_states_what_it_requires():
    for key in TREATMENT_ORDER:
        assert check(3, decision=key) != [], f"« {key} » devrait exiger un écrit"


def test_only_reduction_produces_a_goal():
    assert produces_goal("reduce") is True
    for key in ("avoid", "share", "retain", "", "n'importe quoi"):
        assert produces_goal(key) is False, f"« {key} » ne doit produire aucune exigence"


def test_unknown_decision_is_reported():
    problemes = check(3, decision="ignorer")
    assert len(problemes) == 1 and "inconnue" in problemes[0]


def test_partial_entry_on_a_low_risk_is_still_checked():
    """Une décision entamée puis laissée en plan est pire qu'une absence de décision."""
    assert check(1, decision="reduce") == ["l'objectif de cybersécurité manque"]


def test_out_of_range_risk_is_rejected():
    for bad in (0, 6, -1):
        try:
            requires_decision(bad)
        except InvalidRating:
            continue
        raise AssertionError(f"un risque de {bad} aurait dû être refusé")


def test_booleans_are_rejected():
    try:
        requires_decision(True)
    except InvalidRating:
        return
    raise AssertionError("un booléen aurait dû être refusé")


def test_served_options_match_the_engine():
    """La page ne réécrit ni les libellés ni ce que chaque décision impose."""
    served = treatment_scales()
    assert served["order"] == TREATMENT_ORDER
    assert set(served["options"]) == set(TREATMENT_ORDER)
    assert served["decisionThreshold"] == 1

    for key, option in served["options"].items():
        for champ in ("label", "hint", "requires", "prompt"):
            assert option.get(champ), f"« {key} » : le champ {champ} manque"
        assert option["requires"] in ("goal", "rationale")

    # Une seule décision produit une exigence — sinon l'outil dirait n'importe quoi
    # sur ce qu'une TARA fabrique.
    produisent = [k for k, o in served["options"].items() if o["requires"] == "goal"]
    assert produisent == ["reduce"]


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
