"""Tests des parseurs de flux et de pages — RegWatch, étape 2.

Exécutable sans pytest :  .venv/bin/python3 -B tests/test_regwatch_parsing.py

Le drapeau `-B` n'est pas décoratif — voir l'en-tête de `tests/test_asil.py`.

⚠️ **Aucun appel réseau, et c'est structurel** : `feeds` et `scrape` prennent
des chaînes. Les fixtures de `tests/fixtures/regwatch/` sont des fragments
**réels**, capturés le 23/08/2026, non retouchés, avec leur URL d'origine en
en-tête. Leurs champs de contenu ont été vidés : RegWatch ne les lit jamais,
et un dépôt public n'a pas à héberger le corps des articles d'autrui.

⚠️ **Une fixture prouve le parseur, pas que la source a encore cette forme.**
C'est le rôle de `--check-sources` (étape 3), manuel et en ligne. Ici on
vérifie qu'un balisage donné produit les bons items — rien de plus, et c'est
déjà ce qui casse le plus souvent.

Trois défauts ont été trouvés en écrivant ces tests, tous invisibles sur des
exemples inventés : un titre en `<b>` au lieu de `<strong>`, une date à
l'année seule, et un titre tronqué par le site lui-même.
"""

import sys
from datetime import date
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from regwatch.feeds import (  # noqa: E402
    FeedError,
    RawItem,
    parse_feed,
)
from regwatch.scrape import (  # noqa: E402
    PARSERS,
    parse_globalautoregs,
    parse_iso_committee_news,
    parse_vda_publications,
)

FIXTURES = _ROOT / "tests" / "fixtures" / "regwatch"

# Texte qui remplace les champs de contenu dans les fixtures. Il ne doit
# ressortir nulle part : si on le voit, c'est qu'un parseur lit un corps.
PLACEHOLDER = "corps retiré de la fixture"


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# Flux RSS et Atom
# --------------------------------------------------------------------------

# (fixture, [(date, titre, 1re catégorie)]) — écrit à la main d'après les
# flux réels, jamais recalculé depuis le parseur.
FEED_TABLE = [
    ("rss_sres.xml", [
        (date(2026, 8, 11),
         "Safety Standards for Humanoid and General-Purpose Robots: A Practical Guide",
         "Robotics & Physical AI"),
        (date(2026, 8, 7),
         "ISO 26262 Challenges for ADS: Item Definition and HARA",
         "Functional Safety"),
        (date(2026, 8, 3), "SRES SafeStack | August 2026", "News"),
    ]),
    ("rss_iso27ksecurity.xml", [
        (date(2026, 8, 18), "ISO/IEC 27017 (cloud security) updated", "ISO27k standards"),
        (date(2026, 7, 19), "Generic infosec controls", "ISO27k standards"),
        # ⚠️ Titre doublement échappé dans le flux : `&amp;#38;`. Sans la
        # seconde passe de désencodage, on afficherait « 27000 &#38; 27017 ».
        (date(2026, 6, 5), '27000 & 27017 updates "soon-as"', "ISO27k standards"),
    ]),
    ("rss_intacs.xml", [
        (date(2026, 8, 21), "iNTACS Procedures and Templates", "News"),
        (date(2025, 10, 20), "ASCON Final Chance for Early Bird Registration", "News"),
        (date(2025, 2, 12),
         "The North American SPICE Conference CALL FOR PRESENTATIONS IS LIVE!", "News"),
    ]),
]


def test_feed_reference_table():
    """Les trois flux réels rendent exactement les items attendus."""
    for name, expected in FEED_TABLE:
        items = parse_feed(_fixture(name), name)
        assert len(items) == len(expected), f"{name} : {len(items)} items"
        for item, (published, title, category) in zip(items, expected):
            assert item.title == title, f"{name} : titre {item.title!r}"
            assert item.published == published, f"{name} : date de « {title[:40]} »"
            assert item.categories[0] == category, f"{name} : catégorie {item.categories!r}"
            assert item.url.startswith("http"), f"{name} : lien {item.url!r}"


