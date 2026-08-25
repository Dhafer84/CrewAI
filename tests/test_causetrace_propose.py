"""Tests des propositions par IA — Ishikawa 5M et questions discriminantes.

Exécutable sans pytest :  .venv/bin/python3 -B tests/test_causetrace_propose.py

Le drapeau `-B` n'est pas décoratif — voir l'en-tête de `tests/test_asil.py`.

⚠️ **Aucun appel au LLM.** On teste les parseurs sur des sorties réalistes et
les CONSIGNES données au modèle, jamais le modèle lui-même.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from causetrace.crew import SEPARATOR, build_ishikawa_crew, build_questions_crew  # noqa: E402
from causetrace.example import mediocre_example  # noqa: E402
from causetrace.model import Dossier, InvalidDossier, build_dossier  # noqa: E402
from causetrace.propose import (  # noqa: E402
    AXIS_ORDER,
    FAMILY_ORDER,
    MAX_PER_FAMILY,
    CauseHypothesis,
    DiscriminatingQuestion,
    axis_labels,
    family_labels,
    parse_hypotheses,
    parse_questions,
    problem_statement,
    suggest_causes,
)
from causetrace.whychain import TERMINAL_NATURES  # noqa: E402


# --------------------------------------------------------------------------
# Ce que la structure garantit
# --------------------------------------------------------------------------

def test_a_hypothesis_is_never_qualified():
    """⚠️ Le verrou central de l'étape : l'IA propose, elle ne cote pas.

    Qualifier une hypothèse (technique, procédé, système, personne) serait
    coter — et aucun agent de ce catalogue ne cote. Pendant exact de « les
    cartes proposées arrivent vides côté cotation » dans SafetyScope.
    """
    assert set(CauseHypothesis.__dataclass_fields__) == {"family", "text"}
    for interdit in ("nature", "rank", "score", "likelihood", "confidence",
                     "root", "selected"):
        assert interdit not in CauseHypothesis.__dataclass_fields__


def test_a_question_carries_no_answer():
    """Une question ne s'applique pas dans un champ : elle se creuse."""
    assert set(DiscriminatingQuestion.__dataclass_fields__) == {"axis", "question"}
    for interdit in ("answer", "value", "field"):
        assert interdit not in DiscriminatingQuestion.__dataclass_fields__


def test_the_people_family_and_the_chain_rule_do_not_contradict_each_other():
    """⚠️ Cohérence entre l'étape 2 et l'étape 6, vérifiée et non supposée.

    L'Ishikawa propose des pistes « Main-d'œuvre » — légitimes : une personne
    est une hypothèse recevable **au milieu** d'une chaîne. Ce que `whychain`
    interdit, c'est de s'y **arrêter**. Les deux règles se complètent :
    l'Ishikawa ouvre la piste, la chaîne oblige à aller au-delà.
    """
    assert "manpower" in FAMILY_ORDER
    assert "person" not in TERMINAL_NATURES


# --------------------------------------------------------------------------
# Ce qui part au modèle
# --------------------------------------------------------------------------

def test_only_the_problem_description_is_sent():
    """⚠️ Seul le D2 part. Les autres disciplines ne servent pas à chercher
    des causes, et une charge plus large exposerait du texte pour rien."""
    dossier = build_dossier(mediocre_example())
    enonce = problem_statement(dossier)
    assert "capteur" in enonce.lower()
    # Rien du D4, du D7 ni du D1 ne doit s'y trouver.
    assert "Serrage insuffisant" not in enonce
    assert "Sensibilisation" not in enonce
    assert "Mercier" not in enonce


def test_an_undescribed_problem_needs_no_call():
    """Aucun appel au modèle si le D2 est vide — le quota est partagé."""
    try:
        suggest_causes(Dossier())
    except InvalidDossier:
        return
    raise AssertionError("un dossier sans problème décrit aurait dû être refusé")


def test_families_and_axes_travel_by_number():
    """⚠️ « Méthode » reviendrait en « Method » : rien de lexical ne fait contrat."""
    crew = build_ishikawa_crew("un problème", "1. Méthode\n2. Machine", 3)
    consigne = crew.tasks[0].description
    assert "numéro" in consigne
    assert "Le numéro est celui de la liste ci-dessus" in crew.tasks[0].expected_output


# --------------------------------------------------------------------------
# Les parseurs
# --------------------------------------------------------------------------

def test_hypotheses_are_grouped_by_family_in_order():
    brut = (f"3 {SEPARATOR} Lot de connecteurs hors spécification\n"
            f"1 {SEPARATOR} Gamme sans valeur de couple\n"
            f"1 {SEPARATOR} Autocontrôle non prévu au poste\n")
    pistes = parse_hypotheses(brut)
    # L'ordre suit celui des familles, jamais celui de la réponse.
    assert [p.family for p in pistes] == ["method", "method", "material"]
    assert pistes[0].text == "Gamme sans valeur de couple"


