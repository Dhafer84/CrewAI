"""Tests de complétude et de verrouillage d'un dossier 8D.

Exécutable sans pytest :  .venv/bin/python3 -B tests/test_causetrace_check.py

Le drapeau `-B` n'est pas décoratif — voir l'en-tête de `tests/test_asil.py`.

Ce qui est vérifié ici tient en une phrase : **l'outil refuse d'appeler
« résolu » un dossier qui ne l'est pas**, et il dit précisément où il pèche.

⚠️ La table de référence ci-dessous est écrite **à la main**, constat par
constat, et non recalculée depuis `_REQUIRED`. Un test qui re-dériverait la
table du moteur ne vérifierait que sa propre cohérence — même raison que la
table ASIL de `test_asil.py`.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from causetrace.check import (  # noqa: E402
    SLOT_ORDER,
    check,
    gap_codes,
    discipline_label,
    gap_label,
    is_closable,
    is_empty,
    rules,
    slot_label,
    status,
)
from causetrace.example import mediocre_example  # noqa: E402
from causetrace.model import (  # noqa: E402
    DISCIPLINE_ORDER,
    FIELD_ORDER,
    Dossier,
    InvalidDossier,
    build_dossier,
)


def _codes(dossier) -> list[str]:
    return [g.code for g in check(dossier)]


# Un dossier irréprochable, dont chaque test retire ce qu'il veut éprouver.
def _full() -> dict:
    return {
        "reference": "8D-2026-014",
        "title": "Perte intermittente du signal de vitesse roue",
        "d1": {"owner": "M. Bonnet", "members": ["Atelier", "Qualité fournisseur"]},
        "d2": {
            "what": "Capteur de vitesse roue avant gauche : signal perdu au-delà de 80 km/h",
            "where": "Détecté en fin de ligne, poste de contrôle 4",
            "since": "Depuis le lot du 12 mai 2026",
            "how_many": "7 pièces sur 1 240 contrôlées",
            "is_not": "Aucune occurrence sur la roue avant droite ni sur le lot d'avril",
        },
        "d3": {
            "action": "Tri à 100 % des lots en stock et blocage des expéditions",
            "due_date": "2026-06-30",
            "effectiveness_check": "Aucun défaut sorti du tri sur 3 lots consécutifs",
        },
        "d4": {
            "occurrence": "Serrage du connecteur hors tolérance sur la ligne 2",
            "escape": "Le contrôle de fin de ligne ne teste le signal qu'à l'arrêt",
            # Les deux chaînes descendent du symptôme vers le système, et
            # s'arrêtent là où quelque chose est prévenable.
            "occurrence_chain": [
                {"statement": "Le connecteur perd le contact en vibration",
                 "nature": "technical"},
                {"statement": "Le couple appliqué est sous la spécification",
                 "nature": "technical"},
                {"statement": "La visseuse de la ligne 2 n'est pas asservie au couple",
                 "nature": "process"},
                {"statement": "Le standard de poste ne l'exige pas pour ce connecteur",
                 "nature": "system"},
            ],
            "escape_chain": [
                {"statement": "Le défaut n'apparaît qu'au-delà de 80 km/h",
                 "nature": "technical"},
                {"statement": "Le banc de fin de ligne ne sollicite le capteur qu'à l'arrêt",
                 "nature": "technical"},
                {"statement": "Le plan de surveillance ne prévoit aucun essai dynamique",
                 "nature": "process"},
                {"statement": "L'AMDEC ne cotait pas ce mode de défaillance",
                 "nature": "system"},
            ],
        },
        "d5": {
            "on_occurrence": "Visseuse asservie au couple, avec relevé archivé",
            "on_escape": "Ajout d'un test dynamique à 90 km/h au banc de fin de ligne",
        },
        "d6": {
            "implemented_on": "2026-07-15",
            "evidence": "0 défaut sur 4 300 pièces produites après mise en œuvre",
        },
        "d7": {
            "systemic_update": "AMDEC processus et plan de surveillance mis à jour",
            "lessons": "Étendu aux trois autres lignes de capteurs",
        },
        "d8": {"claimed_closed": True, "closed_on": "2026-07-31"},
    }


def _dossier(**ecrase) -> Dossier:
    charge = _full()
    for cle, valeur in ecrase.items():
        if valeur is None:
            charge[cle] = {}
        else:
            charge[cle].update(valeur)
    return build_dossier(charge)


# --------------------------------------------------------------------------
# La table de référence — écrite à la main
# --------------------------------------------------------------------------

# Dossier entièrement vierge. D4, D5 et D6 sont verrouillés en cascade ;
# D8 se tait, parce que rappeler qu'un dossier vide n'est pas clos serait du
# bruit. D3, lui, est bien contrôlé : le containment n'attend personne.
BLANK_EXPECTED = [
    "d1.no_owner",
    "d2.no_what",
    "d2.no_where",
    "d2.no_since",
    "d2.no_extent",
    "d2.no_is_not",
    "d3.no_action",
    "d3.no_due_date",
    "d3.no_effectiveness_check",
    "d4.locked",
    "d5.locked",
    "d6.locked",
    "d7.no_systemic_update",
]


def test_a_blank_dossier_matches_the_reference_table():
    assert _codes(Dossier()) == BLANK_EXPECTED


def test_a_flawless_dossier_has_nothing_to_say():
    assert check(build_dossier(_full())) == []


# --------------------------------------------------------------------------
# Les verrous
# --------------------------------------------------------------------------

def test_containment_never_waits_for_the_root_cause():
    """⚠️ D3 ne dépend de rien. Protéger le client n'attend pas la cause.

    Si ce test tombe parce que quelqu'un a « harmonisé » les verrous, c'est
    une faute de métier qui aurait été introduite, pas une rigueur de plus.
    """
    dossier = _dossier(d2=None, d4=None)
    codes = _codes(dossier)
    assert "d3.locked" not in codes, "le containment ne doit jamais être verrouillé"
    # Et ses champs restent bel et bien contrôlés.
    manquant = _codes(_dossier(d2=None, d3={"due_date": ""}))
    assert "d3.no_due_date" in manquant


def test_a_locked_discipline_reports_only_its_lock():
    """Lister les champs d'une discipline verrouillée noierait l'information."""
    codes = _codes(_dossier(d4=None))
    assert "d5.locked" in codes
    assert not [c for c in codes if c.startswith("d5.") and c != "d5.locked"]


def test_a_permanent_action_written_before_the_cause_is_still_flagged():
    """Le D5 est rempli, mais la cause n'est pas établie : le verrou tient.

    C'est le cœur du parti pris — une action corrective qui précède la cause
    racine corrige une intuition, même bien rédigée.
    """
    dossier = _dossier(d4={"occurrence": "", "escape": ""})
    assert dossier.d5.on_occurrence, "le jeu d'essai doit bien porter une action"
    assert "d5.locked" in _codes(dossier)


def test_the_lock_cascades():
    """Un D2 incomplet verrouille D4, qui verrouille D5, qui verrouille D6."""
    codes = _codes(_dossier(d2={"is_not": ""}))
    for attendu in ("d4.locked", "d5.locked", "d6.locked"):
        assert attendu in codes, f"{attendu} manque : la cascade est rompue"


def test_a_lock_is_blocking():
    verrous = [g for g in check(Dossier()) if g.is_lock]
    assert verrous, "un dossier vierge doit porter des verrous"
    assert all(g.blocking for g in verrous)


# --------------------------------------------------------------------------
# Les deux causes, et les deux actions
# --------------------------------------------------------------------------

def test_the_escape_cause_is_required_as_much_as_the_occurrence_one():
    """⚠️ Le trou n° 1 des 8D réels : on dit pourquoi le défaut est né, jamais
    pourquoi les contrôles l'ont laissé passer."""
    assert "d4.no_escape_cause" in _codes(_dossier(d4={"escape": ""}))
    assert "d4.no_occurrence_cause" in _codes(_dossier(d4={"occurrence": ""}))


