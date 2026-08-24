"""Tests du rattachement aux normes et du niveau de signal.

Exécutable sans pytest :  .venv/bin/python3 -B tests/test_regwatch_classify.py

Le drapeau `-B` n'est pas décoratif — voir l'en-tête de `tests/test_asil.py`.

⚠️ **Aucun appel réseau ici**, et c'est structurel : `classify` prend des
chaînes, pas des objets issus d'un fetch. Il n'a aucun moyen d'aller sur
Internet même si on le lui demandait.

⚠️ **La table de référence est faite de titres réellement publiés**, capturés
le 23/08/2026 sur les flux des sources retenues, et les attentes sont
écrites à la main. Un test qui re-dériverait la classification depuis les
listes de marqueurs ne vérifierait que sa propre cohérence — il passerait au
vert avec des marqueurs faux. C'est la même discipline que la table ASIL
recopiée à la main plutôt que recalculée depuis S+E+C.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from regwatch.classify import (  # noqa: E402
    SIGNAL_DRAFT,
    SIGNAL_EVENT,
    SIGNAL_INFO,
    SIGNAL_ORDER,
    SIGNAL_PUBLICATION,
    attaches_to,
    is_noise,
    qualify,
    signal_of,
)
from regwatch.norms import (  # noqa: E402
    NORM_ORDER,
    NORMS,
    InvalidSelection,
    parse_selection,
)

# (titre, catégories du flux, norme visée, signal attendu)
# `None` en signal = l'item ne doit être retenu pour AUCUNE des cinq normes.
REAL_TITLES = [
    # --- globalautoregs.com, champ « Relevant to » de la source ------------
    # ⚠️ Ces quatre lignes sont un VERROU, pas une illustration. Avec un
    # marqueur « wp.29 », les quatre remontaient sous ISO/SAE 21434 alors
    # qu'aucune ne parle de cybersécurité : GlobalAutoRegs étiquette
    # « WP.29 … » l'intégralité de ses documents. Mesuré en production le
    # 24/08/2026, sur une veille réelle.
    ("Glare prevention: Draft recommendation on periodic technical inspections for GRE",
     ["WP.29 Discussion Topic | Glare prevention"], "iso21434", None),
    ("Children left in vehicles: Draft UN Regulation for approval of light vehicles",
     ["WP.29 Regulatory Project | Children left in vehicles"], "iso21434", None),
    ("Simplification of Lighting Regulations: Report of the 73rd (July 2025) session",
     ["UN Regulation No. 48 | Installation of Lighting and Lighting-Signalling Equipment"],
     "iso21434", None),
    # Contre-épreuve : le MÊME gabarit d'étiquette, mais sur le bon règlement.
    # ⚠️ Seule ligne CONSTRUITE de cette table, et elle est signalée comme
    # telle : aucun document R155 ne figurait sur GlobalAutoRegs au moment
    # de la capture. Le titre reprend le gabarit observé (« Sujet : … ») et
    # l'étiquette la forme exacte servie par la source.
    ("Cyber security: Proposal for amendments to UN Regulation No. 155",
     ["UN Regulation No. 155 | Cyber security and cyber security management system"],
     "iso21434", SIGNAL_DRAFT),
    # --- iso27001security.com, flux « ISO27k standards » -------------------
    ("ISO/IEC 27017 (cloud security) updated",
     ["ISO27k standards", "Website", "Control"], "iso27001", SIGNAL_PUBLICATION),
    ("Slimline ISO/IEC 27000 published",
     ["ISO27k standards"], "iso27001", SIGNAL_PUBLICATION),
    ('27000 & 27017 updates "soon-as"',
     ["ISO27k standards", "Control", "Risk"], "iso27001", SIGNAL_PUBLICATION),
    # Rattaché par la CATÉGORIE seule : le titre ne cite aucun numéro.
    ("Updated ISO/IEC Directives",
     ["ISO27k standards", "Risk", "Policy"], "iso27001", SIGNAL_PUBLICATION),
    ("AI security standard at FDIS",
     ["ISO27k standards", "Risk", "AI"], "iso27001", SIGNAL_DRAFT),
    ("AI security standard 27090",
     ["ISO27k standards", "Control", "Risk"], "iso27001", SIGNAL_INFO),
    ("Adversaries as 'interested parties'",
     ["ISO27k standards", "Risk", "Security"], "iso27001", SIGNAL_INFO),
    ("Losing faith in ISO27k",
     ["ISO27k standards", "Security"], "iso27001", SIGNAL_INFO),
    ("Portuguese toolkit materials",
     ["Website", "Security"], "iso27001", None),

    # --- sres.ai, ISO 26262 ------------------------------------------------
    ("ISO 26262 Challenges for ADS: Item Definition and HARA",
     ["Functional Safety"], "iso26262", SIGNAL_INFO),
    ("ISO 26262 Edition 3: Part 3 and Part 4 – Item and System Level",
     ["Functional Safety"], "iso26262", SIGNAL_INFO),
    ("Certificate vs. Certification in ISO 26262 Assessments and Audits: "
     "What You Need to Know",
     ["Functional Safety"], "iso26262", SIGNAL_INFO),
    # Les trois suivants portent la MÊME catégorie et ne parlent pas de la
    # norme. C'est la règle mesurée : une catégorie thématique ne rattache pas.
    ("Quantitative Analysis for Multi-Point Failures",
     ["Functional Safety"], "iso26262", None),
    ("ISO/PAS 8800 Walkthrough (Part 1): Overview of Clauses and Essential "
     "Work Products",
     ["Functional Safety"], "iso26262", None),
    ("Beyond Standards: Why Humanoid Robot Safety Requires What No Framework "
     "Has Codified Yet",
     ["Functional Safety"], "iso26262", None),
    ("SRES Announces New IEC 61508 Training and First Physical AI Safety Week",
     ["News"], "iso26262", None),

    # --- sres.ai, ISO/SAE 21434 -------------------------------------------
    ("ISO/SAE 21434: Why Implement TARA for ADS Systems?",
     ["Autonomous Systems", "Cybersecurity"], "iso21434", SIGNAL_INFO),
    ("Beyond TARA: How STPA Strengthens Automotive Cybersecurity",
     ["Cybersecurity"], "iso21434", SIGNAL_INFO),
    ("Could ISO/SAE 21434 Have Stopped the TeslaLogger Exploit?",
     ["Cybersecurity"], "iso21434", SIGNAL_INFO),
    # Publicité de formation : retenue, mais étiquetée pour ce qu'elle est.
    ("New Training: ISO/SAE 21434:2021, Automotive Cybersecurity Training "
     "– SGS TÜV Saar",
     ["Cybersecurity", "News"], "iso21434", SIGNAL_EVENT),
    ("Vultara and SRES partner to provide automotive security and safety services",
     ["Cybersecurity", "News"], "iso21434", None),
    ("Short series:  ISA/IEC 62443",
     ["Cybersecurity", "Videos"], "iso21434", None),

    # --- intacs.info, ASPICE ----------------------------------------------
    ("iNTACS Procedures and Templates",
     ["News and Updates"], "aspice", SIGNAL_INFO),
    ("INTACS information letter 2026-08",
     ["News and Updates"], "aspice", SIGNAL_INFO),
    ("ASCON Final Chance for Early Bird Registration",
     ["News and Updates"], "aspice", SIGNAL_EVENT),
    ("The North American SPICE Conference CALL FOR PRESENTATIONS IS LIVE!",
     ["News and Updates"], "aspice", SIGNAL_EVENT),
    ("Datenschutzinformation iNTACS e.V.",
     ["News and Updates"], "aspice", None),

    # --- vda-qmc.de, flux abandonné ---------------------------------------
    ("Test", ["Unkategorisiert"], "aspice", None),
]


def test_reference_table():
    """Chaque titre réel tombe sur la norme et le niveau attendus."""
    for title, categories, norm_key, expected in REAL_TITLES:
        got = qualify(title, categories, "", NORMS[norm_key])
        assert got == expected, (
            f"« {title[:60]} » ({norm_key}) : attendu {expected!r}, obtenu {got!r}"
        )


def test_rejected_titles_are_rejected_by_every_norm():
    """Un item écarté ne doit pas ressurgir sous une autre norme.

    Vérifier le rejet sur la seule norme visée laisserait passer un
    rattachement croisé — un item ISO 27001 qui apparaîtrait sous ASPICE.
    """
    for title, categories, _norm_key, expected in REAL_TITLES:
        if expected is not None:
            continue
        for key in NORM_ORDER:
            got = qualify(title, categories, "", NORMS[key])
            assert got is None, (
                f"« {title[:60]} » aurait dû être écarté, retenu sous {key} ({got})"
            )


def test_thematic_category_does_not_attach():
    """La règle mesurée : « Functional Safety » ne rattache pas à l'ISO 26262.

    Sur 14 items réels rangés par leur auteur dans cette catégorie, 2 seulement
    concernaient la norme. Si ce test tombe, c'est que quelqu'un a ajouté la
    catégorie au catalogue — et douze items hors sujet sont entrés avec elle.
    """
    assert not attaches_to(
        "Quantitative Analysis for Multi-Point Failures",
        ["Functional Safety"],
        NORMS["iso26262"],
    )


def test_category_containing_a_marker_does_attach():
    """La contre-épreuve : « ISO27k standards » CONTIENT le marqueur `iso27k`.

    Sans elle, « Updated ISO/IEC Directives » — qui ne cite aucun numéro
    dans son titre — serait perdu. C'est l'écart entre ce test et le
    précédent qui définit la règle : ce n'est pas « être une catégorie » qui
    rattache, c'est contenir un marqueur.
    """
    assert attaches_to("Updated ISO/IEC Directives",
                       ["ISO27k standards"], NORMS["iso27001"])


def test_regulatory_topic_attaches_a_wp29_document():
    """GlobalAutoRegs dit lui-même à quel règlement un document se rattache.

    Son champ « Relevant to » devient les catégories de l'item. Le titre
    d'un document WP.29 ne nomme pas toujours le règlement ; ce libellé, si.
    """
    topics = ["UN Regulation No. 155 | Cyber security and cyber security "
              "management system"]
    assert qualify("Proposal for amendments", topics, "",
                   NORMS["iso21434"]) is not None
    # Contre-épreuve : un autre règlement ne doit rien rattacher.
    autre = ["UN Regulation No. 48 | Installation of Lighting and "
             "Lighting-Signalling Equipment"]
    assert qualify("Proposal for amendments", autre, "",
                   NORMS["iso21434"]) is None


def test_noise_is_rejected_even_when_it_names_the_norm():
    """L'ordre compte : le bruit s'écarte AVANT le rattachement.

    « Datenschutzinformation iNTACS e.V. » cite un marqueur ASPICE valide.
    """
    assert is_noise("Datenschutzinformation iNTACS e.V.")
    assert attaches_to("Datenschutzinformation iNTACS e.V.", [], NORMS["aspice"])
    assert qualify("Datenschutzinformation iNTACS e.V.", [], "",
                   NORMS["aspice"]) is None


def test_noise_detected_by_url_when_the_title_says_nothing():
    assert is_noise("ISO 27001", [], "https://example.org/legal/privacy-notice/")
    assert not is_noise("ISO 27001", [], "https://example.org/news/iso-27001/")


def test_draft_stage_wins_over_publication():
    """Un stade de rédaction cité l'emporte, même sur « published ».

    Un FDIS publié pour vote n'est pas la norme. L'annoncer en
    « Publication » ferait croire à un texte arrêté.
    """
    assert signal_of("FDIS 27090 published for ballot") == SIGNAL_DRAFT
    assert signal_of("ISO/IEC 27017 updated") == SIGNAL_PUBLICATION


def test_publication_wins_over_event():
    """Une conférence sur un amendement reste d'abord un amendement."""
    assert signal_of("Conference on the ISO 26262 amendment") == SIGNAL_PUBLICATION


