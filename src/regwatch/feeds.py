"""Lecture des flux RSS 2.0 et Atom.

Ce module ne connaît ni HTTP ni les sources : il reçoit une **chaîne** XML et
rend des `RawItem`. Ce n'est pas une convention de style, c'est ce qui rend
l'interdit « aucun test ne touche le réseau » **structurel** — ce module n'a
aucun moyen d'aller sur Internet, même si un test le lui demandait.

RSS et Atom sont des spécifications publiques et figées : contrairement à un
parseur HTML, celui-ci ne peut pas « dériver » parce qu'un site a refait sa
maquette. C'est pourquoi les deux formats sont traités ici, alors que les
scrapers de `scrape.py` sont écrits un par un.
"""

import html
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime

_ATOM = "http://www.w3.org/2005/Atom"

# Plafond de sécurité : un flux malveillant ou cassé ne doit pas faire gonfler
# la mémoire du service. Aucun flux réel n'en approche (le plus fourni en
# publie 100).
MAX_ITEMS_PER_FEED = 200


@dataclass(frozen=True)
class RawItem:
    """Un signal repéré, avant classification.

    ⚠️ **Aucun champ de contenu, délibérément.** Le corps d'un article n'est
    ni téléchargé, ni stocké, ni transmis à un modèle : ce qui n'a pas de
    champ ne peut pas fuiter par mégarde. Même discipline que
    `sentinelscan.Hit`, qui n'a aucun champ d'extrait de code, et que
    `threatscope.DamageProposal`, qui n'a ni exposition ni contrôlabilité.

    `published` vaut None quand la source ne donne pas de date exploitable.
    **Jamais de date inventée** : une date fausse ferait entrer ou sortir un
    item de la fenêtre de veille sans que personne ne puisse le vérifier.
    """

    title: str
    url: str
    published: date | None
    source_key: str
    categories: tuple[str, ...] = ()


class FeedError(ValueError):
    """Le document reçu n'est pas un flux exploitable."""


def _text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return re.sub(r"\s+", " ", "".join(element.itertext())).strip()


def _title(element: ET.Element | None) -> str:
    """Titre d'un item, désencodé une seconde fois si besoin.

    Beaucoup de flux échappent deux fois : le XML contient `&amp;#38;`, que
    le parseur XML rend en `&#38;`, qui s'affiche tel quel. Constaté sur un
    titre réel — « 27000 &#38; 27017 updates ». Une passe de plus rend le
    « & » attendu.

    ⚠️ **Conséquence pour la couche de présentation : un titre est du TEXTE,
    jamais du HTML.** Il vient d'un tiers ; il doit être posé via
    `textContent` ou échappé, jamais via `innerHTML`. C'était déjà vrai
    avant ce désencodage — le corriger ne crée pas l'exigence, il la rend
    plus visible.
    """
    return re.sub(r"\s+", " ", html.unescape(_text(element))).strip()


def _parse_rfc822(raw: str) -> date | None:
    """Date d'un `pubDate` RSS : « Tue, 18 Aug 2026 19:43:00 +0000 »."""
    if not raw:
        return None
    try:
        parsed = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if parsed is None:
        return None
    # Les flux mélangent naïf et localisé ; on ramène tout en UTC pour que
    # deux items publiés à la même heure ne tombent pas des jours différents.
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc)
    return parsed.date()


def _parse_iso8601(raw: str) -> date | None:
    """Date d'un `<updated>` Atom : « 2026-08-11T22:02:01+00:00 » ou « …Z »."""
    if not raw:
        return None
    cleaned = raw.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError:
        try:
            return date.fromisoformat(cleaned[:10])
        except ValueError:
            return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc)
    return parsed.date()


def _rss_items(root: ET.Element, source_key: str) -> list[RawItem]:
    items: list[RawItem] = []
    for node in root.findall("./channel/item"):
        title = _title(node.find("title"))
        url = _text(node.find("link")) or _text(node.find("guid"))
        if not title or not url:
            # Entrée bancale : ignorée, jamais fatale. Un flux à moitié cassé
            # doit rendre ses items valides, pas un écran d'erreur.
            continue
        items.append(
            RawItem(
                title=title,
                url=url,
                published=_parse_rfc822(_text(node.find("pubDate"))),
                source_key=source_key,
                categories=tuple(
                    _text(c) for c in node.findall("category") if _text(c)
                ),
            )
        )
    return items


def _atom_entries(root: ET.Element, source_key: str) -> list[RawItem]:
    items: list[RawItem] = []
    for node in root.findall(f"{{{_ATOM}}}entry"):
        title = _title(node.find(f"{{{_ATOM}}}title"))

        url = ""
        for link in node.findall(f"{{{_ATOM}}}link"):
            rel = link.get("rel", "alternate")
            if rel == "alternate" and link.get("href"):
                url = link.get("href", "")
                break
        if not url:
            url = _text(node.find(f"{{{_ATOM}}}id"))

        if not title or not url:
            continue

        # `published` d'abord : `updated` bouge à chaque correction de coquille
        # et ferait ressortir un vieil article comme une nouveauté.
        stamp = _text(node.find(f"{{{_ATOM}}}published")) or _text(
            node.find(f"{{{_ATOM}}}updated")
        )

        items.append(
            RawItem(
                title=title,
                url=url,
                published=_parse_iso8601(stamp),
                source_key=source_key,
                categories=tuple(
                    (c.get("term") or "").strip()
                    for c in node.findall(f"{{{_ATOM}}}category")
                    if (c.get("term") or "").strip()
                ),
            )
        )
    return items


def parse_feed(xml: str, source_key: str) -> list[RawItem]:
    """Lit un flux RSS 2.0 ou Atom et rend ses items, dédupliqués.

    Le format est détecté sur la racine du document, pas sur l'extension ni
    sur le `Content-Type` : un serveur qui annonce `text/html` pour un flux
    valide ne doit pas faire échouer la lecture.

    Raises:
        FeedError: le XML est illisible, ou ce n'est ni du RSS ni de l'Atom.
            Distinguer ce cas d'un flux vide compte : un flux vide dit
            « rien de neuf », un document illisible dit « la source a changé ».
    """
    try:
        root = ET.fromstring((xml or "").strip())
    except ET.ParseError as exc:
        raise FeedError(f"Flux illisible : {exc}") from exc

    tag = root.tag.split("}")[-1].lower()
    if tag == "rss":
        items = _rss_items(root, source_key)
    elif tag == "feed":
        items = _atom_entries(root, source_key)
    else:
        raise FeedError(f"Racine « {tag} » : ni RSS ni Atom.")

    seen: set[tuple[str, str]] = set()
    unique: list[RawItem] = []
    for item in items:
        key = (item.title.lower(), item.url.lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
        if len(unique) >= MAX_ITEMS_PER_FEED:
            break
    return unique
