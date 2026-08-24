"""Tests de l'orchestration de la veille — RegWatch, étape 3.

Exécutable sans pytest :  .venv/bin/python3 -B tests/test_regwatch_watch.py

Le drapeau `-B` n'est pas décoratif — voir l'en-tête de `tests/test_asil.py`.

⚠️ **Aucun appel réseau.** `fetch.get_text` est remplacé par une fonction qui
sert les fixtures de l'étape 2. Ce n'est pas de la simulation complaisante :
les octets servis sont ceux des vraies sources, seul le transport est court-
circuité. Le reste — fenêtre, classification, déduplication, tri, couverture
— est le code de production.

Ce que cette suite couvre et qu'aucune autre ne voit : **la composition**.
Les parseurs marchent, la classification marche, et pourtant une veille peut
mentir — en présentant une source muette comme une source calme, en retenant
un item sur une date inventée, ou en lisant deux fois la même source.
"""

import sys
from datetime import date, timedelta
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from regwatch import core, fetch  # noqa: E402
from regwatch.config import LOOKBACK_DAYS  # noqa: E402
from regwatch.core import WatchItem, run_watch  # noqa: E402
from regwatch.norms import parse_selection  # noqa: E402
from regwatch.sources import SOURCES  # noqa: E402

FIXTURES = _ROOT / "tests" / "fixtures" / "regwatch"

# Date de référence figée : celle de la capture des fixtures. Toutes les
# attentes ci-dessous sont donc stables dans le temps.
TODAY = date(2026, 8, 24)

# Quelle fixture répond pour quelle source. Les deux comités ISO partagent le
# même gabarit de page — et donc la même fixture, ce qui met la
# déduplication à l'épreuve.
FIXTURE_BY_SOURCE = {
    "intacs": "rss_intacs.xml",
    "vda_spice": "vda_publications.html",
    "sres": "rss_sres.xml",
    "globalautoregs": "globalautoregs_documents.html",
    "iso27ksecurity": "rss_iso27ksecurity.xml",
    "iso_tc176": "iso_committee_sc2.html",
    "iso_tc176sc2": "iso_committee_sc2.html",
}

_URL_TO_FIXTURE = {
    source.url: FIXTURE_BY_SOURCE[source.key] for source in SOURCES
}


class _Server:
    """Sert les fixtures à la place du réseau, et compte les appels."""

    def __init__(self, overrides: dict[str, object] | None = None) -> None:
        self.calls: list[str] = []
        self.overrides = overrides or {}

    def get_text(self, url: str) -> str:
        self.calls.append(url)
        if url in self.overrides:
            answer = self.overrides[url]
            if isinstance(answer, Exception):
                raise answer
            return str(answer)
        return (FIXTURES / _URL_TO_FIXTURE[url]).read_text(encoding="utf-8")


def _watch(keys, overrides=None, today=TODAY):
    """Lance une veille hors ligne et rend (résultat, serveur)."""
    server = _Server(overrides)
    original = fetch.get_text
    core.fetch.get_text = server.get_text
    try:
        return run_watch(parse_selection(keys), today=today), server
    finally:
        core.fetch.get_text = original


def _url_of(key: str) -> str:
    return next(source.url for source in SOURCES if source.key == key)


# --------------------------------------------------------------------------
# Fenêtre de veille
# --------------------------------------------------------------------------

def test_window_keeps_the_recent_and_drops_the_old():
    """iNTACS publie peu : un item récent, deux de l'an passé.

    Les trois sont pertinents et bien datés. Seul le récent doit ressortir —
    sinon la veille répondrait « il s'est passé quelque chose » à propos de
    février 2025.
    """
    result, _ = _watch(["aspice"], overrides={_url_of("vda_spice"): "<html></html>"})
    intacs = [item for item in result.items if item.source_key == "intacs"]
    assert len(intacs) == 1, [item.title for item in intacs]
    assert intacs[0].published == date(2026, 8, 21)


