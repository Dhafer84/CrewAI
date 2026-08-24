"""Tests de la phrase « pourquoi ça compte » — RegWatch, étape 5.

Exécutable sans pytest :  .venv/bin/python3 -B tests/test_regwatch_explain.py

Le drapeau `-B` n'est pas décoratif — voir l'en-tête de `tests/test_asil.py`.

⚠️ **Aucun appel au LLM.** On teste le parseur et l'orchestration sur des
sorties réalistes, pas le modèle. Une suite qui dépend d'un fournisseur
externe ne se lance plus le jour où on en a besoin — et consommerait le quota
gratuit partagé par les trois outils du site.

Ce que cette suite protège avant tout : **l'IA ne décide de rien**. Elle
ajoute une phrase à des lignes déjà retenues par la classification
déterministe. Si un jour elle peut en écarter une, en ajouter une ou changer
un ordre, plusieurs tests d'ici tombent — et c'est le moment de se demander
pourquoi, pas de les ajuster.
"""

import sys
from datetime import date
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from regwatch import explain  # noqa: E402
from regwatch.classify import SIGNAL_ORDER  # noqa: E402
from regwatch.core import WatchItem  # noqa: E402
from regwatch.crew import UNKNOWN  # noqa: E402
from regwatch.explain import (  # noqa: E402
    MAX_EXPLAINED,
    MAX_SENTENCE_LENGTH,
    build_block,
    explain_items,
    parse_explanations,
    select,
)


# Les champs qui ne doivent PAS partir au modèle portent des valeurs
# distinctives : chercher « s » dans un bloc de texte trouverait toujours
# quelque chose et le test ne prouverait rien.
def item(title, signal=SIGNAL_ORDER[0], jour=1, norm="iso9001"):
    return WatchItem(
        norm_key=norm, norm_label="ISO 9001", signal=signal, title=title,
        published=date(2026, 8, jour), source_key="clef-interne-temoin",
        source_label="ISO/TC 176/SC 2", source_tier="officiel",
        url="https://committee.iso.org/url-temoin.html",
    )


# --------------------------------------------------------------------------
# Le parseur
# --------------------------------------------------------------------------

def test_clean_output_is_parsed():
    brut = ("1 || La révision entre en phase de vote : le calendrier se précise.\n"
            "2 || Une mise à jour de la famille ISO27k touche les mesures de sécurité.")
    resultat = parse_explanations(brut, 2)
    assert resultat[0].startswith("La révision entre en phase de vote")
    assert resultat[1].startswith("Une mise à jour")


def test_noise_the_model_adds_anyway():
    """Puces, gras, numérotation, phrase d'introduction, ligne de séparation."""
    brut = (
        "Voici les explications demandées :\n"
        "\n"
        "- **1** || Le stade FDIS signale un texte quasi figé.\n"
        "2) `2` || Le commentaire vient d'un blog, pas d'un normalisateur.\n"
        "---\n"
        "En espérant que cela vous aide."
    )
    resultat = parse_explanations(brut, 2)
    assert resultat[0].startswith("Le stade FDIS")
    assert resultat[1].startswith("Le commentaire vient")


def test_a_missing_line_leaves_a_hole_it_never_shifts():
    """⚠️ Le test le plus important du parseur.

    Si la ligne 2 est illisible, la ligne 3 doit rester à sa place. Un
    décalage attribuerait l'explication d'un signal à un autre — une phrase
    fausse posée sous un titre juste, ce que personne ne verrait.
    """
    brut = ("1 || Phrase du premier.\n"
            "ligne bancale sans séparateur ni numéro\n"
            "3 || Phrase du troisième.")
    resultat = parse_explanations(brut, 3)
    assert resultat == ["Phrase du premier.", "", "Phrase du troisième."]


def test_numbers_outside_the_range_are_ignored():
    """Un modèle qui invente un 9ᵉ item ne doit rien écraser."""
    brut = "1 || Bonne phrase.\n9 || Item qui n'existe pas.\n0 || Numérotation à zéro."
    resultat = parse_explanations(brut, 2)
    assert resultat == ["Bonne phrase.", ""]


def test_a_repeated_number_keeps_the_first_answer():
    brut = "1 || Première réponse.\n1 || Deuxième réponse pour le même item."
    assert parse_explanations(brut, 1) == ["Première réponse."]


def test_sentences_are_capped():
    brut = "1 || " + "mot " * 200
    assert len(parse_explanations(brut, 1)[0]) <= MAX_SENTENCE_LENGTH


def test_empty_output_gives_empty_slots_not_a_crash():
    assert parse_explanations("", 3) == ["", "", ""]
    assert parse_explanations("le modèle a répondu n'importe quoi", 2) == ["", ""]


# --------------------------------------------------------------------------
# La sélection — quand il y a plus de signaux que le plafond
# --------------------------------------------------------------------------

def test_selection_prefers_the_strongest_signals():
    """Publications d'abord : c'est la question que pose l'outil.

    « S'est-il passé quelque chose d'important ? » — une publication répond
    oui, une note d'information non. Expliquer les secondes en laissant les
    premières de côté serait un contresens.
    """
    items = ([item(f"info {i}", SIGNAL_ORDER[3], jour=20) for i in range(MAX_EXPLAINED)]
             + [item("publication", SIGNAL_ORDER[0], jour=1)])
    retenus = select(items)
    assert len(retenus) == MAX_EXPLAINED
    assert len(items) - 1 in retenus, "la publication doit être expliquée"


def test_selection_keeps_the_original_order():
    """Les indices rendus sont croissants : l'affichage n'est pas réordonné."""
    items = [item(f"t{i}", SIGNAL_ORDER[i % 4], jour=i + 1) for i in range(20)]
    retenus = select(items)
    assert retenus == sorted(retenus)
    assert len(retenus) == MAX_EXPLAINED


