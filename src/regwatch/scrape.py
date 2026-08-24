"""Parseurs HTML dédiés, un par source.

Même contrat que `feeds` : une **chaîne** en entrée, des `RawItem` en sortie,
aucun accès réseau possible. Les tests tournent donc sur des fragments figés.

⚠️ **Un scraper casse toujours en silence.** Le site refait sa maquette, le
parseur rend `[]`, et l'outil annonce fièrement « rien de neuf ». C'est le
faux négatif le plus grave pour une veille — le même que l'`incomplete_results`
de SentinelScan. La parade n'est pas ici mais dans `core` (étape 3), qui
signale « source dégradée » quand une page volumineuse ne donne aucun item.
Ces parseurs ont donc un devoir simple : **ne jamais inventer** pour éviter
de rendre une liste vide.

Trois parseurs, pas un parseur générique : chaque page a sa structure, et un
« parseur universel » serait un parseur qui ne comprend rien à aucune.
"""

import re
from collections.abc import Callable, Iterator
from datetime import date
from html.parser import HTMLParser
from urllib.parse import urljoin

from .feeds import RawItem

# Mois en toutes lettres, anglais ET allemand : le catalogue VDA écrit
# « Dezember 2023 » et « March 2025 » sur la même page. `strptime` avec %B
# dépend de la locale du serveur — ce qui marcherait sur ma machine et
# échouerait sur le VPS. Une table explicite ne dépend de rien.
_MONTHS = {
    "january": 1, "januar": 1, "jan": 1,
    "february": 2, "februar": 2, "feb": 2,
    "march": 3, "marz": 3, "mar": 3, "mrz": 3,
    "april": 4, "apr": 4,
    "may": 5, "mai": 5,
    "june": 6, "juni": 6, "jun": 6,
    "july": 7, "juli": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oktober": 10, "oct": 10, "okt": 10,
    "november": 11, "nov": 11,
    "december": 12, "dezember": 12, "dec": 12, "dez": 12,
}

_Event = tuple


