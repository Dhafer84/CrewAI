"""Tests de la relecture d'une discipline par l'IA.

Exécutable sans pytest :  .venv/bin/python3 -B tests/test_causetrace_review.py

Le drapeau `-B` n'est pas décoratif — voir l'en-tête de `tests/test_asil.py`.

⚠️ **Aucun appel au LLM.** On teste le parseur sur des sorties réalistes et
la CONSIGNE donnée au modèle, jamais le modèle lui-même. On ne peut pas
tester un modèle hors ligne ; on peut au moins refuser qu'une consigne
disparaisse — la parade adoptée pour RegWatch le 24/08/2026, après que douze
phrases soient sorties en anglais sur un site francophone.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from causetrace.crew import DEMAND_MARK, SEPARATOR, _output_rule, build_crew  # noqa: E402
from causetrace.example import mediocre_example  # noqa: E402
from causetrace.model import build_dossier  # noqa: E402
from causetrace.review import (  # noqa: E402
    MAX_DEMANDS,
    DisciplineReview,
    FieldReview,
    parse_review,
    review_discipline,
    reviewable_items,
)


def _dossier():
    return build_dossier(mediocre_example())


ITEMS = [
    ("what", "Quoi", "Le capteur perd son signal"),
    ("how_many", "Combien", "Plusieurs pièces"),
    ("is_not", "Pas touché", "Pas d'autre défaut signalé"),
]


# --------------------------------------------------------------------------
# Ce que la structure garantit
# --------------------------------------------------------------------------

def test_a_review_carries_no_verdict():
    """⚠️ Deux champs, et deux seulement.

    Ni note, ni score, ni niveau : dire si un 8D est complet appartient au
    moteur déterministe. Si quelqu'un ajoute un jour un champ de jugement,
    ce test tombe — c'est le moment de se demander pourquoi.
    """
    assert set(FieldReview.__dataclass_fields__) == {"field", "rewritten"}
    for interdit in ("score", "severity", "level", "ok", "verdict", "rating",
                     "complete", "confidence"):
        assert interdit not in FieldReview.__dataclass_fields__


def test_only_written_fields_are_submitted():
    """L'IA ne remplit pas un champ vide : elle relit ce qui est écrit."""
    champs = [cle for cle, _, _ in reviewable_items(_dossier(), "d3")]
    assert "action" in champs, "le champ rempli doit être relu"
    # `due_date` et `effectiveness_check` sont vides dans l'exemple.
    assert "effectiveness_check" not in champs


def test_dates_and_checkboxes_are_never_reviewed():
    """Une date n'a pas de rédaction à améliorer."""
    complet = _dossier()
    assert reviewable_items(complet, "d8") == [], "D8 ne porte qu'une date et une case"
    champs = [cle for cle, _, _ in reviewable_items(complet, "d3")]
    assert "due_date" not in champs


def test_the_chain_of_the_fourth_discipline_is_reviewed():
    """C'est dans la chaîne que vit le raisonnement — donc là qu'on relit."""
    champs = [cle for cle, _, _ in reviewable_items(_dossier(), "d4")]
    assert "occurrence" in champs
    assert "occurrence_chain.1" in champs and "occurrence_chain.3" in champs
    # La cause de non-détection est absente : sa chaîne l'est aussi.
    assert not [c for c in champs if c.startswith("escape")]


def test_a_discipline_without_prose_needs_no_call():
    """Aucun appel au modèle si rien n'est relisible — le quota est partagé."""
    relecture = review_discipline(_dossier(), "d8")
    assert relecture == DisciplineReview("d8")
    assert not relecture


# --------------------------------------------------------------------------
# Le parseur
# --------------------------------------------------------------------------

def test_a_plain_answer_is_parsed():
    brut = (
        f"1 {SEPARATOR} Le capteur de vitesse avant gauche perd son signal\n"
        f"2 {SEPARATOR} 7 pièces sur 1 240 contrôlées\n"
        f"{DEMAND_MARK} {SEPARATOR} Sur quelle période les pièces ont-elles été contrôlées ?\n"
    )
    relecture = parse_review(brut, ITEMS)
    assert [f.field for f in relecture.fields] == ["what", "how_many"]
    assert relecture.demands == ("Sur quelle période les pièces ont-elles été contrôlées ?",)