def test_atom_and_rss_describe_the_same_reality():
    """Le même contenu, servi en RSS et en Atom, doit donner les mêmes items.

    Contre-épreuve la plus utile du module : elle compare deux chemins de
    code sur une source réelle, sans qu'aucune attente n'ait à être écrite
    à la main. Les dates viennent pourtant de deux formats différents —
    RFC-822 d'un côté, ISO-8601 de l'autre.
    """
    rss = parse_feed(_fixture("rss_sres.xml"), "sres")
    atom = parse_feed(_fixture("atom_sres.xml"), "sres")

    assert atom, "la fixture Atom est vide"
    for feed_item, atom_item in zip(rss, atom):
        assert feed_item.title == atom_item.title
        assert feed_item.url == atom_item.url
        assert feed_item.published == atom_item.published
        assert feed_item.categories == atom_item.categories


def test_double_escaped_titles_are_decoded():
    """Beaucoup de flux échappent deux fois. Le titre doit rester lisible.

    Cas réel : le XML porte `&amp;#38;`, le parseur XML rend `&#38;`, et
    l'écran affichait « 27000 &#38; 27017 » au lieu de « 27000 & 27017 ».

    ⚠️ Corollaire pour l'étape 4 : un titre est du TEXTE venu d'un tiers. Il
    se pose via `textContent`, jamais via `innerHTML`.
    """
    titres = [item.title for item in
              parse_feed(_fixture("rss_iso27ksecurity.xml"), "x")]
    assert not any("&#" in titre for titre in titres), titres


def test_content_is_never_read():
    """Aucun champ de contenu ne doit ressortir d'un parseur.

    Les fixtures portent volontairement un texte témoin dans leurs
    `description`, `summary` et `content:encoded`. Le voir apparaître
    signifierait que RegWatch republie le corps d'un article — ce que
    l'outil s'interdit.
    """
    for name in ("rss_sres.xml", "rss_iso27ksecurity.xml",
                 "rss_intacs.xml", "atom_sres.xml"):
        assert PLACEHOLDER in _fixture(name), f"{name} : le témoin a disparu"
        for item in parse_feed(_fixture(name), name):
            for value in (item.title, item.url, *item.categories):
                assert PLACEHOLDER not in value, f"{name} : contenu lu dans {value!r}"


def test_raw_item_has_no_content_field():
    """Verrou structurel : ce qui n'a pas de champ ne peut pas fuiter.

    Même garantie que `sentinelscan.Hit`, sans champ d'extrait, et que
    `threatscope.DamageProposal`, sans exposition ni contrôlabilité. Si
    quelqu'un ajoute un jour `summary` ou `content` ici, ce test tombe —
    **c'est le moment de se demander pourquoi, pas d'ajuster le test.**
    """
    champs = set(RawItem.__dataclass_fields__)
    assert champs == {"title", "url", "published", "source_key", "categories"}, champs


def test_broken_xml_raises_instead_of_looking_empty():
    """Un document illisible n'est pas « rien de neuf ».

    Rendre `[]` ici ferait passer une panne de source pour une absence
    d'actualité — le faux négatif fatal d'un outil de veille.
    """
    for garbage in ("<rss><channel><item>", "pas du xml du tout", ""):
        try:
            parse_feed(garbage, "x")
        except FeedError:
            continue
        raise AssertionError(f"{garbage!r} aurait dû lever FeedError")


def test_html_served_as_a_feed_raises():
    """Une page d'erreur servie en 200 ne doit pas passer pour un flux vide."""
    try:
        parse_feed("<html><body><h1>404</h1></body></html>", "x")
    except FeedError:
        return
    raise AssertionError("une page HTML aurait dû lever FeedError")


def test_an_empty_feed_is_not_an_error():
    """Un flux valide sans item dit « rien de neuf » — ça, c'est légitime."""
    vide = '<?xml version="1.0"?><rss version="2.0"><channel><title>x</title></channel></rss>'
    assert parse_feed(vide, "x") == []


def test_malformed_entries_are_skipped_not_fatal():
    """Une entrée sans titre ni lien s'ignore ; les bonnes doivent survivre.

    Construit en retirant les balises `<link>` d'un flux réel, plutôt qu'en
    inventant un flux de toutes pièces.
    """
    ampute = _fixture("rss_sres.xml").replace("<link>", "<absent>").replace(
        "</link>", "</absent>", )
    items = parse_feed(ampute, "x")
    # Sans <link>, le parseur retombe sur <guid> : la source reste lisible.
    assert items, "un flux amputé de ses <link> doit rester exploitable"

    sans_titre = _fixture("rss_sres.xml").replace(
        "<title>Safety Standards for Humanoid and General-Purpose Robots: "
        "A Practical Guide</title>", "<title></title>", 1)
    restants = parse_feed(sans_titre, "x")
    assert len(restants) == 2, f"{len(restants)} items après suppression d'un titre"


