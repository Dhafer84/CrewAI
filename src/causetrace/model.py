"""Objets métier du dossier 8D.

Le dossier saisi dans l'interface est reconstruit ici avant toute
vérification et avant tout export : on ne fait jamais confiance aux données
reçues du navigateur — même discipline que `threatscope.analysis`.

## ⚠️ Aucune chaîne d'affichage ne pilote quoi que ce soit

Le chantier d'internationalisation a fait découvrir **quatre fois** qu'un
libellé servait d'identifiant (`TREATMENTS["requires"]`, `Source.label`, la
lettre S/E/C de l'export HARA, `_SHAPE_CHECKS` de SentinelScan). Ici la
leçon est appliquée d'emblée : disciplines et constats portent des
**identifiants stables** (`d4`, `d4.no_escape_cause`), et leur libellé se
demande au catalogue au moment de l'affichage. Rien dans ce module ne dépend
d'une langue.

## Pourquoi le D2 est découpé en champs

Un 8D moyen décrit son problème en une phrase — « défaut sur calculateur » —
qui ne permet ni de trier, ni de comparer, ni de borner. Le découper en
**quoi / où / depuis quand / combien / ce qui n'est pas touché** rend la
complétude *mécanique* : il n'y a rien à interpréter, le champ est rempli ou
il ne l'est pas.

C'est ce qui permet à l'IA de rester facultative. Si le moteur devait deviner
dans un texte libre s'il « manque une quantification », il faudrait un modèle
pour produire le résultat de l'outil. Ici le modèle ne fait qu'aider à mieux
écrire ce que la structure réclame déjà.

⚠️ `is_not` est le champ que personne ne remplit et c'est le plus utile :
dire ce qui n'est **pas** touché est ce qui sépare une cause d'une
coïncidence. Il est traité comme les autres, donc exigé.
"""

from dataclasses import dataclass, field
from datetime import date

# Les huit disciplines, dans l'ordre. Identifiants stables : ce sont eux qui
# voyagent, jamais les libellés.
DISCIPLINE_ORDER = ["d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8"]

# Ordre d'affichage des champs, discipline par discipline — y compris les
# facultatifs, que `check._REQUIRED` ne connaît pas.
#
# ⚠️ UNE seule liste, consommée par la page ET par l'export. Sans elle, un
# champ ajouté au modèle apparaîtrait à l'écran et **disparaîtrait du
# classeur envoyé au client**, sans qu'aucun test le voie. C'est le motif
# déjà payé par les deux listes d'actifs versionnés qui avaient divergé.
# `test_no_field_escapes_the_display_order` verrouille l'inverse.
FIELD_ORDER: dict[str, tuple[str, ...]] = {
    "d1": ("owner", "members"),
    "d2": ("what", "where", "since", "how_many", "is_not"),
    "d3": ("action", "due_date", "effectiveness_check"),
    "d4": ("occurrence", "escape"),
    "d5": ("on_occurrence", "on_escape"),
    "d6": ("implemented_on", "evidence"),
    "d7": ("systemic_update", "lessons"),
    "d8": ("claimed_closed", "closed_on"),
}

# Nature de saisie de chaque champ. ⚠️ TROISIÈME consommateur d'une même
# information : la page en tire son type de champ, l'export son formatage,
# et la relecture par IA ce qu'elle a le droit de reformuler — une date ne se
# reformule pas. Trois listes parallèles auraient divergé ; il n'y en a qu'une.
#   "text" court · "long" texte libre · "date" ISO · "bool" case à cocher
FIELD_KIND: dict[str, str] = {
    "owner": "text", "members": "text",
    "what": "long", "where": "text", "since": "text", "how_many": "text",
    "is_not": "long",
    "action": "long", "due_date": "date", "effectiveness_check": "long",
    "occurrence": "long", "escape": "long",
    "on_occurrence": "long", "on_escape": "long",
    "implemented_on": "date", "evidence": "long",
    "systemic_update": "long", "lessons": "long",
    "claimed_closed": "bool", "closed_on": "date",
}

