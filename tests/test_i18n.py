"""Tests des catalogues de traduction — étape A1.

Exécutable sans pytest :  .venv/bin/python3 -B tests/test_i18n.py

Le drapeau `-B` n'est pas décoratif — voir l'en-tête de `tests/test_asil.py`.

⚠️ **`t()` est indulgent, cette suite est sévère.** En production une clé
manquante dégrade une ligne ; ici elle fait échouer le test. C'est la seule
répartition tenable : un site vitrine ne doit pas rendre une page blanche
parce qu'une traduction a été oubliée, mais l'oubli ne doit pas non plus
passer inaperçu.

Le test qui compte vraiment est `test_the_pages_match_their_catalogue` : il
compare, caractère par caractère, le texte affiché dans les pages et la
valeur française du catalogue. C'est lui qui garantit que **l'extraction n'a
rien changé à l'écran** — la promesse entière de l'étape A.
"""

import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

import i18n  # noqa: E402
from i18n import (  # noqa: E402
    DEFAULT_LANG,
    LANGUAGES,
    catalogue,
    keys,
    missing_keys,
    normalize,
    orphan_keys,
    placeholders,
    t,
)

SITE = _ROOT / "site"

# Emplacements où une clé peut être référencée.
# `data-i18n` porte le CONTENU d'un élément ; `data-i18n-content` porte
# l'attribut `content` d'une balise <meta> — la description que Google
# affiche sous le lien.
# `data-i18n` porte le CONTENU d'un élément ; `data-i18n-<attribut>` porte
# un attribut traduisible — `content` d'une <meta>, `placeholder` d'un champ.
_KEY_IN_HTML = re.compile(r'data-i18n(?:-\w+)?="([^"]+)"')
# `tr` est l'alias de `t` dans api/main.py — voir le commentaire là-bas.
_KEY_IN_PYTHON = re.compile(r'\b(?:t|tr)\(\s*["\']([a-z](?:[\w.]*\w)?)["\']')
_KEY_IN_JS = re.compile(r'\bT\(\s*["\']([a-z](?:[\w.]*\w)?)["\']')

# ⚠️ Les familles indexées se construisent : `t(f"hara.severity.{n}")`. Le
# scanner en retient le PRÉFIXE littéral et considère comme employée toute
# clé qui en découle.
#
# Limite assumée : une clé morte à l'intérieur d'une famille — un
# `hara.severity.9` qui n'existe pas dans la boucle — passerait inaperçue
# ici. Le contrôle compensatoire est
# `test_the_json_contracts_are_byte_for_byte_unchanged` : une clé absente
# fait rendre la clé elle-même par `t()`, et le contrat cesse aussitôt de
# correspondre à l'instantané.
_KEY_FAMILY = re.compile(r'\b(?:t|tr|T)\(\s*f["\']([a-z][\w.]*?)\{')
# Une famille se construit aussi par CONCATÉNATION côté JavaScript —
# `T('scan.crit.' + level)`. Sans ce motif, le scanner déclarait le préfixe
# inconnu ET les quatre criticités mortes, alors que c'est le mécanisme normal.
_KEY_FAMILY_JS = re.compile(r'\bT\(\s*["\']([a-z][\w.]*\.)["\']\s*\+')
# ⚠️ Une clé ne voyage pas toujours jusqu'à `t()` : depuis le 24/08/2026 les
# erreurs réseau de RegWatch PORTENT une clé, et `core` la compose plus tard
# dans la langue voulue. Les ignorer les faisait passer pour mortes.
_KEY_IN_ERROR = re.compile(r'\b(?:FeedError|FetchError)\(\s*["\']([a-z][\w.]+)["\']')


def _fixture(fr: dict, en: dict):
    """Remplace les catalogues le temps d'un test.

    Éprouver le mécanisme sur un catalogue jouet plutôt que sur le vrai :
    le comportement de `t()` ne doit pas dépendre des chaînes qui se
    trouvent extraites ce jour-là.
    """
    original = dict(i18n._CATALOGUES)
    i18n._CATALOGUES = {"fr": fr, "en": en}
    return original


