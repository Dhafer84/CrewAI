# Review Report — BTM SRS & Test Plan

**Projet :** BTM
**Version des documents revus :** SRS v1.0, Test Plan v1.0
**Type de revue :** revue par les pairs (première passe)

> Document fictif à but de démonstration. Aucune donnée réelle.

---

## 1. Participants

- Revue menée par un ingénieur qualité (première passe).
- Auteurs des documents présents.

## 2. Constats de la revue

### R-01 — SRS-002, valeur de période
La période de 100 ms est-elle cohérente avec le temps de réponse exigé pour
l'ouverture du contacteur ? À vérifier avec l'équipe système.
- Statut : ouvert.

### R-03 — SRS-010, format d'horodatage
Le format d'horodatage du journal n'est pas précisé (résolution, base de
temps). À clarifier.
- Statut : ouvert.

### R-04 — Cohérence des seuils
Les seuils T_warn = 50 °C, T_high = 60 °C, T_crit = 70 °C sont cohérents
entre eux et avec le dérating décrit.
- Statut : accepté.

### R-05 — SRS-013, initialisation
Bonne pratique : la vérification capteur au démarrage est explicitement
requise. Rien à signaler.
- Statut : accepté.

## 3. Remarques générales

- La structure du SRS est globalement claire et la majorité des exigences
  sont formulées avec un critère d'acceptation.
- La revue de première passe ne couvre pas l'analyse exhaustive de
  traçabilité ni la complétude de la couverture de test ; ces points sont
  délégués à l'analyse qualité automatisée.
