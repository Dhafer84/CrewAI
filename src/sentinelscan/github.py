"""Client de l'API de recherche GitHub — sources publiques uniquement.

RÈGLE ABSOLUE tenue par ce module : on ne demande jamais l'extrait de code
correspondant (media type `text-match`), et on ne conserve jamais le contenu
d'un fichier. Seules les métadonnées sont remontées — dépôt, chemin, URL.

Un secret trouvé se révoque, il ne se lit pas, il ne se teste pas.
"""

import time
from dataclasses import dataclass

import requests

from .config import (
    CODE_SEARCH_DELAY_SECONDS,
    GITHUB_API_BASE,
    GITHUB_TOKEN,
    RESULTS_PER_QUERY,
)

_TIMEOUT_SECONDS = 20


@dataclass(frozen=True)
class Hit:
    """Une occurrence trouvée. Volontairement dépourvue du contenu du fichier."""

    repo: str
    owner: str
    path: str
    url: str


@dataclass(frozen=True)
class SearchOutcome:
    """Résultat d'une requête, avec l'état de complétude annoncé par GitHub.

    `incomplete` reprend le champ `incomplete_results` de l'API : GitHub
    interrompt une recherche trop longue et répond 200 avec une liste vide ou
    partielle. Ignorer ce champ reviendrait à présenter un abandon de GitHub
    comme une absence d'exposition — le pire faux négatif pour cet outil.
    """

    hits: list[Hit]
    incomplete: bool


class GitHubError(RuntimeError):
    """Échec d'appel à l'API GitHub, formulé pour l'utilisateur final."""


def _headers() -> dict[str, str]:
    return {
        # Pas de "application/vnd.github.text-match+json" : on ne veut PAS
        # récupérer les extraits de code correspondants.
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "SentinelScan",
    }


def _get(endpoint: str, query: str) -> dict:
    url = f"{GITHUB_API_BASE}{endpoint}"
    params = {"q": query, "per_page": RESULTS_PER_QUERY}

    try:
        response = requests.get(
            url, headers=_headers(), params=params, timeout=_TIMEOUT_SECONDS
        )
    except requests.RequestException as exc:
        raise GitHubError(f"Appel GitHub impossible : {type(exc).__name__}") from exc

    if response.status_code == 200:
        return response.json()

    if response.status_code == 401:
        raise GitHubError("Jeton GitHub invalide ou expiré (HTTP 401).")

    if response.status_code == 422:
        raise GitHubError("Requête refusée par GitHub (HTTP 422) — syntaxe invalide.")

    if response.status_code in (403, 429):
        retry_after = response.headers.get("Retry-After")
        detail = f" Réessayer dans {retry_after} s." if retry_after else ""
        raise GitHubError(f"Quota GitHub atteint (HTTP {response.status_code}).{detail}")

    raise GitHubError(f"Réponse GitHub inattendue (HTTP {response.status_code}).")


def search_code(query: str) -> SearchOutcome:
    """Recherche dans le contenu des fichiers des dépôts publics."""
    payload = _get("/search/code", query)

    hits: list[Hit] = []
    for item in payload.get("items", []):
        repository = item.get("repository") or {}
        hits.append(
            Hit(
                repo=repository.get("full_name", "—"),
                owner=(repository.get("owner") or {}).get("login", "—"),
                path=item.get("path", "—"),
                url=item.get("html_url", ""),
            )
        )
    return SearchOutcome(hits, bool(payload.get("incomplete_results")))


def search_repositories(query: str) -> SearchOutcome:
    """Recherche par nom / description de dépôt public."""
    payload = _get("/search/repositories", query)

    hits: list[Hit] = []
    for item in payload.get("items", []):
        hits.append(
            Hit(
                repo=item.get("full_name", "—"),
                owner=(item.get("owner") or {}).get("login", "—"),
                path="(dépôt)",
                url=item.get("html_url", ""),
            )
        )
    return SearchOutcome(hits, bool(payload.get("incomplete_results")))


def pace_code_search() -> None:
    """Respecte la limite de 10 requêtes/minute de la recherche de code.

    L'attente est le comportement normal, pas un ralentissement à corriger.
    """
    time.sleep(CODE_SEARCH_DELAY_SECONDS)