def _restore(original):
    i18n._CATALOGUES = original


# --------------------------------------------------------------------------
# Cohérence des catalogues
# --------------------------------------------------------------------------

def test_the_two_catalogues_carry_the_same_keys():
    assert missing_keys("en") == [], f"absentes de l'anglais : {missing_keys('en')}"
    assert orphan_keys("en") == [], f"inconnues du français : {orphan_keys('en')}"


def test_french_is_the_source_of_truth():
    """Une clé naît en français. L'anglais s'aligne, jamais l'inverse."""
    assert DEFAULT_LANG == "fr"
    assert set(catalogue("fr")) == keys()


def test_no_value_is_empty():
    for lang in LANGUAGES:
        for cle, valeur in catalogue(lang).items():
            assert valeur.strip(), f"{lang} : « {cle} » est vide"


def test_a_placeholder_mismatch_is_detected():
    """Le détecteur de paramètres fonctionne — prouvé sur un cas jouet.

    ⚠️ Nécessaire parce que `test_placeholders_match_between_languages`
    est **vide aujourd'hui** : aucune chaîne extraite ne porte encore de
    paramètre. Il deviendra porteur à l'étape A4, quand les 303
    concaténations JavaScript seront converties en messages paramétrés.
    Sans ce test-ci, on croirait le garde-fou actif alors qu'il ne
    vérifie rien.
    """
    assert placeholders("Il reste {n} secondes sur {total}") == {"n", "total"}
    assert placeholders("Aucun paramètre") == set()
    assert placeholders("{n} signal") != placeholders("one signal"), \
        "un paramètre perdu à la traduction doit se voir"


def test_placeholders_match_between_languages():
    """⚠️ Un `{n}` oublié dans une traduction donne un texte à trous.

    C'est le défaut de traduction le plus courant et le plus silencieux :
    la page s'affiche, mais le chiffre a disparu.

    ⚠️ Vide tant qu'aucune chaîne extraite ne porte de paramètre — voir
    `test_a_placeholder_mismatch_is_detected`.
    """
    fr, en = catalogue("fr"), catalogue("en")
    # Les clés absentes d'un côté relèvent de
    # `test_the_two_catalogues_carry_the_same_keys` : lever ici masquerait
    # son diagnostic derrière une exception.
    for cle in set(fr) & set(en):
        assert placeholders(fr[cle]) == placeholders(en[cle]), (
            f"« {cle} » : fr {placeholders(fr[cle])} ≠ en {placeholders(en[cle])}"
        )


def test_plural_keys_come_in_pairs():
    """Une forme `.one` sans `.other` casse le pluriel d'un côté seulement."""
    for lang in LANGUAGES:
        cles = set(catalogue(lang))
        for cle in cles:
            if cle.endswith(".one"):
                assert cle[:-4] + ".other" in cles, f"{lang} : {cle} sans .other"
            if cle.endswith(".other"):
                assert cle[:-6] + ".one" in cles, f"{lang} : {cle} sans .one"


# --------------------------------------------------------------------------
# Comportement de t()
# --------------------------------------------------------------------------

def test_french_puts_zero_in_the_singular():
    """« 0 signal retenu » — et non « 0 signaux »."""
    original = _fixture(
        {"x.one": "{n} signal retenu", "x.other": "{n} signaux retenus"},
        {"x.one": "{n} signal kept", "x.other": "{n} signals kept"})
    try:
        assert t("x", "fr", n=0) == "0 signal retenu"
        assert t("x", "fr", n=1) == "1 signal retenu"
        assert t("x", "fr", n=2) == "2 signaux retenus"
    finally:
        _restore(original)