def test_word_boundaries_are_enforced():
    """Sans frontières, « cd » matcherait « record » et « dis » « display »."""
    assert signal_of("Recorded display of the new dashboard") == SIGNAL_INFO
    assert signal_of("A committee draft is out") == SIGNAL_DRAFT
    # Un numéro plus long ne doit pas déclencher un numéro plus court.
    assert not attaches_to("The 262620 series", [], NORMS["iso26262"])
    assert attaches_to("Update on ISO 26262", [], NORMS["iso26262"])
    # « iso26262 » collé : sans marqueur dédié, aucune frontière ne l'ouvre.
    assert attaches_to("What iso26262 requires", [], NORMS["iso26262"])


def test_case_and_accents_are_folded():
    assert attaches_to("ISO/SAE 21434", [], NORMS["iso21434"])
    assert attaches_to("iso/sae 21434", [], NORMS["iso21434"])
    assert attaches_to("Retour d'expérience CSMS", [], NORMS["iso21434"])
    assert is_noise("Mentions légales")


def test_one_item_can_concern_two_norms():
    """Aligner 26262 et 21434 intéresse les deux veilles, pas une seule."""
    title = "Aligning ISO 26262 and ISO/SAE 21434 in one programme"
    assert qualify(title, [], "", NORMS["iso26262"]) == SIGNAL_INFO
    assert qualify(title, [], "", NORMS["iso21434"]) == SIGNAL_INFO
    assert qualify(title, [], "", NORMS["iso9001"]) is None


