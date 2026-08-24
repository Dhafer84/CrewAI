"""Catalogues de traduction — utilitaire partagé par tous les outils.

Deuxième exception assumée à « moteurs strictement indépendants », après
`src/xlsxsafe/`, et pour la même raison : **ce n'est pas de la logique
métier**. Un libellé n'appartient pas au domaine, il appartient à la
présentation. Les moteurs ne contiennent donc aucune traduction — ils
délèguent ici, exactement comme ils délèguent le durcissement d'un classeur.

## Le principe qui rend ce chantier sûr

`t()` **ne lève jamais**. Clé absente → repli sur le français → repli sur la
clé elle-même. Sur un site vitrine en production, une traduction oubliée doit
dégrader l'affichage d'une ligne, jamais rendre une page blanche.

En contrepartie, `tests/test_i18n.py` est **intransigeant** : il refuse une
clé manquante, une clé morte, un paramètre qui ne correspond pas d'une langue
à l'autre, et un texte de page qui aurait divergé de son catalogue.
Indulgent à l'exécution, sévère en test.

## Convention de nommage

`<zone>.<élément>` en minuscules : `nav.back`, `footer.regwatch`,
`hara.severity.s2`. Les formes plurielles se déclarent en **paires**
`<clé>.one` / `<clé>.other`, et `t()` choisit selon `n`.

⚠️ **La règle du pluriel n'est pas la même dans les deux langues.** En
français, zéro est un singulier — « 0 signal retenu » ; en anglais, non —
« 0 signals kept ». C'est le genre de détail qui distingue une traduction
d'une transposition.
"""

import re

from .en import CATALOGUE as _EN
from .fr import CATALOGUE as _FR

DEFAULT_LANG = "fr"
LANGUAGES = ("fr", "en")

_CATALOGUES: dict[str, dict[str, str]] = {"fr": _FR, "en": _EN}

_PLACEHOLDER = re.compile(r"\{(\w+)\}")


def normalize(lang: str | None) -> str:
    """Ramène une étiquette de langue à une langue servie.

    « en-US » → « en ». Une langue inconnue, vide ou absente retombe sur le
    français : le visiteur voit toujours quelque chose.
    """
    if not lang:
        return DEFAULT_LANG
    court = str(lang).strip().lower().replace("_", "-").split("-")[0]
    return court if court in LANGUAGES else DEFAULT_LANG


def catalogue(lang: str) -> dict[str, str]:
    """Le catalogue d'une langue, prêt à être servi en JSON."""
    return dict(_CATALOGUES[normalize(lang)])


def keys() -> set[str]:
    """Les clés de référence — c'est le français qui fait foi."""
    return set(_CATALOGUES[DEFAULT_LANG])


def missing_keys(lang: str) -> list[str]:
    """Clés présentes en français et absentes de `lang`. Outil de test."""
    return sorted(set(_CATALOGUES[DEFAULT_LANG]) - set(_CATALOGUES[normalize(lang)]))


def orphan_keys(lang: str) -> list[str]:
    """Clés présentes dans `lang` mais inconnues du français."""
    return sorted(set(_CATALOGUES[normalize(lang)]) - set(_CATALOGUES[DEFAULT_LANG]))


def placeholders(text: str) -> set[str]:
    """Les paramètres `{nom}` d'un texte."""
    return set(_PLACEHOLDER.findall(text or ""))


def _plural_suffix(lang: str, count: int) -> str:
    """⚠️ Le français met zéro au singulier, l'anglais au pluriel."""
    if lang == "fr":
        return "one" if abs(count) < 2 else "other"
    return "one" if count == 1 else "other"


def t(key: str, lang: str = DEFAULT_LANG, n: int | None = None, **params) -> str:
    """Rend le texte d'une clé. Ne lève jamais.

    Args:
        key: clé du catalogue, en notation pointée.
        lang: langue voulue ; toute valeur inconnue retombe sur le français.
        n: quantité, quand la clé a des formes `.one` / `.other`. Elle est
            aussi exposée au formatage sous le nom `n`.
        **params: valeurs des `{paramètres}` du texte.

    Returns:
        Le texte traduit ; à défaut le texte français ; à défaut la clé.
        **Jamais d'exception** — voir l'en-tête du module.
    """
    lang = normalize(lang)

    candidates = []
    if n is not None:
        candidates.append(f"{key}.{_plural_suffix(lang, n)}")
    candidates.append(key)

    texte = None
    # ⚠️ Le repli passe par le registre, pas par le catalogue importé :
    # sinon remplacer un catalogue (tests) laisserait le repli pointer
    # ailleurs, et le mécanisme ne serait plus celui qu'on croit tester.
    for source in (_CATALOGUES[lang], _CATALOGUES[DEFAULT_LANG]):
        for candidate in candidates:
            if candidate in source:
                texte = source[candidate]
                break
        if texte is not None:
            break

    if texte is None:
        # Dernier recours : la clé. Visible, mais la page tient debout.
        return key

    if n is not None:
        params.setdefault("n", n)
    if not params:
        return texte

    try:
        return texte.format(**params)
    except (KeyError, IndexError):
        # Paramètre manquant : mieux vaut un texte à trous qu'une page en
        # erreur. `test_i18n.py` refuse de laisser passer ce cas.
        return texte