def test_english_puts_zero_in_the_plural():
    """⚠️ La règle n'est PAS la même qu'en français : « 0 signals kept ».

    Transposer la règle française donnerait « 0 signal kept », qui sonne
    faux pour un anglophone. C'est ce genre de détail qui distingue une
    traduction d'une transposition.
    """
    original = _fixture(
        {"x.one": "{n} signal retenu", "x.other": "{n} signaux retenus"},
        {"x.one": "{n} signal kept", "x.other": "{n} signals kept"})
    try:
        assert t("x", "en", n=0) == "0 signals kept"
        assert t("x", "en", n=1) == "1 signal kept"
        assert t("x", "en", n=2) == "2 signals kept"
    finally:
        _restore(original)


def test_an_unknown_key_returns_the_key_and_never_raises():
    """Sur un site vitrine, une page blanche est pire qu'un libellé brut."""
    assert t("cle.qui.nexiste.pas") == "cle.qui.nexiste.pas"
    assert t("cle.qui.nexiste.pas", "en") == "cle.qui.nexiste.pas"


def test_an_untranslated_key_falls_back_to_french():
    """Mieux vaut du français dans une page anglaise qu'un trou."""
    original = _fixture({"seulement.fr": "Texte français"}, {})
    try:
        assert t("seulement.fr", "en") == "Texte français"
    finally:
        _restore(original)


def test_a_missing_parameter_returns_the_text_not_an_exception():
    original = _fixture({"avec.param": "Il reste {n} secondes"}, {})
    try:
        assert t("avec.param", "fr") == "Il reste {n} secondes"
        assert t("avec.param", "fr", n=10) == "Il reste 10 secondes"
    finally:
        _restore(original)


def test_language_labels_are_normalised():
    assert normalize("en-US") == "en"
    assert normalize("EN") == "en"
    assert normalize("de") == DEFAULT_LANG, "une langue non servie retombe sur le français"
    assert normalize(None) == DEFAULT_LANG
    assert normalize("") == DEFAULT_LANG
    assert t("nav.back", "en-US") == t("nav.back", "en")


# --------------------------------------------------------------------------
# Cohérence entre le catalogue et le projet
# --------------------------------------------------------------------------

def _keys_used() -> set[str]:
    """Toutes les clés réellement référencées dans le projet."""
    utilisees: set[str] = set()
    familles: set[str] = set()

    def relever(texte: str, motifs) -> None:
        for motif in motifs:
            utilisees.update(motif.findall(texte))
        familles.update(_KEY_FAMILY.findall(texte))
        familles.update(_KEY_FAMILY_JS.findall(texte))

    for chemin in SITE.glob("*.html"):
        relever(chemin.read_text(encoding="utf-8"), (_KEY_IN_HTML, _KEY_IN_JS))
    # ⚠️ Les scripts partagés du site portent des clés eux aussi. Ne balayer
    # que le HTML faisait passer pour mortes toutes celles de `aistatus.js`.
    for chemin in SITE.glob("*.js"):
        relever(chemin.read_text(encoding="utf-8"), (_KEY_IN_JS,))
    for dossier in ("src", "api", "scripts"):
        for chemin in (_ROOT / dossier).rglob("*.py"):
            if "i18n" in chemin.parts:
                continue
            relever(chemin.read_text(encoding="utf-8"),
                    (_KEY_IN_PYTHON, _KEY_IN_ERROR))

    # Toute clé du catalogue qui découle d'un préfixe construit est employée.
    for cle in keys():
        if any(cle.startswith(prefixe) for prefixe in familles):
            utilisees.add(cle)
    return utilisees


def _resout(cle: str) -> set[str]:
    """Les clés de catalogue que satisfait une référence.

    ⚠️ Une forme plurielle se référence par sa BASE : `t("x", n=3)` va
    chercher `x.one` ou `x.other`. Sans cette résolution, le scanner
    déclarerait la base inconnue et les deux formes mortes — alors que
    c'est le mécanisme normal du pluriel.
    """
    catalogue_fr = keys()
    if cle in catalogue_fr:
        return {cle}
    formes = {f"{cle}.one", f"{cle}.other"} & catalogue_fr
    return formes