class _BlockParser(HTMLParser):
    """Découpe un document en blocs délimités par une balise d'intérêt.

    Rend, pour chaque bloc, la suite plate de ses événements — début de
    balise avec ses attributs, texte, fin de balise. Assez pour des
    structures tabulaires ; inutile d'embarquer un DOM complet.

    `html.parser` plutôt qu'une expression régulière : les attributs
    d'ISO.org sont en apostrophes simples, ceux de GlobalAutoRegs en
    guillemets, et une regex qui gère les deux gère mal les deux.
    """

    def __init__(self, is_start: Callable[[str, dict], bool]) -> None:
        super().__init__(convert_charrefs=True)
        self._is_start = is_start
        self._depth = 0
        self._current: list[_Event] | None = None
        self._tag = ""
        self.blocks: list[list[_Event]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = {k: (v or "") for k, v in attrs}
        if self._current is None:
            if self._is_start(tag, attributes):
                self._current = [("start", tag, attributes)]
                self._tag = tag
                self._depth = 1
            return
        if tag == self._tag:
            self._depth += 1
        self._current.append(("start", tag, attributes))

    def handle_endtag(self, tag: str) -> None:
        if self._current is None:
            return
        if tag == self._tag:
            self._depth -= 1
            if self._depth == 0:
                self.blocks.append(self._current)
                self._current = None
                return
        self._current.append(("end", tag))

    def handle_data(self, data: str) -> None:
        if self._current is not None and data.strip():
            self._current.append(("text", data))


def _blocks(html: str, is_start: Callable[[str, dict], bool]) -> list[list[_Event]]:
    parser = _BlockParser(is_start)
    parser.feed(html or "")
    parser.close()
    return parser.blocks


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _text(events: list[_Event]) -> str:
    return _clean("".join(e[1] for e in events if e[0] == "text"))


def _subblocks(events: list[_Event], tag: str,
               match: Callable[[dict], bool] | None = None) -> Iterator[list[_Event]]:
    """Itère les sous-blocs délimités par `tag`, à n'importe quelle profondeur."""
    index = 0
    while index < len(events):
        event = events[index]
        if event[0] == "start" and event[1] == tag and (match is None or match(event[2])):
            depth = 1
            end = index + 1
            while end < len(events) and depth:
                nxt = events[end]
                if nxt[0] == "start" and nxt[1] == tag:
                    depth += 1
                elif nxt[0] == "end" and nxt[1] == tag:
                    depth -= 1
                end += 1
            yield events[index + 1:end - 1]
            index = end
            continue
        index += 1


def _links(events: list[_Event]) -> list[tuple[str, str]]:
    """Couples (href, texte du lien), dans l'ordre d'apparition."""
    found: list[tuple[str, str]] = []
    for index, event in enumerate(events):
        if event[0] != "start" or event[1] != "a" or not event[2].get("href"):
            continue
        depth, end = 1, index + 1
        while end < len(events) and depth:
            nxt = events[end]
            if nxt[0] == "start" and nxt[1] == "a":
                depth += 1
            elif nxt[0] == "end" and nxt[1] == "a":
                depth -= 1
            end += 1
        found.append((event[2]["href"], _text(events[index + 1:end - 1])))
    return found


def _attribute(events: list[_Event], tag: str, name: str) -> str:
    for event in events:
        if event[0] == "start" and event[1] == tag and event[2].get(name):
            return event[2][name]
    return ""


def _month_year(text: str) -> date | None:
    """« Dezember 2023 » ou « March 2025 » → 1er du mois.

    ⚠️ Le jour est une **convention explicite**, pas une donnée : le
    catalogue VDA ne date qu'au mois. On prend le 1er, ce qui vieillit l'item
    d'au plus 30 jours et peut le faire sortir de la fenêtre un peu tôt.
    L'inverse — le dernier jour du mois — daterait dans le futur les
    publications du mois en cours. Aucune des deux n'est parfaite ; celle-ci
    est au moins prévisible et écrite.

    Une date à l'année seule (« 2nd Edition 2025 ») rend None : mieux vaut
    un item sans date qu'un 1er janvier arbitraire.
    """
    match = re.search(r"([A-Za-zÄÖÜäöüß]{3,10})\.?\s+((?:19|20)\d{2})", text or "")
    if not match:
        return None
    month = _MONTHS.get(_fold_month(match.group(1)))
    if not month:
        return None
    return date(int(match.group(2)), month, 1)


def _fold_month(name: str) -> str:
    lowered = name.lower()
    for accented, plain in (("ä", "a"), ("ö", "o"), ("ü", "u"), ("ß", "ss")):
        lowered = lowered.replace(accented, plain)
    return lowered


def _day_month_year(text: str) -> date | None:
    """« 20 Aug 26 » ou « 20 Aug 2026 » → date complète."""
    match = re.search(r"\b(\d{1,2})\s+([A-Za-z]{3,10})\.?\s+(\d{2,4})\b", text or "")
    if not match:
        return None
    month = _MONTHS.get(_fold_month(match.group(2)))
    if not month:
        return None
    year = int(match.group(3))
    if year < 100:
        year += 2000
    try:
        return date(year, month, int(match.group(1)))
    except ValueError:
        return None


def _absolute(href: str, base_url: str) -> str:
    if not href:
        return ""
    return urljoin(base_url, href) if base_url else href


def _dedupe(items: list[RawItem]) -> list[RawItem]:
    seen: set[tuple[str, str]] = set()
    unique: list[RawItem] = []
    for item in items:
        key = (item.title.lower(), item.url.lower())
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


# --------------------------------------------------------------------------
# committee.iso.org — pages « News » des comités et sous-comités
#
# Un seul parseur pour TC 176 et TC 176/SC 2 : même gabarit. Tout comité ISO
# qu'on voudra ajouter plus tard n'aura besoin que d'une ligne dans `sources`.
# --------------------------------------------------------------------------

def parse_iso_committee_news(html: str, source_key: str,
                             base_url: str = "") -> list[RawItem]:
    """Actualités d'un comité ISO.

    La date est lue dans l'attribut `datetime` de `<time>`, pas dans le texte
    affiché : le premier est normalisé par le site, le second est de la mise
    en page (« 7 August 2026 ») et changerait avec la langue du visiteur.
    """
    items: list[RawItem] = []

    for block in _blocks(html, lambda tag, attrs:
                         tag == "article" and "media-news" in attrs.get("class", "")):
        published = None
        stamp = _attribute(block, "time", "datetime")
        if stamp:
            try:
                published = date.fromisoformat(stamp.strip()[:10])
            except ValueError:
                published = None

        title, href = "", ""
        for entry in _subblocks(block, "div",
                                lambda attrs: "entry-title" in attrs.get("class", "")):
            links = _links(entry)
            if links:
                href, title = links[0][0], links[0][1]
                break

        if not title or not href:
            continue

        items.append(RawItem(title=title, url=_absolute(href, base_url),
                             published=published, source_key=source_key))

    return _dedupe(items)


# --------------------------------------------------------------------------
# globalautoregs.com — derniers documents WP.29
#
# ⚠️ Le tableau visible TRONQUE les titres (« …periodic technical inspect… »)
# et n'a pas de lien : ses lignes ouvrent une fenêtre modale. C'est donc le
# modal qu'on lit — lui porte le titre entier, la date, le lien canonique et
# le rattachement réglementaire. Lire le tableau serait plus simple et
# donnerait des titres coupés au milieu d'un mot.
# --------------------------------------------------------------------------

_GAR_LABEL = re.compile(r"^(.*?):\s*$")


def _gar_topics(relevant: str) -> tuple[str, ...]:
    """« A, B, and C » → trois libellés.

    ⚠️ On ne découpe QUE sur la virgule. Découper aussi sur « and » couperait
    « Installation of Lighting and Lighting-Signalling Equipment » en deux
    moitiés qui ne veulent plus rien dire. Un « A and B » sans virgule reste
    donc d'un seul tenant — sans importance pour la classification, qui
    cherche des marqueurs à l'intérieur de la chaîne.
    """
    topics = []
    for part in (relevant or "").split(", "):
        cleaned = re.sub(r"^and\s+", "", part.strip())
        if cleaned:
            topics.append(cleaned)
    return tuple(topics)


def parse_globalautoregs(html: str, source_key: str,
                         base_url: str = "") -> list[RawItem]:
    """Documents récents, lus dans les fenêtres modales de la page.

    Le champ « Relevant to » — « UN Regulation No. 155 | Cyber security » —
    devient les `categories` de l'item : c'est la source elle-même qui dit à
    quel règlement le document se rattache, personne n'a à le deviner.
    """
    items: list[RawItem] = []

    for block in _blocks(html, lambda tag, attrs:
                         tag == "div"
                         and re.fullmatch(r"document\d+", attrs.get("id", ""))
                         and "modal" in attrs.get("class", "")):
        title = ""
        fields: dict[str, str] = {}

        for cell in _subblocks(block, "td"):
            labels = [_text(label) for label in
                      _subblocks(cell, "span", lambda a: "gray" in a.get("class", ""))]
            content = _text(cell)
            if not labels:
                # La seule cellule sans étiquette grise est le titre.
                if not title and content:
                    title = content
                continue
            label = _GAR_LABEL.match(labels[0])
            if label:
                fields[label.group(1).strip().lower()] = _clean(
                    content[len(labels[0]):]
                )

        href = ""
        for link, _label in _links(block):
            if re.fullmatch(r"/documents/\d+", link):
                href = link
                break

        if not title or not href:
            continue

        items.append(RawItem(
            title=title,
            url=_absolute(href, base_url),
            published=_day_month_year(fields.get("document date", "")),
            source_key=source_key,
            categories=_gar_topics(fields.get("relevant to", "")),
        ))

    return _dedupe(items)


# --------------------------------------------------------------------------
# vda-qmc.de — catalogue des publications Automotive SPICE
#
# ⚠️ Un catalogue, pas un fil d'actualité : la page re-liste tout à chaque
# fois. Ça marche quand même sans conserver d'état, parce que la fenêtre de
# veille écarte seule ce qui est ancien — une édition de 2017 ne franchit
# jamais 90 jours.
# --------------------------------------------------------------------------

_VDA_VERSION = re.compile(r"Version\s*:\s*(.+?)\s*(?:Sprache|Format|$)", re.I)


def parse_vda_publications(html: str, source_key: str,
                           base_url: str = "") -> list[RawItem]:
    """Publications officielles ASPICE, avec leur version et leur date.

    Une section sans ligne « Version: » n'est pas une publication (bandeau,
    contact, navigation) : elle est ignorée. C'est ce marqueur, et non la
    position dans la page, qui distingue une entrée de catalogue du décor.
    """
    items: list[RawItem] = []

    for block in _blocks(html, lambda tag, attrs:
                         tag == "section" and "b-section" in attrs.get("class", "")):
        version_line = _VDA_VERSION.search(_text(block))
        if not version_line:
            continue

        # ⚠️ `<strong>` OU `<b>` : la même page emploie les deux, et ne
        # chercher que le premier faisait disparaître en silence une
        # publication entière — constaté sur les Guidelines Cybersecurity.
        title = ""
        for tag in ("strong", "b"):
            for emphasised in _subblocks(block, tag):
                title = _text(emphasised)
                if title:
                    break
            if title:
                break
        if not title:
            continue

        version = _clean(version_line.group(1))
        links = _links(block)

        items.append(RawItem(
            title=f"{title} — version {version}",
            url=_absolute(links[0][0], base_url) if links else base_url,
            published=_month_year(version),
            source_key=source_key,
        ))

    return _dedupe(items)


PARSERS: dict[str, Callable[..., list[RawItem]]] = {
    "iso_committee_news": parse_iso_committee_news,
    "globalautoregs": parse_globalautoregs,
    "vda_publications": parse_vda_publications,
}