def test_signal_of_only_returns_declared_levels():
    """Tout niveau produit doit être affichable : SIGNAL_ORDER fait foi."""
    for title, categories, norm_key, expected in REAL_TITLES:
        got = qualify(title, categories, "", NORMS[norm_key])
        assert got is None or got in SIGNAL_ORDER, f"niveau inconnu : {got!r}"
    assert len(set(SIGNAL_ORDER)) == len(SIGNAL_ORDER), "doublon dans SIGNAL_ORDER"


def test_selection_is_ordered_and_deduplicated():
    """Deux visiteurs qui cochent les mêmes normes ont le même rapport."""
    selection = parse_selection(["iso9001", "ASPICE", " iso9001 "])
    assert [n.key for n in selection] == ["aspice", "iso9001"]

    inverse = parse_selection(["aspice", "iso9001"])
    assert [n.key for n in inverse] == [n.key for n in selection]


def test_unknown_norm_is_refused_not_ignored():
    """Une clé hors catalogue signale un frontend désynchronisé.

    L'ignorer produirait une veille partielle que personne ne remarquerait.
    """
    for bad in (["iso14001"], ["aspice", "iso9002"], ["'; drop table"]):
        try:
            parse_selection(bad)
        except InvalidSelection:
            continue
        raise AssertionError(f"{bad} aurait dû être refusé")


def test_empty_selection_is_refused():
    for empty in ([], ["", "  "], None):
        try:
            parse_selection(empty)
        except InvalidSelection:
            continue
        raise AssertionError(f"{empty!r} aurait dû être refusé")


def test_every_norm_has_markers():
    """Une norme sans marqueur ne remonterait jamais rien, en silence."""
    for key, norm in NORMS.items():
        assert norm.markers, f"{key} n'a aucun marqueur"
        assert norm.label, f"{key} n'a pas de libellé"
        for marker in norm.markers:
            assert marker == marker.lower().strip(), (
                f"{key} : « {marker} » doit être en minuscules, sinon il ne "
                "matchera jamais le texte replié"
            )


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