def test_the_window_is_the_configured_one():
    """Un item juste dans la fenêtre y reste ; un jour plus tôt, il en sort."""
    limite = TODAY - timedelta(days=LOOKBACK_DAYS)
    result, _ = _watch(["iso9001"])
    dates = [item.published for item in result.items]
    assert dates, "aucun item retenu"
    assert min(dates) >= limite

    # Contre-épreuve : en avançant la date de référence, le plus ancien sort.
    plus_tard, _ = _watch(["iso9001"], today=min(dates) + timedelta(days=LOOKBACK_DAYS + 1))
    assert min(dates) not in [item.published for item in plus_tard.items]


def test_undated_items_are_reported_never_silently_dropped():
    """Le catalogue VDA date au mois, parfois à l'année seule.

    Un item pertinent qu'on ne peut pas situer dans la fenêtre est écarté —
    mais nommé. Le taire ferait disparaître une publication officielle sans
    que personne ne le sache.
    """
    result, _ = _watch(["aspice"])
    assert result.undated, "l'item sans date exploitable a disparu en silence"
    assert any("Guidelines" in titre for _cle, titre in result.undated), result.undated
    assert all(cle == "vda_spice" for cle, _t in result.undated), result.undated
    assert not any("Guidelines" in item.title for item in result.items)


# --------------------------------------------------------------------------
# Couverture — le cœur du WatchResult
# --------------------------------------------------------------------------

def test_an_unreachable_source_is_named_not_silent():
    """Une source muette doit se voir. C'est la leçon d'`incomplete_results`."""
    result, _ = _watch(
        ["iso9001"],
        overrides={_url_of("iso_tc176"): fetch.FetchError("défi anti-robot")},
    )
    # ⚠️ Des CLÉS, pas des libellés : c'est ce qui permet à l'export et à
    # la page de comparer sans dépendre de la langue.
    assert result.unreachable == ["iso_tc176"]
    assert any("anti-robot" in message for message in result.errors)
    assert result.coverage_is_incomplete, "la couverture doit être signalée incomplète"


def test_a_page_that_parses_to_nothing_is_degraded_not_calm():
    """⚠️ Le faux négatif fatal : 200 OK, page volumineuse, zéro item.

    C'est une maquette qui a changé, pas une absence d'actualité. Sans ce
    contrôle, l'outil annoncerait fièrement « rien de neuf ».
    """
    maquette_changee = "<html><body>" + ("<div>page refaite</div>" * 400) + "</body></html>"
    result, _ = _watch(["iso9001"], overrides={_url_of("iso_tc176"): maquette_changee})

    assert result.degraded == ["iso_tc176"]
    assert any("ne reconnaît plus sa structure" in message for message in result.errors)
    assert result.coverage_is_incomplete


def test_a_small_empty_feed_is_calm_not_degraded():
    """Un flux valide et vide dit « rien de neuf ». Ça, c'est légitime.

    L'asymétrie est assumée : on préfère un faux « dégradé », visible et
    vérifiable, à un faux « rien de neuf », silencieux.
    """
    vide = ('<?xml version="1.0"?><rss version="2.0"><channel>'
            '<title>rien</title></channel></rss>')
    result, _ = _watch(["iso27001"], overrides={_url_of("iso27ksecurity"): vide})
    assert result.degraded == []
    assert result.items == []
    assert not result.coverage_is_incomplete


def test_an_unreadable_feed_is_degraded():
    result, _ = _watch(["iso27001"],
                       overrides={_url_of("iso27ksecurity"): "<rss><channel><item>"})
    assert result.degraded == ["iso27ksecurity"]


def test_a_broken_parser_does_not_kill_the_watch():
    """Une source en échec ne doit pas emporter les autres — ni se taire."""
    result, _ = _watch(
        ["aspice", "iso9001"],
        overrides={_url_of("intacs"): fetch.FetchError("injoignable")},
    )
    assert result.unreachable, "la panne doit être signalée"
    assert result.items, "les autres sources doivent avoir été lues"
    assert result.sources_read == result.sources_total


# --------------------------------------------------------------------------
# Sélection et déduplication
# --------------------------------------------------------------------------

def test_only_the_sources_of_the_selected_norms_are_read():
    """Pas de balayage systématique : cocher une norme n'en lit pas cinq."""
    _, server = _watch(["iso27001"])
    assert server.calls == [_url_of("iso27ksecurity")], server.calls


