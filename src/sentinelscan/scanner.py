"""Interface stable du moteur SentinelScan.

Ce module est le SEUL point d'entrée que les couches de présentation
(CLI local, API FastAPI) doivent appeler.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from . import github
from .config import require_github_token
from .queries import (
    CRITICALITY_ORDER,
    build_queries,
    normalize_keywords,
    refine_criticality,
)


@dataclass(frozen=True)
class Finding:
    """Un constat qualifié. Ne contient jamais la valeur d'un secret."""

    criticality: str
    detection: str
    repo: str
    owner: str
    path: str
    url: str
    keyword: str


@dataclass
class ScanResult:
    keywords: list[str]
    started_at: datetime
    finished_at: datetime | None = None
    findings: list[Finding] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    queries_run: int = 0
    queries_total: int = 0

    @property
    def duration_seconds(self) -> float:
        if not self.finished_at:
            return 0.0
        return (self.finished_at - self.started_at).total_seconds()

    def count_by_criticality(self) -> dict[str, int]:
        counts = {level: 0 for level in CRITICALITY_ORDER}
        for finding in self.findings:
            counts[finding.criticality] = counts.get(finding.criticality, 0) + 1
        return counts


def run_scan(keywords: list[str], progress_callback=None) -> ScanResult:
    """Lance un scan de veille sur les mots-clés fournis.

    Args:
        keywords: termes à rechercher. Nettoyés, dédupliqués et plafonnés
            (voir queries.normalize_keywords).
        progress_callback: appelé avec un dict d'événement à chaque étape.
            Types émis : "query_start", "query_done", "query_error".

    Returns:
        ScanResult — métadonnées uniquement, jamais de contenu de fichier.

    Raises:
        InvalidKeyword: si aucun mot-clé exploitable n'est fourni.
        RuntimeError: si le jeton GitHub est absent.
    """
    require_github_token()

    cleaned = normalize_keywords(keywords)
    queries = build_queries(cleaned)

    result = ScanResult(
        keywords=cleaned,
        started_at=datetime.now(timezone.utc),
        queries_total=len(queries),
    )

    def emit(event: dict) -> None:
        if progress_callback:
            progress_callback(event)

    seen: set[tuple[str, str]] = set()

    for index, query in enumerate(queries):
        emit({
            "type": "query_start",
            "index": index,
            "total": len(queries),
            "keyword": query.keyword,
            "detection": query.detection,
        })

        try:
            if query.kind == "code":
                hits = github.search_code(query.expression)
            else:
                hits = github.search_repositories(query.expression)
        except github.GitHubError as exc:
            result.errors.append(f"{query.detection} — {exc}")
            emit({"type": "query_error", "index": index, "message": str(exc)})
            continue
        finally:
            result.queries_run += 1
            # Cadence imposée par GitHub, sauf après la dernière requête.
            if query.kind == "code" and index < len(queries) - 1:
                github.pace_code_search()

        new_findings = 0
        for hit in hits:
            key = (hit.repo, hit.path)
            if key in seen:
                continue
            seen.add(key)

            criticality, detection = refine_criticality(
                query.criticality, query.detection, hit.path
            )
            result.findings.append(
                Finding(
                    criticality=criticality,
                    detection=detection,
                    repo=hit.repo,
                    owner=hit.owner,
                    path=hit.path,
                    url=hit.url,
                    keyword=query.keyword,
                )
            )
            new_findings += 1

        emit({
            "type": "query_done",
            "index": index,
            "total": len(queries),
            "keyword": query.keyword,
            "detection": query.detection,
            "criticality": query.criticality,
            "found": new_findings,
        })

    result.findings.sort(key=lambda f: CRITICALITY_ORDER.index(f.criticality))
    result.finished_at = datetime.now(timezone.utc)
    return result