def test_the_parser_never_shifts():
    """⚠️ Une reformulation attribuée au mauvais champ serait invisible.

    Un texte plausible sous un mauvais libellé ne se remarque pas — c'est
    bien pire qu'une case vide. Même règle que `regwatch.explain`.
    """
    brut = (f"9 {SEPARATOR} hors bornes\n"
            f"0 {SEPARATOR} hors bornes aussi\n"
            f"3 {SEPARATOR} Aucune occurrence sur les autres capteurs\n")
    relecture = parse_review(brut, ITEMS)
    assert [f.field for f in relecture.fields] == ["is_not"]
    assert relecture.fields[0].rewritten == "Aucune occurrence sur les autres capteurs"


def test_an_empty_rewrite_is_dropped():
    """⚠️ Une reformulation vide EFFACERAIT le champ — donc changerait le verdict.

    C'est la seule façon dont l'IA pourrait modifier ce que le moteur dit.
    Elle est fermée.
    """
    for vide in ("", "   ", "**", "``"):
        relecture = parse_review(f"1 {SEPARATOR} {vide}\n", ITEMS)
        assert relecture.fields == (), f"« {vide} » a été retenu comme reformulation"


def test_a_rewrite_identical_to_the_original_is_dropped():
    """Proposer le texte déjà écrit ne ferait cliquer « Appliquer » pour rien."""
    brut = f"1 {SEPARATOR}  le CAPTEUR   perd son signal  \n"
    assert parse_review(brut, ITEMS).fields == ()


def test_the_parser_tolerates_bullets_bold_and_noise():
    brut = (
        "Voici ma relecture :\n\n"
        f"- **1** {SEPARATOR} *Le capteur avant gauche perd son signal en roulage*\n"
        f"  2. {SEPARATOR} `7 pièces sur 1 240`\n"
        "ligne sans séparateur\n"
        f"> {DEMAND_MARK} {SEPARATOR} Depuis quelle date exactement ?\n"
    )
    relecture = parse_review(brut, ITEMS)
    assert [f.field for f in relecture.fields] == ["what", "how_many"]
    assert relecture.fields[1].rewritten == "7 pièces sur 1 240"
    assert relecture.demands == ("Depuis quelle date exactement ?",)


def test_a_repeated_index_keeps_the_first_answer():
    brut = (f"1 {SEPARATOR} Première proposition\n"
            f"1 {SEPARATOR} Seconde proposition\n")
    assert parse_review(brut, ITEMS).fields[0].rewritten == "Première proposition"


def test_demands_are_capped_and_deduplicated():
    lignes = [f"{DEMAND_MARK} {SEPARATOR} Question {i}" for i in range(MAX_DEMANDS + 3)]
    lignes.append(f"{DEMAND_MARK} {SEPARATOR} Question 0")
    relecture = parse_review("\n".join(lignes), ITEMS)
    assert len(relecture.demands) == MAX_DEMANDS
    assert len(set(relecture.demands)) == MAX_DEMANDS


def test_the_order_follows_the_form_not_the_model():
    """L'ingénieur relit dans l'ordre de sa saisie, pas dans celui du modèle."""
    brut = (f"3 {SEPARATOR} Rien sur les autres capteurs\n"
            f"1 {SEPARATOR} Le capteur avant gauche perd son signal en roulage\n")
    assert [f.field for f in parse_review(brut, ITEMS).fields] == ["what", "is_not"]


def test_an_unreadable_answer_never_fails_the_review():
    for brut in ("", None, "Je n'ai rien à dire.", "===", "1 || "):
        relecture = parse_review(brut, ITEMS)
        assert relecture.fields == () and relecture.demands == ()


# --------------------------------------------------------------------------
# La consigne donnée au modèle
# --------------------------------------------------------------------------

def _prompt(lang="fr") -> str:
    crew = build_crew("D2 — Description du problème", "1. Quoi : x", 1, lang=lang)
    tache = crew.tasks[0]
    agent = crew.agents[0]
    return " ".join([tache.description, tache.expected_output,
                     agent.role, agent.goal, agent.backstory])


def test_the_prompt_forbids_inventing_facts():
    """⚠️ Le verrou central : un fait inventé part chez le client.

    La structure ne peut pas l'empêcher — seule la consigne le peut. On ne
    peut pas tester un modèle hors ligne, on peut refuser que la consigne
    disparaisse.
    """
    texte = _prompt()
    assert "N'ajoute AUCUN fait" in texte
    for interdit in ("date", "quantité", "numéro de lot"):
        assert interdit in texte, f"la consigne ne cite plus « {interdit} »"
    assert "jamais dans une reformulation" in texte


def test_the_prompt_forbids_judging():
    """Le verdict appartient au moteur déterministe, pas au modèle."""
    texte = _prompt()
    assert "Ne dis jamais si le dossier est complet" in texte
    assert "ce n'est pas ton rôle" in texte


