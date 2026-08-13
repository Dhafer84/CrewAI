# Software Requirements Specification — Battery Temperature Monitor (BTM)

**Projet :** BTM — Module de surveillance de température de batterie
**Version :** 1.0
**Contexte :** module logiciel embarqué fictif pour un pack batterie.
**Référentiel visé :** ASPICE (SWE.1 / SWE.2), ISO 26262 Part 6.

> Document fictif à but de démonstration. Aucune donnée réelle.

---

## 1. Introduction

Le module BTM lit périodiquement la température des cellules d'un pack
batterie via un capteur, évalue le niveau de risque thermique, et déclenche
des actions de protection (alerte, dérating, ouverture du contacteur) selon
des seuils définis. Ce document spécifie les exigences logicielles du module.

## 2. Définitions

- **T_cell** : température de cellule mesurée, en °C.
- **Dérating** : réduction volontaire du courant admissible.
- **Contacteur** : relais de puissance isolant le pack en cas de danger.
- **Cycle** : période d'exécution nominale de la tâche BTM.

## 3. Exigences fonctionnelles

### SRS-001 — Acquisition de la température
Le module DOIT lire la température de chaque cellule via l'interface capteur
à chaque cycle d'exécution.
- Critère d'acceptation : à chaque cycle, une valeur T_cell est disponible
  pour chaque cellule.
- Trace amont : SYS-REQ-010.

### SRS-002 — Période d'exécution
La tâche BTM DOIT s'exécuter avec une période de 100 ms (± 10 ms).
- Critère d'acceptation : l'intervalle mesuré entre deux exécutions reste
  dans [90 ms, 110 ms].
- Trace amont : SYS-REQ-011.

### SRS-003 — Détection de surchauffe
Si T_cell dépasse le seuil de surchauffe (T_high = 60 °C), le module DOIT
lever un drapeau d'alerte thermique dans le même cycle.
- Critère d'acceptation : pour T_cell > 60 °C, le drapeau d'alerte passe à
  vrai dans le cycle courant.
- Trace amont : SYS-REQ-012.

### SRS-004 — Réponse rapide en cas de surchauffe
Le système devrait réagir rapidement lorsque la température devient trop
élevée, afin de protéger l'utilisateur.
- Trace amont : SYS-REQ-012.

### SRS-005 — Dérating progressif
Lorsque T_cell est comprise entre T_warn (50 °C) et T_high (60 °C), le
module DOIT appliquer un dérating linéaire du courant admissible, de 100 %
à T_warn jusqu'à 20 % à T_high.
- Critère d'acceptation : à 55 °C, le courant admissible calculé vaut 60 %
  (± 2 %) du courant nominal.
- Trace amont : SYS-REQ-013.

### SRS-006 — Ouverture du contacteur
Si T_cell dépasse le seuil critique (T_crit = 70 °C), le module DOIT
commander l'ouverture du contacteur dans un délai maximal de 50 ms.
- Critère d'acceptation : pour T_cell > 70 °C, la commande d'ouverture est
  émise en moins de 50 ms.
- Trace amont : SYS-REQ-014.

### SRS-007 — Gestion de capteur défaillant
Si la lecture capteur est invalide (hors plage physique [-40 °C, 125 °C] ou
absence de réponse), le module DOIT entrer en état de repli sûr et commander
l'ouverture du contacteur.
- Critère d'acceptation : pour une lecture hors plage, l'état de repli est
  actif et le contacteur est ouvert.
- Trace amont : SYS-REQ-015.

### SRS-008 — Filtrage de la mesure
Le module DOIT appliquer un filtre moyenne glissante sur les 5 dernières
mesures de chaque cellule avant évaluation des seuils.
- Critère d'acceptation : la valeur évaluée est la moyenne des 5 dernières
  mesures valides.
- Trace amont : SYS-REQ-016.

### SRS-009 — Optimisation mémoire du buffer
Le buffer de filtrage doit être rapide.
- Trace amont : SYS-REQ-016.

### SRS-010 — Journalisation des événements
Le module DOIT enregistrer chaque franchissement de seuil (warn, high, crit)
avec un horodatage dans le journal d'événements non volatile.
- Critère d'acceptation : chaque franchissement génère une entrée horodatée.
- Trace amont : SYS-REQ-017.

### SRS-011 — Hystérésis de sortie d'alerte
Le drapeau d'alerte thermique DOIT rester actif tant que T_cell n'est pas
redescendue sous (T_high − 5 °C), afin d'éviter les oscillations.
- Critère d'acceptation : le drapeau se désactive uniquement pour
  T_cell < 55 °C.
- Trace amont : SYS-REQ-012.

### SRS-012 — Confort thermique de l'habitacle
Le module DOIT maintenir une température d'habitacle agréable pour les
passagers en pilotant la ventilation.
- Critère d'acceptation : la température d'habitacle reste confortable.
- Trace amont : (aucune).

### SRS-013 — Initialisation
Au démarrage, le module DOIT initialiser toutes les variables d'état et
vérifier la disponibilité du capteur avant d'entrer en mode nominal.
- Critère d'acceptation : après init, l'état est défini et le capteur est
  confirmé disponible.
- Trace amont : SYS-REQ-018.

### SRS-014 — Redondance de la mesure critique
Pour l'évaluation du seuil critique T_crit, le module DOIT utiliser deux
sources de mesure indépendantes et comparer leur écart.
- Critère d'acceptation : si l'écart entre les deux sources dépasse 5 °C,
  l'état de repli sûr est activé.
- Trace amont : SYS-REQ-014.

### SRS-015 — Temps de réponse global
Le délai entre le franchissement de T_crit et l'ouverture effective du
contacteur DOIT être borné et vérifiable.
- Critère d'acceptation : le délai total mesuré est inférieur à 100 ms.
- Trace amont : SYS-REQ-014.

## 4. Exigences non fonctionnelles

### SRS-016 — Robustesse
Le module DOIT continuer à fonctionner de manière déterministe en présence
de mesures bruitées, sans blocage ni dépassement de délai.
- Critère d'acceptation : sur un jeu de mesures bruitées, aucun dépassement
  de la période d'exécution n'est observé.
- Trace amont : SYS-REQ-019.
