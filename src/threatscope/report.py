"""Export Excel du dossier TARA.

Le classeur doit être **relisible sans l'outil**. C'est pourquoi il embarque le
barème réellement appliqué : un tableau de risques dont on ne peut pas
reconstituer la méthode ne vaut rien six mois plus tard, quand personne ne se
souvient de la calibration retenue.

Il dit aussi ce qui **manque** — traitements non tranchés, écrits absents. Un
classeur qui tait ses trous est pire qu'un classeur qui les liste.
"""

from io import BytesIO

from xlsxsafe import harden

from .analysis import PARAMETER_LABELS, TaraAnalysis
from .rating import (
    FEASIBILITY_ORDER,
    IMPACT_CATEGORIES,
    IMPACT_ORDER,
    MAX_POTENTIAL,
    PARAMETERS,
    determine_risk,
    full_scales,
)
from .treatment import TREATMENT_ORDER, TREATMENTS

_DISCLAIMER = (
    "Démonstration pédagogique. Le barème de potentiel d'attaque employé ici "
    "est une calibration propre à cet outil : il ne reproduit ni l'ISO/SAE "
    "21434 ni l'ISO 18045, documents sous licence. La norme laisse chaque "
    "organisation définir sa méthode de détermination du risque — celle-ci est "
    "donc une méthode, pas la méthode, et ne se substitue à aucun référentiel."
)

_LIMITS = [
    ("La cotation d'impact et de faisabilité relève du jugement de l'ingénieur",
     "L'outil calcule et trace, il ne décide pas à votre place"),
    ("Le barème de potentiel d'attaque est une calibration propre",
     "À confronter au barème de votre organisation avant tout usage réel"),
    ("La matrice de risque est une méthode parmi d'autres",
     "La norme laisse chaque organisation définir la sienne"),
    ("Les scénarios de menace ne sont pas exhaustifs",
     "Une TARA complète balaie systématiquement les actifs et leurs propriétés"),
    ("Les chemins d'attaque sont décrits en texte, sans arbre d'attaque",
     "L'analyse de chemins d'une TARA réelle va plus loin"),
    ("La sévérité reprise d'une HARA est une proposition",
     "L'exposition et la contrôlabilité, elles, ne traversent jamais le pont"),
    ("Aucune donnée n'est conservée",
     "Ce classeur est le seul artefact produit — pensez à l'archiver"),
]

# Colonnes laissées vides pour le suivi projet : c'est à l'équipe de les
# remplir, pas à l'outil de les inventer.
_GOAL_FOLLOWUP = ["Responsable", "Échéance", "Statut", "Vérification", "Commentaire"]


