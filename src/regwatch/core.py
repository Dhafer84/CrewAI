"""Interface stable du moteur RegWatch.

Seul point d'entrée destiné aux couches de présentation (CLI, API FastAPI) :
`run_watch()`. Le moteur ne sait rien du web ni du terminal.

Le pipeline en trois temps, dans l'ordre, aucun ne saute le précédent :
  1. **collecte** déterministe — `fetch` + `feeds`/`scrape`
  2. **classification** déterministe — `classify`, zéro réseau, zéro IA
  3. **IA en dernier** — une phrase « pourquoi ça compte », étape 5, et
     jamais pour filtrer : `WatchItem.why` est rempli après coup, il n'est
     lu par personne pour décider de retenir un item.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

from . import fetch
from .classify import SIGNAL_ORDER, qualify
from .config import DEGRADED_MIN_BODY_BYTES, LOOKBACK_DAYS
from .feeds import FeedError, RawItem, parse_feed
from .norms import NORMS, Norm
from .scrape import PARSERS
from .sources import Source, sources_for


@dataclass(frozen=True)
class WatchItem:
    """Un signal retenu, rattaché à une norme.

    ⚠️ **Aucun champ de contenu** — titre, date, source, lien, rien d'autre.
    Le corps de la page n'est jamais téléchargé, donc jamais republié :
    c'est ce qui rend l'outil défendable face à des normes payantes. Même
    discipline que `RawItem`, `sentinelscan.Hit` et
    `threatscope.DamageProposal`.

    `why` est la seule chose que l'IA produise, et elle arrive **après** que
    la décision de retenir l'item a été prise.
    """

    norm_key: str
    norm_label: str
    signal: str
    title: str
    published: date
    source_key: str
    source_label: str
    source_tier: str
    url: str
    why: str = ""


@dataclass
class WatchResult:
    """Le résultat d'une veille — items **et** état de la couverture.

    ⚠️ Ce n'est pas une simple liste, et c'est le point de conception le plus
    important du moteur. Une liste ne peut pas dire « j'ai interrogé six
    sources, deux étaient muettes » : elle présenterait une panne comme une
    absence d'actualité. C'est la leçon d'`incomplete_results` de
    SentinelScan, où ignorer un champ faisait annoncer « 0 détection » alors
    que GitHub n'avait pas cherché.

    - `unreachable` : la source n'a pas répondu (réseau, HTTP, anti-robot)
    - `degraded` : elle a répondu, mais on n'en tire aucun item alors que la
      page est volumineuse — le parseur est probablement cassé
    - `undated` : des items pertinents que la source ne date pas assez pour
      qu'on puisse affirmer qu'ils tombent dans la fenêtre
    """

    norms: list[str]
    lookback_days: int
    started_at: datetime
    finished_at: datetime | None = None
    items: list[WatchItem] = field(default_factory=list)
    unreachable: list[str] = field(default_factory=list)
    degraded: list[str] = field(default_factory=list)
    undated: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    sources_read: int = 0
    sources_total: int = 0

    @property
    def duration_seconds(self) -> float:
        if not self.finished_at:
            return 0.0
        return (self.finished_at - self.started_at).total_seconds()

    @property
    def coverage_is_incomplete(self) -> bool:
        """Tant que c'est vrai, une absence de signal ne prouve rien."""
        return bool(self.unreachable or self.degraded)

    def count_by_norm(self) -> dict[str, int]:
        counts = {key: 0 for key in self.norms}
        for item in self.items:
            counts[item.norm_key] = counts.get(item.norm_key, 0) + 1
        return counts

    def count_by_signal(self) -> dict[str, int]:
        counts = {signal: 0 for signal in SIGNAL_ORDER}
        for item in self.items:
            counts[item.signal] = counts.get(item.signal, 0) + 1
        return counts


def _read(source: Source, body: str) -> list[RawItem]:
    """Applique le bon parseur — un flux ou un scraper dédié."""
    if source.kind == "rss":
        return parse_feed(body, source.key)
    return PARSERS[source.parser](body, source.key, source.url)


