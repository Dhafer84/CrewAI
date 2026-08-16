"""Génération des rapports SentinelScan — markdown (aperçu) et Excel (livrable).

Le rapport documente honnêtement ce que le scan couvre ET ce qu'il ne couvre
pas. Une veille dont on connaît les limites vaut mieux qu'une veille dont on
croit à tort qu'elle est exhaustive.
"""

from io import BytesIO

from .queries import CRITICALITY_ORDER, CRITICALITY_SLA
from .scanner import ScanResult

# Ce que le scan ne voit pas — à assumer explicitement dans tout dossier d'audit.
KNOWN_LIMITS = [
    ("GitHub n'indexe que la branche par défaut",
     "Un secret sur une branche secondaire n'est pas détecté"),
    ("GitHub exclut certains dépôts inactifs",
     "Angle mort sur les dépôts anciens"),
    ("Gists et Pastebin n'ont pas d'API de recherche",
     "Passage manuel indispensable — c'est statistiquement la 1re source de fuite"),
    ("Les autres forges ne sont pas interrogées",
     "GitLab, Gitee, npm, Docker Hub hors périmètre de cette démo"),
    ("Dépôts supprimés mais forkés",
     "Le contenu survit à la suppression — nécessite une demande au support"),
]

COVERAGE = [
    ("GitHub — code", "Recherche dans le contenu des fichiers", "Automatisé"),
    ("GitHub — dépôts", "Recherche par nom et description", "Automatisé"),
    ("Gist / Pastebin", "Aucune API exploitable", "Manuel — non couvert ici"),
]


def _procedure_lines() -> list[str]:
    return [
        "1. **Préserver la preuve** — capture horodatée, URL, SHA de commit.",
        "2. **Qualifier** — faux positif / homonyme / vrai positif.",
        "3. **Si un secret est exposé : révoquer sous 24 h**, puis analyser les logs.",
        "4. **Demander le retrait** ensuite seulement — jamais avant la révocation.",
        "5. **Vérifier la suppression effective** — les forks et le cache survivent.",
        "6. **Traiter la cause** — hook `gitleaks` en pre-commit, sensibilisation.",
    ]


def coverage_warning(result: ScanResult) -> str | None:
    """Avertissement quand GitHub n'a pas mené toutes les requêtes à terme.

    C'est le plus important des avertissements : sans lui, un abandon de
    GitHub se lit comme une absence d'exposition.
    """
    if not result.coverage_is_incomplete:
        return None

    incomplete = len(result.incomplete_queries)
    return (
        f"⚠️ **Couverture incomplète.** GitHub n'a pas mené à terme "
        f"{incomplete} requête(s) sur {result.queries_run} : sa recherche a "
        "dépassé le délai qu'il s'accorde et il a répondu par un résultat "
        "partiel. **Sur ces requêtes, l'absence de détection ne prouve rien.** "
        "Relancez le scan pour obtenir une couverture complète avant de "
        "conclure quoi que ce soit."
    )


def homonym_warning(result: ScanResult) -> str | None:
    """Avertissement quand les constats sentent le terme courant."""
    if not result.looks_like_common_term:
        return None
    return (
        f"⚠️ **Probable homonymie.** Les {len(result.findings)} détections se "
        f"répartissent sur {result.distinct_owners} propriétaires distincts — "
        "la signature d'un terme courant (prénom, mot du langage) plutôt que "
        "d'un identifiant d'organisation. L'homonymie est le principal piège "
        "de cette veille. Reprenez avec un terme plus distinctif : nom de "
        "projet interne, domaine e-mail, référence documentaire."
    )


def build_markdown(result: ScanResult) -> str:
    """Rapport de synthèse en markdown, destiné à l'affichage web."""
    counts = result.count_by_criticality()
    lines: list[str] = []

    lines.append("## Synthèse")
    lines.append("")
    lines.append(f"**Termes recherchés :** {', '.join(result.keywords)}")
    lines.append("")
    lines.append(
        f"**{len(result.findings)} détection(s)** sur {result.queries_run} requête(s) "
        f"exécutée(s) en {result.duration_seconds:.0f} s."
    )
    lines.append("")

    # La couverture passe avant tout le reste : elle conditionne la lecture
    # de l'ensemble du rapport.
    coverage = coverage_warning(result)
    if coverage:
        lines.append(coverage)
        lines.append("")

    warning = homonym_warning(result)
    if warning:
        lines.append(warning)
        lines.append("")

    lines.append("| Criticité | Nombre | Délai de traitement |")
    lines.append("| --- | --- | --- |")
    for level in CRITICALITY_ORDER:
        lines.append(f"| {level} | {counts.get(level, 0)} | {CRITICALITY_SLA[level]} |")
    lines.append("")

    if result.findings:
        lines.append("## Détections")
        lines.append("")
        lines.append("| Criticité | Détection | Dépôt | Chemin |")
        lines.append("| --- | --- | --- | --- |")
        for finding in result.findings[:50]:
            link = f"[{finding.repo}]({finding.url})" if finding.url else finding.repo
            lines.append(
                f"| {finding.criticality} | {finding.detection} | {link} | `{finding.path}` |"
            )
        if len(result.findings) > 50:
            lines.append("")
            lines.append(
                f"*{len(result.findings) - 50} détection(s) supplémentaire(s) "
                "dans le rapport Excel.*"
            )
        lines.append("")
    else:
        lines.append("## Détections")
        lines.append("")
        lines.append("Aucune exposition détectée sur ce périmètre.")
        lines.append("")

    lines.append("## Procédure de traitement")
    lines.append("")
    lines.extend(_procedure_lines())
    lines.append("")

    lines.append("## Limites connues")
    lines.append("")
    lines.append("| Limite | Conséquence |")
    lines.append("| --- | --- |")
    for limit, consequence in KNOWN_LIMITS:
        lines.append(f"| {limit} | {consequence} |")
    lines.append("")

    if result.errors:
        lines.append("## Erreurs")
        lines.append("")
        lines.append(
            "Une plateforme en échec laisse un trou dans la couverture — "
            "à vérifier avant de conclure."
        )
        lines.append("")
        for error in result.errors:
            lines.append(f"- {error}")
        lines.append("")

    return "\n".join(lines)