# Les natures que l'IA a le droit de reformuler. Une date ou une case à
# cocher n'ont pas de rédaction à améliorer.
REVIEWABLE_KINDS = ("text", "long")

# Bornes de saisie. Généreuses sur les causes et les actions — c'est là que
# le fond se joue — serrées sur les champs de repérage.
MAX_SHORT = 120
MAX_TEXT = 500
MAX_MEMBERS = 8
MAX_STATEMENT = 300

# Plafond de profondeur d'une chaîne de pourquoi. Borne d'interface, pas une
# règle de méthode : la règle vit dans `whychain`.
MAX_STEPS = 7

# ⚠️ La NATURE d'un pourquoi, choisie dans une liste fermée — et c'est tout
# l'édifice de l'étape 2. Identifiants stables, jamais des libellés.
#
# Détecter « la chaîne s'arrête sur un opérateur » dans du texte libre
# demanderait un lexique de mots de blâme, en deux langues. Ce serait
# exactement l'erreur « Functional Safety » de RegWatch — un THÈME pris pour
# un marqueur — avec en prime deux lexiques appelés à diverger.
#
# En faisant qualifier chaque pourquoi par l'ingénieur, la règle devient
# mécanique, sans un seul mot de vocabulaire métier dans le moteur. Même
# geste qu'au D2 : on structure la saisie au lieu d'interpréter du texte.
NATURE_ORDER = ["technical", "process", "system", "person"]


class InvalidDossier(ValueError):
    """Dossier inexploitable — message destiné à l'utilisateur final."""


def _clean(value, cap: int) -> str:
    """Ramène une entrée quelconque à une chaîne bornée.

    Le navigateur peut envoyer `None`, un nombre ou une liste. On ne lève
    pas : un champ illisible devient un champ vide, et c'est alors le
    contrôle de complétude qui le signalera — au bon endroit, avec le bon
    message.
    """
    if value is None or isinstance(value, (dict, list, tuple)):
        return ""
    return str(value).strip()[:cap]


def _clean_date(value) -> str:
    """Une date ISO `AAAA-MM-JJ`, ou la chaîne vide si elle est illisible.

    ⚠️ Volontairement limité à l'ISO : `%B` / `%b` dépendent de la locale du
    serveur, piège déjà rencontré sur RegWatch. Le champ de saisie de la page
    sera un `<input type="date">`, qui rend précisément ce format.

    Une date mal formée est **écartée**, pas devinée. Un 31 février inventé
    dans un engagement client vaut moins que pas de date du tout.
    """
    brut = _clean(value, 10)
    if not brut:
        return ""
    try:
        return date.fromisoformat(brut).isoformat()
    except ValueError:
        return ""


@dataclass(frozen=True)
class Team:
    """D1 — l'équipe, et surtout son pilote.

    Un 8D sans pilote nommé n'avance pas : c'est le constat le plus banal du
    métier, et il se vérifie mécaniquement.
    """

    owner: str = ""
    members: tuple[str, ...] = ()

    @staticmethod
    def build(owner="", members=()) -> "Team":
        if isinstance(members, str):
            members = [members]
        elif not isinstance(members, (list, tuple)):
            members = []
        propres = [m for m in (_clean(x, MAX_SHORT) for x in members) if m]
        return Team(owner=_clean(owner, MAX_SHORT), members=tuple(propres[:MAX_MEMBERS]))


@dataclass(frozen=True)
class Problem:
    """D2 — la description du problème, découpée pour être vérifiable."""

    what: str = ""
    where: str = ""
    since: str = ""
    how_many: str = ""
    is_not: str = ""

    @staticmethod
    def build(what="", where="", since="", how_many="", is_not="") -> "Problem":
        return Problem(
            what=_clean(what, MAX_TEXT),
            where=_clean(where, MAX_SHORT),
            since=_clean(since, MAX_SHORT),
            how_many=_clean(how_many, MAX_SHORT),
            is_not=_clean(is_not, MAX_TEXT),
        )


