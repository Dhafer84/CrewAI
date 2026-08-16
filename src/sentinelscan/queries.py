"""Construction des requêtes de recherche et échelle de criticité.

C'est ici que se joue la valeur du scan : une requête trop générique remonte
du bruit, une requête contextualisée remonte des vrais positifs.
"""

import re
from dataclasses import dataclass

from .config import MAX_KEYWORDS, MIN_KEYWORD_LENGTH

# Échelle de criticité — pilote le délai de traitement attendu.
CRITICALITY_ORDER = ["CRITIQUE", "MAJEUR", "MINEUR", "INFO"]

CRITICALITY_SLA = {
    "CRITIQUE": "24 h",
    "MAJEUR": "5 jours ouvrés",
    "MINEUR": "15 jours",
    "INFO": "au fil de l'eau",
}

# Termes trop ambigus pour être cherchés seuls : ils noieraient le rapport
# sous des dizaines de milliers de faux positifs (cf. "AES" qui est aussi
# Advanced Encryption Standard).
GENERIC_TERMS = {
    "aes", "api", "app", "test", "demo", "dev", "prod", "data", "code",
    "admin", "user", "web", "http", "json", "null", "true", "false",
}

# Caractères autorisés dans un mot-clé. Tout le reste est retiré pour éviter
# qu'un utilisateur n'injecte des qualifiers GitHub (org:, path:, …) dans la
# requête construite.
_ALLOWED_CHARS = re.compile(r"[^A-Za-z0-9\-_. ]")


@dataclass(frozen=True)
class Query:
    """Une requête à exécuter, avec le sens à donner à ses résultats."""

    expression: str
    kind: str  # "code" ou "repo"
    criticality: str
    detection: str
    keyword: str


# Recherche dans le CONTENU des fichiers — la partie à haute valeur.
# GitHub est la seule plateforme grand public qui l'autorise par API.
_CODE_PATTERNS = [
    ('"{kw}" filename:.env', "CRITIQUE", "Fichier .env exposé"),
    ('"{kw}" extension:pem', "CRITIQUE", "Clé privée / certificat"),
    ('"{kw}" filename:credentials', "CRITIQUE", "Fichier de credentials"),
    ('"{kw}" AND "api_key"', "MAJEUR", "Référence à une clé API"),
    ('"{kw}" filename:config', "MAJEUR", "Fichier de configuration"),
]

# Recherche par NOM de dépôt — signal faible, sert au cadrage.
_REPO_PATTERN = ("{kw}", "INFO", "Dépôt mentionnant le terme")


class InvalidKeyword(ValueError):
    """Mot-clé rejeté avant tout appel API."""


def sanitize_keyword(raw: str) -> str:
    """Nettoie un mot-clé saisi par l'utilisateur.

    Lève InvalidKeyword si le terme est inexploitable, plutôt que de gaspiller
    du quota API sur une requête qui ne remontera que du bruit.
    """
    cleaned = _ALLOWED_CHARS.sub("", raw).strip()

    if len(cleaned) < MIN_KEYWORD_LENGTH:
        raise InvalidKeyword(
            f"« {raw} » est trop court (minimum {MIN_KEYWORD_LENGTH} caractères)."
        )

    if cleaned.lower() in GENERIC_TERMS:
        raise InvalidKeyword(
            f"« {cleaned} » est trop générique et remonterait surtout des faux "
            "positifs. Utilisez un terme distinctif : nom d'entreprise, nom de "
            "projet interne, domaine e-mail."
        )

    return cleaned


def normalize_keywords(raw_keywords: list[str]) -> list[str]:
    """Nettoie, déduplique et plafonne la liste de mots-clés."""
    seen: list[str] = []
    for raw in raw_keywords:
        if not raw or not raw.strip():
            continue
        cleaned = sanitize_keyword(raw)
        if cleaned.lower() not in {k.lower() for k in seen}:
            seen.append(cleaned)

    if not seen:
        raise InvalidKeyword("Aucun mot-clé exploitable fourni.")

    return seen[:MAX_KEYWORDS]


def build_queries(keywords: list[str]) -> list[Query]:
    """Construit la liste ordonnée des requêtes pour les mots-clés donnés."""
    queries: list[Query] = []

    for kw in keywords:
        for template, criticality, detection in _CODE_PATTERNS:
            queries.append(
                Query(
                    expression=template.format(kw=kw),
                    kind="code",
                    criticality=criticality,
                    detection=detection,
                    keyword=kw,
                )
            )

        template, criticality, detection = _REPO_PATTERN
        queries.append(
            Query(
                expression=template.format(kw=kw),
                kind="repo",
                criticality=criticality,
                detection=detection,
                keyword=kw,
            )
        )

    return queries
