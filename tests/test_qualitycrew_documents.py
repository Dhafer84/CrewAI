"""Tests de la vérification des documents du visiteur, avant l'audit.

Exécutable sans pytest :  .venv/bin/python3 -B tests/test_qualitycrew_documents.py

Le drapeau `-B` n'est pas décoratif — voir l'en-tête de `tests/test_asil.py`.

Ce qui est vérifié tient en deux phrases : **un envoi inexploitable est refusé
avant de consommer un audit**, avec un message qui dit quoi corriger ; et
**un document maladroit mais réel passe** — ses défauts sont le travail de
l'audit, pas de ce filtre. Les codes attendus sont écrits à la main.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from qualitycrew.documents import (  # noqa: E402
    DOC_ORDER,
    MAX_DOC_BYTES,
    MAX_TOTAL_BYTES,
    check_documents,
    messages,
)

_ROOT = Path(__file__).resolve().parent.parent
_SAMPLE = {d: (_ROOT / "data" / "sample_project" / f"{d}.md").read_text(encoding="utf-8") for d in DOC_ORDER}


def _template(lang: str) -> dict:
    return {d: (_ROOT / "data" / "templates" / lang / f"{d}.md").read_text(encoding="utf-8") for d in DOC_ORDER}


def _codes(docs) -> list[tuple]:
    return [(p.doc, p.code) for p in check_documents(docs)[1]]


def test_the_sample_project_is_accepted():
    """L'exemple de la démo — avec ses 12 défauts injectés — passe : le filtre
    ne juge pas la qualité. Ses « [90 ms, 110 ms] » ne sont pas des crochets
    de gabarit."""
    clean, problems = check_documents(_SAMPLE)
    assert problems == [], problems
    assert set(clean) == set(DOC_ORDER)


def test_the_limits_are_the_provisional_ones():
    # Écrites à la main : les changer doit être un choix (mesure de l'étape 5)
    assert (MAX_DOC_BYTES, MAX_TOTAL_BYTES) == (12_000, 20_000)
    assert sum(len(t.encode("utf-8")) for t in _SAMPLE.values()) < MAX_TOTAL_BYTES


def test_an_unfilled_template_is_refused_in_both_languages():
    for lang in ("fr", "en"):
        assert _codes(_template(lang)) == [
            ("srs", "unfilled"), ("test_plan", "unfilled"), ("review_report", "unfilled"),
        ], lang


def test_a_filled_template_with_one_or_two_leftovers_passes():
    """Un ou deux [crochets] oubliés : l'audit les trouvera, on ne bloque pas."""
    docs = dict(_SAMPLE)
    docs["srs"] = _SAMPLE["srs"] + "\n- Trace amont : [SYS-REQ-xxx].\n**Projet :** [Nom du projet]\n"
    assert _codes(docs) == []


def test_missing_empty_and_non_text_documents():
    assert _codes({"srs": _SAMPLE["srs"]}) == [("test_plan", "missing"), ("review_report", "missing")]
    assert _codes({**_SAMPLE, "test_plan": "  \n\t "}) == [("test_plan", "empty")]
    assert _codes({**_SAMPLE, "srs": 42}) == [("srs", "missing")]
    binaire = "PK\x03\x04" + "\x00" * 20 + "contenu"
    assert _codes({**_SAMPLE, "review_report": binaire}) == [("review_report", "not_text")]
    # Un fichier binaire lu comme texte par le navigateur : plein de « � »
    remplace = "### R-01\n" + "�" * 50 + "a" * 100
    assert _codes({**_SAMPLE, "review_report": remplace}) == [("review_report", "not_text")]
    assert _codes(None) == [(d, "missing") for d in DOC_ORDER]
    assert _codes("pas un dictionnaire") == [(d, "missing") for d in DOC_ORDER]


def test_swapped_documents_are_caught_by_their_headings():
    """Le plan de test cite des SRS-… (« Vérifie : SRS-001 »), jamais en titre."""
    inverses = {"srs": _SAMPLE["test_plan"], "test_plan": _SAMPLE["srs"], "review_report": _SAMPLE["review_report"]}
    assert _codes(inverses) == [("srs", "no_ids"), ("test_plan", "no_ids")]


def test_size_limits_per_document_and_in_total():
    gros = "### SRS-001 — Exigence\n" + "Le module DOIT faire ceci. " * 500   # ~13,5 Ko
    assert ("srs", "too_big") in _codes({**_SAMPLE, "srs": gros})
    # Chacun sous la limite, ensemble au-dessus
    moyen = "### {id} — Titre\n" + "Un texte de remplissage réaliste. " * 210   # ~7 Ko
    docs = {"srs": moyen.format(id="SRS-001"), "test_plan": moyen.format(id="TC-001"),
            "review_report": moyen.format(id="R-01")}
    assert _codes(docs) == [(None, "total_too_big")]


def test_bom_and_windows_line_endings_are_normalised():
    windows = "﻿" + _SAMPLE["srs"].replace("\n", "\r\n")
    clean, problems = check_documents({**_SAMPLE, "srs": windows})
    assert problems == []
    assert clean["srs"] == _SAMPLE["srs"]


def test_every_refusal_has_a_message_in_both_languages_naming_the_document():
    cas = [
        {"srs": _SAMPLE["srs"]},                                           # missing
        {**_SAMPLE, "test_plan": " "},                                       # empty
        {**_SAMPLE, "review_report": "\x00\x00"},                            # not_text
        {**_SAMPLE, "srs": _SAMPLE["test_plan"]},                            # no_ids
        _template("fr"),                                                     # unfilled
        {**_SAMPLE, "srs": "### SRS-001\n" + "x" * 21_000},                  # too_big + total
    ]
    vus = set()
    for docs in cas:
        _, problems = check_documents(docs)
        for p in problems:
            fr, en = p.message("fr"), p.message("en")
            assert fr and en and fr != en, p
            assert "qc.docs" not in fr + en, f"clé non traduite : {p}"
            if p.doc:
                assert fr.startswith(("Exigences", "Plan de test", "Rapport de revue")), fr
                assert en.startswith(("Requirements", "Test plan", "Review report")), en
            vus.add(p.code)
    assert vus == {"missing", "empty", "not_text", "no_ids", "unfilled", "too_big", "total_too_big"}
    assert "21,1 Ko" in messages(check_documents(cas[-1])[1], "fr")[0]
    assert "21.1 KB" in messages(check_documents(cas[-1])[1], "en")[0]
    # Au dixième supérieur : jamais « 20 Ko, au-delà de la limite de 20 Ko »
    juste = {"srs": "### SRS-001\n" + "x" * 6_988, "test_plan": "### TC-001\n" + "x" * 6_989,
             "review_report": "### R-01\n" + "x" * 6_021}   # 20 030 octets au total
    assert messages(check_documents(juste)[1], "fr") == [
        "Les trois documents font 20,1 Ko ensemble, au-delà de la limite de 20 Ko."]


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"  ok    {test.__name__}")
        except (AssertionError, Exception) as exc:
            failures += 1
            print(f"  ÉCHEC {test.__name__} : {type(exc).__name__}: {exc}")
    print(f"\n{len(tests) - failures}/{len(tests)} tests passés")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