def run_watch(norms: list[Norm], progress_callback=None,
              today: date | None = None) -> WatchResult:
    """Lance une veille sur les normes fournies.

    Ne lit **que** les sources des normes demandées : pas de balayage
    systématique. Une source partagée par deux normes cochées n'est lue
    qu'une fois (voir `sources.sources_for`).

    Args:
        norms: normes à surveiller, telles que rendues par
            `norms.parse_selection`.
        progress_callback: appelé avec un dict à chaque étape. Types émis :
            "source_start", "source_done", "source_error".
        today: date de référence de la fenêtre. **Couture de test, jamais
            renseignée en production** : sans elle, un test qui vérifie
            qu'un item de mai est encore dans la fenêtre commencerait à
            échouer tout seul quelques jours plus tard. Un test qui pourrit
            avec le calendrier finit par être désactivé.

    Returns:
        WatchResult — jamais une simple liste : la couverture fait partie du
        résultat.

    Raises:
        ValueError: aucune norme fournie.
    """
    if not norms:
        raise ValueError("Aucune norme à surveiller.")

    selected = {norm.key for norm in norms}
    sources = sources_for(norms)
    result = WatchResult(
        norms=[norm.key for norm in norms],
        lookback_days=LOOKBACK_DAYS,
        started_at=datetime.now(timezone.utc),
        sources_total=len(sources),
    )
    reference = today or datetime.now(timezone.utc).date()
    cutoff = reference - timedelta(days=LOOKBACK_DAYS)

    def emit(event: dict) -> None:
        if progress_callback:
            progress_callback(event)

    seen: set[tuple[str, str]] = set()

    for index, source in enumerate(sources):
        emit({
            "type": "source_start", "index": index, "total": len(sources),
            "source": source.label, "tier": source.tier,
        })

        try:
            body = fetch.get_text(source.url)
        except fetch.FetchError as exc:
            result.sources_read += 1
            result.unreachable.append(source.label)
            result.errors.append(f"{source.label} — {exc}")
            emit({"type": "source_error", "index": index, "total": len(sources),
                  "source": source.label, "message": str(exc)})
            continue

        result.sources_read += 1

        try:
            raw = _read(source, body)
        except FeedError as exc:
            result.degraded.append(source.label)
            result.errors.append(f"{source.label} — {exc}")
            emit({"type": "source_error", "index": index, "total": len(sources),
                  "source": source.label, "message": str(exc)})
            continue
        except Exception as exc:  # noqa: BLE001
            # Un parseur qui plante ne doit pas emporter la veille entière —
            # mais il ne doit pas non plus passer pour une source calme.
            result.degraded.append(source.label)
            result.errors.append(
                f"{source.label} — parseur en échec ({type(exc).__name__})."
            )
            emit({"type": "source_error", "index": index, "total": len(sources),
                  "source": source.label, "message": "Lecture de la source impossible."})
            continue

        # ⚠️ Zéro item extrait d'une page volumineuse n'est pas « rien de
        # neuf » : c'est le symptôme d'une maquette qui a changé.
        degraded = not raw and len(body.encode("utf-8")) >= DEGRADED_MIN_BODY_BYTES
        if degraded:
            result.degraded.append(source.label)
            result.errors.append(
                f"{source.label} — la page répond mais aucun élément n'en est "
                "extrait : le parseur ne reconnaît plus sa structure."
            )

        retained = 0
        for item in raw:
            signals = {}
            for norm_key in source.norm_keys:
                if norm_key not in selected:
                    continue
                signal = qualify(item.title, item.categories, item.url, NORMS[norm_key])
                if signal:
                    signals[norm_key] = signal

            if not signals:
                continue

            # Pertinent mais non daté : on ne peut pas AFFIRMER qu'il tombe
            # dans la fenêtre. On l'écarte en le disant, plutôt que de le
            # retenir sur une date inventée ou de le taire.
            if item.published is None:
                result.undated.append(f"{source.label} — {item.title}")
                continue

            if item.published < cutoff:
                continue

            for norm_key, signal in signals.items():
                key = (item.url.lower(), norm_key)
                if key in seen:
                    continue
                seen.add(key)
                result.items.append(WatchItem(
                    norm_key=norm_key,
                    norm_label=NORMS[norm_key].label,
                    signal=signal,
                    title=item.title,
                    published=item.published,
                    source_key=source.key,
                    source_label=source.label,
                    source_tier=source.tier,
                    url=item.url,
                ))
                retained += 1

        emit({
            "type": "source_done", "index": index, "total": len(sources),
            "source": source.label, "found": retained,
            "state": "degraded" if degraded else "ok",
        })

    # Le plus récent d'abord ; à date égale, le signal le plus fort d'abord.
    result.items.sort(
        key=lambda item: (item.published, -SIGNAL_ORDER.index(item.signal)),
        reverse=True,
    )
    result.finished_at = datetime.now(timezone.utc)
    return result
