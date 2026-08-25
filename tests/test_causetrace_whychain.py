"""Tests de la chaîne de pourquoi.

Exécutable sans pytest :  .venv/bin/python3 -B tests/test_causetrace_whychain.py

Le drapeau `-B` n'est pas décoratif — voir l'en-tête de `tests/test_asil.py`.

Ce qui est vérifié ici tient en une phrase : **une chaîne qui s'arrête sur une
personne n'a pas trouvé de cause.** Et la façon dont c'est vérifié compte
autant que le résultat — par la nature déclarée de chaque marche, jamais en
lisant le texte.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from causetrace.model import MAX_STEPS, NATURE_ORDER, Chain  # noqa: E402
from causetrace.whychain import (  # noqa: E402
    CHAIN_CODES,
    MIN_STEPS,
    TERMINAL_NATURES,
    analyse,
    chain_rules,
    is_sound,
    nature_labels,
)


def _chaine(*marches) -> Chain:
    """`_chaine(("texte", "nature"), …)` — la forme brute que rend le navigateur."""
    return Chain.build([{"statement": s, "nature": n} for s, n in marches])


# Chaîne de référence, écrite à la main : du symptôme vers le système.
SAINE = (
    ("Le connecteur perd le contact en vibration", "technical"),
    ("Le couple appliqué est sous la spécification", "technical"),
    ("La visseuse n'est pas asservie au couple", "process"),
    ("Le standard de poste ne l'exige pas", "system"),
)


def test_a_sound_chain_has_nothing_to_say():
    assert analyse(_chaine(*SAINE)) == []
    assert is_sound(_chaine(*SAINE)) is True


# --------------------------------------------------------------------------
# La règle centrale : où une chaîne a le droit de s'arrêter
# --------------------------------------------------------------------------

def test_a_chain_that_stops_on_a_person_is_refused():
    """« L'opérateur ne s'est pas appliqué » ne se corrige ni ne se prévient."""
    chaine = _chaine(*SAINE[:2], ("L'opérateur n'a pas suivi la consigne", "person"))
    assert "chain_ends_on_person" in analyse(chaine)
    assert is_sound(chaine) is False


def test_a_person_in_the_middle_is_perfectly_legitimate():
    """⚠️ La nuance qui sépare la règle utile de la règle bête.

    « L'opérateur s'est trompé » → *pourquoi ?* → « la gamme admet deux
    lectures » est exactement la bonne pratique. C'est s'y ARRÊTER qui est la
    faute, pas l'évoquer. Si ce test tombe, la règle est devenue une chasse
    au mot plutôt qu'un contrôle de terminaison.
    """
    chaine = _chaine(
        ("Le couple appliqué est sous la spécification", "technical"),
        ("L'opérateur a serré au jugé", "person"),
        ("La gamme n'indique aucune valeur de couple", "process"),
        ("Le standard de rédaction des gammes ne l'impose pas", "system"),
    )
    assert analyse(chaine) == []


def test_a_chain_that_stops_on_a_technical_state_is_refused():
    """Un état technique est le symptôme qu'on cherchait à expliquer."""
    chaine = _chaine(*SAINE[:2], ("Le contact est oxydé", "technical"))
    assert "chain_ends_on_symptom" in analyse(chaine)


def test_both_terminal_natures_are_accepted_and_only_those():
    assert set(TERMINAL_NATURES) == {"process", "system"}
    for nature in NATURE_ORDER:
        chaine = _chaine(*SAINE[:2], ("La dernière marche", nature))
        fautes = [c for c in analyse(chaine) if c.startswith("chain_ends_on")]
        if nature in TERMINAL_NATURES:
            assert not fautes, f"« {nature} » doit pouvoir conclure"
        else:
            assert fautes, f"« {nature} » ne doit pas pouvoir conclure"


# --------------------------------------------------------------------------
# Profondeur, plafond, qualification
# --------------------------------------------------------------------------

def test_a_missing_chain_is_reported():
    for rien in (Chain(), Chain.build([]), Chain.build(None)):
        assert analyse(rien) == ["chain_missing"]