def test_a_cause_alone_does_not_unlock_the_permanent_actions():
    """Une seule des deux causes ne suffit pas à étayer le D4."""
    assert "d5.locked" in _codes(_dossier(d4={"escape": ""}))


def test_a_chain_that_stops_on_a_person_locks_the_permanent_actions():
    """⚠️ Le contrôle qui donne son sens à l'étape 2.

    La cause est énoncée, les deux champs du D4 sont remplis — mais la chaîne
    s'arrête sur une personne. Sans ce verrou, la chaîne de pourquoi ne
    serait qu'un ornement décoratif à côté d'un champ de texte.
    """
    boiteuse = [
        {"statement": "Le connecteur perd le contact", "nature": "technical"},
        {"statement": "Le couple appliqué est trop faible", "nature": "technical"},
        {"statement": "L'opérateur n'a pas respecté la consigne", "nature": "person"},
    ]
    dossier = _dossier(d4={"occurrence_chain": boiteuse})
    codes = _codes(dossier)
    assert "d4.chain_ends_on_person" in codes
    assert "d5.locked" in codes, "une cause mal étayée doit verrouiller le D5"
    assert is_closable(dossier) is False


def test_a_chain_finding_names_which_cause_it_targets():
    """Deux chaînes par D4 : un constat sans créneau serait inexploitable."""
    dossier = _dossier(d4={"escape_chain": []})
    vises = [g for g in check(dossier) if g.code.startswith("d4.chain")]
    assert vises and all(g.slot == "escape" for g in vises)
    assert slot_label("escape", "fr") != slot_label("escape", "en")


