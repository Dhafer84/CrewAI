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

Pour chaque problème trouvé, ajoute une ligne à un tableau markdown avec les colonnes
Exigence | Point | Constat.

Si une exigence est conforme sur tous les points, ne la mentionne pas.

SRS :
{srs}
""",
        expected_output=(
            "Un tableau markdown valide (ligne d'en-tête + ligne de séparation ---) "
            "avec les colonnes Exigence | Point | Constat, une ligne par problème détecté. "
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

INSTRUCTIONS CRITIQUES pour CHK-07 et CHK-14 (couverture de test) :
- Extrais d'abord la liste COMPLÈTE des identifiants du SRS (SRS-001, SRS-002, ... jusqu'au dernier).
- Pour chaque identifiant, cherche s'il apparaît dans une ligne "Vérifie : SRS-XXX" du plan de test.
- Tout identifiant SRS absent du plan de test est un trou de couverture à signaler NOMINATIVEMENT.
- CHK-07 est Non conforme dès qu'une seule exigence n'a pas de cas de test.
- Ne te contente pas de vérifier si la matrice déclarée est "cohérente avec elle-même" : vérifie
  qu'elle couvre TOUTES les exigences du SRS.

INSTRUCTIONS CRITIQUES pour CHK-11 et CHK-13 (sûreté ISO 26262) :
- CHK-11 exige que les temps de réponse soient bornés ET vérifiables (= qu'un TC les mesure).
  Une exigence de délai spécifiée mais sans TC n'est PAS vérifiable : verdict Non conforme.
- CHK-13 exige cohérence entre seuils, hystérésis et redondance. Vérifie également que
  les fonctions de sécurité spécifiant une redondance matérielle (ex. double source de mesure)
  ont bien un TC qui valide ce comportement.

CHECKLIST :
{checklist}

PLAN DE TEST :
{test_plan}

SRS (rappel) :
{srs}
""",
        expected_output=(
            "Tableau markdown à 4 colonnes, 15 lignes (CHK-01 à CHK-15) : "
            "| Point | Libellé | Verdict | Justification | "
            "La justification de CHK-07 doit lister les SRS-XXX sans TC. "
            "La justification de CHK-11 doit préciser si les délais sont testés ou seulement spécifiés."
        ),
        agent=agents["verificateur"],
    )

    detection_risques = Task(
        description=f"""
À partir des constats des deux analyses précédentes, identifie les risques de plus haut niveau.

ÉTAPE 1 — Trous de couverture (à faire AVANT tout le reste) :
Dresse la liste exhaustive des exigences SRS sans aucun cas de test.
Méthode : pour chaque SRS-XXX du document, vérifie qu'au moins un TC indique "Vérifie : SRS-XXX".
Liste NOMINATIVEMENT chaque SRS-XXX non couvert. Ne pas écrire "certaines exigences" : cite les IDs.

ÉTAPE 2 — Risques sûreté ISO 26262 (fonctions critiques non vérifiées) :
Examine chaque exigence portant sur une fonction de sécurité (ouverture contacteur, redondance
de mesure, temps de réponse, repli sûr). Pour chacune :
  a) La fonction est-elle spécifiée avec un comportement déterministe ? (CHK-10)
  b) Existe-t-il un TC qui la mesure réellement ? Si non → risque à signaler.
Porte une attention particulière aux exigences liées à SYS-REQ-014 (SRS-006, SRS-014, SRS-015) :
ce sont les exigences critiques de temps de réponse et de redondance.

ÉTAPE 3 — Incohérences croisées :
  - SRS-006 impose ouverture contacteur < 50 ms après T_crit.
  - SRS-015 impose délai global T_crit → ouverture < 100 ms.
  Ces deux contraintes sont-elles testées ? Si non, note l'incohérence : spécifié mais non vérifié.

ÉTAPE 4 — Constats de revue ouverts non adressés dans le plan de test.

Pour chaque risque :
  Niveau : Critique | Majeur | Mineur
  Réf(s) : SRS-XXX et/ou TC-XXX concernés
  Description : une phrase précise

Classe par niveau décroissant (Critique en premier).

RAPPORT DE REVUE :
{review_report}

SRS (rappel pour les étapes 2 et 3) :
{srs}

PLAN DE TEST (rappel pour les étapes 1, 2 et 3) :
{test_plan}
""",
        expected_output=(
            "Liste structurée de risques par niveau décroissant. "
            "L'étape 1 doit nommer chaque SRS-XXX sans TC. "
            "L'étape 2 doit mentionner explicitement SRS-014 et SRS-015 si non testés. "
            "L'étape 3 doit statuer sur la cohérence SRS-006 / SRS-015 et leur couverture de test."
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