def test_a_chain_too_short_is_reported():
    assert "chain_too_short" in analyse(_chaine(*SAINE[:2]))


def test_the_minimum_is_three_not_five():
    """⚠️ Arbitrage assumé : « cinq pourquoi » est un repère, pas une loi.

    Exiger exactement cinq marches produirait du remplissage à la quatrième
    et à la cinquième — le contraire de ce que l'outil cherche à obtenir.
    """
    assert MIN_STEPS == 3
    trois = _chaine(SAINE[0], SAINE[2], SAINE[3])
    assert analyse(trois) == [], "trois marches suffisent à raisonner"


def test_the_cap_never_hides_work():
    """Écarter les derniers pourquoi en silence ferait croire à une chaîne courte."""
    longue = Chain.build(
        [{"statement": f"pourquoi {i}", "nature": "technical"} for i in range(MAX_STEPS)]
        + [{"statement": "le standard ne l'exige pas", "nature": "system"}]
    )
    assert longue.truncated is True
    assert len(longue) == MAX_STEPS
    assert "chain_truncated" in analyse(longue)


def test_an_unqualified_step_is_reported():
    chaine = _chaine(SAINE[0], ("Un pourquoi sans nature", ""), SAINE[3])
    assert "chain_step_without_nature" in analyse(chaine)


def test_an_unqualified_last_step_is_not_also_called_a_symptom():
    """Deux constats pour un seul défaut, dont un avec un mot faux."""
    chaine = _chaine(SAINE[0], SAINE[1], ("Dernière marche non qualifiée", ""))
    constats = analyse(chaine)
    assert "chain_step_without_nature" in constats
    assert not [c for c in constats if c.startswith("chain_ends_on")]


def test_an_unknown_nature_is_dropped_not_trusted():
    chaine = _chaine(SAINE[0], SAINE[1], ("La dernière", "systémique"))
    assert chaine.steps[-1].nature == ""
    assert "chain_step_without_nature" in analyse(chaine)


def test_blank_lines_are_form_artefacts_not_omissions():
    """Une ligne vide du formulaire n'est pas un pourquoi oublié."""
    chaine = Chain.build([
        {"statement": SAINE[0][0], "nature": SAINE[0][1]},
        {"statement": "   ", "nature": "process"},
        {"statement": SAINE[2][0], "nature": SAINE[2][1]},
        {"statement": SAINE[3][0], "nature": SAINE[3][1]},
    ])
    assert len(chaine) == 3
    assert analyse(chaine) == []


# --------------------------------------------------------------------------
# Répétition
# --------------------------------------------------------------------------

def test_a_repeated_why_is_reported():
    """Une chaîne qui se répète n'a pas avancé d'une marche."""
    chaine = _chaine(
        ("Le couple est trop faible", "technical"),
        ("le couple est trop faible.", "technical"),
        ("Le standard ne l'exige pas", "system"),
    )
    assert "chain_repeats_itself" in analyse(chaine)


def test_a_chain_that_loops_back_is_reported():
    """La répétition se cherche partout, pas seulement entre voisines."""
    chaine = _chaine(
        ("Le contact est perdu", "technical"),
        ("Le couple est trop faible", "technical"),
        ("La gamme est muette", "process"),
        ("Le contact est perdu", "technical"),
    )
    assert "chain_repeats_itself" in analyse(chaine)


# --------------------------------------------------------------------------
# La propriété qui découle du choix de structurer plutôt que de lexicaliser
# --------------------------------------------------------------------------

