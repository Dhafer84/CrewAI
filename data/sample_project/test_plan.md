# Test Plan — Battery Temperature Monitor (BTM)

**Projet :** BTM
**Version :** 1.0
**Objet :** cas de test de vérification des exigences logicielles du module BTM.

> Document fictif à but de démonstration. Aucune donnée réelle.

---

## 1. Portée

Ce plan décrit les cas de test associés aux exigences du SRS BTM v1.0.
Chaque cas référence l'exigence qu'il vérifie.

## 2. Cas de test

### TC-001 — Acquisition périodique
- Vérifie : SRS-001
- Description : injecter des valeurs capteur connues, vérifier qu'une valeur
  T_cell est disponible à chaque cycle pour chaque cellule.
- Résultat attendu : une valeur par cellule et par cycle.

### TC-002 — Période d'exécution
- Vérifie : SRS-002
- Description : mesurer l'intervalle entre exécutions sur 1000 cycles.
- Résultat attendu : intervalle dans [90 ms, 110 ms].

### TC-003 — Détection de surchauffe
- Vérifie : SRS-003
- Description : appliquer T_cell = 62 °C, vérifier le drapeau d'alerte.
- Résultat attendu : drapeau vrai dans le cycle courant.

### TC-004 — Dérating à mi-plage
- Vérifie : SRS-005
- Description : appliquer T_cell = 55 °C, lire le courant admissible.
- Résultat attendu : 60 % (± 2 %) du courant nominal.

### TC-005 — Ouverture du contacteur en surchauffe critique
- Vérifie : SRS-006
- Description : appliquer T_cell = 72 °C, mesurer le délai d'émission de la
  commande d'ouverture.
- Résultat attendu : commande émise en moins de 50 ms.

### TC-006 — Capteur hors plage
- Vérifie : SRS-007
- Description : injecter une lecture à 200 °C (hors plage).
- Résultat attendu : état de repli sûr actif, contacteur ouvert.

### TC-007 — Filtre moyenne glissante
- Vérifie : SRS-008
- Description : injecter une séquence de 5 mesures connues, lire la valeur
  évaluée.
- Résultat attendu : moyenne des 5 dernières mesures valides.

### TC-008 — Journalisation d'un franchissement
- Vérifie : SRS-010
- Description : provoquer un franchissement de T_high, inspecter le journal.
- Résultat attendu : une entrée horodatée présente.

### TC-009 — Initialisation
- Vérifie : SRS-013
- Description : démarrer le module, inspecter l'état et la vérification
  capteur.
- Résultat attendu : état défini, capteur confirmé disponible.

### TC-010 — Robustesse au bruit
- Vérifie : SRS-016
- Description : injecter un signal bruité sur 5000 cycles.
- Résultat attendu : aucun dépassement de la période d'exécution.

## 3. Matrice de couverture (déclarée par l'équipe test)

| Exigence | Cas de test |
|----------|-------------|
| SRS-001  | TC-001      |
| SRS-002  | TC-002      |
| SRS-003  | TC-003      |
| SRS-005  | TC-004      |
| SRS-006  | TC-005      |
| SRS-007  | TC-006      |
| SRS-008  | TC-007      |
| SRS-010  | TC-008      |
| SRS-013  | TC-009      |
| SRS-016  | TC-010      |
