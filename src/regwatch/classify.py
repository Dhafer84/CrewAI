"""Classification déterministe : rattachement à une norme, niveau de signal.

Zéro réseau, zéro IA, zéro état — et c'est **l'étape qui décide**. Ce qui
sort d'ici est ce que la veille retiendra ; l'IA n'intervient qu'ensuite,
pour écrire une phrase, jamais pour filtrer ni pour coter. Une
classification qui appellerait un modèle ne serait ni reproductible d'un
jour sur l'autre, ni testable hors ligne, ni défendable devant un auditeur.

Trois principes, dans l'ordre où ils s'appliquent :

1. **Le bruit est écarté d'abord.** Une mention légale reste une mention
   légale, même publiée par un organisme normatif. La liste est
   volontairement courte : on n'écarte que ce qui ne porte **aucun** signal
   de veille.
2. **Le rattachement exige un marqueur.** Être publié par une source qui ne
   parle que d'ASPICE ne suffit pas — c'est le titre (ou une catégorie qui
   nomme une famille de normes) qui doit le dire. S'en remettre à la
   provenance ferait entrer toutes les publicités de formation d'un
   organisme de certification.
3. **Le niveau de signal ne supprime rien.** Un item rattaché est toujours
   rendu, seulement étiqueté. Même discipline que
   `sentinelscan.refine_criticality`, qui déclasse un constat mais ne
   l'efface jamais : c'est à l'humain de qualifier, pas à l'outil de
   trancher seul.

⚠️ **Limite assumée : le niveau est déduit du titre seul.** Le corps des
pages n'est jamais téléchargé (contrainte de droit d'auteur, voir
`__init__.py`), donc « How to update your ISMS » ressort en
« Publication / amendement » alors que c'est un mode d'emploi. L'étiquette
oriente la lecture ; elle ne la remplace pas. Le lien vers la source, lui,
est toujours juste — et c'est lui le livrable.
"""

from i18n import DEFAULT_LANG, t

import re
import unicodedata
from collections.abc import Sequence
from functools import lru_cache

from .norms import Norm

# Ordre d'affichage, du signal le plus fort au plus faible. ⚠️ Ce n'est PAS
# l'ordre d'évaluation : voir `signal_of`.
# ⚠️ **Des IDENTIFIANTS, pas des libellés.** Ces valeurs sont stockées dans
# `WatchItem.signal`, servent de clés à `count_by_signal()` et d'ordre de
# force à la sélection de l'étape 5. Y mettre du texte affichable — ce qui
# était le cas jusqu'au 24/08/2026 — les rendait français dans une page
# anglaise, et intraduisibles sans casser les comptages.
#
# Cinquième occurrence du motif sur ce projet, après `TREATMENTS["requires"]`,
# `Source.label`, la lettre S/E/C de l'export HARA et `_SHAPE_CHECKS`.
SIGNAL_PUBLICATION = "publication"
SIGNAL_DRAFT = "draft"
SIGNAL_EVENT = "event"
SIGNAL_INFO = "info"

SIGNAL_ORDER: tuple[str, ...] = (
    SIGNAL_PUBLICATION, SIGNAL_DRAFT, SIGNAL_EVENT, SIGNAL_INFO,
)


def signal_label(signal: str, lang: str = DEFAULT_LANG) -> str:
    """Libellé affichable d'un niveau de signal."""
    return t(f"regwatch.signal.{signal}", lang)

# Un texte parvenu jusqu'à la norme, mais qui n'est pas une actualité :
# pages légales, offres d'emploi, billets de remplissage. Liste courte —
# écarter à tort coûte plus cher qu'étiqueter à tort.
_NOISE_MARKERS = (
    "datenschutz", "datenschutzinformation",
    "privacy notice", "privacy policy", "cookie policy",
    "impressum", "imprint", "mentions legales",
    "terms of use", "terms of service",
    "stellenangebot", "job posting", "vacancy",
)

# Chemins d'URL qui trahissent la même chose quand le titre reste muet.
_NOISE_PATHS = (
    "datenschutz", "privacy", "impressum", "imprint", "legal", "cookie",
)

# Stades de rédaction d'une norme. Un titre qui en cite un décrit un
# document **en cours**, quoi qu'il dise par ailleurs.
_DRAFT_MARKERS = (
    # Vocabulaire des documents réglementaires : une « proposition
    # d'amendement » déposée à la WP.29 est un travail en cours, pas une
    # norme publiée. Sans ces marqueurs elle ressortait en « Information ».
    "proposal", "proposals", "proposed",
    "draft", "working draft", "committee draft",
    "wd", "cd", "dis", "fdis", "nwip", "new work item",
    "ballot", "enquiry", "comment period",
    "under development", "in development",
)

# Une norme qui bouge pour de bon.
_PUBLICATION_MARKERS = (
    "published", "publication", "release", "released",
    "amendment", "amendments", "amended", "corrigendum",
    "revised", "revision", "new edition",
    "withdrawn", "superseded", "supersedes",
    "now available", "update", "updates", "updated",
    # Un catalogue de publications annonce une sortie en donnant sa version,
    # sans jamais écrire « published » : « Automotive SPICE 4.0 — version 4.0
    # / Dezember 2023 ». Sans ce marqueur, la sortie d'un nouveau PAM
    # ressortirait en simple « Information ».
    "version",
)

