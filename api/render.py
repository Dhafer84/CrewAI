"""Rendu d'une page dans une langue, côté serveur.

⚠️ **Côté serveur, et pas en JavaScript — c'est le point qui décide de tout.**
Un remplacement dans le navigateur laisserait Google n'indexer que le
français : la version anglaise n'existerait pour personne, ce qui la viderait
de son intérêt sur un site vitrine. Le rendu serveur donne à chaque langue
une URL réelle, indexable, partageable.

Aucun moteur de template, aucune dépendance : les pages restent des fichiers
HTML lisibles et modifiables à la main. On y substitue le contenu des
éléments annotés `data-i18n`, rien de plus.

⚠️ **Le découpage se fait par pile de balises, jamais par expression
régulière.** Le HTML s'imbrique ; une regex ne sait pas où s'arrête un
élément, et l'a prouvé à l'étape A3 en avalant une carte entière au lieu
d'un paragraphe.
"""

import re
from html import unescape
from pathlib import Path

from i18n import DEFAULT_LANG, LANGUAGES, normalize, t

# Balises sans contenu : elles ne s'empilent pas.
_VOIDS = {"br", "img", "input", "meta", "link", "hr", "path", "circle",
          "polyline", "rect", "line", "use", "source"}

_TAG = re.compile(r'<(/?)([a-zA-Z][\w-]*)([^>]*?)(/?)>')
_ANNOTATED = re.compile(r'<([a-zA-Z][\w-]*)([^>]*?data-i18n="([^"]+)"[^>]*?)>')
_ATTR_KEY = re.compile(r'data-i18n-content="([^"]+)"')

# Chemins de page, en français — les seuls href que le rendu préfixe.
# ⚠️ UNE seule liste d'actifs versionnés — celle qui APPLIQUE le `?v=` et
# celle qui le CALCULE (`api.main._asset_version`) doivent être la même. Elles
# ont divergé le 25/08/2026 : `aistatus.js` n'avait été ajouté qu'ici, et un
# visiteur qui revenait gardait l'ancien script en cache indéfiniment.
VERSIONED_ASSETS = ("style.css", "i18n.js", "aistatus.js",
                    "og-fr.png", "og-en.png")

# Image de partage, une par langue — ce que LinkedIn, Slack ou WhatsApp
# affichent quand on colle un lien du site. Construite par
# `scripts/build_og_image.py` ; **ce n'est pas un fichier à retoucher à la
# main**, c'est une sortie.
#
# ⚠️ **Une image PAR LANGUE, et non une seule.** Tout le chantier i18n a
# consisté à empêcher le français de survivre dans une page anglaise. Une
# carte française en `og:image` sur `/en` serait exactement cette faute, au
# seul endroit qu'un visiteur voit *avant* d'avoir ouvert le site.
OG_IMAGE = {"fr": "og-fr.png", "en": "og-en.png"}
OG_IMAGE_SIZE = (1200, 630)

# `og:site_name` — un nom propre, identique dans les deux langues.
OG_SITE_NAME = "Dhafer Bouthelja"

_LOCALES = {"fr": "fr_FR", "en": "en_US"}

_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.S)
_DESCRIPTION = re.compile(
    r'<meta\s+name="description"[^>]*?\scontent="([^"]*)"')

PAGE_PATHS = ("", "/qualitycrew", "/sentinelscan", "/hara", "/tara", "/regwatch", "/8d")


def _end_of_element(html: str, tag: str, after: int) -> int | None:
    """Position du début de la balise fermante correspondante."""
    depth = 1
    for m in _TAG.finditer(html, after):
        if m.group(2).lower() != tag.lower():
            continue
        if m.group(1):
            depth -= 1
            if depth == 0:
                return m.start()
        elif not m.group(4) and m.group(2).lower() not in _VOIDS:
            depth += 1
    return None


