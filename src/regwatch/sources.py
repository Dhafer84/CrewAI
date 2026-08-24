"""Le catalogue des sources : **où** l'on cherche.

`norms` dit ce qu'on cherche, ce module dit où. La séparation permet
d'ajouter une source à une norme existante, ou une sixième norme, sans
toucher à une ligne de logique.

⚠️ **Le palier de fiabilité (`tier`) est obligatoire et affiché.** Un outil
de veille qui présente le blog d'un cabinet de conseil et la page d'un
comité ISO sur la même ligne mentirait par omission. Ce n'est pas un détail
d'interface : c'est ce qui rend l'outil défendable.

⚠️ **HTTP 200 ne veut pas dire utilisable.** Chaque source de cette liste a
été sondée une par une le 23/08/2026. Trois candidates du plan initial
répondaient 200 et étaient mortes — le flux du VDA ne contenait qu'un billet
« Test » de 2024, ceux d'Advisera n'avaient rien publié depuis 2021 et 2023.
Elles ne sont pas ici. Ajouter une source sans la lire d'abord est le
meilleur moyen de livrer une veille qui ne remonte rien.
"""

from dataclasses import dataclass

from .config import LOOKBACK_DAYS
from .norms import NORM_ORDER, NORMS, Norm

# Paliers, du plus au moins probant. L'ordre compte : il sert au tri et à
# l'affichage.
TIERS: dict[str, str] = {
    "officiel": "Source officielle — l'organisme qui produit ou administre le référentiel",
    "communaute": "Base communautaire — un tiers qui agrège des documents publics",
    "commentaire": "Commentaire spécialisé — blog ou organisme de conseil, pas un normalisateur",
}
TIER_ORDER = tuple(TIERS)


@dataclass(frozen=True)
class Source:
    """Une page ou un flux à lire, et ce qu'il vaut.

    `norm_keys` est au pluriel parce qu'une source peut servir plusieurs
    normes : le flux de SRES couvre l'ISO 26262 et la cybersécurité
    véhicule. Elle n'est alors lue **qu'une fois** par veille.
    """

    key: str
    label: str
    url: str
    kind: str        # "rss" (RSS 2.0 ou Atom) | "html" (parseur dédié)
    parser: str      # nom dans scrape.PARSERS ; vide pour un flux
    tier: str
    norm_keys: tuple[str, ...]
    note: str