def test_an_unstated_cause_does_not_also_get_a_chain_complaint():
    """Dire « la cause manque » ET « sa chaîne manque » serait redondant."""
    codes = _codes(_dossier(d4={"escape": "", "escape_chain": []}))
    assert "d4.no_escape_cause" in codes
    assert "d4.chain_missing" not in codes


def test_a_permanent_action_is_required_on_each_cause():
    assert "d5.no_action_on_escape" in _codes(_dossier(d5={"on_escape": ""}))
    assert "d5.no_action_on_occurrence" in _codes(_dossier(d5={"on_occurrence": ""}))


def test_what_is_not_affected_is_required():
    """Le champ que personne ne remplit, et qui sépare une cause d'une coïncidence."""
    assert "d2.no_is_not" in _codes(_dossier(d2={"is_not": ""}))


def test_validation_demands_evidence_not_an_intention():
    assert "d6.no_evidence" in _codes(_dossier(d6={"evidence": ""}))


def test_prevention_demands_a_reference_document():
    assert "d7.no_systemic_update" in _codes(_dossier(d7={"systemic_update": ""}))


def test_lessons_learned_stay_optional():
    """Asymétrie assumée : exiger ce champ ajouterait de la bureaucratie."""
    assert _codes(_dossier(d7={"lessons": ""})) == []


# --------------------------------------------------------------------------
# La clôture — la seule discipline qui juge les autres
# --------------------------------------------------------------------------

def test_premature_closure_is_reported():
    codes = _codes(_dossier(d4={"escape": ""}))
    assert "d8.premature_closure" in codes
    assert [g for g in check(_dossier(d4={"escape": ""}))
            if g.code == "d8.premature_closure"][0].blocking


def test_an_unfinished_case_left_open_says_nothing_about_closure():
    """Rappeler qu'un dossier en cours n'est pas clos serait du bruit."""
    codes = _codes(_dossier(d4={"escape": ""}, d8={"claimed_closed": False}))
    assert not [c for c in codes if c.startswith("d8.")]


def test_a_complete_case_left_open_is_reported():
    assert _codes(_dossier(d8={"claimed_closed": False})) == ["d8.not_closed"]


def test_closure_needs_a_date():
    assert _codes(_dossier(d8={"closed_on": ""})) == ["d8.no_closure_date"]


def test_the_right_to_close_is_computed_not_claimed():
    """⚠️ `is_closable` ne dit pas que le dossier EST clos — qu'il a le droit."""
    assert is_closable(build_dossier(_full())) is True
    # La prétention seule ne donne aucun droit.
    assert is_closable(_dossier(d4={"escape": ""})) is False
    # Et l'absence de prétention n'en retire aucun.
    assert is_closable(_dossier(d8={"claimed_closed": False})) is True