def test_every_key_used_in_the_project_exists():
    """Une clé référencée mais absente afficherait la clé au visiteur."""
    inconnues = sorted(cle for cle in _keys_used() if not _resout(cle))
    assert not inconnues, f"référencées mais absentes du catalogue : {inconnues}"


def test_no_key_is_dead():
    """Une clé que plus personne n'emploie finit par mentir.

    Elle survit aux refontes, se désynchronise du reste, et personne ne
    sait plus si elle est traduite correctement puisque personne ne la voit.
    """
    couvertes: set[str] = set()
    for cle in _keys_used():
        couvertes |= _resout(cle)
    mortes = sorted(keys() - couvertes)
    assert not mortes, f"jamais référencées : {mortes}"


def test_the_pages_match_their_catalogue():
    """⚠️ LE test de l'étape A : l'extraction n'a rien changé à l'écran.

    Pour chaque `data-i18n` des pages, le texte inline doit être exactement
    la valeur française du catalogue. Tant que c'est vrai, on peut extraire
    sans risque — et le jour où quelqu'un modifie un libellé dans le HTML
    sans toucher au catalogue, ce test le dit.
    """
    annote = re.compile(r'<([a-z]+)([^>]*?)data-i18n="([^"]+)"([^>]*?)>(.*?)</\1>', re.S)
    verifies = 0

    for chemin in sorted(SITE.glob("*.html")):
        texte = chemin.read_text(encoding="utf-8")
        for _balise, _av, cle, _ap, contenu in annote.findall(texte):
            inline = re.sub(r"\s+", " ", contenu).strip()
            attendu = t(cle, "fr")
            assert inline == attendu, (
                f"{chemin.name} · « {cle} »\n"
                f"   page      : {inline!r}\n"
                f"   catalogue : {attendu!r}"
            )
            verifies += 1

    assert verifies >= 20, f"seulement {verifies} annotations vérifiées"


# --------------------------------------------------------------------------
# Le filet de l'étape A : les contrats n'ont pas bougé
# --------------------------------------------------------------------------

CONTRATS = _ROOT / "tests" / "fixtures" / "i18n" / "contracts_fr.json"


def test_the_json_contracts_are_byte_for_byte_unchanged():
    """⚠️ LE filet de sécurité de l'extraction Python.

    L'instantané a été capturé **avant** la première ligne d'extraction, sur
    le code en production. Tant que les cinq contrats rendus sans argument
    lui sont identiques, le déplacement des libellés vers le catalogue n'a
    rien changé pour les pages — ni un espace, ni une virgule, ni un ordre
    de clés.

    C'est le seul contrôle qui couvre les 66 libellés d'un coup, et il est
    plus fiable que 66 assertions écrites à la main : personne ne peut
    l'ajuster sans s'en rendre compte.
    """
    import json

    from regwatch.sources import source_catalog
    from safetyscope.asil import full_matrix
    from threatscope.analysis import analysis_limits
    from threatscope.bridge import bridge_rule
    from threatscope.rating import full_scales
    from threatscope.treatment import treatment_scales

    actuel = {
        "full_matrix": full_matrix(),
        "full_scales": full_scales(),
        "treatment_scales": treatment_scales(),
        "bridge_rule": bridge_rule(),
        "analysis_limits": analysis_limits(),
        "source_catalog": source_catalog(),
    }
    attendu = json.loads(CONTRATS.read_text(encoding="utf-8"))

    # ⚠️ On compare les SÉRIALISATIONS, pas les objets Python : un tuple et
    # une liste sont deux objets différents pour `!=` alors qu'ils rendent le
    # même JSON. Or c'est le JSON qui fait contrat avec les pages.
    def serialise(valeur):
        return json.dumps(valeur, ensure_ascii=False, sort_keys=True)

    for nom in sorted(attendu):
        assert nom in actuel, f"contrat « {nom} » disparu"
        a, e = serialise(actuel[nom]), serialise(attendu[nom])
        if a != e:
            position = next((i for i, (x, y) in enumerate(zip(a, e)) if x != y),
                            min(len(a), len(e)))
            raise AssertionError(
                f"« {nom} » a changé vers le caractère {position} :\n"
                f"   attendu : …{e[max(0, position - 40):position + 60]}…\n"
                f"   obtenu  : …{a[max(0, position - 40):position + 60]}…"
            )
    assert set(actuel) == set(attendu)


