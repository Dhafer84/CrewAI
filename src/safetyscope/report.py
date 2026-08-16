"""Export Excel du tableau HARA.

Le classeur est un livrable de travail : il porte la cotation faite par
l'ingénieur, et laisse vides les colonnes qui relèvent de la suite de la
démarche (objectif de sécurité, état sûr, responsable).
"""

from io import BytesIO

from .analysis import HaraAnalysis
from .asil import (
    ASIL_ORDER,
    CONTROLLABILITY_LABELS,
    EXPOSURE_LABELS,
    SEVERITY_LABELS,
)

_DISCLAIMER = (
    "Démonstration pédagogique. Cet outil implémente la logique de "
    "détermination ASIL avec des formulations qui lui sont propres. Il ne "
    "reproduit pas le texte de l'ISO 26262, document sous licence, et ne s'y "
    "substitue en aucun cas."
)

_LIMITS = [
    ("La cotation S/E/C relève du jugement de l'ingénieur",
     "L'outil calcule, il ne décide pas à votre place"),
    ("Les situations de conduite ne sont pas exhaustives",
     "Une HARA complète balaie systématiquement les situations opérationnelles"),
    ("Les décompositions supposent une indépendance suffisante",
     "Cette indépendance doit être démontrée, pas postulée"),
    ("Aucun objectif de sécurité n'est généré automatiquement",
     "Sa formulation et l'état sûr associé restent à rédiger"),
    ("Aucune donnée n'est conservée",
     "Ce classeur est le seul artefact produit — pensez à l'archiver"),
]


def build_excel(analysis: HaraAnalysis) -> bytes:
    """Construit le classeur HARA et le rend sous forme d'octets."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="6D4AA6")
    title_font = Font(bold=True, size=13)

    workbook = Workbook()

    def write_header(sheet, headers: list[str]) -> None:
        sheet.append(headers)
        for cell in sheet[sheet.max_row]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(vertical="center", wrap_text=True)

    def autosize(sheet, widths: list[int]) -> None:
        for index, width in enumerate(widths, start=1):
            sheet.column_dimensions[get_column_letter(index)].width = width

    # --- Analyse HARA ---
    hara = workbook.active
    hara.title = "Analyse HARA"
    write_header(hara, [
        "N°", "Dysfonctionnement", "Situation de conduite",
        "S", "E", "C", "Cotation", "ASIL",
        "Objectif de sécurité", "État sûr", "Responsable", "Commentaire",
    ])
    for number, event in enumerate(analysis.events, start=1):
        hara.append([
            f"HZ-{number:03d}",
            event.malfunction,
            event.situation,
            event.severity,
            event.exposure,
            event.controllability,
            event.rating,
            event.asil,
        ])
    for row in hara.iter_rows(min_row=2, min_col=2, max_col=3):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    if analysis.events:
        hara.auto_filter.ref = f"A1:L{hara.max_row}"
    autosize(hara, [10, 44, 40, 5, 5, 5, 12, 10, 34, 26, 18, 30])

    # --- Synthèse ---
    summary = workbook.create_sheet("Synthèse")
    summary["A1"] = "SafetyScope — analyse de risques HARA"
    summary["A1"].font = title_font
    summary.append([])
    summary.append(["Item étudié", analysis.item])
    summary.append(["Date (UTC)", analysis.created_at.strftime("%Y-%m-%d %H:%M")])
    summary.append(["Événements redoutés", len(analysis.events)])
    summary.append(["ASIL le plus élevé", analysis.max_asil])
    summary.append([])

    counts = analysis.count_by_asil()
    write_header(summary, ["ASIL", "Nombre d'événements"])
    for level in ASIL_ORDER:
        summary.append([level, counts[level]])
    summary.append([])

    summary.append(["Décompositions admises pour " + analysis.max_asil])
    summary[summary.max_row][0].font = Font(bold=True)
    if analysis.decompositions:
        for first, second in analysis.decompositions:
            summary.append([
                f"{first}({analysis.max_asil}) + {second}({analysis.max_asil})"
            ])
        summary.append([
            "Sous réserve d'une indépendance suffisante entre les éléments."
        ])
    else:
        summary.append(["Aucune — un QM ne se décompose pas."])
    summary.append([])
    summary.append([_DISCLAIMER])
    summary[summary.max_row][0].alignment = Alignment(wrap_text=True, vertical="top")
    autosize(summary, [30, 60])

    # --- Échelles ---
    scales = workbook.create_sheet("Échelles")
    scales["A1"] = "Échelles de cotation"
    scales["A1"].font = title_font
    scales.append([])
    for axis, labels in (
        ("Sévérité (S)", SEVERITY_LABELS),
        ("Exposition (E)", EXPOSURE_LABELS),
        ("Contrôlabilité (C)", CONTROLLABILITY_LABELS),
    ):
        scales.append([axis])
        scales[scales.max_row][0].font = Font(bold=True)
        for value, label in sorted(labels.items()):
            scales.append([f"{axis[-2]}{value}", label])
        scales.append([])
    autosize(scales, [20, 56])

    # --- Limites ---
    limits = workbook.create_sheet("Limites")
    write_header(limits, ["Limite", "Ce que cela implique"])
    for row in _LIMITS:
        limits.append(list(row))
    for row in limits.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    autosize(limits, [52, 58])

    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