def build_excel(result: ScanResult) -> bytes:
    """Rapport Excel multi-onglets, livrable téléchargeable."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="1D9E75")
    title_font = Font(bold=True, size=13)

    workbook = Workbook()

    def write_header(sheet, headers: list[str]) -> None:
        sheet.append(headers)
        for cell in sheet[sheet.max_row]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(vertical="center")

    def autosize(sheet, widths: list[int]) -> None:
        for index, width in enumerate(widths, start=1):
            sheet.column_dimensions[get_column_letter(index)].width = width

    # --- Synthèse ---
    summary = workbook.active
    summary.title = "Synthèse"
    summary["A1"] = "SentinelScan — rapport de veille"
    summary["A1"].font = title_font
    summary.append([])
    summary.append(["Termes recherchés", ", ".join(result.keywords)])
    summary.append(["Date du scan (UTC)", result.started_at.strftime("%Y-%m-%d %H:%M")])
    summary.append(["Durée", f"{result.duration_seconds:.0f} s"])
    summary.append(["Requêtes exécutées", result.queries_run])
    summary.append(["Détections", len(result.findings)])
    summary.append(["Propriétaires distincts", result.distinct_owners])
    summary.append([
        "Couverture",
        "INCOMPLÈTE" if result.coverage_is_incomplete else "Complète",
    ])
    summary.append([])

    for warning in (coverage_warning(result), homonym_warning(result)):
        if not warning:
            continue
        summary.append([warning.replace("⚠️ ", "").replace("**", "")])
        summary[summary.max_row][0].font = Font(bold=True, color="B45309")
        summary.append([])

    counts = result.count_by_criticality()
    write_header(summary, ["Criticité", "Nombre", "Délai de traitement"])
    for level in CRITICALITY_ORDER:
        summary.append([level, counts.get(level, 0), CRITICALITY_SLA[level]])
    summary.append([])
    summary.append(["Procédure de traitement"])
    summary[summary.max_row][0].font = Font(bold=True)
    for line in _procedure_lines():
        summary.append([line.replace("**", "")])
    autosize(summary, [28, 60, 24])

    # --- Détections ---
    # Colonnes automatiques puis colonnes à remplir par l'analyste.
    detections = workbook.create_sheet("Détections")
    write_header(detections, [
        "ID", "Criticité", "Détection", "Terme", "Dépôt", "Propriétaire",
        "Chemin", "URL",
        "Statut", "Vrai positif ?", "Secret exposé ?", "Action menée",
        "Responsable", "Date traitement", "Commentaire",
    ])
    for number, finding in enumerate(result.findings, start=1):
        detections.append([
            f"LEAK-{number:04d}",
            finding.criticality,
            finding.detection,
            finding.keyword,
            finding.repo,
            finding.owner,
            finding.path,
            finding.url,
        ])
    if result.findings:
        detections.auto_filter.ref = f"A1:O{detections.max_row}"
    autosize(detections, [12, 12, 26, 14, 34, 20, 40, 50, 18, 16, 16, 26, 18, 16, 30])

    # --- Couverture ---
    coverage = workbook.create_sheet("Couverture")
    write_header(coverage, ["Source", "Méthode d'interrogation", "Statut"])
    for row in COVERAGE:
        coverage.append(list(row))

    if result.incomplete_queries:
        coverage.append([])
        coverage.append(["Requêtes abandonnées par GitHub (résultat partiel)"])
        coverage[coverage.max_row][0].font = Font(bold=True, color="B45309")
        for detection in result.incomplete_queries:
            coverage.append([detection, "Résultat incomplet — ne rien conclure"])
    autosize(coverage, [40, 46, 28])

    # --- Limites ---
    limits = workbook.create_sheet("Limites")
    write_header(limits, ["Limite", "Conséquence"])
    for row in KNOWN_LIMITS:
        limits.append(list(row))
    autosize(limits, [52, 62])

    # --- Erreurs ---
    errors = workbook.create_sheet("Erreurs")
    write_header(errors, ["Erreur rencontrée"])
    if result.errors:
        for error in result.errors:
            errors.append([error])
    else:
        errors.append(["Aucune erreur — couverture complète sur le périmètre interrogé."])
    autosize(errors, [100])

    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