# --------------------------------------------------------------------------
# États, robustesse, et la règle des identifiants
# --------------------------------------------------------------------------

def test_status_names_every_discipline():
    etats = status(Dossier())
    assert list(etats) == DISCIPLINE_ORDER
    assert etats["d2"] == "empty"
    assert etats["d5"] == "locked"
    assert etats["d8"] == "complete", "un D8 muet n'est pas un D8 fautif"

    complet = status(build_dossier(_full()))
    assert set(complet.values()) == {"complete"}

    partiel = status(_dossier(d2={"is_not": ""}))
    assert partiel["d2"] == "incomplete"
    assert partiel["d1"] == "complete"


def test_empty_is_not_incomplete():
    assert is_empty(Dossier(), "d2") is True
    assert is_empty(_dossier(d2={"is_not": ""}), "d2") is False


def test_a_malformed_date_is_treated_as_absent():
    """⚠️ Un 31 février inventé dans un engagement client vaut moins que rien."""
    for mauvaise in ("2026-02-31", "30/06/2026", "bientôt", "2026-13-01"):
        codes = _codes(_dossier(d3={"due_date": mauvaise}))
        assert "d3.no_due_date" in codes, f"« {mauvaise} » aurait dû être écartée"


def test_a_payload_from_a_browser_is_never_trusted():
    """Un champ absent, en trop ou du mauvais type devient un champ vide."""
    charge = _full()
    charge["d2"] = ["pas", "un", "objet"]
    charge["d4"] = {"occurrence": None, "escape": 42, "inconnu": "ignoré"}
    charge["d1"] = {"owner": {"nested": 1}, "members": "seul"}
    dossier = build_dossier(charge)
    assert dossier.d2.what == ""
    assert dossier.d4.escape == "42", "un nombre reste une saisie, il n'est pas rejeté"
    assert dossier.d1.owner == ""
    assert dossier.d1.members == ("seul",)
    check(dossier)  # ne doit pas lever


def test_a_dossier_is_required():
    for mauvais in ({}, "8D", None, 3):
        try:
            check(mauvais)
        except InvalidDossier:
            continue
        raise AssertionError(f"{mauvais!r} aurait dû être refusé")


def test_unknown_discipline_is_rejected():
    for mauvaise in ("d9", "D1", "", "d4.locked"):
        try:
            discipline_label(mauvaise)
        except InvalidDossier:
            continue
        raise AssertionError(f"« {mauvaise} » aurait dû être refusée")


def test_gaps_carry_identifiers_never_labels():
    """⚠️ La leçon payée quatre fois par le chantier d'internationalisation.

    Un constat voyage sous forme d'identifiant ; son texte se demande au
    catalogue au moment de l'affichage.
    """
    tous = check(Dossier()) + check(_dossier(d8={"closed_on": ""}))
    tous += check(_dossier(d4={"escape": ""}))
    assert tous
    for gap in tous:
        assert gap.code.startswith(gap.discipline + ".")
        for langue in ("fr", "en"):
            texte = gap_label(gap, langue)
            assert texte != f"ct.gap.{gap.code}", f"{gap.code} absent du catalogue {langue}"
            assert texte.strip()


def test_every_discipline_is_named_in_both_languages():
    for cle in DISCIPLINE_ORDER:
        for langue in ("fr", "en"):
            texte = discipline_label(cle, langue)
            assert texte != f"ct.discipline.{cle}", f"{cle} absent du catalogue {langue}"
        assert discipline_label(cle, "fr") != discipline_label(cle, "en"), (
            f"{cle} : contre-épreuve — un catalogue anglais vide passerait sinon"
        )


def test_translating_never_changes_the_verdict():
    """Traduire change les mots, jamais le verdict.

    Contre-épreuve du même esprit que `test_translating_never_touches_the_numbers`
    de la TARA : la langue n'entre nulle part dans la décision.
    """
    dossier = _dossier(d2={"is_not": ""}, d8={"claimed_closed": True})
    reference = _codes(dossier)
    for gap in check(dossier):
        gap_label(gap, "en")
    assert _codes(dossier) == reference
    assert is_closable(dossier) is False


