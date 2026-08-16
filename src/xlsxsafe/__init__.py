"""Écrire des classeurs Excel sans y glisser de formule exécutable.

Utilitaire de sérialisation partagé par les trois outils. Ce n'est pas de la
logique métier : les moteurs restent indépendants les uns des autres, ils
partagent seulement un outil d'écriture.

## Le problème (CWE-1236)

openpyxl décide du type d'une cellule à partir de sa valeur : **toute chaîne
commençant par `=` est écrite comme une formule**, pas comme du texte. Un
rapport construit à partir de données saisies — ou pire, de données venues de
tiers — embarque alors des formules vivantes.

Le cas dangereux n'est pas théorique : SentinelScan écrit dans ses colonnes le
nom du dépôt, du propriétaire et le chemin du fichier, **tous fournis par
GitHub**. Il suffit de nommer un dépôt public `=HYPERLINK(...)` et d'attendre
qu'un scan le remonte. La victime est alors l'analyste qui ouvre le classeur.

## Ce que ce module garantit, et ce qu'il ne garantit pas

`harden()` retype en texte toute cellule qu'Excel évaluerait. **Le contenu
n'est pas modifié** — pas d'apostrophe ajoutée, pas de caractère escamoté :
l'analyste lit exactement ce qui a été détecté, ce qui est le minimum pour un
rapport censé faire foi.

Portée exacte, sans exagération :

- ✅ **Dans le classeur `.xlsx`, c'est réglé.** Le format est typé : une
  cellule de type texte n'est jamais évaluée à l'ouverture. Le seul cas
  réellement vivant était `=`, écrit en type formule par openpyxl.
- ⚠️ **Une conversion ultérieure en CSV rouvre le sujet.** Le CSV n'a aucun
  type : à la réimportation, Excel reparse tout, et les têtes `+`, `-`, `@`
  redeviennent des amorces de formule. Ce module les retype aussi par
  précaution, mais si un jour un export CSV est ajouté, il lui faudra sa
  propre protection — le préfixe apostrophe — et ce module ne l'apporte pas.
"""

# Caractères par lesquels Excel reconnaît une amorce de formule.
FORMULA_STARTERS = ("=", "+", "-", "@")

# Excel ignore ces caractères en tête de cellule et « découvre » le suivant :
# "\t=1+1" est donc aussi dangereux que "=1+1".
_IGNORED_LEADING = "\t\r\n\x0b\x0c\x00 "

# Type openpyxl d'une cellule texte, et celui d'une formule.
_TEXT = "s"
_FORMULA = "f"


def looks_like_formula(value: object) -> bool:
    """La valeur serait-elle interprétée comme une formule ?

    Seules les chaînes sont concernées : un entier, une date ou un booléen ne
    peuvent pas porter de formule.
    """
    if not isinstance(value, str):
        return False
    return value.lstrip(_IGNORED_LEADING).startswith(FORMULA_STARTERS)


def harden(workbook) -> int:
    """Retype en texte toute cellule qu'Excel évaluerait, dans tout le classeur.

    À appeler **une fois, juste avant `workbook.save()`**. C'est délibérément
    un balayage complet plutôt qu'un contrôle à chaque écriture : une nouvelle
    ligne ajoutée un jour dans un rapport est couverte sans que personne ait à
    y penser. Un garde-fou qu'on peut oublier d'appliquer n'est pas un
    garde-fou.

    Returns:
        Le nombre de cellules neutralisées — utile aux tests, et pour se
        rendre compte si un rapport en contient beaucoup.
    """
    neutralized = 0
    for sheet in workbook.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if cell.data_type == _FORMULA or looks_like_formula(cell.value):
                    cell.data_type = _TEXT
                    neutralized += 1
    return neutralized