SOURCES: tuple[Source, ...] = (
    Source(
        key="intacs",
        label="iNTACS — actualités",
        url="https://www.intacs.info/component/content/category/news?format=feed&type=rss",
        kind="rss",
        parser="",
        tier="officiel",
        norm_keys=("aspice",),
        note="Association qui administre le schéma de certification des assesseurs "
             "Automotive SPICE. Publie peu — quelques actualités par an. Le flux "
             "n'est pas exposé sur le site, il faut demander le format RSS.",
    ),
    Source(
        key="vda_spice",
        label="VDA QMC — publications Automotive SPICE",
        url="https://vda-qmc.de/automotive-spice/automotive-spice-veroeffentlichungen/",
        kind="html",
        parser="vda_publications",
        tier="officiel",
        norm_keys=("aspice",),
        note="Catalogue officiel des publications, pas un fil d'actualité : c'est le "
             "signal ASPICE le plus fort qui soit — les versions réellement publiées. "
             "Réserve : dates au mois près, parfois à l'année seule, page en allemand. "
             "(Le flux RSS du VDA, lui, est abandonné : un billet « Test » de 2024.)",
    ),
    Source(
        key="sres",
        label="SRES — commentaire sûreté et cybersécurité automobile",
        url="https://sres.ai/feed/",
        kind="rss",
        parser="",
        tier="commentaire",
        norm_keys=("iso26262", "iso21434"),
        note="⚠️ Aucune source officielle n'est atteignable pour l'ISO 26262 : "
             "ISO.org répond par un défi anti-robot et le TC 22/SC 32 n'a pas de "
             "micro-site. Ce blog spécialisé est donc un palier « commentaire », "
             "jamais présenté comme officiel. C'est la seule norme dans ce cas.",
    ),
    Source(
        key="globalautoregs",
        label="GlobalAutoRegs — documents WP.29",
        url="https://globalautoregs.com/documents",
        kind="html",
        parser="globalautoregs",
        tier="communaute",
        norm_keys=("iso21434",),
        note="Base tierce qui agrège les documents publics de la WP.29 — la voie "
             "praticable puisque unece.org répond par un défi anti-robot. Le "
             "rattachement à un règlement UN vient du champ « Relevant to » de la "
             "source elle-même, pas d'une devinette de notre part.",
    ),
    Source(
        key="iso27ksecurity",
        label="ISO27k Forum — veille sur la famille ISO/IEC 27000",
        url="https://www.iso27001security.com/blog-feed.xml",
        kind="rss",
        parser="",
        tier="commentaire",
        norm_keys=("iso27001",),
        note="Blog spécialisé tenu par un praticien, remarquablement à jour sur les "
             "stades de rédaction de la famille ISO27k. Ce n'est pas l'ISO, et le "
             "ton y est parfois d'opinion — d'où le palier « commentaire ».",
    ),
    Source(
        key="iso_tc176",
        label="ISO/TC 176 — actualités du comité",
        url="https://committee.iso.org/sites/tc176/home/news.html",
        kind="html",
        parser="iso_committee_news",
        tier="officiel",
        norm_keys=("iso9001",),
        note="Le comité qui porte l'ISO 9001. ⚠️ committee.iso.org est ouvert alors "
             "que www.iso.org est fermé : deux sous-domaines, deux politiques. Son "
             "robots.txt autorise tout le monde avec « use=reference » — RegWatch "
             "ne recopie rien et lie la source, ce qui est exactement ça.",
    ),
    Source(
        key="iso_tc176sc2",
        label="ISO/TC 176/SC 2 — actualités du sous-comité",
        url="https://committee.iso.org/sites/tc176sc2/home/news.html",
        kind="html",
        parser="iso_committee_news",
        tier="officiel",
        norm_keys=("iso9001",),
        note="Le sous-comité qui mène la révision de l'ISO 9001 — c'est ici que "
             "passe le signal le plus concret (« ISO/FDIS 9001 approuvé »). Même "
             "gabarit de page que le TC 176 : un seul parseur couvre les deux, et "
             "tout comité ISO qu'on voudra ajouter plus tard.",
    ),
)


class UnknownSource(KeyError):
    """Source demandée qui n'existe pas au catalogue."""


def by_key(key: str) -> Source:
    for source in SOURCES:
        if source.key == key:
            return source
    raise UnknownSource(key)


def sources_for(norms: list[Norm]) -> list[Source]:
    """Les sources à lire pour ces normes — **dédupliquées**.

    Une source partagée entre deux normes cochées n'est lue qu'une fois.
    C'est ce qui permet d'avoir des sources multi-normes sans doubler le
    trafic ni compter deux fois une panne.
    """
    wanted = {norm.key for norm in norms}
    return [
        source for source in SOURCES
        if wanted.intersection(source.norm_keys)
    ]


def source_catalog() -> dict:
    """Catalogue complet, prêt à servir en JSON — source de vérité unique.

    Même motif que `/hara/matrix` et `/tara/scales` : la page lit ce
    catalogue et l'affiche, elle ne réécrit ni les libellés de normes, ni les
    paliers, ni la fenêtre de veille. Un ajout de source devient visible sans
    toucher au HTML.
    """
    return {
        "lookbackDays": LOOKBACK_DAYS,
        "tiers": [{"key": key, "label": label} for key, label in TIERS.items()],
        "norms": [
            {
                "key": key,
                "label": NORMS[key].label,
                "sources": [
                    {
                        "key": source.key,
                        "label": source.label,
                        "url": source.url,
                        "tier": source.tier,
                        "note": source.note,
                    }
                    for source in SOURCES
                    if key in source.norm_keys
                ],
            }
            for key in NORM_ORDER
        ],
    }
