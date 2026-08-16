"""Tests de la détermination ASIL.

Exécutable sans pytest :  .venv/bin/python3 tests/test_asil.py

La table de référence ci-dessous est écrite **à la main**, ligne par ligne,
et non recalculée à partir de la formule du module. Un test qui re-dériverait
la somme S+E+C ne vérifierait que sa propre cohérence.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from safetyscope.asil import (  # noqa: E402
    DECOMPOSITIONS,
    InvalidRating,
    determine_asil,
    full_matrix,
    rate,
)

# Table de référence : EXPECTED[severity][exposure] = (C1, C2, C3)
EXPECTED = {
    1: {
        1: ("QM", "QM", "QM"),
        2: ("QM", "QM", "QM"),
        3: ("QM", "QM", "A"),
        4: ("QM", "A", "B"),
    },
    2: {
        1: ("QM", "QM", "QM"),
        2: ("QM", "QM", "A"),
        3: ("QM", "A", "B"),
        4: ("A", "B", "C"),
    },
    3: {
        1: ("QM", "QM", "A"),
        2: ("QM", "A", "B"),
        3: ("A", "B", "C"),
        4: ("B", "C", "D"),
    },
}


def test_reference_table():
    """Les 36 combinaisons S1-3 / E1-4 / C1-3 correspondent à la table."""
    for severity, by_exposure in EXPECTED.items():
        for exposure, by_controllability in by_exposure.items():
            for index, expected in enumerate(by_controllability):
                controllability = index + 1
                got = determine_asil(severity, exposure, controllability)
                assert got == expected, (
                    f"S{severity}E{exposure}C{controllability} : "
                    f"attendu {expected}, obtenu {got}"
                )


def test_zero_on_any_axis_gives_qm():
    """Un S0, E0 ou C0 sort l'événement du périmètre ASIL."""
    assert determine_asil(0, 4, 3) == "QM"
    assert determine_asil(3, 0, 3) == "QM"
    assert determine_asil(3, 4, 0) == "QM"
    assert determine_asil(0, 0, 0) == "QM"


def test_extremes():
    assert determine_asil(3, 4, 3) == "D", "le cas le plus sévère doit donner D"
    assert determine_asil(1, 1, 1) == "QM"


def test_out_of_range_is_rejected():
    for bad in [(4, 1, 1), (1, 5, 1), (1, 1, 4), (-1, 1, 1)]:
        try:
            determine_asil(*bad)
        except InvalidRating:
            continue
        raise AssertionError(f"{bad} aurait dû être refusé")


def test_booleans_are_rejected():
    """True vaut 1 en Python — accepter un booléen masquerait une erreur d'appel."""
    try:
        determine_asil(True, 4, 3)
    except InvalidRating:
        return
    raise AssertionError("un booléen aurait dû être refusé")


def test_decompositions_never_exceed_parent():
    """Aucune branche d'une décomposition ne peut dépasser l'ASIL d'origine."""
    from safetyscope.asil import ASIL_ORDER

    for parent, pairs in DECOMPOSITIONS.items():
        for first, second in pairs:
            assert ASIL_ORDER.index(first) <= ASIL_ORDER.index(parent)
            assert ASIL_ORDER.index(second) <= ASIL_ORDER.index(parent)


def test_decomposition_notation():
    result = rate(3, 4, 3)
    assert result.asil == "D"
    assert "B(D) + B(D)" in result.decomposition_notation()
    assert result.is_safety_relevant is True

    qm = rate(1, 1, 1)
    assert qm.is_safety_relevant is False
    assert qm.decomposition_notation() == []


def test_full_matrix_is_complete():
    """La table servie à l'interface couvre toutes les combinaisons."""
    matrix = full_matrix()
    assert len(matrix["table"]) == 4 * 5 * 4, "4 S × 5 E × 4 C attendues"
    assert matrix["table"]["S3E4C3"] == "D"
    assert matrix["table"]["S0E4C3"] == "QM"
    # La table servie doit coller à la fonction, sinon l'interface mentirait.
    for severity, by_exposure in EXPECTED.items():
        for exposure, by_controllability in by_exposure.items():
            for index, expected in enumerate(by_controllability):
                key = f"S{severity}E{exposure}C{index + 1}"
                assert matrix["table"][key] == expected


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