def test_the_parser_ignores_an_index_out_of_range():
    """⚠️ « 0 » donne un index de -1, qui désigne le DERNIER élément en Python.

    Le contrôle de bornes est aujourd'hui de la défense en profondeur : les
    parseurs relisent leur dictionnaire par `range(count)`, donc une clé hors
    bornes n'est jamais lue — le retirer ne change rien, mesuré par mutation.
    Ce test pin le comportement pour le jour où quelqu'un indexera
    `FAMILY_ORDER[position]` directement : une ligne « 0 || … » se rangerait
    alors dans « Milieu » sans que rien ne proteste.
    """
    brut = (f"0 {SEPARATOR} hors bornes\n"
            f"9 {SEPARATOR} hors bornes aussi\n"
            f"2 {SEPARATOR} Visseuse non asservie au couple\n")
    pistes = parse_hypotheses(brut)
    assert len(pistes) == 1 and pistes[0].family == "machine"
    assert "hors bornes" not in " ".join(p.text for p in pistes)
    # Et la dernière famille ne récupère jamais l'index négatif.
    assert not [p for p in pistes if p.family == FAMILY_ORDER[-1]]


def test_the_parser_caps_each_family():
    lignes = [f"1 {SEPARATOR} Piste {i}" for i in range(MAX_PER_FAMILY + 4)]
    pistes = parse_hypotheses("\n".join(lignes))
    assert len(pistes) == MAX_PER_FAMILY


def test_duplicates_are_dropped_across_families():
    brut = (f"1 {SEPARATOR} Gamme sans valeur de couple\n"
            f"2 {SEPARATOR}   gamme SANS valeur de couple  \n")
    assert len(parse_hypotheses(brut)) == 1


def test_the_parser_tolerates_bullets_and_noise():
    brut = ("Voici mes pistes :\n\n"
            f"- **1** {SEPARATOR} *Gamme sans valeur de couple*\n"
            "une ligne sans séparateur\n"
            f"  2. {SEPARATOR} `Visseuse non asservie`\n")
    pistes = parse_hypotheses(brut)
    assert [p.text for p in pistes] == ["Gamme sans valeur de couple",
                                        "Visseuse non asservie"]


def test_one_question_per_axis_and_in_order():
    brut = (f"3 {SEPARATOR} Le défaut apparaît-il en dehors du lot de mai ?\n"
            f"1 {SEPARATOR} D'autres capteurs du même véhicule sont-ils touchés ?\n"
            f"1 {SEPARATOR} Une seconde question sur le même axe\n")
    questions = parse_questions(brut)
    assert [q.axis for q in questions] == ["what", "when"]
    assert questions[0].question.startswith("D'autres capteurs")


def test_an_unreadable_answer_never_fails_the_proposal():
    for brut in ("", None, "Je ne sais pas.", "===", f"1 {SEPARATOR} "):
        assert parse_hypotheses(brut) == ()
        assert parse_questions(brut) == ()


# --------------------------------------------------------------------------
# Les consignes
# --------------------------------------------------------------------------

def _ishikawa_prompt(lang="fr") -> str:
    crew = build_ishikawa_crew("un problème", "1. Méthode", 3, lang=lang)
    return " ".join([crew.tasks[0].description, crew.tasks[0].expected_output,
                     crew.agents[0].role, crew.agents[0].goal,
                     crew.agents[0].backstory])


def _questions_prompt(lang="fr") -> str:
    crew = build_questions_crew("un problème", "1. Quoi", lang=lang)
    return " ".join([crew.tasks[0].description, crew.tasks[0].expected_output])


def test_the_prompt_forbids_concluding():
    """Ce sont des hypothèses à vérifier, pas une cause racine désignée."""
    texte = _ishikawa_prompt()
    assert "HYPOTHÈSES à vérifier, pas des conclusions" in texte
    assert "Ne dis jamais laquelle est la cause racine" in texte
    assert "ne les classe pas, ne les note pas" in texte


def test_the_prompt_forbids_qualifying():
    assert "Ne qualifie pas la nature d'une hypothèse" in _ishikawa_prompt()


def test_the_prompt_demands_checkable_hypotheses():
    """Une piste qui ne se vérifie pas ne fait pas avancer un 8D."""
    texte = _ishikawa_prompt()
    assert "contrôlable sur le terrain" in texte
    assert "Problème de qualité" in texte, "le contre-exemple a disparu"


def test_the_questions_prompt_looks_for_contrast():
    """⚠️ C'est le contraste qui distingue cette proposition de la relecture.

    La relecture demande de préciser ce qui est écrit ; ici on cherche ce qui
    aurait pu être touché et ne l'est pas.
    """
    texte = _questions_prompt()
    assert "Cherche le CONTRASTE" in texte
    assert "Ne réponds pas aux questions" in texte


def test_both_prompts_demand_the_output_language():
    assert "EN FRANÇAIS" in _ishikawa_prompt("fr")
    assert "EN ANGLAIS" in _ishikawa_prompt("en")
    assert "EN ANGLAIS" in _questions_prompt("en")


def test_families_and_axes_are_named_in_both_languages():
    for cle, libelles in (("ct.5m", family_labels), ("ct.axis", axis_labels)):
        for langue in ("fr", "en"):
            rendus = libelles(langue)
            for nom, texte in rendus.items():
                assert texte and texte != f"{cle}.{nom}", f"{cle}.{nom} absent en {langue}"
        assert libelles("fr") != libelles("en"), "contre-épreuve : les langues diffèrent"
    assert list(family_labels()) == list(FAMILY_ORDER)
    assert list(axis_labels()) == list(AXIS_ORDER)


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
