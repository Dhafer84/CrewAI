"""Complétude et verrouillage d'un dossier 8D — le cœur déterministe.

Un 8D est une **démarche ordonnée**, pas un formulaire à huit cases. Ce
module dit deux choses, et rien d'autre :

1. **ce qui manque**, discipline par discipline ;
2. **ce qui n'a pas le droit d'être renseigné encore**, parce qu'une étape
   amont n'est pas étayée.

Aucun appel réseau, aucun LLM. C'est ce qui permet à l'outil d'être complet
et livrable sans qu'aucun modèle ne soit appelé — l'IA n'aidera qu'à mieux
écrire ce que ces règles réclament déjà.

## Les verrous, et le seul qui n'existe pas

    D2 ──▶ D4 ──▶ D5 ──▶ D6            D3 ne dépend de rien

- **D4 attend D2.** Chercher la cause d'un problème qu'on n'a pas su décrire
  produit une hypothèse, pas une cause. C'est la faute la plus courante : on
  saute à la cause.
- **D5 attend D4.** Une action corrective permanente qui précède la cause
  racine corrige une intuition.
- **D6 attend D5.** On ne valide pas ce qui n'a pas été décidé.
- ⚠️ **D3 ne dépend de RIEN, délibérément.** Protéger le client n'attend pas
  la cause racine — c'est même tout l'intérêt du containment. Le verrouiller
  serait une faute de métier, pas une rigueur supplémentaire.

⚠️ **Une discipline verrouillée ne signale que son verrou.** Lister en plus
ses champs manquants noierait l'information utile sous du bruit : ce n'est
pas « il manque l'action corrective », c'est « il est trop tôt pour l'écrire ».

## Ce qui est jugé ici, et ce qui ne l'est pas

Ce module vérifie la **présence** des éléments et compose les contrôles
propres à chaque discipline — la solidité des chaînes de pourquoi du D4 est
déléguée à `whychain`, qui ne sait pas pour qui il travaille. Et la qualité de la
*rédaction* relève de l'IA, qui **propose** sans jamais décider : le verdict
de complétude reste ici, il ne se délègue pas à un modèle.
"""

from dataclasses import dataclass

from i18n import DEFAULT_LANG, t

from .model import (
    DISCIPLINE_ORDER,
    FIELD_KIND,
    FIELD_ORDER,
    REVIEWABLE_KINDS,
    Dossier,
    InvalidDossier,
)
from .whychain import CHAIN_CODES, analyse, chain_rules

# Champs exigés par discipline : (attribut, identifiant du constat).
#
# ⚠️ Table déclarative, et non une suite de `if` : les règles se lisent d'un
# coup d'œil, et un test peut vérifier qu'aucune discipline n'est oubliée.
_REQUIRED: dict[str, list[tuple[str, str]]] = {
    "d1": [("owner", "d1.no_owner")],
    "d2": [
        ("what", "d2.no_what"),
        ("where", "d2.no_where"),
        ("since", "d2.no_since"),
        ("how_many", "d2.no_extent"),
        # ⚠️ Le champ que personne ne remplit, et le plus discriminant.
        ("is_not", "d2.no_is_not"),
    ],
    "d3": [
        ("action", "d3.no_action"),
        ("due_date", "d3.no_due_date"),
        ("effectiveness_check", "d3.no_effectiveness_check"),
    ],
    "d4": [
        ("occurrence", "d4.no_occurrence_cause"),
        # ⚠️ À égalité avec la précédente. Voir `model.RootCause`.
        ("escape", "d4.no_escape_cause"),
    ],
    "d5": [
        ("on_occurrence", "d5.no_action_on_occurrence"),
        ("on_escape", "d5.no_action_on_escape"),
    ],
    "d6": [
        ("implemented_on", "d6.no_date"),
        ("evidence", "d6.no_evidence"),
    ],
    # ⚠️ Asymétrie assumée : seul le retour dans les documents de référence
    # est exigé. « Leçons apprises » est un champ de confort ; en faire une
    # obligation ajouterait de la bureaucratie, pas de la rigueur.
    "d7": [("systemic_update", "d7.no_systemic_update")],
}