def build_excel(analysis: TaraAnalysis) -> bytes:
    """Construit le classeur TARA et le rend sous forme d'octets."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="1D9E75")
    title_font = Font(bold=True, size=13)

    workbook = Workbook()
    rows = analysis.rows()
    gaps = analysis.gaps()
    goals = analysis.goals()

    def write_header(sheet, headers):
        sheet.append(headers)
        for cell in sheet[sheet.max_row]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(vertical="center", wrap_text=True)

    def autosize(sheet, widths):
        from openpyxl.utils import get_column_letter

        for index, width in enumerate(widths, start=1):
            sheet.column_dimensions[get_column_letter(index)].width = width

    # --- Synthèse ---------------------------------------------------------
    summary = workbook.active
    summary.title = "Synthèse"
    summary.append(["Analyse de menaces et de risques (TARA)"])
    summary["A1"].font = title_font
    summary.append([])
    summary.append(["Item étudié", analysis.item])
    summary.append(["Date (UTC)", analysis.created_at.strftime("%Y-%m-%d %H:%M")])
    summary.append(["Scénarios de dommage", len(analysis.damages)])
    summary.append(["Chemins d'attaque cotés", len(rows)])
    summary.append(["Risque le plus élevé", analysis.max_risk or "—"])
    summary.append(["Objectifs de cybersécurité produits", len(goals)])
    summary.append(["Repris d'une analyse HARA", analysis.from_hara])
    summary.append([])

    # Ce qui manque passe AVANT la répartition : c'est l'information la plus
    # susceptible d'être ignorée, et la plus coûteuse à découvrir tard.
    if gaps:
        summary.append([f"⚠ {len(gaps)} point(s) à compléter avant de clore l'analyse"])
        summary[summary.max_row][0].font = Font(bold=True)
        for ref, problem in gaps:
            summary.append([f"Menace {ref}", problem])
    else:
        summary.append(["Tous les risques à traiter sont tranchés et justifiés."])
    summary.append([])

    summary.append(["Répartition des valeurs de risque"])
    summary[summary.max_row][0].font = Font(bold=True)
    for value, count in analysis.count_by_risk().items():
        summary.append([f"Risque {value}", count])
    summary.append([])
    summary.append([_DISCLAIMER])
    summary[summary.max_row][0].alignment = Alignment(wrap_text=True, vertical="top")
    autosize(summary, [38, 62])

    # --- Tableau TARA -----------------------------------------------------
    table = workbook.create_sheet("Tableau TARA")
    parameter_keys = list(PARAMETERS)
    write_header(table, [
        "Réf.", "Actif", "Scénario de dommage", "Traçabilité",
        *IMPACT_CATEGORIES.values(), "Impact retenu",
        "Scénario de menace", "Chemin d'attaque",
        *[PARAMETER_LABELS[key] for key in parameter_keys],
        "Potentiel", "Faisabilité", "Risque",
        "Traitement", "Objectif / justification", "Complétude",
    ])

    for row in rows:
        damage, threat = row.damage, row.threat
        levels = [PARAMETERS[key][1][getattr(threat, key)][0] for key in parameter_keys]
        table.append([
            row.ref, damage.asset, damage.description, damage.traceability,
            IMPACT_ORDER[damage.safety], IMPACT_ORDER[damage.financial],
            IMPACT_ORDER[damage.operational], IMPACT_ORDER[damage.privacy],
            damage.impact_label,
            threat.description, threat.path,
            *levels,
            f"{threat.potential} / {MAX_POTENTIAL}", threat.feasibility_label, row.risk,
            threat.decision_label or "—",
            threat.written or "—",
            "Complet" if row.complete else " · ".join(row.problems),
        ])

    for line in table.iter_rows(min_row=2):
        for cell in line:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    autosize(table, [7, 22, 40, 26, 14, 14, 14, 14, 14, 34, 40,
                     18, 18, 18, 18, 18, 12, 14, 8, 20, 44, 32])

    # --- Objectifs de cybersécurité ---------------------------------------
    sheet = workbook.create_sheet("Objectifs de cybersécurité")
    write_header(sheet, ["Réf.", "Objectif de cybersécurité", "Issu de la menace",
                         "Risque traité", "Actif", *_GOAL_FOLLOWUP])
    if goals:
        for index, row in enumerate(goals, start=1):
            sheet.append([f"OC-{index}", row.threat.goal, row.ref, row.risk,
                          row.damage.asset])
    else:
        sheet.append(["—", "Aucun objectif produit : aucune décision de réduire un risque "
                      "n'a été prise et rédigée."])
    for line in sheet.iter_rows(min_row=2):
        for cell in line:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    autosize(sheet, [8, 58, 16, 12, 24, 18, 14, 14, 18, 30])

    # --- Barème appliqué --------------------------------------------------
    # Sans lui, le classeur ne serait pas relisible : impossible de savoir
    # comment un « risque 4 » a été obtenu.
    scales = workbook.create_sheet("Barème appliqué")
    scales.append(["Barème de potentiel d'attaque réellement appliqué"])
    scales["A1"].font = title_font
    scales.append([])
    scales.append([full_scales()["calibration"]])
    scales[scales.max_row][0].alignment = Alignment(wrap_text=True, vertical="top")
    scales.append([])

    write_header(scales, ["Paramètre", "Niveau", "Points"])
    for key in parameter_keys:
        label, levels_map = PARAMETERS[key]
        for level, (level_label, points) in sorted(levels_map.items()):
            scales.append([label if level == 0 else "", level_label, points])
    scales.append([])

    scales.append([f"Total possible : 0 à {MAX_POTENTIAL} points"])
    scales[scales.max_row][0].font = Font(bold=True)
    write_header(scales, ["Potentiel d'attaque", "Faisabilité"])
    previous = 0
    for threshold in full_scales()["feasibilityThresholds"]:
        scales.append([f"{previous} à {threshold['upTo']}",
                       FEASIBILITY_ORDER[threshold["level"]]])
        previous = threshold["upTo"] + 1
    scales.append([f"{previous} et au-delà", FEASIBILITY_ORDER[0]])
    scales.append([])

    scales.append(["Matrice impact × faisabilité → valeur de risque"])
    scales[scales.max_row][0].font = Font(bold=True)
    write_header(scales, ["Impact \\ Faisabilité", *FEASIBILITY_ORDER])
    for impact, impact_label in enumerate(IMPACT_ORDER):
        scales.append([impact_label,
                       *[determine_risk(impact, f) for f in range(len(FEASIBILITY_ORDER))]])
    scales.append([])

    scales.append(["Décisions de traitement et écrit exigé"])
    scales[scales.max_row][0].font = Font(bold=True)
    write_header(scales, ["Décision", "Ce qu'elle impose d'écrire", "Portée"])
    for key in TREATMENT_ORDER:
        option = TREATMENTS[key]
        scales.append([option["label"], option["prompt"], option["hint"]])
    autosize(scales, [30, 34, 20, 20, 20])

    # --- Limites ----------------------------------------------------------
    limits = workbook.create_sheet("Limites")
    write_header(limits, ["Ce que cet outil ne fait pas", "Pourquoi c'est important"])
    for row_values in _LIMITS:
        limits.append(list(row_values))
    for line in limits.iter_rows(min_row=2):
        for cell in line:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
    autosize(limits, [56, 62])

    # ⚠️ Intitulés, chemins d'attaque et objectifs sont saisis par
    # l'utilisateur : sans ce balayage, une chaîne commençant par « = »
    # partirait en formule vivante. Voir src/xlsxsafe/.
    harden(workbook)

    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
