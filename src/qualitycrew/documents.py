"""Documents du visiteur : la vérification AVANT l'audit (11/10/2026).

Étape 2 de « l'audit sur les documents du visiteur » (voir CLAUDE.md). Aucun
appel réseau, aucun LLM : ce module dit si les trois documents envoyés sont
**exploitables** par les agents, et sinon quoi corriger — sans consommer
d'audit (10 par jour pour tout le site).

## Ce qui est refusé

- un document **manquant**, **vide**, ou qui **n'est pas du texte** (un
  binaire renommé en `.md` arrive plein de NUL ou de caractères de
  remplacement « � » une fois lu par le navigateur) ;
- un document **trop gros**, ou les trois ensemble : la taille fait le coût
  en jetons, sur un quota Groq quotidien (limites PROVISOIRES, à fixer après
  la mesure de l'étape 5) ;
- un document **sans sa structure** : au moins un titre `SRS-001`, `TC-001`
  ou `R-01` selon le document. Attrape aussi deux documents inversés (le plan
  de test cite des `SRS-…`, mais jamais en titre) ;
- un **gabarit pas rempli** : il reste au moins `_UNFILLED_MIN` des
  `[crochets]` du gabarit téléchargé.

## Ce qui n'est PAS refusé, délibérément

Une exigence sans critère d'acceptation, une trace amont absente, une
matrice de couverture incomplète, un ou deux `[crochets]` oubliés : ce sont
précisément les défauts que l'audit doit TROUVER. Les refuser ici viderait
l'audit de son objet. Ce module juge la forme minimale, jamais la qualité.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from i18n import DEFAULT_LANG, t

# Les trois documents, dans l'ordre des agents (et de `run_audit`)
DOC_ORDER = ("srs", "test_plan", "review_report")

# ⚠️ PROVISOIRES : l'exemple fait ~10 Ko au total (srs 5,7 Ko). À fixer avec
# la mesure réelle (jetons, durée) de l'étape 5 — voir CLAUDE.md.
MAX_DOC_BYTES = 12_000
MAX_TOTAL_BYTES = 20_000

# Structure minimale : au moins un TITRE de section portant l'identifiant.
# En titre seulement : le plan de test cite des SRS-… dans « Vérifie : », il ne
# doit pas passer pour un document d'exigences.
_REQUIRED_HEADING = {
    "srs": re.compile(r"^#{2,4}[ \t]*SRS-\d{3}\b", re.M),
    "test_plan": re.compile(r"^#{2,4}[ \t]*TC-\d{3}\b", re.M),
    "review_report": re.compile(r"^#{2,4}[ \t]*R-\d{2}\b", re.M),
}

# Un gabarit est « pas rempli » s'il reste au moins ce nombre de ses
# [crochets] (distincts). Un ou deux oubliés passent : l'audit les verra.
_UNFILLED_MIN = 3
# Au-delà de cette part de caractères de contrôle ou « � », ce n'est pas du texte
_MAX_GARBAGE_RATIO = 0.01

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "templates"
_PLACEHOLDER = re.compile(r"\[[^\]\n]{2,80}\]")


def _template_placeholders() -> dict[str, frozenset[str]]:
    """Les [crochets] des gabarits téléchargeables (fr et en), par document.

    Lus dans les gabarits eux-mêmes : modifier un gabarit met la détection à
    jour. Un texte réel entre crochets (« [90 ms, 110 ms] ») n'en fait pas
    partie, il ne compte donc jamais.
    """
    out = {}
    for doc in DOC_ORDER:
        found = set()
        for lang_dir in ("fr", "en"):
            path = _TEMPLATES_DIR / lang_dir / f"{doc}.md"
            if path.exists():
                found.update(_PLACEHOLDER.findall(path.read_text(encoding="utf-8")))
        out[doc] = frozenset(found)
    return out


_PLACEHOLDERS = _template_placeholders()


@dataclass(frozen=True)
class Problem:
    """Un motif de refus. `doc` vaut None pour un problème d'ensemble."""

    code: str
    doc: str | None = None
    params: tuple = ()

    def message(self, lang: str = DEFAULT_LANG) -> str:
        params = dict(self.params)
        if lang != "en":  # tailles : virgule décimale en français
            params = {k: v.replace(".", ",") if k in ("size", "max") else v for k, v in params.items()}
        if self.doc is not None:
            params["doc"] = t(f"qc.docs.name.{self.doc}", lang)
        # ⚠️ Clés écrites en f-string DANS l'appel à t() : c'est ainsi que
        # tests/test_i18n.py reconnaît une famille de clés (sinon « mortes »).
        if self.code == "no_ids":
            return t(f"qc.docs.no_ids.{self.doc}", lang, **params)
        return t(f"qc.docs.{self.code}", lang, **params)


def _kb(size: int) -> str:
    """Taille en Ko, au dixième SUPÉRIEUR : 20 030 octets donnent « 20.1 », jamais
    « 20 Ko, au-delà de la limite de 20 Ko »."""
    tenths = -(-size // 100)
    return str(tenths // 10) if tenths % 10 == 0 else f"{tenths // 10}.{tenths % 10}"


def normalize(text: str) -> str:
    """Retire l'éventuel BOM et unifie les fins de ligne (Windows → \\n)."""
    return text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")


def _is_text(text: str) -> bool:
    if "\x00" in text:
        return False
    garbage = sum(1 for ch in text if ch == "�" or (ord(ch) < 32 and ch not in "\n\t"))
    return garbage <= len(text) * _MAX_GARBAGE_RATIO


def check_documents(docs: dict) -> tuple[dict[str, str], list[Problem]]:
    """Vérifie les trois documents envoyés par le visiteur.

    Args:
        docs: {"srs": texte, "test_plan": texte, "review_report": texte} ;
            toute autre clé est ignorée.

    Returns:
        (documents normalisés, problèmes). Aucun problème = prêt pour l'audit.
        Jamais d'exception : une entrée de forme inattendue est un problème.
    """
    clean: dict[str, str] = {}
    problems: list[Problem] = []
    total = 0
    for doc in DOC_ORDER:
        text = docs.get(doc) if isinstance(docs, dict) else None
        if not isinstance(text, str):
            problems.append(Problem("missing", doc))
            continue
        text = normalize(text)
        if not text.strip():
            problems.append(Problem("empty", doc))
            continue
        if not _is_text(text):
            problems.append(Problem("not_text", doc))
            continue
        size = len(text.encode("utf-8"))
        total += size
        if size > MAX_DOC_BYTES:
            problems.append(Problem("too_big", doc, (("size", _kb(size)), ("max", _kb(MAX_DOC_BYTES)))))
        if not _REQUIRED_HEADING[doc].search(text):
            problems.append(Problem("no_ids", doc))
        # Dans l'ordre d'apparition : les exemples cités sont les premiers à remplir
        left = list(dict.fromkeys(p for p in _PLACEHOLDER.findall(text) if p in _PLACEHOLDERS[doc]))
        if len(left) >= _UNFILLED_MIN:
            problems.append(Problem("unfilled", doc, (("examples", ", ".join(left[:3])),)))
        clean[doc] = text
    if total > MAX_TOTAL_BYTES:
        problems.append(Problem("total_too_big", None, (("size", _kb(total)), ("max", _kb(MAX_TOTAL_BYTES)))))
    return clean, problems


def messages(problems: list[Problem], lang: str = DEFAULT_LANG) -> list[str]:
    """Les motifs de refus, prêts à afficher, dans l'ordre des documents."""
    return [p.message(lang) for p in problems]
