"""Proposition de contenu par l'IA — Ishikawa 5M et questions discriminantes.

⚠️ **Étape distincte de `review`.** La relecture porte sur ce que l'ingénieur
a **écrit** ; ici l'IA propose ce qu'il n'a **pas** écrit. C'est le même usage
que dans SafetyScope et ThreatScope : dérouler cinq familles de causes est
long et répétitif, et un modèle y est réellement bon.

## ⚠️ Ce que l'IA ne fait toujours pas

Elle **ne qualifie pas**. `CauseHypothesis` ne porte aucune nature : une
hypothèse arrive brute, et c'est l'ingénieur qui décide si elle relève d'un
état technique, d'un procédé, d'un système ou d'une personne. C'est le
pendant exact de « les cartes proposées arrivent vides côté cotation » dans
SafetyScope, et le test le verrouille.

Conséquence voulue : une hypothèse reprise dans une chaîne y entre **non
qualifiée**, et le moteur signale aussitôt `chain_step_without_nature`. L'outil
dit donc « à toi de dire ce que c'est » au lieu de le décider à ta place.

## ⚠️ La cohérence avec la règle de la chaîne

La famille « Main-d'œuvre » propose des hypothèses qui mettent en cause des
personnes — et c'est légitime : une personne est une hypothèse recevable **au
milieu** d'une chaîne. Ce que `whychain` interdit, c'est de s'y **arrêter**.
Les deux règles ne se contredisent pas, elles se complètent : l'Ishikawa ouvre
la piste, la chaîne oblige à aller au-delà.

## ⚠️ Familles et axes voyagent par NUMÉRO

Le prompt est en français, la sortie suit la langue du visiteur : « Méthode »
reviendrait en « Method » et l'appariement serait perdu. Même raison que le
marqueur « ? » de la relecture — rien de lexical ne fait contrat.
"""

import re
from dataclasses import dataclass

from i18n import DEFAULT_LANG, t

from .crew import SEPARATOR, build_ishikawa_crew, build_questions_crew
from .model import Dossier, InvalidDossier

# Les cinq familles de l'Ishikawa (5M). Identifiants stables.
FAMILY_ORDER = ("method", "machine", "material", "manpower", "environment")

# Les axes de la discrimination « est / n'est pas ».
AXIS_ORDER = ("what", "where", "when", "extent")

MAX_PER_FAMILY = 3
MAX_TEXT_LENGTH = 220

# Les champs du D2 qui décrivent le problème, dans l'ordre où on les donne.
_PROBLEM_FIELDS = ("what", "where", "since", "how_many", "is_not")

_LEADING_NOISE = re.compile(r"^[\s*_`#>\-–—•.)\]]+")


@dataclass(frozen=True)
class CauseHypothesis:
    """Une piste de cause, rattachée à une famille.

    ⚠️ Deux champs, et **aucune nature**. Qualifier une hypothèse serait
    coter, et l'IA ne cote jamais dans ce catalogue.
    `test_a_hypothesis_is_never_qualified` tombe si quelqu'un ajoute un champ
    `nature`, `rank` ou `score` — c'est le moment de se demander pourquoi.
    """

    family: str
    text: str


@dataclass(frozen=True)
class DiscriminatingQuestion:
    """Une question « est / n'est pas », rattachée à un axe.

    ⚠️ Une question ne s'applique jamais dans un champ : elle se réfléchit.
    C'est exactement le défaut corrigé à l'étape 5, où une question proposée
    comme valeur serait partie chez le client.
    """

    axis: str
    question: str


def family_labels(lang: str = DEFAULT_LANG) -> dict[str, str]:
    return {cle: t(f"ct.5m.{cle}", lang) for cle in FAMILY_ORDER}


def axis_labels(lang: str = DEFAULT_LANG) -> dict[str, str]:
    return {cle: t(f"ct.axis.{cle}", lang) for cle in AXIS_ORDER}


def problem_statement(dossier: Dossier, lang: str = DEFAULT_LANG) -> str:
    """La description du problème, telle qu'elle sera donnée au modèle.

    ⚠️ Seul le D2 est transmis. Les autres disciplines ne servent pas à
    chercher des causes, et une charge utile plus large ne ferait qu'exposer
    davantage de texte au fournisseur du modèle.
    """
    lignes = []
    for champ in _PROBLEM_FIELDS:
        valeur = (getattr(dossier.d2, champ, "") or "").strip()
        if valeur:
            lignes.append(f"{t(f'ct.f.d2.{champ}', lang)} : {valeur}")
    return "\n".join(lignes)


