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

from i18n import DEFAULT_LANG, t

from dataclasses import dataclass

from .config import LOOKBACK_DAYS
from .norms import NORM_ORDER, NORMS, Norm

# Paliers, du plus au moins probant. L'ordre compte : il sert au tri et à
# l'affichage.
TIER_ORDER = ("officiel", "communaute", "commentaire")


def tiers(lang: str = DEFAULT_LANG) -> dict[str, str]:
    """Les paliers de fiabilité, du plus au moins probant."""
    return {cle: t(f"regwatch.tier.{cle}", lang) for cle in TIER_ORDER}


@dataclass(frozen=True)
class Source:
    """Une page ou un flux à lire, et ce qu'il vaut.

    `norm_keys` est au pluriel parce qu'une source peut servir plusieurs
    normes : le flux de SRES couvre l'ISO 26262 et la cybersécurité
    véhicule. Elle n'est alors lue **qu'une fois** par veille.
    """

    key: str
    url: str
    kind: str        # "rss" (RSS 2.0 ou Atom) | "html" (parseur dédié)
    parser: str      # nom dans scrape.PARSERS ; vide pour un flux
    tier: str
    norm_keys: tuple[str, ...]

    def label(self, lang: str = DEFAULT_LANG) -> str:
        """Nom affichable de la source.

        ⚠️ Une méthode et non un champ, **délibérément** : un libellé a
        longtemps servi de clé de comparaison entre `WatchResult` et
        l'onglet Couverture de l'export. Le sortir du dataclass rend cette
        confusion impossible — ce qui n'existe pas ne peut pas être comparé.
        """
        return t(f"regwatch.source.{self.key}.label", lang)

    def note(self, lang: str = DEFAULT_LANG) -> str:
        """Ce qu'il faut savoir de cette source — palier, réserves, pièges.

        ⚠️ Le texte vit dans `src/i18n/`, pas ici : `sources.py` dit **où**
        l'on cherche, pas comment on le raconte.
        """
        return t(f"regwatch.source.{self.key}.note", lang)


SOURCES: tuple[Source, ...] = (
    Source(
        key="intacs",
        url="https://www.intacs.info/component/content/category/news?format=feed&type=rss",
        kind="rss",
        parser="",
        tier="officiel",
        norm_keys=("aspice",),
    ),
    Source(
        key="vda_spice",
        url="https://vda-qmc.de/automotive-spice/automotive-spice-veroeffentlichungen/",
        kind="html",
        parser="vda_publications",
        tier="officiel",
        norm_keys=("aspice",),
    ),
    Source(
        key="sres",
        url="https://sres.ai/feed/",
        kind="rss",
        parser="",
        tier="commentaire",
        norm_keys=("iso26262", "iso21434"),
    ),
    Source(
        key="globalautoregs",
        url="https://globalautoregs.com/documents",
        kind="html",
        parser="globalautoregs",
        tier="communaute",
        norm_keys=("iso21434",),
    ),
    Source(
        key="iso27ksecurity",
        url="https://www.iso27001security.com/blog-feed.xml",
        kind="rss",
        parser="",
        tier="commentaire",
        norm_keys=("iso27001",),
    ),
    Source(
        key="iso_tc176",
        url="https://committee.iso.org/sites/tc176/home/news.html",
        kind="html",
        parser="iso_committee_news",
        tier="officiel",
        norm_keys=("iso9001",),
    ),
    Source(
        key="iso_tc176sc2",
        url="https://committee.iso.org/sites/tc176sc2/home/news.html",
        kind="html",
        parser="iso_committee_news",
        tier="officiel",
        norm_keys=("iso9001",),
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


def source_catalog(lang: str = DEFAULT_LANG) -> dict:
    """Catalogue complet, prêt à servir en JSON — source de vérité unique.

    Même motif que `/hara/matrix` et `/tara/scales` : la page lit ce
    catalogue et l'affiche, elle ne réécrit ni les libellés de normes, ni les
    paliers, ni la fenêtre de veille. Un ajout de source devient visible sans
    toucher au HTML.
    """
    return {
        "lookbackDays": LOOKBACK_DAYS,
        "tiers": [{"key": key, "label": label} for key, label in tiers(lang).items()],
        "norms": [
            {
                "key": key,
                "label": NORMS[key].label,
                "sources": [
                    {
                        "key": source.key,
                        "label": source.label(lang),
                        "url": source.url,
                        "tier": source.tier,
                        "note": source.note(lang),
                    }
                    for source in SOURCES
                    if key in source.norm_keys
                ],
            }
            for key in NORM_ORDER
        ],
    }
