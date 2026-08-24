"""Export Excel d'une veille RegWatch.

Le classeur doit être **relisible sans l'outil**, six mois plus tard, par
quelqu'un qui n'a jamais vu la page. D'où l'onglet « Sources » : un signal
étiqueté « commentaire » ne veut rien dire si personne ne peut retrouver de
quelle source il vient ni ce qu'elle vaut.

Il dit aussi ce qu'il **n'a pas pu voir**. Un classeur de veille qui tait ses
sources muettes est pire qu'un classeur qui les liste : il transforme une
panne en « rien de neuf », et c'est le seul défaut vraiment grave pour cet
outil.

⚠️ **Le contenu des normes n'y figure pas davantage que sur la page** — titre,
date, lien. Ce classeur ne doit jamais devenir un moyen détourné de republier
ce que RegWatch s'interdit d'afficher.
"""

from io import BytesIO

from xlsxsafe import harden

from .classify import SIGNAL_ORDER
from .config import LOOKBACK_DAYS
from .core import WatchResult
from .norms import NORMS
from .sources import SOURCES, TIERS

_DISCLAIMER = (
    "Démonstration pédagogique. RegWatch ne republie jamais le contenu des "
    "normes — elles sont payantes et protégées : seuls le titre, la date et le "
    "lien vers la source sont remontés, et le corps des pages n'est même pas "
    "téléchargé. Le niveau de signal est déduit du titre seul : il oriente, "
    "c'est le lien qui fait foi. Cet outil ne remplace ni la lecture des "
    "normes, ni un service de veille réglementaire."
)

_LIMITS = [
    ("La fenêtre est fixe, elle ne suit pas vos visites",
     f"Ce classeur couvre les {LOOKBACK_DAYS} derniers jours au moment de "
     "l'export, pas « depuis la dernière fois » : l'outil ne garde aucune "
     "trace de vos passages"),
    ("Le niveau de signal est déduit du titre seul",
     "Faute de corps de page, un article « comment mettre à jour votre SMSI » "
     "peut ressortir en « Publication ». L'étiquette oriente, le lien est le "
     "livrable"),
    ("Toutes les sources ne se valent pas",
     "Le palier est porté par chaque ligne et détaillé dans l'onglet Sources. "
     "Un blog spécialisé n'est pas un organisme de normalisation"),
    ("Une absence de signal n'est pas une preuve",
     "Vérifiez l'onglet Couverture avant de conclure que rien n'a bougé"),
    ("La colonne « Pourquoi ça compte » est écrite par un modèle",
     "À partir du seul intitulé, sans avoir lu le document. Elle n'a joué "
     "aucun rôle dans la sélection des lignes de ce classeur"),
    ("Les sources ne couvrent pas tout ce qui existe",
     "ISO.org et unece.org refusent l'accès aux programmes : certaines normes "
     "n'ont donc aucune source officielle atteignable"),
    ("Ce classeur est le seul artefact durable",
     "Rien n'est conservé sur le serveur après l'export — pensez à l'archiver"),
]

# Colonnes laissées vides : c'est au veilleur de qualifier, pas à l'outil de
# décider. Même parti pris que l'onglet Détections de SentinelScan.
_FOLLOWUP = ["À lire ?", "Impact pour nous", "Action décidée", "Responsable",
             "Échéance", "Commentaire"]