@dataclass(frozen=True)
class Containment:
    """D3 — les actions immédiates de protection du client.

    Une action de containment sans date de fin ni contrôle d'efficacité ne se
    referme jamais : elle devient un état permanent que plus personne ne
    remet en cause.
    """

    action: str = ""
    due_date: str = ""
    effectiveness_check: str = ""

    @staticmethod
    def build(action="", due_date="", effectiveness_check="") -> "Containment":
        return Containment(
            action=_clean(action, MAX_TEXT),
            due_date=_clean_date(due_date),
            effectiveness_check=_clean(effectiveness_check, MAX_TEXT),
        )


@dataclass(frozen=True)
class Step:
    """Un « pourquoi » : une affirmation, et sa nature."""

    statement: str = ""
    nature: str = ""


@dataclass(frozen=True)
class Chain:
    """Une chaîne de pourquoi, du symptôme vers la cause.

    ⚠️ `truncated` existe pour que le plafond **ne cache jamais de travail**.
    Écarter les derniers pourquoi en silence ferait croire à une chaîne
    courte là où il y a une chaîne trop longue — même discipline que la
    reprise HARA → TARA, qui importe six événements sur neuf **et le dit**.
    """

    steps: tuple[Step, ...] = ()
    truncated: bool = False

    def __len__(self) -> int:
        return len(self.steps)

    @staticmethod
    def build(raw) -> "Chain":
        if isinstance(raw, (str, bytes)) or not isinstance(raw, (list, tuple)):
            return Chain()

        etapes: list[Step] = []
        # Borne de traitement : le plafond utile est MAX_STEPS, mais on lit un
        # peu au-delà pour pouvoir dire « tronquée ». Au-delà, c'est une charge
        # utile abusive et non une saisie.
        for brut in list(raw)[:100]:
            if isinstance(brut, dict):
                affirmation = _clean(brut.get("statement"), MAX_STATEMENT)
                nature = _clean(brut.get("nature"), MAX_SHORT)
            else:
                # Une chaîne de caractères seule reste une saisie valable :
                # c'est un pourquoi qu'on n'a pas encore qualifié.
                affirmation, nature = _clean(brut, MAX_STATEMENT), ""
            if not affirmation:
                # Ligne vide du formulaire : un artefact d'interface, pas un
                # oubli de l'ingénieur. La chaîne trop courte le dira.
                continue
            etapes.append(Step(affirmation, nature if nature in NATURE_ORDER else ""))

        return Chain(steps=tuple(etapes[:MAX_STEPS]), truncated=len(etapes) > MAX_STEPS)


@dataclass(frozen=True)
class RootCause:
    """D4 — les DEUX causes racines.

    ⚠️ C'est le trou n° 1 des 8D réels. On explique pourquoi le défaut est
    **né** (cause d'occurrence) et on s'arrête là ; personne n'explique
    pourquoi les contrôles en place l'ont **laissé passer** (cause de
    non-détection). Or sans la seconde, le prochain défaut — qui ne sera pas
    le même — sortira par la même porte.

    Les deux sont donc exigées, à égalité.

    Chaque cause porte **sa propre chaîne de pourquoi** : énoncer une cause
    sans montrer comment on y est arrivé ne démontre rien. Les règles qui
    jugent ces chaînes vivent dans `whychain`.
    """

    occurrence: str = ""
    escape: str = ""
    occurrence_chain: Chain = field(default_factory=Chain)
    escape_chain: Chain = field(default_factory=Chain)

    @staticmethod
    def build(occurrence="", escape="", occurrence_chain=(), escape_chain=()) -> "RootCause":
        return RootCause(
            occurrence=_clean(occurrence, MAX_TEXT),
            escape=_clean(escape, MAX_TEXT),
            occurrence_chain=Chain.build(occurrence_chain),
            escape_chain=Chain.build(escape_chain),
        )


