"""La chaîne de pourquoi — ce qu'un moteur peut honnêtement juger d'un raisonnement.

Énoncer une cause racine sans montrer comment on y est arrivé ne démontre
rien. Chaque cause du D4 porte donc sa chaîne, et ce module dit si cette
chaîne tient debout.

## ⚠️ Structurer plutôt que lexicaliser — la décision centrale

La règle qu'on veut tenir est celle que tout le métier connaît : **une chaîne
qui s'arrête sur un opérateur n'a pas trouvé de cause.** « L'opérateur ne
s'est pas appliqué » ne se corrige pas, ne se prévient pas, et ne survit pas
au départ de l'opérateur.

La façon évidente de la coder serait un lexique de mots de blâme —
« opérateur », « négligence », « pas formé ». Elle est fausse pour trois
raisons, et le projet a déjà payé les deux premières :

1. C'est un **thème pris pour un marqueur**, l'erreur exacte de
   « Functional Safety » dans RegWatch : sur 14 items rangés sous cette
   catégorie par leur propre auteur, 2 concernaient la norme visée.
2. Il faudrait **deux lexiques**, un par langue, appelés à diverger — et le
   chantier d'internationalisation a montré quatre fois ce que coûte une
   chaîne d'affichage qui pilote quelque chose.
3. Un lexique se contourne sans le vouloir : « le monteur a mal interprété la
   gamme » n'est pas du blâme, c'est une cause de procédé mal écrit.

D'où le choix inverse : **l'ingénieur qualifie chaque pourquoi** dans une
liste fermée de quatre natures, et la règle devient mécanique. Aucun mot de
vocabulaire métier ne vit dans ce module. Même geste qu'au D2, dont le
découpage en champs rend la complétude vérifiable sans interpréter du texte.

⚠️ Conséquence remarquable : **l'analyse ne lit jamais le texte des
pourquoi.** Elle rend donc exactement le même verdict quelle que soit la
langue de saisie — c'est une propriété, pas un hasard, et un test la
verrouille.

## Ce que ce module NE juge pas

Il juge la **forme du raisonnement**, jamais sa substance. Une chaîne dont
les affirmations seraient vides de sens mais correctement qualifiées passe :
c'est assumé et c'est la limite exacte de ce qu'un moteur déterministe peut
affirmer. C'est là que l'IA gagne sa place (étape 5) — elle **conteste** le
fond, en annotation, sans jamais rendre de verdict. Le verdict reste ici.

## Les natures, et pourquoi deux seulement peuvent conclure

| Nature | Peut conclure ? |
|---|---|
| `system` — dispositif de management ou de conception | ✅ On peut le changer, et le changement protège d'autres défauts |
| `process` — règle, procédé, mode opératoire | ✅ Idem |
| `technical` — état technique constaté | ❌ C'est le symptôme qu'on cherchait à expliquer |
| `person` — une personne et son geste | ❌ Ne se corrige pas, ne se prévient pas |

⚠️ Un pourquoi `person` **au milieu** d'une chaîne est parfaitement légitime,
et même fréquent dans une bonne analyse : « l'opérateur s'est trompé » →
*pourquoi ?* → « la gamme admet deux lectures » (`process`). C'est s'y
**arrêter** qui est la faute. La règle porte donc sur la dernière marche,
pas sur la présence.
"""

import re

from i18n import DEFAULT_LANG, t

from .model import MAX_STEPS, NATURE_ORDER, Chain

# Profondeur minimale d'une chaîne recevable.
#
# ⚠️ Trois, et non cinq. « Cinq pourquoi » est un repère de méthode, pas une
# loi : exiger exactement cinq marches produirait du remplissage à la
# quatrième et à la cinquième. Trois est le minimum en deçà duquel il n'y a
# pas de raisonnement — symptôme, procédé, système.
MIN_STEPS = 3

# Les seules natures sur lesquelles une chaîne a le droit de s'arrêter.
TERMINAL_NATURES = ("process", "system")

# Tous les constats que `analyse` peut rendre. Déclaratif, pour que le
# contrat servi à la page ne puisse pas en oublier un — un test vérifie que
# la fonction n'en émet aucun autre.
CHAIN_CODES = (
    "chain_missing",
    "chain_too_short",
    "chain_truncated",
    "chain_step_without_nature",
    "chain_repeats_itself",
    "chain_ends_on_person",
    "chain_ends_on_symptom",
)

_ESPACES = re.compile(r"\s+")


def _normalise(affirmation: str) -> str:
    """Forme comparable d'un pourquoi, pour détecter une répétition.

    Volontairement sommaire — casse, espaces, ponctuation de bord. On ne
    cherche pas la paraphrase (ce serait juger le fond), seulement le
    copier-coller d'une marche à l'autre.
    """
    return _ESPACES.sub(" ", affirmation.strip().lower()).strip(" .,;:!?-—…")


def analyse(chain: Chain) -> list[str]:
    """Ce qui empêche cette chaîne d'étayer une cause racine.

    Rend des **identifiants** de constat, sans préfixe de discipline : ce
    module ignore qu'il travaille pour un D4. C'est `check` qui les situe.
    Une liste vide signifie que la chaîne tient.
    """
    if not isinstance(chain, Chain) or not chain.steps:
        return ["chain_missing"]

    constats: list[str] = []

    if len(chain) < MIN_STEPS:
        constats.append("chain_too_short")
    if chain.truncated:
        constats.append("chain_truncated")
    if any(not marche.nature for marche in chain.steps):
        constats.append("chain_step_without_nature")

    vues = [_normalise(m.statement) for m in chain.steps]
    if len(set(vues)) < len(vues):
        constats.append("chain_repeats_itself")

    derniere = chain.steps[-1].nature
    # ⚠️ Une dernière marche non qualifiée est déjà signalée plus haut ;
    # ajouter « s'arrête sur un symptôme » serait dire deux fois la même
    # chose avec un mot faux.
    if derniere and derniere not in TERMINAL_NATURES:
        constats.append(
            "chain_ends_on_person" if derniere == "person" else "chain_ends_on_symptom"
        )

    return constats


def is_sound(chain: Chain) -> bool:
    """La chaîne étaye-t-elle une cause racine ?"""
    return not analyse(chain)


def nature_labels(lang: str = DEFAULT_LANG) -> dict[str, str]:
    """Les quatre natures, libellées. Le moteur, lui, n'en connaît aucune."""
    return {cle: t(f"ct.nature.{cle}", lang) for cle in NATURE_ORDER}


def chain_rules(lang: str = DEFAULT_LANG) -> dict:
    """Les règles de chaîne, prêtes à servir à l'interface.

    ⚠️ La page ne réécrit ni la profondeur minimale, ni les natures qui ont
    le droit de conclure : elle les lit. Même motif que `/hara/matrix` et
    `/tara/scales` — une règle décidée à deux endroits finit par diverger.
    """
    return {
        "minSteps": MIN_STEPS,
        "maxSteps": MAX_STEPS,
        "natures": list(NATURE_ORDER),
        "natureLabels": nature_labels(lang),
        "terminal": list(TERMINAL_NATURES),
    }