def test_everything_is_explained_below_the_cap():
    items = [item(f"t{i}") for i in range(4)]
    assert select(items) == [0, 1, 2, 3]


# --------------------------------------------------------------------------
# Ce qui part au modèle
# --------------------------------------------------------------------------

def test_the_model_only_ever_receives_metadata():
    """⚠️ Le corps d'une page n'est ni téléchargé, ni stocké, ni transmis.

    C'est ce qui rend l'étape défendable face à des normes payantes. La
    garantie est structurelle — `WatchItem` n'a aucun champ de contenu — mais
    on vérifie aussi ce qui sort réellement d'ici.
    """
    items = [item("ISO 9001 revision update")]
    bloc = build_block(items, [0])

    assert "ISO 9001 revision update" in bloc
    assert "2026-08-01" in bloc
    assert "ISO/TC 176/SC 2" in bloc
    assert "officiel" in bloc, "le palier doit accompagner le titre"

    # Rien d'autre que les champs de l'item ne doit s'y trouver.
    autorises = {"norm_label", "signal", "title", "published",
                 "source_label", "source_tier"}
    for champ in WatchItem.__dataclass_fields__:
        valeur = getattr(items[0], champ)
        if champ in autorises or not isinstance(valeur, str) or not valeur:
            continue
        assert valeur not in bloc, f"le champ « {champ} » ne doit pas partir au modèle"


# --------------------------------------------------------------------------
# L'orchestration — sans LLM
# --------------------------------------------------------------------------

class _FakeResult:
    def __init__(self, raw):
        self.raw = raw


class _FakeCrew:
    """Remplace le crew : aucune clé, aucun réseau, aucun quota consommé."""

    def __init__(self, raw):
        self.raw = raw
        self.calls = 0

    def kickoff(self):
        self.calls += 1
        return _FakeResult(self.raw)


def _with_crew(raw, items):
    """Exécute explain_items avec un crew simulé, et rend (résultat, crew)."""
    crew = _FakeCrew(raw)
    original = explain.build_crew
    explain.build_crew = lambda block, count, task_callback=None: crew
    try:
        return explain_items(items), crew
    finally:
        explain.build_crew = original


def test_explanation_never_drops_reorders_or_adds():
    """⚠️ Le verrou central : l'IA n'a aucun pouvoir sur ce qui est retenu.

    Même longueur, même ordre, mêmes titres. Seul `why` change. Si ce test
    tombe un jour, c'est que le modèle a gagné un droit de veto sur la
    pertinence — exactement ce que le pipeline interdit.
    """
    items = [item("Alpha"), item("Bravo", jour=2), item("Charlie", jour=3)]
    resultat, _ = _with_crew("1 || Parce que A.\n2 || Parce que B.\n3 || Parce que C.",
                             items)

    assert len(resultat) == len(items)
    assert [i.title for i in resultat] == ["Alpha", "Bravo", "Charlie"]
    assert [i.signal for i in resultat] == [i.signal for i in items]
    assert [i.why for i in resultat] == ["Parce que A.", "Parce que B.", "Parce que C."]


def test_a_single_call_covers_every_item():
    """Un appel par item épuiserait le quota quotidien en une veille."""
    items = [item(f"t{i}", jour=i + 1) for i in range(MAX_EXPLAINED)]
    _, crew = _with_crew("\n".join(f"{i + 1} || phrase {i}" for i in range(MAX_EXPLAINED)),
                         items)
    assert crew.calls == 1, f"{crew.calls} appels au modèle"


def test_an_unusable_answer_leaves_the_line_untouched():
    """Sans phrase, la ligne reste telle quelle — le tableau vaut sans l'IA."""
    items = [item("Alpha"), item("Bravo", jour=2)]
    resultat, _ = _with_crew("1 || Parce que A.", items)
    assert resultat[0].why == "Parce que A."
    assert resultat[1].why == "", "une case vide, pas une phrase inventée"


def test_the_dont_know_marker_is_not_stored_as_an_explanation():
    """« Je ne peux pas me prononcer » n'est pas une explication.

    L'afficher donnerait l'illusion d'une information là où il n'y a qu'un
    intitulé. Mieux vaut ne rien afficher sous ce signal.
    """
    items = [item("Alpha")]
    resultat, _ = _with_crew(f"1 || {UNKNOWN}", items)
    assert resultat[0].why == ""


def test_an_empty_list_is_refused():
    try:
        explain_items([])
    except ValueError:
        return
    raise AssertionError("une liste vide aurait dû être refusée")


def test_the_prompt_demands_french():
    """⚠️ Les intitulés sources sont anglais ou allemands, le site est français.

    Constaté en conditions réelles le 24/08/2026 : sans consigne explicite,
    le modèle répond dans la langue des titres qu'on lui donne, et la page
    affichait douze phrases en anglais. On ne peut pas tester un modèle
    depuis une suite hors ligne — on peut au moins verrouiller la consigne,
    et la poser à deux endroits pour qu'un oubli n'emporte pas tout.
    """
    import inspect

    from regwatch.crew import _make_agent, _output_rule

    assert "FRANÇAIS" in _output_rule(3).upper(), _output_rule(3)
    assert "français" in inspect.getsource(_make_agent).lower(), \
        "la consigne doit vivre aussi dans le rôle de l'agent"


def test_the_module_cannot_reach_the_network():
    """Comme les parseurs : la frontière est structurelle, pas disciplinaire."""
    source = (_ROOT / "src" / "regwatch" / "explain.py").read_text(encoding="utf-8")
    for interdit in ("import requests", "urllib.request", "http.client"):
        assert interdit not in source, f"explain.py touche au réseau : {interdit}"


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