def translate_markup(html: str, lang: str) -> str:
    """Remplace le contenu de chaque élément `data-i18n` par sa traduction.

    Les substitutions sont appliquées **de la fin vers le début** : remplacer
    un contenu décale tout ce qui suit.
    """
    remplacements = []
    for m in _ANNOTATED.finditer(html):
        tag, cle = m.group(1), m.group(3)
        if tag.lower() in _VOIDS:
            continue
        fin = _end_of_element(html, tag, m.end())
        if fin is None:
            continue
        remplacements.append((m.end(), fin, t(cle, lang)))

    for debut, fin, texte in reversed(remplacements):
        html = html[:debut] + texte + html[fin:]

    # Attributs traduisibles. Deux cas, et deux seulement :
    #   `content`     — la description <meta>, ce que Google affiche
    #   `placeholder` — le texte d'exemple d'un champ de saisie
    # Un attribut n'a pas de contenu à remplacer : il faut le nommer.
    for attribut in ("content", "placeholder"):
        html = re.sub(
            rf'data-i18n-{attribut}="([^"]+)"\s+{attribut}="[^"]*"',
            lambda m, a=attribut: f'{a}="{t(m.group(1), lang)}"',
            html)
    return html


def _urls(chemin: str, base: str) -> tuple[str, str]:
    """Les deux URL canoniques d'une page. Exactes, sans slash superflu.

    ⚠️ Un `hreflang` qui pointe vers une redirection est une erreur
    silencieuse : Google suit, mais n'apparie plus les deux versions.
    """
    return base + (chemin or "/"), base + "/en" + chemin


def _alternates(chemin: str, base: str) -> str:
    """Liens `hreflang` réciproques — ce que Google attend d'un site bilingue."""
    fr, en = _urls(chemin, base)
    return "\n  ".join([
        f'<link rel="alternate" hreflang="fr" href="{fr}">',
        f'<link rel="alternate" hreflang="en" href="{en}">',
        f'<link rel="alternate" hreflang="x-default" href="{fr}">',
    ])


def _attr(valeur: str) -> str:
    """Prépare une valeur pour un attribut `content`.

    ⚠️ Deux provenances, deux échappements — et c'est le piège. Le titre et la
    description sont extraits du HTML, donc **déjà** échappés (`&amp;`) ; le
    texte alternatif sort du catalogue Python, donc **brut** (`&`). Les
    concaténer tels quels produirait un `&` nu dans un attribut. On désamorce
    d'abord, on ré-échappe ensuite : le traitement devient le même pour les
    deux, et il est idempotent.

    ⚠️ **L'apostrophe n'est PAS échappée**, à la différence de `html.escape` :
    dans un attribut entre guillemets doubles elle n'a rien d'ambigu, et
    l'échapper rendrait `og:description` littéralement différent de la
    description de la page — deux textes identiques qui ne se comparent plus.
    """
    valeur = unescape(valeur)
    for brut, code in (("&", "&amp;"), ("<", "&lt;"),
                       (">", "&gt;"), ('"', "&quot;")):
        valeur = valeur.replace(brut, code)
    return valeur