def test_translating_never_touches_the_numbers():
    """⚠️ Traduire change les mots, jamais la calibration.

    C'est l'invariant qui rend l'internationalisation sûre pour ces deux
    outils : la table ASIL, le barème de potentiel d'attaque et la matrice
    de risque sont des **décisions d'ingénierie**, pas de la présentation.
    Si un jour un chiffre diffère entre deux langues, c'est qu'un libellé
    et une donnée ont été mélangés quelque part.
    """
    from safetyscope.asil import full_matrix
    from threatscope.rating import full_scales

    fr_matrice, en_matrice = full_matrix("fr"), full_matrix("en")
    assert fr_matrice["table"] == en_matrice["table"], "la table ASIL a bougé"
    assert fr_matrice["decompositions"] == en_matrice["decompositions"]

    fr_bareme, en_bareme = full_scales("fr"), full_scales("en")
    assert fr_bareme["risk"] == en_bareme["risk"], "la matrice de risque a bougé"
    assert fr_bareme["maxPotential"] == en_bareme["maxPotential"]
    assert fr_bareme["feasibilityByPotential"] == en_bareme["feasibilityByPotential"]
    for cle in fr_bareme["parameters"]:
        points_fr = [n["points"] for n in fr_bareme["parameters"][cle]["levels"]]
        points_en = [n["points"] for n in en_bareme["parameters"][cle]["levels"]]
        assert points_fr == points_en, f"les points de « {cle} » diffèrent"


def test_the_two_languages_really_differ():
    """Contre-épreuve : sans elle, un catalogue anglais vide passerait.

    Un repli intégral sur le français rendrait tous les tests précédents
    verts — et la version anglaise serait en français.
    """
    from threatscope.rating import full_scales

    assert full_scales("fr")["impactOrder"] != full_scales("en")["impactOrder"]
    assert t("nav.back", "fr") != t("nav.back", "en")


CLASSEURS = _ROOT / "tests" / "fixtures" / "i18n" / "workbooks_fr.json"


def test_the_workbooks_are_unchanged_in_french():
    """Le pendant de l'instantané des contrats, pour les quatre exports.

    Les classeurs ne passent par aucun contrat JSON : rien d'autre ne
    verrouille leurs ~450 chaînes. Sans cet instantané, l'extraction du
    texte des exports se ferait à l'aveugle.
    """
    import json
    sys.path.insert(0, str(_ROOT / "tests"))
    from _workbooks import cell_values, workbooks

    attendu = json.loads(CLASSEURS.read_text(encoding="utf-8"))
    actuel = {nom: cell_values(data) for nom, data in workbooks("fr").items()}

    for nom in sorted(attendu):
        for onglet in sorted(attendu[nom]):
            assert onglet in actuel[nom], f"{nom} : onglet « {onglet} » disparu"
            avant, apres = attendu[nom][onglet], actuel[nom][onglet]
            if avant != apres:
                divergence = next(
                    (f"{x!r} → {y!r}" for x, y in zip(avant, apres) if x != y),
                    f"{len(avant)} chaînes → {len(apres)}")
                raise AssertionError(f"{nom} / {onglet} : {divergence}")
        assert set(actuel[nom]) == set(attendu[nom]), f"{nom} : onglets modifiés"