def test_a_shared_source_is_read_once():
    """SRES sert l'ISO 26262 et la cybersécurité. Deux normes, une lecture.

    Sans la déduplication de `sources_for`, on doublerait le trafic vers un
    tiers et on compterait deux fois une éventuelle panne.
    """
    _, server = _watch(["iso26262", "iso21434"])
    assert server.calls.count(_url_of("sres")) == 1, server.calls


def test_the_same_item_seen_from_two_sources_is_not_duplicated():
    """Les deux comités ISO servent le même gabarit — et parfois la même page.

    Un item identique ne doit apparaître qu'une fois par norme, sinon la
    veille gonfle artificiellement son propre résultat.
    """
    result, server = _watch(["iso9001"])
    assert len(server.calls) == 2, "les deux comités doivent bien être lus"
    urls = [item.url for item in result.items]
    assert len(urls) == len(set(urls)), urls


def test_items_are_sorted_most_recent_first():
    result, _ = _watch(["iso9001", "iso27001", "iso26262"])
    dates = [item.published for item in result.items]
    assert dates == sorted(dates, reverse=True), dates


def test_counts_add_up():
    result, _ = _watch(["iso9001", "iso27001"])
    assert sum(result.count_by_norm().values()) == len(result.items)
    assert sum(result.count_by_signal().values()) == len(result.items)


# --------------------------------------------------------------------------
# Verrous structurels
# --------------------------------------------------------------------------

def test_watch_item_has_no_content_field():
    """Ce qui n'a pas de champ ne peut pas être republié.

    `why` est la phrase produite par l'IA à l'étape 5 — pas un extrait de la
    source. Si un champ de contenu apparaît ici un jour, c'est le moment de
    se demander pourquoi, pas d'ajuster le test.
    """
    champs = set(WatchItem.__dataclass_fields__)
    assert champs == {
        "norm_key", "norm_label", "signal", "title", "published",
        "source_key", "source_label", "source_tier", "url", "why",
    }, champs


def test_the_engine_reaches_the_network_only_through_fetch():
    """Un seul module parle à Internet ; les autres ne peuvent pas.

    Si `core` importait `requests`, la frontière deviendrait déclarative et
    un test finirait un jour par sortir sur le réseau pour de vrai.
    """
    for module in ("core.py", "sources.py", "classify.py", "norms.py",
                   "feeds.py", "scrape.py"):
        source = (_ROOT / "src" / "regwatch" / module).read_text(encoding="utf-8")
        assert "import requests" not in source, f"{module} importe requests"
    passerelle = (_ROOT / "src" / "regwatch" / "fetch.py").read_text(encoding="utf-8")
    assert "import requests" in passerelle, "fetch.py doit être la seule passerelle"


def test_the_user_agent_is_pure_ascii():
    """⚠️ Un accent dans un en-tête HTTP fait répondre 403 à certaines sources.

    Vécu le 24/08/2026 : « démonstration » dans le User-Agent, et
    committee.iso.org refusait l'accès — là précisément où l'on savait déjà
    que www.iso.org bloque les robots. Le diagnostic évident était faux, et
    aurait fait renoncer à la seule source officielle de l'ISO 9001.

    Les valeurs d'en-tête HTTP sont ASCII par spécification. Ce test est le
    seul endroit du projet qui empêche l'erreur de revenir.
    """
    from regwatch.config import USER_AGENT
    assert USER_AGENT.isascii(), USER_AGENT
    assert "+https://" in USER_AGENT, "le UA doit rester identifiable et joignable"


def test_every_source_is_declared_coherently():
    """Le catalogue est une donnée : elle doit tenir debout toute seule."""
    from regwatch.norms import NORMS
    from regwatch.scrape import PARSERS
    from regwatch.sources import tiers

    for source in SOURCES:
        assert source.tier in tiers(), f"{source.key} : palier {source.tier}"
        assert source.url.startswith("https://"), f"{source.key} : {source.url}"
        assert source.note, f"{source.key} n'explique pas ce qu'il vaut"
        assert source.norm_keys, f"{source.key} ne sert aucune norme"
        for key in source.norm_keys:
            assert key in NORMS, f"{source.key} cite la norme inconnue {key}"
        if source.kind == "html":
            assert source.parser in PARSERS, f"{source.key} : parseur {source.parser}"
        else:
            assert source.kind == "rss" and not source.parser


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