def test_the_prompt_demands_the_output_language():
    """⚠️ La consigne reste EN FRANÇAIS, seule la sortie change de langue.

    Décision du projet, prise à l'étape B4 : traduire les prompts serait
    risqué pour rien, un modèle suit une consigne de langue explicite quelle
    que soit la langue de la consigne. Mon premier test cherchait
    « IN ENGLISH » — il décrivait une conception que le projet a écartée.
    """
    assert "EN FRANÇAIS" in _output_rule(2, "fr")
    assert "EN ANGLAIS" in _output_rule(2, "en")
    # Et la consigne insiste sur la langue des ENTRÉES — c'est précisément
    # là qu'on s'est fait prendre sur RegWatch le 24/08/2026.
    assert "autre langue" in _output_rule(2, "fr")
    assert "ne recopie pas leur langue" in _output_rule(2, "en")


def test_the_demand_mark_is_not_a_word():
    """⚠️ Un marqueur lexical se ferait TRADUIRE par le modèle.

    Le prompt est en français, la sortie suit la langue du visiteur : un
    « MANQUE » deviendrait « MISSING » et le parseur ne reconnaîtrait plus
    rien. Un « ? » ne se traduit pas.
    """
    assert DEMAND_MARK == "?"
    assert not DEMAND_MARK.isalpha()


def test_the_prompt_asks_to_stay_silent_on_what_is_already_clear():
    assert "Ne reformule pas un champ déjà clair" in _prompt()


def test_the_prompt_asks_what_lies_behind_a_blamed_person():
    """⚠️ Interroger le fond sans le juger — la nuance de l'étape.

    Ce test vérifie que la CONSIGNE est là, pas qu'elle porte : on ne peut
    pas tester un modèle hors ligne.

    ⚠️ Et son effet n'est PAS établi. Deux runs réels le 25/08/2026, un sans
    la consigne et un avec : dans les deux cas le modèle a réclamé des faits
    (valeur de couple, référence de consigne, nombre de pièces) et jamais
    « qu'est-ce qui a rendu ce geste possible ». Le plafond de quatre
    demandes les évince probablement. Un run avant / un run après ne
    mesurent rien — c'est du bruit, et l'ajuster serait du surapprentissage,
    la leçon de l'étape B4.

    Ce qui porte le point, lui, ne dépend pas du modèle : `whychain` signale
    la terminaison sur une personne de façon déterministe, et la consigne
    interdit explicitement au modèle de formuler ce verdict.
    """
    texte = _prompt()
    assert "met en cause une personne" in texte
    assert "rendu ce geste possible" in texte
    assert "Ne dis PAS que la chaîne est fautive" in texte


def test_a_question_is_never_a_reformulation():
    """⚠️ Défaut trouvé en conditions réelles, en anglais, le 25/08/2026.

    Le modèle a rendu ses demandes sur des lignes NUMÉROTÉES au lieu de
    lignes « ? ». Le champ « Depuis quand » se voyait proposer « What is the
    exact date when the issue was first observed? » — et cliquer
    « Appliquer » aurait écrit une **question** dans un document qui part
    chez le client.

    La parade est structurelle, pas un durcissement du prompt : la valeur
    d'un champ de 8D n'est jamais une question. Elle est donc reclassée en
    demande, ce qui est d'ailleurs ce que le modèle voulait dire.
    """
    brut = (f"1 {SEPARATOR} Le capteur avant gauche perd son signal en roulage\n"
            f"2 {SEPARATOR} Combien de pièces sont concernées ?\n")
    relecture = parse_review(brut, ITEMS)
    assert [f.field for f in relecture.fields] == ["what"], (
        "une question a été retenue comme reformulation")
    assert relecture.demands == ("Combien de pièces sont concernées ?",)


def test_a_field_that_is_already_a_question_may_be_rephrased():
    """La contre-épreuve : si l'original est une question, on n'y touche pas."""
    items = [("what", "Quoi", "Le capteur perd-il son signal ?")]
    brut = f"1 {SEPARATOR} Le capteur avant gauche perd-il son signal en roulage ?\n"
    relecture = parse_review(brut, items)
    assert [f.field for f in relecture.fields] == ["what"]
    assert relecture.demands == ()


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"  ok    {test.__name__}")
        # Même écart assumé que les autres suites CauseTrace : une régression
        # ici lève plus souvent qu'elle n'assère.
        except (AssertionError, Exception) as exc:
            failures += 1
            print(f"  ÉCHEC {test.__name__} : {type(exc).__name__}: {exc}")
    print(f"\n{len(tests) - failures}/{len(tests)} tests passés")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
