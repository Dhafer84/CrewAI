"""Tests de la cotation du risque cybersécurité.

Exécutable sans pytest :  .venv/bin/python3 -B tests/test_rating.py

Le drapeau `-B` n'est pas décoratif — voir l'en-tête de `tests/test_asil.py`
pour la raison détaillée. En deux mots : un `.pyc` périmé fait mentir les
tests, `-B` n'écrit aucun cache.

Les tables de référence ci-dessous sont écrites **à la main**, cellule par
cellule, et non recalculées à partir du module. Un test qui re-dériverait la
somme ou relirait `_RISK` ne vérifierait que sa propre cohérence.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from threatscope.rating import (  # noqa: E402
    FEASIBILITY_ORDER,
    IMPACT_ORDER,
    MAX_POTENTIAL,
    InvalidRating,
    attack_potential,
    determine_risk,
    feasibility_from_potential,
    full_scales,
    overall_impact,
    rate,
)

# Matrice de référence : EXPECTED_RISK[impact] = (TrèsFaible, Faible, Moyenne, Élevée)
EXPECTED_RISK = {
    0: (1, 1, 1, 1),  # Négligeable
    1: (1, 2, 2, 3),  # Modéré
    2: (1, 2, 3, 4),  # Majeur
    3: (2, 3, 4, 5),  # Sévère
}

# Seuils de faisabilité attendus : total de points → niveau.
# Bornes écrites une par une, de part et d'autre de chaque palier.
EXPECTED_FEASIBILITY = {
    0: 3,   # Élevée
    13: 3,
    14: 2,  # Moyenne
    23: 2,
    24: 1,  # Faible
    33: 1,
    34: 0,  # Très faible
    50: 0,
}


def test_risk_matrix_reference():
    """Les 16 croisements impact × faisabilité correspondent à la matrice."""
    for impact, by_feasibility in EXPECTED_RISK.items():
        for feasibility, expected in enumerate(by_feasibility):
            got = determine_risk(impact, feasibility)
            assert got == expected, (
                f"impact {impact} / faisabilité {feasibility} : "
                f"attendu {expected}, obtenu {got}"
            )


def test_feasibility_thresholds():
    """Les paliers tombent exactement où ils sont annoncés."""
    for potential, expected in EXPECTED_FEASIBILITY.items():
        got = feasibility_from_potential(potential)
        assert got == expected, (
            f"{potential} points : attendu {FEASIBILITY_ORDER[expected]}, "
            f"obtenu {FEASIBILITY_ORDER[got]}"
        )


def test_archetypes_land_in_their_band():
    """Chaque palier est ancré sur un archétype concret d'investissement attaquant.

    C'est la justification du barème : si un de ces cas changeait de bande,
    la calibration serait à revoir, pas le test.
    """
    # Le tutoriel en ligne : quelques jours, matériel courant. 2+2+0+2+0
    assert attack_potential(1, 1, 0, 1, 0) == 6
    assert feasibility_from_potential(6) == 3, "élevée"

    # Quelques semaines, matériel spécialisé accessible. 5+2+2+5+3
    assert attack_potential(2, 1, 1, 2, 1) == 17
    assert feasibility_from_potential(17) == 2, "moyenne"

    # Plusieurs mois, équipement sur mesure. 9+5+5+5+7
    assert attack_potential(3, 2, 2, 2, 2) == 31
    assert feasibility_from_potential(31) == 1, "faible"

    # Effort de niveau laboratoire, tout au maximum. 14+8+8+9+11
    assert attack_potential(4, 3, 3, 3, 3) == 50
    assert feasibility_from_potential(50) == 0, "très faible"


def test_time_and_equipment_actually_discriminate():
    """Le barème doit séparer nettement le dongle à 30 € du banc de laboratoire.

    C'est la raison pour laquelle CVSS a été écarté : il ne mesure ni le temps
    ni l'équipement, et rapproche ces deux attaques. Si ce test venait à
    échouer, l'argument qui a présidé au choix du barème tomberait avec lui.
    """
    # Dongle radio, quelques jours, voiture en stationnement.
    dongle = rate(impact=3, time=1, expertise=1, knowledge=0, window=1, equipment=0)
    # Banc de laboratoire, plusieurs mois, calculateur à démonter.
    laboratoire = rate(impact=3, time=3, expertise=2, knowledge=2, window=3, equipment=2)

    assert dongle.potential == 6
    assert laboratoire.potential == 35
    assert dongle.feasibility == 3, "le dongle doit rester en faisabilité élevée"
    assert laboratoire.feasibility == 0, "le laboratoire doit tomber en très faible"

    # À impact sévère identique, l'écart de faisabilité doit se voir sur le risque.
    assert dongle.risk == 5
    assert laboratoire.risk == 2


def test_risk_is_monotone():
    """Le risque ne doit jamais décroître quand l'impact ou la faisabilité croît.

    Une matrice non monotone serait incohérente : elle récompenserait une
    aggravation.
    """
    for impact in range(len(IMPACT_ORDER)):
        for feasibility in range(len(FEASIBILITY_ORDER) - 1):
            assert determine_risk(impact, feasibility) <= determine_risk(
                impact, feasibility + 1
            ), f"non monotone en faisabilité à l'impact {impact}"

    for feasibility in range(len(FEASIBILITY_ORDER)):
        for impact in range(len(IMPACT_ORDER) - 1):
            assert determine_risk(impact, feasibility) <= determine_risk(
                impact + 1, feasibility
            ), f"non monotone en impact à la faisabilité {feasibility}"


def test_negligible_impact_never_exceeds_one():
    """Sans dommage significatif, il n'y a pas de risque à traiter."""
    for feasibility in range(len(FEASIBILITY_ORDER)):
        assert determine_risk(0, feasibility) == 1


