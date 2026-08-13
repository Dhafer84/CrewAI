"""Définition des 4 tâches du crew, une par agent."""

from crewai import Agent, Task


def make_tasks(agents: dict[str, Agent], docs: dict[str, str]) -> list[Task]:
    srs = docs["srs"]
    test_plan = docs["test_plan"]
    review_report = docs["review_report"]
    checklist = docs["checklist"]

    analyse_exigences = Task(
        description=f"""
Analyse chaque exigence du SRS ci-dessous selon les critères CHK-01 à CHK-06 :

- CHK-01 : identifiant unique présent
- CHK-02 : critère d'acceptation présent et mesurable
- CHK-03 : absence de termes vagues sans valeur chiffrée (ex. "rapidement", "rapide", "agréable")
- CHK-04 : une seule exigence par item (pas de "et" masquant deux besoins)
- CHK-05 : périmètre cohérent avec le module BTM (pas de besoin hors-sujet)
- CHK-06 : trace amont vers une exigence système (ou justification d'absence)

Pour chaque problème trouvé, indique sur une ligne :
  [ID exigence] | [CHK-XX] | [description courte du problème]

Si une exigence est conforme sur tous les points, ne la mentionne pas.

SRS :
{srs}
""",
        expected_output=(
            "Liste des constats au format : [ID] | [CHK-XX] | [description]. "
            "Une ligne par problème détecté. "
            "Si aucun problème : écrire 'Aucun constat — toutes les exigences sont conformes.'"
        ),
        agent=agents["analyste"],
    )

    verification_conformite = Task(
        description=f"""
Sur la base des constats de l'analyse d'exigences (tâche précédente),
croise le SRS et le plan de test avec la checklist ci-dessous.

Pour chaque point CHK-01 à CHK-15, produis une ligne du tableau :
| CHK-XX | Libellé court | Conforme / Non conforme / Non applicable | Justification (1-2 phrases) |

Appuie-toi sur les éléments de preuve dans les documents : cite l'exigence ou le cas de test
qui justifie le verdict, ou explique ce qui manque.

CHECKLIST :
{checklist}

PLAN DE TEST :
{test_plan}

SRS (rappel) :
{srs}
""",
        expected_output=(
            "Tableau markdown à 4 colonnes, 15 lignes (CHK-01 à CHK-15) : "
            "| Point | Libellé | Verdict | Justification |"
        ),
        agent=agents["verificateur"],
    )

    detection_risques = Task(
        description=f"""
À partir des constats des deux analyses précédentes, identifie les risques de plus haut niveau.

Cherche systématiquement :
1. Trous de couverture : exigences du SRS sans aucun cas de test dans le plan de test
2. Points ISO 26262 spécifiés dans le SRS mais non testés (notamment sûreté, redondance, temps de réponse)
3. Incohérences entre SRS, plan de test et rapport de revue
4. Constats de revue avec statut "ouvert" non adressés

Pour chaque risque identifié :
  - Référence(s) concernée(s) : ex. SRS-014, TC-xxx
  - Nature du risque en une phrase
  - Niveau : Critique | Majeur | Mineur

Classe les risques par niveau décroissant.

RAPPORT DE REVUE :
{review_report}
""",
        expected_output=(
            "Liste de risques classés par sévérité décroissante. "
            "Format par risque : Niveau | Réf(s) | Description du risque."
        ),
        agent=agents["detecteur"],
    )

    redaction_rapport = Task(
        description="""
Rédige le rapport d'audit final en markdown. Utilise uniquement les constats
produits par les trois agents précédents — ne pas inventer de nouveaux problèmes.

Structure obligatoire :

## Rapport d'audit — BTM SRS & Test Plan

### 1. En-tête
Projet, date (aujourd'hui), version des documents audités (SRS v1.0, Test Plan v1.0, Checklist v1.0).

### 2. Résumé exécutif
3 à 5 lignes : verdict global, nombre de non-conformités par sévérité (Critique / Majeur / Mineur / Observation).

### 3. Tableau de synthèse des non-conformités
| # | Réf. | Type | Sévérité | Description | Recommandation |
Trié par sévérité décroissante. Une ligne par constat distinct.

### 4. Points de conformité
Liste des CHK-XX pour lesquels le verdict est "Conforme".

### 5. Recommandations prioritaires
Top 3 actions à mener en priorité, numérotées, formulées comme des actions concrètes.

### 6. Conclusion
Une phrase de verdict global.
""",
        expected_output=(
            "Rapport d'audit complet en markdown, autonome (lisible sans les "
            "analyses intermédiaires), structuré selon les 6 sections demandées."
        ),
        agent=agents["redacteur"],
    )

    return [analyse_exigences, verification_conformite, detection_risques, redaction_rapport]
