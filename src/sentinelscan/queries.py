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
    # Noms d'entreprise fictifs universels : présents dans des milliers de
    # fichiers d'exemple, ils ne remontent que du bruit.
    "acme", "acme-corp", "acmecorp", "contoso", "example", "example-corp",
    "foobar", "mycompany", "yourcompany", "initech", "widgets",
}

# Marqueurs de fichier-modèle, cherchés dans le CHEMIN COMPLET. Un
# `.env.example` ou un `templates/.env.x` est publié volontairement et ne
# contient pas de secret — le classer CRITIQUE, c'est crier au loup.
_TEMPLATE_MARKERS = (
    "example", "sample", "template", "dist", "mock", "fixture",
    "dummy", "specimen", "placeholder", "demo", "/doc", "/test",
)

# Extensions de code source ou de documentation. Un fichier qui *manipule*
# des credentials (`salesforceClientCredentials.ts`) n'est pas un fichier
# de credentials, et `get-api-credentials.Rmd` est une notice.
_NON_SECRET_EXTENSIONS = (
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".rb", ".go",
    ".java", ".cs", ".php", ".r", ".rmd", ".sh", ".ps1", ".c", ".cpp",
    ".rs", ".swift", ".md", ".mdx", ".rst", ".org", ".html", ".adoc",
)

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
    ('"{kw}" filename:config', "MAJEUR", "Fichier de configuration"),
    # Signal faible : GitHub n'offre aucune contrainte de proximité, les deux
    # termes peuvent être à des milliers de lignes l'un de l'autre. Un tutoriel
    # qui cite le terme et « api_key » matche autant qu'un vrai fichier. D'où
    # MINEUR, et un libellé qui dit ce qui a réellement été constaté.
    ('"{kw}" AND "api_key"', "MINEUR", "Co-occurrence avec « api_key »"),
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


def _looks_like_env_file(basename: str) -> bool:
    """Un vrai fichier d'environnement : `.env`, `.env.local`, `prod.env`…

    Écarte `event.envelope.json` ou `.env.md` que `filename:.env` remonte.
    """
    return (
        basename == ".env"
        or basename.startswith(".env.")
        or basename.endswith(".env")
        or basename == ".envrc"
    )


def _looks_like_credentials_file(basename: str) -> bool:
    """Un vrai magasin de credentials : `credentials`, `credentials.json`…

    Écarte le code source qui manipule des credentials.
    """
    if "credential" not in basename:
        return False
    return not basename.endswith(_NON_SECRET_EXTENSIONS)


def _looks_like_config_file(basename: str) -> bool:
    """Un vrai fichier de configuration : `config.yaml`, `names.config`…

    Écarte `ConfigurationForm.tsx`, `Config.java` ou `next.config.mjs`, que
    `filename:config` remonte alors qu'il s'agit de code.
    """
    if "config" not in basename:
        return False
    return not basename.endswith(_NON_SECRET_EXTENSIONS)


# Validateur de forme, par type de détection.
_SHAPE_CHECKS = {
    "Fichier .env exposé": _looks_like_env_file,
    "Fichier de credentials": _looks_like_credentials_file,
    "Fichier de configuration": _looks_like_config_file,
}

# Un constat douteux est déclassé d'un cran, jamais supprimé.
_DOWNGRADE = {"CRITIQUE": "MINEUR", "MAJEUR": "MINEUR"}


def refine_criticality(criticality: str, detection: str, path: str) -> tuple[str, str]:
    """Réévalue un constat d'après le chemin réel du fichier.

    GitHub applique le qualifier `filename:` de façon large : `filename:.env`
    remonte aussi `.env.example`, `.env.md` ou `event.envelope.json`, et
    `filename:credentials` remonte le code source qui *manipule* des
    credentials. Sans ce filtre, le rapport classe CRITIQUE des fichiers qui
    ne contiennent aucun secret — et un rapport qui crie au loup ne sert à rien.

    Un constat n'est jamais supprimé : il est déclassé en MINEUR avec le motif.
    C'est à l'analyste de qualifier, pas à l'outil de décider seul.

    Returns:
        Le couple (criticité, libellé) ajusté.
    """
    downgraded = _DOWNGRADE.get(criticality)
    if downgraded is None:
        return criticality, detection

    lowered = path.lower()
    basename = lowered.rsplit("/", 1)[-1]

    if any(marker in lowered for marker in _TEMPLATE_MARKERS):
        return downgraded, f"{detection} — modèle ou exemple"

    check = _SHAPE_CHECKS.get(detection)
    if check and not check(basename):
        return downgraded, f"{detection} — nom de fichier non concluant"

    if basename.endswith(_NON_SECRET_EXTENSIONS):
        return downgraded, f"{detection} — code source ou documentation"

    return criticality, detection


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