# Discipline → discipline dont elle dépend. D3 en est volontairement absent.
_DEPENDS_ON = {"d4": "d2", "d5": "d4", "d6": "d5"}

# Les créneaux du D4 — les deux causes, et donc les deux chaînes.
SLOT_ORDER = ("occurrence", "escape")

# Constats propres à la clôture. Ils ne découlent d'aucun champ : D8 juge les
# sept autres disciplines, il ne se contrôle pas lui-même.
_CLOSURE_CODES = ("d8.premature_closure", "d8.not_closed", "d8.no_closure_date")

# Disciplines dont la complétude conditionne la clôture. D8 juge les sept
# autres, il ne se juge pas lui-même.
_BEFORE_CLOSURE = [k for k in DISCIPLINE_ORDER if k != "d8"]


def gap_codes() -> list[str]:
    """Tous les constats que le moteur peut émettre.

    ⚠️ Construit depuis les tables, jamais recopié à la main : une liste
    parallèle finirait par oublier un constat, et la page afficherait un
    identifiant brut au visiteur. Un test vérifie l'inverse — qu'aucun
    constat émis n'échappe à cette liste.
    """
    codes = [code for regles in _REQUIRED.values() for _, code in regles]
    codes += [f"{cle}.locked" for cle in _DEPENDS_ON]
    codes += [f"d4.{code}" for code in CHAIN_CODES]
    codes += list(_CLOSURE_CODES)
    return codes


@dataclass(frozen=True)
class Gap:
    """Un constat : ce qui manque, ou ce qu'il est trop tôt pour écrire.

    ⚠️ `code` est un **identifiant stable**, jamais un libellé. Le texte se
    demande au catalogue via `gap_label()`, au moment de l'affichage. Le
    chantier d'internationalisation a montré quatre fois ce que coûte une
    chaîne d'affichage qui pilote quelque chose.
    """

    discipline: str
    code: str
    blocking: bool = False
    # Quelle des deux causes du D4 est visée : « occurrence » ou « escape ».
    # Vide partout ailleurs — un constat de D3 ne vise rien de particulier.
    slot: str = ""
    # Le champ visé, quand le constat en vise un. Sert à nommer le coupable
    # dans le message d'un verrou.
    field: str = ""
    # ⚠️ Pour un VERROU : les constats de la discipline amont, afin que le
    # message dise ce qui manque au lieu de laisser deviner. Vide quand
    # l'amont est lui-même verrouillé — le vrai blocage est alors plus haut,
    # et c'est la carte de l'amont qui l'explique.
    missing: tuple[str, ...] = ()

    @property
    def is_lock(self) -> bool:
        return self.code.endswith(".locked")


def _missing(dossier: Dossier, key: str) -> list[Gap]:
    """Les champs exigés qu'une discipline n'a pas renseignés."""
    bloc = dossier.discipline(key)
    return [
        Gap(discipline=key, code=code, field=attribut)
        for attribut, code in _REQUIRED.get(key, [])
        if not getattr(bloc, attribut, "")
    ]


# Contrôles qui ne se ramènent pas à une présence de champ. Table déclarative
# elle aussi : greffer les chaînes de pourquoi ici plutôt que dans le corps
# de `check` garde les règles lisibles d'un coup d'œil.
_EXTRA = {}


def _chain_gaps(dossier: Dossier) -> list["Gap"]:
    """Les deux chaînes du D4, examinées l'une après l'autre.

    ⚠️ Une cause qui n'est pas énoncée ne voit pas sa chaîne examinée. Dire
    « la cause manque » **et** « sa chaîne manque » serait dire deux fois la
    même chose — même principe qu'une discipline verrouillée, qui ne signale
    que son verrou.
    """
    constats: list[Gap] = []
    for creneau, cause, chaine in (
        ("occurrence", dossier.d4.occurrence, dossier.d4.occurrence_chain),
        ("escape", dossier.d4.escape, dossier.d4.escape_chain),
    ):
        if not cause:
            continue
        constats.extend(
            Gap(discipline="d4", code=f"d4.{code}", slot=creneau)
            for code in analyse(chaine)
        )
    return constats