def social(html: str, lang: str, path: str, base_url: str,
           asset_version: str = "") -> str:
    """Les balises que lisent LinkedIn, Slack, WhatsApp et consorts.

    ⚠️ **Elles sont DÉRIVÉES de la page, jamais saisies à côté.** Le titre et
    la description sortent de ce que la page déclare déjà — et donc de ce que
    `translate_markup` vient de traduire. Les écrire à la main dans les sept
    fichiers, en deux langues, ce serait quatorze occasions de laisser une
    version diverger de l'autre en silence : personne ne relit un aperçu
    social, on le découvre publié.

    Sans ces balises, un lien collé sur LinkedIn ne montre qu'une ligne de
    texte grise. Avec elles, il montre la carte du site.
    """
    fr, en = _urls(path, base_url)
    canonique = fr if lang == DEFAULT_LANG else en
    autre = "en" if lang == DEFAULT_LANG else "fr"

    image = base_url + "/static/" + OG_IMAGE.get(lang, OG_IMAGE[DEFAULT_LANG])
    if asset_version:
        image += f"?v={asset_version}"

    titre = _TITLE.search(html)
    description = _DESCRIPTION.search(html)
    largeur, hauteur = OG_IMAGE_SIZE

    balises = [f'<link rel="canonical" href="{canonique}">',
               f'<meta property="og:type" content="website">',
               f'<meta property="og:url" content="{canonique}">',
               f'<meta property="og:site_name" content="{_attr(OG_SITE_NAME)}">',
               f'<meta property="og:locale" content="{_LOCALES[lang]}">',
               f'<meta property="og:locale:alternate" content="{_LOCALES[autre]}">']

    if titre:
        balises.append(
            f'<meta property="og:title" content="{_attr(titre.group(1).strip())}">')
    if description:
        balises.append('<meta property="og:description" '
                       f'content="{_attr(description.group(1))}">')

    balises += [
        f'<meta property="og:image" content="{image}">',
        # ⚠️ Les dimensions ne sont pas décoratives : sans elles, LinkedIn
        # rend souvent la petite vignette carrée le temps d'avoir téléchargé
        # l'image — c'est-à-dire au moment précis où le lien est partagé.
        f'<meta property="og:image:width" content="{largeur}">',
        f'<meta property="og:image:height" content="{hauteur}">',
        f'<meta property="og:image:type" content="image/png">',
        f'<meta property="og:image:alt" content="{_attr(t("og.alt", lang))}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:image:alt" content="{_attr(t("og.alt", lang))}">',
    ]
    return "\n  ".join(balises)


def render(html: str, lang: str, path: str, base_url: str,
           asset_version: str = "") -> str:
    """Rend une page dans la langue demandée.

    Args:
        html: le fichier source, en français.
        lang: langue voulue ; toute valeur inconnue retombe sur le français.
        path: chemin canonique FRANÇAIS de la page ("" pour l'accueil,
            "/hara" sinon). Sert à construire les alternates et le sélecteur.
        base_url: origine du site, pour des `hreflang` absolus.
        asset_version: empreinte des fichiers statiques, ajoutée en query
            string. ⚠️ **Sans elle, un visiteur qui revient garde l'ancien
            CSS en cache et le nouveau HTML** : un élément introduit avec sa
            règle de style s'afficherait nu. C'est arrivé en test.
    """
    lang = normalize(lang)
    html = translate_markup(html, lang)

    html = html.replace('<html lang="fr">', f'<html lang="{lang}">', 1)
    html = html.replace('/i18n/fr.js', f'/i18n/{lang}.js', 1)

    # ⚠️ **Les liens internes doivent rester dans la langue de la page.**
    # Sans ça, un visiteur anglophone qui clique sur une carte retombe en
    # français : la version anglaise devient un cul-de-sac dès le premier
    # clic. Seuls les chemins de PAGE sont préfixés — jamais les routes
    # d'API, qui portent leur langue en query string.
    if lang != DEFAULT_LANG:
        for chemin in sorted(PAGE_PATHS, key=len, reverse=True):
            html = html.replace(f'href="{chemin or "/"}"',
                                f'href="/{lang}{chemin}"')

    if asset_version:
        for actif in VERSIONED_ASSETS:
            html = html.replace(f'"/static/{actif}"',
                                f'"/static/{actif}?v={asset_version}"')

    # Le sélecteur pointe vers la MÊME page dans l'autre langue.
    autre = "en" if lang == "fr" else "fr"
    cible = ("/en" + path) if autre == "en" else (path or "/")
    html = re.sub(
        r'(<a class="nav-link nav-lang"[^>]*?)href="[^"]*"([^>]*?)>[^<]*</a>',
        lambda m: (f'{m.group(1)}href="{cible}" hreflang="{autre}"{m.group(2)}>'
                   f'{autre.upper()}</a>'),
        html, count=1)

    entete = "\n  ".join([_alternates(path, base_url),
                          social(html, lang, path, base_url, asset_version)])
    html = html.replace("</head>", "  " + entete + "\n</head>", 1)
    return html


def catalogue_languages() -> tuple[str, ...]:
    return LANGUAGES


__all__ = ["render", "translate_markup", "social", "catalogue_languages",
           "DEFAULT_LANG"]