def _numbered(labels: dict[str, str]) -> str:
    return "\n".join(f"{rang}. {libelle}"
                     for rang, libelle in enumerate(labels.values(), start=1))


def _parse_indexed(raw: str, count: int, per_index: int) -> dict[int, list[str]]:
    """Range les propositions par numéro d'index.

    Tolérant comme les autres parseurs du projet. Une ligne illisible est
    **ignorée** ; elle ne décale rien et ne fait pas échouer la proposition
    entière.
    """
    par_index: dict[int, list[str]] = {}
    vus: set[str] = set()

    for ligne in (raw or "").splitlines():
        if SEPARATOR not in ligne:
            continue
        gauche, _, droite = ligne.partition(SEPARATOR)
        texte = droite.strip(" *_`").strip()
        if not texte:
            continue

        numero = re.search(r"\d+", _LEADING_NOISE.sub("", gauche).strip(" *_`#"))
        if not numero:
            continue
        position = int(numero.group(0)) - 1
        # ⚠️ Défense en profondeur, pas un contrôle porteur : les deux
        # parseurs relisent ce dictionnaire par `range(count)`, donc une clé
        # hors bornes n'est jamais lue. Le retirer ne change rien AUJOURD'HUI
        # — mesuré par mutation, 19/19.
        #
        # Il reste parce que « 0 » donne `position = -1`, et qu'en Python un
        # index négatif désigne le DERNIER élément : le jour où quelqu'un
        # indexera `FAMILY_ORDER[position]` directement, une ligne « 0 || … »
        # se rangerait silencieusement dans « Milieu ».
        if not 0 <= position < count:
            continue

        empreinte = re.sub(r"\s+", " ", texte).strip().lower()
        if empreinte in vus:
            continue

        siens = par_index.setdefault(position, [])
        if len(siens) >= per_index:
            continue
        vus.add(empreinte)
        siens.append(texte[:MAX_TEXT_LENGTH])

    return par_index


def parse_hypotheses(raw: str) -> tuple[CauseHypothesis, ...]:
    """Extrait les hypothèses, rangées dans l'ordre des familles."""
    par_famille = _parse_indexed(raw, len(FAMILY_ORDER), MAX_PER_FAMILY)
    return tuple(
        CauseHypothesis(FAMILY_ORDER[position], texte)
        for position in range(len(FAMILY_ORDER))
        for texte in par_famille.get(position, [])
    )


def parse_questions(raw: str) -> tuple[DiscriminatingQuestion, ...]:
    """Extrait une question par axe, dans l'ordre des axes."""
    par_axe = _parse_indexed(raw, len(AXIS_ORDER), 1)
    return tuple(
        DiscriminatingQuestion(AXIS_ORDER[position], par_axe[position][0])
        for position in range(len(AXIS_ORDER))
        if par_axe.get(position)
    )


def suggest_causes(dossier: Dossier, task_callback=None,
                   lang: str = DEFAULT_LANG) -> tuple[CauseHypothesis, ...]:
    """Propose des hypothèses de cause — **interface stable**."""
    probleme = problem_statement(dossier, lang)
    if not probleme:
        raise InvalidDossier("Le problème n'est pas décrit.")

    crew = build_ishikawa_crew(probleme, _numbered(family_labels(lang)),
                               MAX_PER_FAMILY, task_callback, lang)
    return parse_hypotheses(str(crew.kickoff()))


def suggest_questions(dossier: Dossier, task_callback=None,
                      lang: str = DEFAULT_LANG) -> tuple[DiscriminatingQuestion, ...]:
    """Propose les questions discriminantes — **interface stable**."""
    probleme = problem_statement(dossier, lang)
    if not probleme:
        raise InvalidDossier("Le problème n'est pas décrit.")

    crew = build_questions_crew(probleme, _numbered(axis_labels(lang)),
                                task_callback, lang)
    return parse_questions(str(crew.kickoff()))