_EXTRA["d4"] = _chain_gaps


def _gaps_of(dossier: Dossier, key: str) -> list["Gap"]:
    """Tout ce qui manque à une discipline — champs ET contrôles propres."""
    constats = _missing(dossier, key)
    extra = _EXTRA.get(key)
    if extra:
        constats.extend(extra(dossier))
    return constats


def is_empty(dossier: Dossier, key: str) -> bool:
    """Aucun champ exigé n'est renseigné — la discipline n'est pas entamée."""
    if key not in DISCIPLINE_ORDER:
        raise InvalidDossier(f"Discipline inconnue : {key!r}.")
    if key == "d8":
        return not dossier.d8.claimed_closed and not dossier.d8.closed_on
    return len(_missing(dossier, key)) == len(_REQUIRED.get(key, []))


def check(dossier: Dossier) -> list[Gap]:
    """Tout ce qui empêche ce dossier d'être tenu pour résolu.

    Rendu dans l'ordre des disciplines. Une liste vide signifie que le
    dossier est complet **et** clos.
    """
    if not isinstance(dossier, Dossier):
        raise InvalidDossier("Un dossier 8D est attendu.")

    constats: list[Gap] = []
    verrouillees: set[str] = set()

    for cle in DISCIPLINE_ORDER:
        if cle == "d8":
            continue

        amont = _DEPENDS_ON.get(cle)
        # ⚠️ `_gaps_of` et non `_missing` : une cause énoncée mais mal étayée
        # ne déverrouille pas les actions permanentes. C'est tout l'objet de
        # la chaîne de pourquoi — sans quoi elle ne serait qu'un ornement.
        amont_cascade = amont in verrouillees if amont else False
        amont_gaps = _gaps_of(dossier, amont) if amont else []
        if amont and (amont_cascade or amont_gaps):
            # Trop tôt : on le dit une fois, et on se tait sur le reste — mais
            # on NOMME ce qui bloque, sinon l'ingénieur doit deviner quelle
            # case d'une autre discipline le retient.
            verrouillees.add(cle)
            constats.append(Gap(
                discipline=cle, code=f"{cle}.locked", blocking=True,
                missing=() if amont_cascade else tuple(g.code for g in amont_gaps),
            ))
            continue

        constats.extend(_gaps_of(dossier, cle))

    constats.extend(_closure_gaps(dossier, amont_incomplet=bool(constats)))
    return constats


def _closure_gaps(dossier: Dossier, amont_incomplet: bool) -> list[Gap]:
    """D8 — la clôture, seule discipline qui juge les sept autres.

    ⚠️ Tant que l'amont est incomplet, D8 ne réclame rien : rappeler qu'un
    dossier en cours n'est pas clos serait du bruit. Il ne parle que si la
    clôture est **prétendue** — et c'est alors le constat le plus grave du
    dossier.
    """
    d8 = dossier.d8

    if amont_incomplet:
        if d8.claimed_closed:
            return [Gap(discipline="d8", code="d8.premature_closure", blocking=True)]
        return []

    if not d8.claimed_closed:
        return [Gap(discipline="d8", code="d8.not_closed")]
    if not d8.closed_on:
        return [Gap(discipline="d8", code="d8.no_closure_date")]
    return []


def is_closable(dossier: Dossier) -> bool:
    """Les sept premières disciplines sont-elles complètes ?

    ⚠️ Ne dit pas que le dossier EST clos — dit qu'il a le droit de l'être.
    La prétention de clôture vit dans le dossier ; le droit se calcule ici.
    """
    if not isinstance(dossier, Dossier):
        raise InvalidDossier("Un dossier 8D est attendu.")
    return not [g for g in check(dossier) if g.discipline in _BEFORE_CLOSURE]


