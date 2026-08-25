"""Relecture d'une discipline par l'IA — interface stable.

⚠️ **Ce module ne rend jamais de verdict.** Il rend des reformulations
*proposées* et des questions. Dire si un 8D est complet appartient à
`check`, qui est déterministe, reproductible et testable hors ligne. Un
modèle qui s'en mêlerait rendrait le verdict différent d'un jour à l'autre.

## La séparation qui rend l'IA facultative

    moteur → les champs VIDES        (mécanique, il suffit de regarder)
    IA     → les champs CREUX        (« Plusieurs pièces » n'est pas une quantité)

Le moteur ne peut rien dire d'un champ rempli — c'est précisément pour ça que
le 8D d'exemple est calibré avec des champs remplis mais vagues. Et l'IA ne
touche jamais à un champ vide : elle ne remplit pas le 8D à la place de
l'ingénieur, elle réclame ce qu'il n'a pas dit.

## Ce que la structure garantit

`FieldReview` ne porte **que** l'identifiant du champ et sa reformulation.
Aucun champ de jugement, aucune note, aucun niveau. Ce qui n'a pas de champ
ne peut pas traverser par mégarde — même discipline que
`threatscope.DamageProposal` et `sentinelscan.Hit`, et un test le verrouille.

⚠️ **Le parseur ne décale jamais.** Une ligne illisible laisse son champ
intact plutôt que de faire glisser les suivantes : une reformulation
attribuée au mauvais champ serait un texte plausible sous un mauvais
libellé, c'est-à-dire invisible.
"""

import re
from dataclasses import dataclass

from i18n import DEFAULT_LANG, t

from .crew import DEMAND_MARK, SEPARATOR, build_crew
from .model import (
    FIELD_KIND,
    FIELD_ORDER,
    REVIEWABLE_KINDS,
    Dossier,
    InvalidDossier,
)

MAX_DEMANDS = 4
MAX_REWRITE_LENGTH = 500
MAX_DEMAND_LENGTH = 200

# Les deux créneaux du D4 portent aussi leurs chaînes : c'est là que vit le
# raisonnement, donc là qu'une relecture sert le plus.
_CHAIN_SLOTS = ("occurrence", "escape")

_LEADING_NOISE = re.compile(r"^[\s*_`#>\-–—•.)\]]+")


class ReviewUnavailable(RuntimeError):
    """La relecture n'a pas pu aboutir — message destiné au visiteur."""


@dataclass(frozen=True)
class FieldReview:
    """Une reformulation proposée pour un champ.

    ⚠️ Deux champs, et deux seulement. Si quelqu'un ajoute un jour une note,
    un score ou un niveau, `test_a_review_carries_no_verdict` tombe — et
    c'est le moment de se demander pourquoi, pas d'ajuster le test.
    """

    field: str
    rewritten: str


@dataclass(frozen=True)
class DisciplineReview:
    """Ce que l'IA rend pour une discipline : des propositions et des questions."""

    discipline: str
    fields: tuple[FieldReview, ...] = ()
    demands: tuple[str, ...] = ()

    def __bool__(self) -> bool:
        return bool(self.fields or self.demands)


def reviewable_items(dossier: Dossier, discipline: str,
                     lang: str = DEFAULT_LANG) -> list[tuple[str, str, str]]:
    """Les éléments relisibles d'une discipline : (identifiant, libellé, valeur).

    Seuls les champs **déjà écrits** et de nature rédigeable y figurent : une
    date ne se reformule pas, et un champ vide relève du moteur.
    """
    if discipline not in FIELD_ORDER:
        raise InvalidDossier(f"Discipline inconnue : {discipline!r}.")

    bloc = dossier.discipline(discipline)
    items: list[tuple[str, str, str]] = []

    for champ in FIELD_ORDER[discipline]:
        if FIELD_KIND.get(champ) not in REVIEWABLE_KINDS:
            continue
        valeur = getattr(bloc, champ, "")
        if isinstance(valeur, (tuple, list)):
            valeur = ", ".join(valeur)
        if not (valeur or "").strip():
            continue
        items.append((champ, t(f"ct.f.{discipline}.{champ}", lang), valeur))

    if discipline == "d4":
        for creneau in _CHAIN_SLOTS:
            chaine = getattr(bloc, f"{creneau}_chain")
            for rang, marche in enumerate(chaine.steps, start=1):
                items.append((
                    f"{creneau}_chain.{rang}",
                    t("ct.review.why", lang,
                      slot=t(f"ct.slot.{creneau}", lang), rank=rang),
                    marche.statement,
                ))
    return items


