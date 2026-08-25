"""CauseTrace — assistant de résolution de réclamation (8D) et d'analyse causale.

Moteur pur : aucune connaissance du web ni du CLI, aucun appel réseau, aucun
LLM. L'outil rend son résultat — le dossier, ses trous, son droit à être
clos — sans qu'aucun modèle ne soit appelé.

Le 8D vient de Ford et relève du domaine public ; Ishikawa, les 5 Pourquoi et
le is/is-not le sont également. **C'est le premier outil du catalogue sans
contrainte de droit d'auteur** : on peut nommer les disciplines par leur nom,
là où SafetyScope et ThreatScope doivent reformuler le texte de normes sous
licence.

Ce que cet outil démontre n'est pas de remplir huit cases — c'est de
**refuser d'appeler « résolu » un dossier qui ne l'est pas**, et de dire
précisément où il pèche.
"""