def test_duplicates_are_removed():
    doublon = _fixture("rss_iso27ksecurity.xml")
    premier = doublon[doublon.index("<item>"):doublon.index("</item>") + len("</item>")]
    avec_doublon = doublon.replace("</channel>", premier + "</channel>")
    assert len(parse_feed(avec_doublon, "x")) == 3


# --------------------------------------------------------------------------
# committee.iso.org
# --------------------------------------------------------------------------

ISO_TABLE = [
    (date(2026, 8, 7), "ISO 9001 revision update"),
    (date(2026, 6, 24), "ISO 9002 Revision update"),
    (date(2026, 5, 27), "ISO 9002 revision update"),
]


def test_iso_committee_reference_table():
    items = parse_iso_committee_news(
        _fixture("iso_committee_sc2.html"), "sc2",
        "https://committee.iso.org/sites/tc176sc2/home/news.html")

    assert len(items) == len(ISO_TABLE), f"{len(items)} actualités"
    for item, (published, title) in zip(items, ISO_TABLE):
        assert item.title == title
        assert item.published == published


def test_iso_committee_uses_the_machine_date_not_the_displayed_one():
    """La date vient de `datetime='2026-08-07'`, pas du texte « 7 August 2026 ».

    Le texte est de la mise en page : il change avec la langue du site et
    n'a aucune garantie de format. L'attribut, lui, est normalisé.
    """
    html = _fixture("iso_committee_sc2.html")
    assert "7 August 2026" in html, "la fixture doit contenir la date affichée"
    assert "datetime='2026-08-07'" in html, "et la date machine"

    # On casse le seul texte affiché : la date lue ne doit pas bouger.
    trafique = html.replace("7 August 2026", "1 January 1970")
    items = parse_iso_committee_news(trafique, "sc2")
    assert items[0].published == date(2026, 8, 7)


def test_relative_links_are_resolved_against_the_page():
    """Les liens d'ISO.org sont relatifs : sans base, ils ne mènent nulle part."""
    html = _fixture("iso_committee_sc2.html")
    assert "href='/sites/tc176sc2" in html, "la fixture doit porter un lien relatif"

    avec_base = parse_iso_committee_news(
        html, "sc2", "https://committee.iso.org/sites/tc176sc2/home/news.html")
    assert avec_base[0].url.startswith("https://committee.iso.org/sites/tc176sc2/")

    sans_base = parse_iso_committee_news(html, "sc2")
    assert sans_base[0].url.startswith("/sites/"), "sans base, le lien reste tel quel"


# --------------------------------------------------------------------------
# globalautoregs.com
# --------------------------------------------------------------------------

def test_globalautoregs_reads_the_modal_not_the_truncated_menu():
    """⚠️ Le tableau visible TRONQUE les titres. C'est le modal qui fait foi.

    Sans ça, la veille afficherait « …periodic technical inspect… » — coupé
    au milieu d'un mot, et le lien manquerait complètement.
    """
    html = _fixture("globalautoregs_documents.html")
    assert "periodic technical inspect..." in html, \
        "la fixture doit contenir la version tronquée du menu"

    items = parse_globalautoregs(html, "gar", "https://globalautoregs.com/documents")
    assert items[0].title == (
        "Glare prevention: Draft recommendation on periodic technical "
        "inspections for GRE")
    assert not items[0].title.endswith("..."), "titre encore tronqué"
    assert items[0].url == "https://globalautoregs.com/documents/43246"
    assert items[0].published == date(2026, 8, 20)


def test_globalautoregs_topics_become_categories():
    """« Relevant to » dit à quel règlement le document se rattache.

    C'est la source elle-même qui l'affirme — personne n'a à le deviner.
    """
    items = parse_globalautoregs(_fixture("globalautoregs_documents.html"), "gar")
    assert items[0].categories == ("WP.29 Discussion Topic | Glare prevention",)

    # « A, B, and C » → trois libellés, sans « and » collé au troisième.
    trois = items[2].categories
    assert len(trois) == 3, trois
    assert trois[2].startswith("GTR No. 25"), trois[2]

    # ⚠️ Contre-épreuve : « A and B » sans virgule reste d'un seul tenant.
    # Découper sur « and » casserait « Lighting and Lighting-Signalling ».
    assert len(items[1].categories) == 1
    assert "Lighting and Lighting-Signalling Equipment" in items[1].categories[0]