def _normalise(texte: str) -> str:
    return re.sub(r"\s+", " ", (texte or "")).strip().lower()


def parse_review(raw: str, items: list[tuple[str, str, str]]) -> DisciplineReview:
    """Extrait reformulations et demandes d'une sortie de crew.

    Tolérant, comme les parseurs de SafetyScope, ThreatScope et RegWatch : le
    modèle ajoute des puces, du gras, une phrase d'introduction. Une ligne
    illisible est **ignorée**, elle ne fait pas échouer la relecture entière.
    """
    reformulations: dict[str, str] = {}
    demandes: list[str] = []

    for ligne in (raw or "").splitlines():
        if SEPARATOR not in ligne:
            continue
        gauche, _, droite = ligne.partition(SEPARATOR)
        gauche = _LEADING_NOISE.sub("", gauche).strip(" *_`#")
        texte = droite.strip(" *_`").strip()
        if not texte:
            continue

        numero = re.search(r"\d+", gauche)
        if numero:
            position = int(numero.group(0)) - 1
            if not 0 <= position < len(items):
                continue
            champ, _, origine = items[position]
            # ⚠️ Une reformulation identique à l'original n'apporte rien et
            # ferait cliquer « Appliquer » pour rien. Et une reformulation
            # VIDE effacerait le champ — donc changerait le verdict du
            # moteur. Les deux sont écartées.
            if _normalise(texte) == _normalise(origine):
                continue
            # ⚠️ **Une question n'est jamais une reformulation.** Vu en vrai
            # le 25/08/2026, en anglais : le modèle a rendu ses demandes sur
            # des lignes NUMÉROTÉES au lieu de lignes « ? ». « Depuis quand »
            # se voyait proposer « What is the exact date… ? » — et cliquer
            # « Appliquer » aurait écrit une question dans un document qui
            # part chez le client.
            #
            # La parade est structurelle et non un durcissement du prompt :
            # la valeur d'un champ de 8D n'est jamais une question. Si
            # l'original en était une, en revanche, on n'y touche pas.
            if texte.rstrip().endswith(("?", "\uff1f")) and not origine.rstrip().endswith("?"):
                if texte not in demandes:
                    demandes.append(texte[:MAX_DEMAND_LENGTH])
                continue
            # Premier arrivé, premier servi : si le modèle répète un numéro,
            # on garde sa première réponse plutôt que d'écraser au hasard.
            reformulations.setdefault(champ, texte[:MAX_REWRITE_LENGTH])
        elif DEMAND_MARK in gauche:
            if texte not in demandes:
                demandes.append(texte[:MAX_DEMAND_LENGTH])

    # L'ordre des champs suit celui de la saisie, pas celui de la réponse.
    ordonnees = tuple(
        FieldReview(champ, reformulations[champ])
        for champ, _, _ in items if champ in reformulations
    )
    return DisciplineReview("", ordonnees, tuple(demandes[:MAX_DEMANDS]))


def review_discipline(dossier: Dossier, discipline: str, task_callback=None,
                      lang: str = DEFAULT_LANG) -> DisciplineReview:
    """Relit une discipline — **interface stable**.

    Rend une relecture vide si la discipline ne contient rien de relisible :
    il n'y a alors rien à reformuler, et le moteur dit déjà ce qui manque.
    """
    items = reviewable_items(dossier, discipline, lang)
    if not items:
        return DisciplineReview(discipline)

    bloc = "\n".join(
        f"{rang}. {libelle} : {valeur}"
        for rang, (_, libelle, valeur) in enumerate(items, start=1)
    )

    crew = build_crew(t(f"ct.discipline.{discipline}", lang), bloc, len(items),
                      task_callback=task_callback, lang=lang)
    sortie = crew.kickoff()
    relecture = parse_review(str(sortie), items)
    return DisciplineReview(discipline, relecture.fields, relecture.demands)