# Ce qui se passe autour de la norme, à une date donnée.
# ⚠️ « newsletter » et « information letter » n'y figurent pas : une lettre
# d'information d'un organisme normatif porte de la vraie actualité, la
# ranger dans un calendrier la déclasserait à tort.
_EVENT_MARKERS = (
    "conference", "webinar", "workshop", "seminar", "symposium", "summit",
    "training", "course", "registration", "early bird", "save the date",
    "call for", "meeting", "session", "announces", "announcement",
)


def _fold(text: str) -> str:
    """Minuscules, accents retirés, espaces normalisés.

    Les titres arrivent de sources allemandes, anglaises et françaises :
    comparer sans replier ferait manquer « Veröffentlichung » comme
    « VEROFFENTLICHUNG ».
    """
    lowered = unicodedata.normalize("NFKD", (text or "").lower())
    without_accents = "".join(c for c in lowered if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", without_accents).strip()


@lru_cache(maxsize=1024)
def _pattern(marker: str) -> "re.Pattern[str]":
    """Marqueur cherché avec de vraies frontières de mot.

    `(?<!\\w)…(?!\\w)` plutôt que `\\b…\\b` : un marqueur peut commencer ou
    finir par une ponctuation (« wp.29 », « iso/iec 27001 »), et `\\b` se
    comporte alors à l'inverse de ce qu'on attend. Sans frontières du tout,
    « cd » matcherait « record » et « dis » matcherait « display ».
    """
    return re.compile(rf"(?<!\w){re.escape(marker)}(?!\w)")


def _mentions(haystack: str, markers: Sequence[str]) -> bool:
    return any(_pattern(marker).search(haystack) for marker in markers)


def is_noise(title: str, categories: Sequence[str] = (), url: str = "") -> bool:
    """L'item est-il dépourvu de tout signal de veille ?

    Évalué **avant** le rattachement : « Datenschutzinformation iNTACS e.V. »
    cite bien un marqueur ASPICE, et passerait sans cette barrière.
    """
    folded = _fold(title)

    if len(folded) < 3:
        return True
    if folded == "test":
        # Billet de test laissé en ligne — vu en vrai sur un flux abandonné.
        return True
    if _mentions(folded, _NOISE_MARKERS):
        return True

    path = _fold(re.sub(r"[-_/]+", " ", url or ""))
    return _mentions(path, _NOISE_PATHS)


def attaches_to(title: str, categories: Sequence[str], norm: Norm) -> bool:
    """L'item parle-t-il de cette norme ?

    Un seul mécanisme : le marqueur, cherché dans **tout ce que la source
    dit de l'item** — son titre et les libellés qu'elle lui attache. Deux
    mécanismes distincts donneraient deux endroits où se tromper.

    ⚠️ Chercher dans les libellés n'ouvre pas la porte aux thèmes : une
    catégorie ne rattache que si elle **contient un marqueur**.
    « Functional Safety » n'en contient aucun et ne rattache donc rien —
    mesuré, voir `norms`. « ISO27k standards » contient `iso27k`, et
    « UN Regulation No. 155 | Cyber security » contient `regulation no. 155`.
    """
    haystack = _fold(title + " | " + " | ".join(categories or ()))
    return _mentions(haystack, norm.markers)


def signal_of(title: str) -> str:
    """Niveau de signal porté par le titre.

    ⚠️ **Les stades de rédaction l'emportent sur la publication**, et pas
    l'inverse : « AI security standard at FDIS » annonce bien un document
    *publié pour vote*, mais ce document n'est pas la norme — le classer en
    « Publication » ferait croire à un texte arrêté. L'ordre d'évaluation
    est donc brouillon → publication → événement, alors que `SIGNAL_ORDER`,
    lui, décroît de la publication vers l'information.
    """
    folded = _fold(title)

    if _mentions(folded, _DRAFT_MARKERS):
        return SIGNAL_DRAFT
    if _mentions(folded, _PUBLICATION_MARKERS):
        return SIGNAL_PUBLICATION
    if _mentions(folded, _EVENT_MARKERS):
        return SIGNAL_EVENT
    return SIGNAL_INFO


def qualify(
    title: str,
    categories: Sequence[str],
    url: str,
    norm: Norm,
) -> str | None:
    """Rend le niveau de signal de l'item pour cette norme, ou None.

    None signifie « cet item ne concerne pas cette norme, ou ne porte aucun
    signal de veille ». C'est le seul endroit du moteur où un item peut
    disparaître — et il le fait sur une règle écrite, relisible, testable
    hors ligne. Aucun modèle n'intervient ici.

    Args:
        title: titre de l'item, tel que publié.
        categories: catégories que le flux lui attribue (souvent vide).
        url: lien vers la source. Sert au repérage du bruit, **pas** au
            rattachement — un domaine qui contient « 27001 » rattacherait
            sinon tout son contenu à la norme.
        norm: la norme candidate.
    """
    if is_noise(title, categories, url):
        return None
    if not attaches_to(title, categories, norm):
        return None
    return signal_of(title)