@dataclass(frozen=True)
class CorrectiveAction:
    """D5 — les actions correctives permanentes, une par cause.

    ⚠️ Symétrique du D4, et pour la même raison : corriger l'occurrence sans
    corriger la détection laisse le dispositif de contrôle aussi aveugle
    qu'avant. Deux causes, deux actions.
    """

    on_occurrence: str = ""
    on_escape: str = ""

    @staticmethod
    def build(on_occurrence="", on_escape="") -> "CorrectiveAction":
        return CorrectiveAction(
            on_occurrence=_clean(on_occurrence, MAX_TEXT),
            on_escape=_clean(on_escape, MAX_TEXT),
        )


@dataclass(frozen=True)
class Validation:
    """D6 — la mise en œuvre, et la PREUVE que ça a marché.

    Une action déclarée mise en œuvre sans mesure de son effet est une
    intention, pas une validation.
    """

    implemented_on: str = ""
    evidence: str = ""

    @staticmethod
    def build(implemented_on="", evidence="") -> "Validation":
        return Validation(
            implemented_on=_clean_date(implemented_on),
            evidence=_clean(evidence, MAX_TEXT),
        )


@dataclass(frozen=True)
class Prevention:
    """D7 — le retour systémique, la seule discipline tournée vers l'avenir.

    Un 8D qui ne remonte pas dans les documents de référence — AMDEC, plan de
    surveillance, standards — soigne un cas et laisse le système identique.
    C'est la différence entre corriger et prévenir.
    """

    systemic_update: str = ""
    lessons: str = ""

    @staticmethod
    def build(systemic_update="", lessons="") -> "Prevention":
        return Prevention(
            systemic_update=_clean(systemic_update, MAX_TEXT),
            lessons=_clean(lessons, MAX_TEXT),
        )


@dataclass(frozen=True)
class Closure:
    """D8 — la clôture.

    Le seul champ qui soit une **prétention** et non une information : le
    dossier n'est clos que si le moteur y consent. Voir `check.is_closable`.
    """

    claimed_closed: bool = False
    closed_on: str = ""

    @staticmethod
    def build(claimed_closed=False, closed_on="") -> "Closure":
        return Closure(
            claimed_closed=bool(claimed_closed),
            closed_on=_clean_date(closed_on),
        )


@dataclass(frozen=True)
class Dossier:
    """Un 8D complet — huit disciplines, aucune facultative."""

    reference: str = ""
    title: str = ""
    d1: Team = field(default_factory=Team)
    d2: Problem = field(default_factory=Problem)
    d3: Containment = field(default_factory=Containment)
    d4: RootCause = field(default_factory=RootCause)
    d5: CorrectiveAction = field(default_factory=CorrectiveAction)
    d6: Validation = field(default_factory=Validation)
    d7: Prevention = field(default_factory=Prevention)
    d8: Closure = field(default_factory=Closure)

    def discipline(self, key: str):
        """La discipline portant cet identifiant."""
        if key not in DISCIPLINE_ORDER:
            raise InvalidDossier(f"Discipline inconnue : {key!r}.")
        return getattr(self, key)


_BUILDERS = {
    "d1": Team,
    "d2": Problem,
    "d3": Containment,
    "d4": RootCause,
    "d5": CorrectiveAction,
    "d6": Validation,
    "d7": Prevention,
    "d8": Closure,
}


def build_dossier(payload) -> Dossier:
    """Reconstruit un dossier depuis une charge utile quelconque.

    Ne lève que si la charge n'est pas un objet : un champ absent, en trop ou
    du mauvais type devient un champ vide, et c'est le contrôle de
    complétude qui parle ensuite. Le but n'est pas de rejeter un brouillon,
    c'est de dire ce qui lui manque.
    """
    if not isinstance(payload, dict):
        raise InvalidDossier("Le dossier attendu est un objet.")

    disciplines = {}
    for cle, classe in _BUILDERS.items():
        brut = payload.get(cle)
        if not isinstance(brut, dict):
            brut = {}
        connus = {c.name for c in classe.__dataclass_fields__.values()}
        disciplines[cle] = classe.build(**{k: v for k, v in brut.items() if k in connus})

    return Dossier(
        reference=_clean(payload.get("reference"), MAX_SHORT),
        title=_clean(payload.get("title"), MAX_SHORT),
        **disciplines,
    )