# --------------------------------------------------------------------------
# Le contrat servi à l'interface, et le 8D d'exemple
# --------------------------------------------------------------------------

def test_every_gap_the_engine_can_emit_is_served():
    """⚠️ Un constat oublié dans le contrat s'afficherait en identifiant brut.

    On fait émettre au moteur autant de constats que possible, et on vérifie
    qu'aucun n'échappe à la liste servie. La liste étant construite depuis les
    tables, c'est bien le SENS INVERSE qui est éprouvé ici.
    """
    emis = set()
    for dossier in (
        Dossier(),
        build_dossier(mediocre_example()),
        _dossier(d8={"claimed_closed": False}),
        _dossier(d8={"closed_on": ""}),
        _dossier(d3={"due_date": ""}, d7={"systemic_update": ""}),
        _dossier(d5={"on_escape": ""}, d6={"evidence": ""}),
        _dossier(d4={"occurrence_chain": [{"statement": "seul", "nature": "system"}]}),
        _dossier(d4={"escape_chain": [{"statement": "x", "nature": "technical"},
                                      {"statement": "x", "nature": ""},
                                      {"statement": "y", "nature": "technical"}]}),
    ):
        emis.update(g.code for g in check(dossier))

    servis = set(gap_codes())
    assert emis <= servis, f"constats émis mais non servis : {sorted(emis - servis)}"
    assert len(gap_codes()) == len(set(gap_codes())), "un constat est servi deux fois"


def test_the_served_rules_let_the_page_rewrite_nothing():
    """La page lit les règles, elle n'en code aucune."""
    contrat = rules()
    assert contrat["order"] == DISCIPLINE_ORDER
    assert contrat["dependsOn"] == {"d4": "d2", "d5": "d4", "d6": "d5"}
    assert "d3" not in contrat["dependsOn"], "le containment ne dépend de rien"
    assert set(contrat["slots"]) == set(SLOT_ORDER)
    assert contrat["chain"]["minSteps"] == 3
    assert contrat["chain"]["terminal"] == ["process", "system"]
    assert set(contrat["gaps"]) == set(gap_codes())

    # Chaque champ exigé sait quel constat il déclenche.
    for cle, champs in contrat["required"].items():
        assert set(champs) == set(contrat["gapOf"][cle])
        for champ in champs:
            assert contrat["gapOf"][cle][champ] in contrat["gaps"]

    # Et rien n'est servi en identifiant brut.
    for code, texte in contrat["gaps"].items():
        assert texte and texte != f"ct.gap.{code}", f"{code} sans libellé"


def test_the_contract_is_translated_end_to_end():
    fr, en = rules("fr"), rules("en")
    assert fr["labels"] != en["labels"]
    assert fr["gaps"] != en["gaps"]
    assert fr["chain"]["natureLabels"] != en["chain"]["natureLabels"]
    # ⚠️ Traduire change les mots, jamais les règles.
    for champ in ("order", "required", "gapOf", "dependsOn"):
        assert fr[champ] == en[champ], f"« {champ} » a bougé avec la langue"
    assert fr["chain"]["minSteps"] == en["chain"]["minSteps"]
    assert fr["chain"]["terminal"] == en["chain"]["terminal"]


# Écrit à la main : ce que l'exemple DOIT faire dire au moteur. Si cette liste
# change, c'est la valeur pédagogique de la démonstration qui a bougé.
EXAMPLE_EXPECTED = [
    ("d3.no_due_date", ""),
    ("d3.no_effectiveness_check", ""),
    ("d4.no_escape_cause", ""),
    ("d4.chain_ends_on_person", "occurrence"),
    ("d5.locked", ""),
    ("d6.locked", ""),
    ("d7.no_systemic_update", ""),
    ("d8.premature_closure", ""),
]