def build_excel(result: WatchResult) -> bytes:
    """Construit le classeur de veille et le rend sous forme d'octets."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="1D9E75")
    title_font = Font(bold=True, size=13)
    warn_font = Font(bold=True, color="C00000")

    workbook = Workbook()

    def write_header(sheet, headers):
        sheet.append(headers)
        for cell in sheet[sheet.max_row]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(vertical="center", wrap_text=True)

    def autosize(sheet, widths):
        for index, width in enumerate(widths, start=1):
            sheet.column_dimensions[get_column_letter(index)].width = width

    surveillees = [NORMS[key].label for key in result.norms if key in NORMS]
    par_norme = result.count_by_norm()
    par_signal = result.count_by_signal()

    # --- Synthèse ---------------------------------------------------------
    summary = workbook.active
    summary.title = "Synthèse"
    summary.append(["Veille de signaux publics autour des normes"])
    summary["A1"].font = title_font
    summary.append([])
    summary.append(["Date de la veille (UTC)",
                    result.started_at.strftime("%Y-%m-%d %H:%M")])
    summary.append(["Fenêtre couverte", f"{result.lookback_days} jours"])
    summary.append(["Référentiels surveillés", ", ".join(surveillees) or "—"])
    summary.append(["Sources interrogées",
                    f"{result.sources_read} / {result.sources_total}"])
    summary.append(["Signaux retenus", len(result.items)])
    summary.append([])

    # ⚠️ Ce qui n'a pas pu être vu passe AVANT toute répartition. C'est
    # l'information la plus facile à ignorer et la plus coûteuse à découvrir
    # tard — même discipline que l'avertissement de couverture de
    # SentinelScan et que les manques en tête de la Synthèse TARA.
    if result.coverage_is_incomplete:
        summary.append([
            f"⚠ COUVERTURE INCOMPLÈTE — {len(result.unreachable)} source(s) "
            f"injoignable(s), {len(result.degraded)} dégradée(s). "
            "Une absence de signal ne prouve rien."])
        summary[summary.max_row][0].font = warn_font
        for label in result.unreachable:
            summary.append(["Injoignable", label])
        for label in result.degraded:
            summary.append(["Structure non reconnue", label])
    else:
        summary.append(["Toutes les sources interrogées ont répondu."])
    summary.append([])

    if result.undated:
        summary.append([f"⚠ {len(result.undated)} élément(s) pertinent(s) écarté(s), "
                        "faute de date exploitable"])
        summary[summary.max_row][0].font = warn_font
        for ligne in result.undated:
            summary.append(["Sans date", ligne])
        summary.append([])

    summary.append(["Répartition par niveau de signal"])
    summary[summary.max_row][0].font = Font(bold=True)
    for signal in SIGNAL_ORDER:
        summary.append([signal, par_signal.get(signal, 0)])
    summary.append([])

    summary.append(["Répartition par référentiel"])
    summary[summary.max_row][0].font = Font(bold=True)
    for key in result.norms:
        summary.append([NORMS[key].label if key in NORMS else key,
                        par_norme.get(key, 0)])
    summary.append([])
    summary.append([_DISCLAIMER])
    summary[summary.max_row][0].alignment = Alignment(wrap_text=True, vertical="top")
    autosize(summary, [34, 74])

    # --- Signaux ----------------------------------------------------------
    signals = workbook.create_sheet("Signaux")
    write_header(signals, [
        "Référentiel", "Date", "Niveau de signal", "Intitulé",
        "Source", "Palier", "Lien", "Pourquoi ça compte (IA)", *_FOLLOWUP,
    ])
    for item in result.items:
        signals.append([
            item.norm_label,
            item.published.isoformat(),
            item.signal,
            item.title,
            item.source_label,
            item.source_tier,
            item.url,
            item.why,
        ])
    signals.freeze_panes = "A2"
    autosize(signals, [22, 12, 22, 62, 30, 14, 52, 52,
                       *[16] * len(_FOLLOWUP)])

    # --- Couverture -------------------------------------------------------
    coverage = workbook.create_sheet("Couverture")
    coverage.append(["Ce que la veille a pu voir, et ce qu'elle n'a pas pu voir"])
    coverage["A1"].font = title_font
    coverage.append([])
    write_header(coverage, ["Source", "État", "Détail"])

    for source in SOURCES:
        if not set(result.norms).intersection(source.norm_keys):
            continue
        if source.label in result.unreachable:
            etat, detail = "INJOIGNABLE", "Aucune réponse exploitable"
        elif source.label in result.degraded:
            etat, detail = ("DÉGRADÉE",
                            "La page répond mais rien ne s'en extrait — la "
                            "structure du site a probablement changé")
        else:
            etat, detail = "Répondu", "Lue et analysée"
        coverage.append([source.label, etat, detail])

    coverage.append([])
    if result.errors:
        coverage.append(["Détail des incidents"])
        coverage[coverage.max_row][0].font = Font(bold=True)
        for message in result.errors:
            coverage.append([message])
    if result.undated:
        coverage.append([])
        coverage.append(["Écartés faute de date exploitable"])
        coverage[coverage.max_row][0].font = Font(bold=True)
        for ligne in result.undated:
            coverage.append([ligne])
    autosize(coverage, [42, 18, 74])

    # --- Sources ----------------------------------------------------------
    catalogue = workbook.create_sheet("Sources")
    catalogue.append(["D'où viennent ces signaux, et ce que chaque source vaut"])
    catalogue["A1"].font = title_font
    catalogue.append([])
    write_header(catalogue, ["Source", "Référentiels", "Palier", "Adresse",
                             "Ce qu'il faut en savoir"])
    for source in SOURCES:
        catalogue.append([
            source.label,
            ", ".join(NORMS[key].label for key in source.norm_keys if key in NORMS),
            source.tier,
            source.url,
            source.note,
        ])
    catalogue.append([])
    catalogue.append(["Paliers de fiabilité"])
    catalogue[catalogue.max_row][0].font = Font(bold=True)
    for key, label in TIERS.items():
        catalogue.append([key, label])
    autosize(catalogue, [40, 34, 16, 52, 86])

    # --- Limites ----------------------------------------------------------
    limits = workbook.create_sheet("Limites")
    limits.append(["Ce que cet outil ne fait pas"])
    limits["A1"].font = title_font
    limits.append([])
    write_header(limits, ["Limite", "Précision"])
    for limite, precision in _LIMITS:
        limits.append([limite, precision])
    autosize(limits, [56, 82])

    # ⚠️ Intitulés, noms de source et liens viennent de **tiers** : un flux
    # public peut très bien publier un titre commençant par « = ». Sans ce
    # balayage, openpyxl l'écrirait comme une formule vivante (CWE-1236) et
    # la victime serait le veilleur qui ouvre le classeur. Même scénario que
    # les noms de dépôt GitHub de SentinelScan. Voir src/xlsxsafe/.
    harden(workbook)

    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