def test_the_analysis_never_reads_the_text():
    """⚠️ Le test qui verrouille la décision d'architecture de l'étape 2.

    Mêmes natures, textes radicalement différents — français, anglais,
    charabia : verdict identique. C'est ce qui rend l'outil bilingue sans
    effort, et ce qui aurait été impossible avec un lexique de mots de blâme.

    S'il tombe un jour, c'est qu'un lexique s'est glissé dans le moteur.
    """
    natures = [n for _, n in SAINE]
    verdicts = []
    for textes in (
        [s for s, _ in SAINE],
        ["The connector loses contact", "Torque is below spec",
         "The driver is not torque-controlled", "The workstation standard does not require it"],
        ["zzz", "qqq", "www", "xxx"],
    ):
        verdicts.append(analyse(_chaine(*zip(textes, natures))))
    assert verdicts[0] == verdicts[1] == verdicts[2] == []

    # Et la contre-épreuve : seule la nature décide.
    fautive = list(natures)
    fautive[-1] = "person"
    assert analyse(_chaine(*zip(["zzz", "qqq", "www", "xxx"], fautive))) == [
        "chain_ends_on_person"
    ]


def test_the_engine_judges_the_form_never_the_substance():
    """⚠️ La limite exacte du déterminisme, assumée et écrite.

    Du blâme déguisé en cause système passe ; une vraie cause système mal
    qualifiée échoue. Le moteur juge la FORME du raisonnement. C'est
    précisément là que l'IA gagne sa place à l'étape 5 — en contestant le
    fond, en annotation, sans jamais rendre de verdict.
    """
    deguise = _chaine(
        ("Le contact est perdu", "technical"),
        ("Le couple est trop faible", "process"),
        ("L'opérateur est négligent et mal formé", "system"),
    )
    assert analyse(deguise) == [], "le moteur ne lit pas le texte — limite assumée"

    honnete = _chaine(
        ("Le contact est perdu", "technical"),
        ("Le couple est trop faible", "process"),
        ("Le standard de poste n'exige aucun asservissement", "person"),
    )
    assert analyse(honnete) == ["chain_ends_on_person"]


# --------------------------------------------------------------------------
# Robustesse et libellés
# --------------------------------------------------------------------------

def test_garbage_is_never_a_chain():
    for mauvais in (None, "une chaîne", 42, {"statement": "x"}, object()):
        assert analyse(Chain.build(mauvais)) == ["chain_missing"]
        assert analyse(mauvais) == ["chain_missing"]


def test_a_bare_string_stays_an_unqualified_why():
    """Le navigateur peut envoyer un texte nu : c'est un pourquoi à qualifier."""
    chaine = Chain.build(["premier", "deuxième", "troisième"])
    assert len(chaine) == 3
    assert analyse(chaine) == ["chain_step_without_nature"]


def test_natures_are_named_in_both_languages():
    for langue in ("fr", "en"):
        libelles = nature_labels(langue)
        assert list(libelles) == NATURE_ORDER
        for cle, texte in libelles.items():
            assert texte and texte != f"ct.nature.{cle}", f"{cle} absent du catalogue {langue}"
    # Contre-épreuve : un catalogue anglais vide passerait sinon par repli.
    assert nature_labels("fr") != nature_labels("en")


def test_analyse_only_ever_emits_declared_codes():
    """La liste servie à la page doit couvrir tout ce que le moteur sait dire."""
    emis = set()
    for chaine in (
        Chain(), _chaine(*SAINE), _chaine(*SAINE[:1]),
        _chaine(*SAINE[:2], ("fin", "person")),
        _chaine(*SAINE[:2], ("fin", "technical")),
        _chaine(SAINE[0], ("x", ""), ("x", "system")),
        Chain.build([{"statement": f"p{i}", "nature": "technical"} for i in range(9)]),
    ):
        emis.update(analyse(chaine))
    assert emis <= set(CHAIN_CODES), f"non déclarés : {sorted(emis - set(CHAIN_CODES))}"
    assert len(CHAIN_CODES) == len(set(CHAIN_CODES))


def test_the_chain_rules_are_served_not_rewritten():
    contrat = chain_rules("en")
    assert contrat["minSteps"] == MIN_STEPS
    assert contrat["maxSteps"] == MAX_STEPS
    assert contrat["terminal"] == list(TERMINAL_NATURES)
    assert set(contrat["natureLabels"]) == set(NATURE_ORDER)
    assert chain_rules("fr")["natureLabels"] != contrat["natureLabels"]
    assert chain_rules("fr")["terminal"] == contrat["terminal"], "une règle ne se traduit pas"


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