def test_the_example_is_deliberately_flawed():
    """⚠️ Un exemple parfait ne démontrerait rien.

    Celui-ci est le 8D qu'on reçoit vraiment d'un fournisseur : plausible,
    bien rempli en apparence, **et déclaré clos**. Chaque défaut enseigne une
    règle du moteur — voir l'en-tête de `example.py`.
    """
    dossier = build_dossier(mediocre_example())
    assert [(g.code, g.slot) for g in check(dossier)] == EXAMPLE_EXPECTED
    assert is_closable(dossier) is False


def test_the_example_never_complains_twice_about_the_same_hole():
    """La cause de non-détection est absente : sa chaîne n'est pas réclamée en plus."""
    codes = _codes(build_dossier(mediocre_example()))
    assert "d4.no_escape_cause" in codes
    assert not [c for c in codes if c.startswith("d4.chain") and c != "d4.chain_ends_on_person"]


def test_the_example_teaches_the_same_lesson_in_both_languages():
    """Le moteur ne lisant aucun texte, la démonstration est identique."""
    verdicts = [[(g.code, g.slot) for g in check(build_dossier(mediocre_example(lg)))]
                for lg in ("fr", "en")]
    assert verdicts[0] == verdicts[1] == EXAMPLE_EXPECTED
    # Contre-épreuve : les textes, eux, diffèrent bel et bien.
    assert mediocre_example("fr")["d2"]["what"] != mediocre_example("en")["d2"]["what"]


def test_the_example_leaves_work_for_the_ai():
    """⚠️ Calibrage : des champs remplis mais creux, que la structure ne peut pas refuser.

    « Plusieurs pièces » n'est pas une quantité et « Depuis fin mai » n'est
    pas une date — le moteur ne peut rien en dire, c'est la matière de
    l'étape 5. Si un jour ces champs deviennent irréprochables, l'exemple
    cesse de démontrer que l'IA sert à quelque chose.
    """
    d2 = build_dossier(mediocre_example()).d2
    assert d2.how_many and d2.since and d2.is_not, "ces champs doivent RESTER remplis"
    assert not [c for c in _codes(build_dossier(mediocre_example()))
                if c.startswith("d2.")], "le D2 de l'exemple doit passer le moteur"


def test_no_field_escapes_the_display_order():
    """⚠️ Un champ hors de `FIELD_ORDER` disparaît du classeur client.

    Il s'afficherait à l'écran — la page lit le contrat — mais l'export
    l'ignorerait, sans qu'aucun test le voie. C'est le motif des deux listes
    d'actifs versionnés qui avaient divergé : une règle recopiée à deux
    endroits finit toujours par diverger, alors on n'en garde qu'une.
    """
    from causetrace.model import Chain

    for cle in DISCIPLINE_ORDER:
        bloc = Dossier().discipline(cle)
        declares = set(FIELD_ORDER[cle])
        reels = {
            champ.name for champ in bloc.__dataclass_fields__.values()
            # Les chaînes de pourquoi ont leur propre onglet, pas une ligne.
            if not isinstance(getattr(bloc, champ.name), Chain)
        }
        assert declares == reels, (
            f"{cle} : FIELD_ORDER dit {sorted(declares)}, le modèle porte {sorted(reels)}")

    # Et tout champ exigé est nécessairement affichable.
    for cle, champs in rules()["required"].items():
        assert set(champs) <= set(FIELD_ORDER[cle]), f"{cle} : un champ exigé est invisible"


def test_the_served_fields_match_the_display_order():
    servis = rules()["fields"]
    assert {cle: tuple(v) for cle, v in servis.items()} == FIELD_ORDER


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"  ok    {test.__name__}")
        # ⚠️ On attrape aussi les exceptions, et pas seulement les
        # `AssertionError` : une régression de cette suite lève plus souvent
        # qu'elle n'assère (une cellule vide, un champ disparu), et une suite
        # qui s'interrompt ne dit pas quels autres tests auraient échoué.
        # Même écart assumé que `tests/test_i18n.py`.
        except (AssertionError, Exception) as exc:
            failures += 1
            print(f"  ÉCHEC {test.__name__} : {type(exc).__name__}: {exc}")
    print(f"\n{len(tests) - failures}/{len(tests)} tests passés")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
