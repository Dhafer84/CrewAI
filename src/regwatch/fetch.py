"""Accès réseau — le SEUL module de RegWatch qui parle à Internet.

Tous les autres (`norms`, `classify`, `feeds`, `scrape`) prennent des
chaînes. La frontière n'est pas décorative : c'est elle qui rend l'interdit
« aucun test ne touche le réseau » **structurel** plutôt que disciplinaire.
Un test qui importerait ce module se verrait immédiatement.

⚠️ **On ne contourne aucun anti-bot.** `www.iso.org` et `unece.org`
répondent par un défi managé Cloudflare : ils sont donc hors périmètre, et
le dire est la seule réponse acceptable. Se déguiser en navigateur pour
passer serait à la fois déloyal et fragile. Le défi est détecté et nommé,
pour qu'une source protégée ne soit jamais confondue avec une source calme.
"""

from i18n import DEFAULT_LANG, t

import time
from dataclasses import dataclass

import requests

from .config import (
    CACHE_TTL_SECONDS,
    HTTP_TIMEOUT_SECONDS,
    MAX_RESPONSE_BYTES,
    REQUEST_DELAY_SECONDS,
    USER_AGENT,
)


class FetchError(RuntimeError):
    """Source injoignable.

    ⚠️ Porte une **clé de catalogue et ses paramètres**, pas un texte. Ce
    module ne connaît pas la langue du visiteur — c'est `core` qui la
    connaît, et qui rend le message au moment de l'afficher.
    """

    def __init__(self, key: str, **params):
        self.key = key
        self.params = params
        super().__init__(key)

    def message(self, lang: str = DEFAULT_LANG) -> str:
        return t(self.key, lang, **self.params)


@dataclass(frozen=True)
class _Entry:
    body: str
    stored_at: float


_cache: dict[str, _Entry] = {}
_last_request_at = 0.0

# Signatures d'un défi anti-bot Cloudflare servi à la place de la page.
# Mesurées le 23/08/2026 sur www.iso.org et unece.org.
_CHALLENGE_MARKERS = ("cf_chl_opt", "challenges.cloudflare.com", "Just a moment...")


def clear_cache() -> None:
    """Vide le cache. Réservé aux tests et au CLI de vérification."""
    _cache.clear()


def is_cached(url: str) -> bool:
    entry = _cache.get(url)
    return entry is not None and (time.monotonic() - entry.stored_at) < CACHE_TTL_SECONDS


def _wait_turn() -> None:
    """Espace les requêtes réseau, sans pénaliser la première ni un cache.

    Compté depuis la requête précédente, pas avant chaque appel : une veille
    sur cinq normes ne doit pas payer une seconde d'attente inutile au
    démarrage.
    """
    global _last_request_at
    if _last_request_at:
        elapsed = time.monotonic() - _last_request_at
        if elapsed < REQUEST_DELAY_SECONDS:
            time.sleep(REQUEST_DELAY_SECONDS - elapsed)
    _last_request_at = time.monotonic()


def _decode(response: requests.Response, data: bytes) -> str:
    """Décode la réponse en se fiant à l'en-tête, à l'UTF-8 sinon.

    `requests` retombe sur ISO-8859-1 quand un `text/*` ne déclare pas son
    charset — la règle HTTP historique, qui massacre les accents d'une page
    UTF-8 non déclarée. On ne suit son avis que s'il y a réellement un
    `charset=` dans l'en-tête.
    """
    content_type = response.headers.get("Content-Type", "").lower()
    charset = response.encoding if "charset=" in content_type else None
    return data.decode(charset or "utf-8", errors="replace")


def get_text(url: str) -> str:
    """Récupère une page ou un flux, en texte.

    Le cache et la cadence sont gérés ici, pas chez l'appelant : un
    garde-fou qu'on peut oublier d'appeler n'en est pas un. Même raisonnement
    que `xlsxsafe.harden()`, appliqué au classeur entier plutôt qu'à chaque
    cellule.

    Raises:
        FetchError: réseau, statut HTTP, taille excessive, ou défi anti-bot.
    """
    entry = _cache.get(url)
    if entry is not None and (time.monotonic() - entry.stored_at) < CACHE_TTL_SECONDS:
        return entry.body

    _wait_turn()

    # Repli défensif : un User-Agent redéfini dans le .env avec un accent
    # provoquerait un 403 chez certaines sources, et le diagnostic serait
    # trompeur au possible (voir le commentaire de config.USER_AGENT).
    # Mieux vaut un UA amputé d'un caractère qu'une source déclarée fermée.
    agent = USER_AGENT.encode("ascii", "ignore").decode("ascii")
    headers = {"User-Agent": agent, "Accept-Language": "en, de;q=0.8, fr;q=0.5"}
    try:
        response = requests.get(
            url, headers=headers, timeout=HTTP_TIMEOUT_SECONDS, stream=True
        )
    except requests.RequestException as exc:
        raise FetchError("regwatch.err.unreachable",
                         cause=type(exc).__name__) from exc

    with response:
        if response.status_code in (401, 403, 429):
            raise FetchError("regwatch.err.refused", code=response.status_code)
        if response.status_code == 404:
            raise FetchError("regwatch.err.notfound")
        if response.status_code != 200:
            raise FetchError("regwatch.err.unexpected", code=response.status_code)

        chunks: list[bytes] = []
        total = 0
        for chunk in response.iter_content(chunk_size=16384):
            total += len(chunk)
            if total > MAX_RESPONSE_BYTES:
                raise FetchError("regwatch.err.toobig",
                                 ko=MAX_RESPONSE_BYTES // 1024)
            chunks.append(chunk)

        body = _decode(response, b"".join(chunks))

    # Un défi anti-bot arrive volontiers en HTTP 200 : sans ce contrôle, la
    # page de challenge serait donnée à parser, rendrait 0 item, et la source
    # passerait pour calme alors qu'elle est fermée.
    if len(body) < 20000 and any(marker in body for marker in _CHALLENGE_MARKERS):
        raise FetchError("regwatch.err.challenge")

    _cache[url] = _Entry(body=body, stored_at=time.monotonic())
    return body
