# Plan de test — [Nom du module]

**Projet :** [Nom du projet]
**Version :** [1.0]
**Objet :** cas de test de vérification des exigences logicielles du module [nom].

> ⚠️ **N'y mettez rien de confidentiel.** Pour l'audit, ce document est envoyé à un
> service d'IA externe (Groq). Utilisez un projet fictif ou anonymisé.
>
> Mode d'emploi : remplacez tout ce qui est entre [crochets], gardez les titres et les
> identifiants (TC-001, TC-002…). Copiez un bloc « TC-… » par cas de test.

---

## 1. Portée

Ce plan décrit les cas de test associés aux exigences de la spécification
[nom du document, version]. Chaque cas référence l'exigence qu'il vérifie.

## 2. Cas de test

### TC-001 — [Titre court]
- Vérifie : SRS-001
- Description : [stimuli, conditions, mesure].
- Résultat attendu : [valeur ou état observable, avec unité].

*Chaque cas de test référence au moins une exigence existante (CHK-08).*

### TC-002 — [Titre court]
- Vérifie : SRS-002
- Description : [stimuli, conditions, mesure].
- Résultat attendu : [valeur ou état observable].

### TC-003 — [Titre court]
- Vérifie : SRS-003
- Description : [stimuli, conditions, mesure du temps de réponse].
- Résultat attendu : [réaction en moins de N unité].

## 3. Matrice de couverture

*Chaque exigence couverte par au moins un cas de test (CHK-07, CHK-14) ; cette matrice
doit correspondre au contenu réel de la spécification et des cas ci-dessus (CHK-09).*

| Exigence | Cas de test |
|----------|-------------|
| SRS-001  | TC-001      |
| SRS-002  | TC-002      |
| SRS-003  | TC-003      |