def test_potential_is_monotone_per_parameter():
    """Aggraver un seul paramètre ne peut pas rendre l'attaque plus faisable."""
    base = [0, 0, 0, 0, 0]
    maxima = [4, 3, 3, 3, 3]
    for index, top in enumerate(maxima):
        previous = -1
        for level in range(top + 1):
            args = list(base)
            args[index] = level
            total = attack_potential(*args)
            assert total > previous, f"paramètre {index} non croissant au niveau {level}"
            previous = total


def test_overall_impact_takes_maximum():
    """Un scénario de dommage est aussi grave que sa pire conséquence."""
    assert overall_impact(0, 0, 0, 0) == 0
    assert overall_impact(3, 0, 0, 0) == 3, "la sécurité des personnes seule suffit"
    assert overall_impact(0, 0, 0, 2) == 2, "la vie privée seule aussi"
    assert overall_impact(1, 2, 1, 0) == 2


def test_out_of_range_is_rejected():
    for bad in [(5, 0, 0, 0, 0), (0, 4, 0, 0, 0), (0, 0, 0, 0, 4), (-1, 0, 0, 0, 0)]:
        try:
            attack_potential(*bad)
        except InvalidRating:
            continue
        raise AssertionError(f"{bad} aurait dû être refusé")

    for bad in [(4, 0), (0, 4), (-1, 0)]:
        try:
            determine_risk(*bad)
        except InvalidRating:
            continue
        raise AssertionError(f"{bad} aurait dû être refusé")

    try:
        feasibility_from_potential(MAX_POTENTIAL + 1)
    except InvalidRating:
        pass
    else:
        raise AssertionError("un potentiel hors barème aurait dû être refusé")


def test_booleans_are_rejected():
    """True vaut 1 en Python — accepter un booléen masquerait une erreur d'appel."""
    for call in (
        lambda: attack_potential(True, 0, 0, 0, 0),
        lambda: determine_risk(True, 0),
        lambda: overall_impact(True, 0, 0, 0),
        lambda: feasibility_from_potential(True),
    ):
        try:
            call()
        except InvalidRating:
            continue
        raise AssertionError("un booléen aurait dû être refusé")


def test_needs_treatment_only_above_one():
    assert rate(3, 1, 1, 0, 1, 0).needs_treatment is True
    assert rate(0, 4, 3, 3, 3, 3).needs_treatment is False


def test_full_scales_matches_the_functions():
    """Le barème servi à l'interface doit coller au moteur, sinon la page mentirait."""
    scales = full_scales()

    assert len(scales["risk"]) == len(IMPACT_ORDER) * len(FEASIBILITY_ORDER)
    for impact, by_feasibility in EXPECTED_RISK.items():
        for feasibility, expected in enumerate(by_feasibility):
            assert scales["risk"][f"I{impact}F{feasibility}"] == expected

    assert scales["maxPotential"] == 50
    assert len(scales["parameters"]) == 5

    # Les points servis doivent être ceux que la somme applique réellement.
    for key, parameter in scales["parameters"].items():
        levels = parameter["levels"]
        assert [entry["value"] for entry in levels] == list(range(len(levels)))
        assert levels[0]["points"] == 0, f"{key} doit démarrer à 0 point"
        points = [entry["points"] for entry in levels]
        assert points == sorted(points), f"{key} : les points doivent croître"

    served_max = sum(
        max(entry["points"] for entry in parameter["levels"])
        for parameter in scales["parameters"].values()
    )
    assert served_max == MAX_POTENTIAL


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