def test_no_key_is_declared_twice():
    """⚠️ Une clé déclarée deux fois écrase la première, en silence.

    Un dictionnaire Python ne proteste pas : la dernière valeur gagne, et
    `t()` rend tranquillement la mauvaise. Vécu à l'étape A3 — la clé
    `tara.calibration`, qui portait le raisonnement de calibration du
    barème, a été écrasée par un titre de section de trois mots. Le
    classeur TARA s'est mis à afficher « Comment ce barème est calibré » à
    la place de dix lignes d'explication.

    Les instantanés l'ont attrapé cette fois-ci ; ce test l'attrape à la
    source, et pour les clés qu'aucun instantané ne couvre.
    """
    for langue in LANGUAGES:
        source = (_ROOT / "src" / "i18n" / f"{langue}.py").read_text(encoding="utf-8")
        declarees = re.findall(r'^    "([\w.]+)":', source, re.M)
        doublons = sorted({c for c in declarees if declarees.count(c) > 1})
        assert not doublons, f"{langue}.py : clés déclarées deux fois — {doublons}"


def test_the_browser_plural_rule_mirrors_the_python_one():
    """⚠️ Deux implémentations du pluriel — elles doivent dire la même chose.

    `site/i18n.js` refait en JavaScript ce que `_plural_suffix` fait en
    Python, parce que les pages composent leurs messages côté navigateur.
    Deux règles qui divergeraient donneraient « 0 signal kept » d'un côté et
    « 0 signals kept » de l'autre, sur la même page.

    Une suite Python ne peut pas exécuter le JavaScript : on verrouille donc
    la **forme** de la règle. La concordance réelle a été vérifiée dans le
    navigateur, valeur par valeur, pour n = 0, 1 et 2 dans les deux langues.
    """
    source = (SITE / "i18n.js").read_text(encoding="utf-8")
    assert "Math.abs(n) < 2" in source, "règle française absente de i18n.js"
    assert "n === 1" in source, "règle anglaise absente de i18n.js"
    # Et la version Python dit bien la même chose. (`_plural_suffix` rend
    # « one » / « other » ; le point est ajouté par `t()`.)
    assert i18n._plural_suffix("fr", 0) == "one", "0 est un singulier en français"
    assert i18n._plural_suffix("en", 0) == "other", "0 est un pluriel en anglais"
    assert i18n._plural_suffix("fr", 1) == i18n._plural_suffix("en", 1) == "one"
    assert i18n._plural_suffix("fr", 2) == i18n._plural_suffix("en", 2) == "other"


def test_every_page_loads_the_catalogue_before_its_own_script():
    """⚠️ L'ordre des scripts n'est pas cosmétique.

    `T()` doit être défini et `window.I18N` peuplé **avant** que le script
    de la page ne s'exécute. Un `<script src>` classique bloque l'analyse du
    document, ce qui le garantit — mais seulement s'il est placé avant.
    """
    for chemin in sorted(SITE.glob("*.html")):
        texte = chemin.read_text(encoding="utf-8")
        catalogue_pos = texte.find('/i18n/fr.js')
        outil_pos = texte.find('/static/i18n.js')
        assert catalogue_pos > 0, f"{chemin.name} ne charge pas le catalogue"
        assert outil_pos > catalogue_pos, f"{chemin.name} : i18n.js avant le catalogue"
        inline = re.search(r"<script>\s*\n", texte)
        if inline:
            assert outil_pos < inline.start(), (
                f"{chemin.name} : le script de page s'exécute avant T()")


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
        except Exception as exc:  # noqa: BLE001
            # Écart assumé avec les autres suites : ici une régression lève
            # plus souvent qu'elle n'assère (clé absente, format cassé). Une
            # suite qui s'interrompt ne dit pas quels autres tests auraient
            # échoué — or c'est justement ce qu'on veut savoir.
            failures += 1
            print(f"  ÉCHEC {test.__name__} : {type(exc).__name__}: {exc}")
    print(f"\n{len(tests) - failures}/{len(tests)} tests passés")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