def status(dossier: Dossier) -> dict[str, str]:
    """État de chaque discipline : empty · incomplete · locked · complete.

    Destiné à l'interface — mais calculé ici, pour que la page n'ait aucune
    règle à réécrire. Même motif que `/hara/matrix` et `/tara/scales`.
    """
    constats = check(dossier)
    par_discipline: dict[str, list[Gap]] = {}
    for gap in constats:
        par_discipline.setdefault(gap.discipline, []).append(gap)

    etats = {}
    for cle in DISCIPLINE_ORDER:
        siens = par_discipline.get(cle, [])
        if any(g.is_lock for g in siens):
            etats[cle] = "locked"
        elif not siens:
            etats[cle] = "complete"
        elif is_empty(dossier, cle):
            etats[cle] = "empty"
        else:
            etats[cle] = "incomplete"
    return etats


# Constat → (discipline, champ), pour nommer un champ plutôt qu'un constat
# dans le message d'un verrou. Construit depuis `_REQUIRED`, jamais recopié.
_FIELD_OF_CODE = {
    code: (discipline, champ)
    for discipline, regles in _REQUIRED.items()
    for champ, code in regles
}


def gap_label(gap: Gap, lang: str = DEFAULT_LANG) -> str:
    """Le constat, dit dans une langue. Le moteur, lui, n'en connaît aucune.

    ⚠️ Un verrou nomme ce qui le cause. « Trop tôt : le problème n'est pas
    encore décrit » obligeait à remonter à la carte amont pour trouver quelle
    case retenait la discipline — une devinette que l'outil imposait sans
    raison.
    """
    texte = t(f"ct.gap.{gap.code}", lang)
    if not gap.missing:
        return texte

    champs, autres = [], []
    for code in gap.missing:
        cible = _FIELD_OF_CODE.get(code)
        if cible:
            champs.append(t(f"ct.f.{cible[0]}.{cible[1]}", lang))
        else:
            autres.append(t(f"ct.gap.{code}", lang))

    # « il manque » ne convient qu'à des champs vides ; un constat de chaîne
    # n'est pas un manque, c'est quelque chose à corriger.
    if autres:
        return texte + t("ct.lock.blocking", lang, items=", ".join(champs + autres))
    return texte + t("ct.lock.missing", lang, items=", ".join(champs))


def slot_label(slot: str, lang: str = DEFAULT_LANG) -> str:
    """« cause d'occurrence » / « cause de non-détection ». Vide si sans objet."""
    return t(f"ct.slot.{slot}", lang) if slot else ""


def discipline_label(key: str, lang: str = DEFAULT_LANG) -> str:
    """Le nom d'une discipline."""
    if key not in DISCIPLINE_ORDER:
        raise InvalidDossier(f"Discipline inconnue : {key!r}.")
    return t(f"ct.discipline.{key}", lang)


def rules(lang: str = DEFAULT_LANG) -> dict:
    """Le contrat servi à l'interface — **source de vérité unique**.

    La page ne code aucune règle : elle lit les champs exigés, les
    dépendances entre disciplines, les natures qui peuvent conclure une
    chaîne, et le texte de chaque constat.

    ⚠️ Elle en tire un indicateur **de commodité**. Le verdict qui compte est
    recalculé côté serveur avant tout export — le tableau vient du navigateur
    et n'est pas de confiance. Même discipline que les exports HARA et TARA.
    """
    return {
        "order": list(DISCIPLINE_ORDER),
        "labels": {cle: discipline_label(cle, lang) for cle in DISCIPLINE_ORDER},
        "fields": {cle: list(champs) for cle, champs in FIELD_ORDER.items()},
        "kinds": dict(FIELD_KIND),
        "reviewableKinds": list(REVIEWABLE_KINDS),
        "required": {cle: [champ for champ, _ in regles]
                     for cle, regles in _REQUIRED.items()},
        "gapOf": {cle: dict(regles) for cle, regles in _REQUIRED.items()},
        "dependsOn": dict(_DEPENDS_ON),
        "slots": {creneau: slot_label(creneau, lang) for creneau in SLOT_ORDER},
        "gaps": {code: t(f"ct.gap.{code}", lang) for code in gap_codes()},
        "chain": chain_rules(lang),
    }