def test_globalautoregs_two_digit_years():
    """« 20 Aug 26 » est une date de 2026, pas de l'an 26."""
    items = parse_globalautoregs(_fixture("globalautoregs_documents.html"), "gar")
    assert all(item.published and item.published.year == 2026 for item in items)


# --------------------------------------------------------------------------
# vda-qmc.de — catalogue des publications
# --------------------------------------------------------------------------

VDA_TABLE = [
    (date(2023, 12, 1), "Automotive SPICE 4.0 — version 4.0 / Dezember 2023"),
    (date(2025, 3, 1),
     "Automotive SPICE for Cybersecurity 2.0 — version 2.0 / March 2025"),
    (None, "Automotive SPICE for Cybersecurity Guidelines — "
           "version 2.0 / 2nd Edition 2025"),
]


def test_vda_reference_table():
    """Mois allemand, mois anglais, titre en <b>, date à l'année seule.

    Les quatre cas viennent de la même page réelle. Les deux derniers sont
    ceux qui cassent un parseur écrit sur des exemples inventés.
    """
    items = parse_vda_publications(
        _fixture("vda_publications.html"), "vda",
        "https://vda-qmc.de/automotive-spice/automotive-spice-veroeffentlichungen/")

    assert len(items) == len(VDA_TABLE), f"{len(items)} publications"
    for item, (published, title) in zip(items, VDA_TABLE):
        assert item.title == title, item.title
        assert item.published == published, f"{title[:45]} : {item.published}"


def test_vda_reads_a_title_written_in_b_as_well_as_strong():
    """La même page emploie les deux balises. N'en lire qu'une en perdait une."""
    html = _fixture("vda_publications.html")
    assert "<b>Automotive SPICE for Cybersecurity Guidelines</b>" in html
    titres = [item.title for item in parse_vda_publications(html, "vda")]
    assert any(t.startswith("Automotive SPICE for Cybersecurity Guidelines")
               for t in titres), titres


def test_vda_year_only_gives_no_date_rather_than_a_fake_one():
    """« 2nd Edition 2025 » ne dit pas le mois : mieux vaut None qu'un 1er janvier.

    Une date inventée ferait entrer ou sortir l'item de la fenêtre de veille
    sans que personne ne puisse le vérifier.
    """
    items = parse_vda_publications(_fixture("vda_publications.html"), "vda")
    annee_seule = [i for i in items if "2nd Edition 2025" in i.title]
    assert annee_seule, "la fixture doit porter le cas de l'année seule"
    assert annee_seule[0].published is None


def test_vda_ignores_sections_without_a_version():
    """Une section sans « Version: » est du décor, pas une publication."""
    html = _fixture("vda_publications.html")
    assert html.count("<section") == 4, "la fixture doit porter 4 sections"
    assert len(parse_vda_publications(html, "vda")) == 3


# --------------------------------------------------------------------------
# Garde-fou d'architecture
# --------------------------------------------------------------------------

def test_no_parser_can_reach_the_network():
    """« Aucun test ne touche le réseau » doit être structurel, pas discipliné.

    Les parseurs prennent une chaîne. S'ils importaient un client HTTP, la
    tentation d'aller chercher une page manquante existerait — et un test
    finirait par consommer un quota ou échouer hors ligne.
    """
    interdits = ("import requests", "urllib.request", "http.client",
                 "urlopen", "socket")
    for module in ("feeds.py", "scrape.py", "classify.py", "norms.py"):
        source = (_ROOT / "src" / "regwatch" / module).read_text(encoding="utf-8")
        for interdit in interdits:
            assert interdit not in source, f"{module} touche au réseau : « {interdit} »"


def test_every_declared_parser_is_callable_on_its_fixture():
    """`PARSERS` est le contrat que `sources.py` consommera à l'étape 3."""
    fixtures = {
        "iso_committee_news": "iso_committee_sc2.html",
        "globalautoregs": "globalautoregs_documents.html",
        "vda_publications": "vda_publications.html",
    }
    assert set(PARSERS) == set(fixtures), set(PARSERS)
    for name, parser in PARSERS.items():
        items = parser(_fixture(fixtures[name]), name, "https://example.org/page")
        assert items, f"{name} ne rend rien sur sa propre fixture"
        for item in items:
            assert isinstance(item, RawItem)
            assert item.source_key == name


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
