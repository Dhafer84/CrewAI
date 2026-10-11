# Spécification des exigences logicielles — [Nom du module]

**Projet :** [Nom du projet]
**Version :** [1.0]
**Contexte :** [Une phrase : ce que fait le module, dans quel système.]
**Référentiel visé :** ASPICE (SWE.1 / SWE.2), ISO 26262 Part 6.

> ⚠️ **N'y mettez rien de confidentiel.** Pour l'audit, ce document est envoyé à un
> service d'IA externe (Groq). Utilisez un projet fictif ou anonymisé.
>
> Mode d'emploi : remplacez tout ce qui est entre [crochets], gardez les titres et les
> identifiants (SRS-001, SRS-002…). Copiez un bloc « SRS-… » par exigence. Les
> remarques en italique renvoient aux points de contrôle de l'audit (CHK-xx) ;
> supprimez-les ensuite si vous voulez.

---

## 1. Introduction

[Ce que fait le module, ses entrées et ses sorties, ce qui est hors de son périmètre.]

## 2. Définitions

- **[Terme]** : [définition, avec unité si c'est une grandeur].
- **[Terme]** : [définition].

## 3. Exigences fonctionnelles

### SRS-001 — [Titre court]
Le module DOIT [un seul comportement, mesurable].
- Critère d'acceptation : [condition vérifiable, avec valeur et unité].
- Trace amont : [SYS-REQ-xxx, ou justification de l'absence de trace].

*Un identifiant unique par exigence (CHK-01) ; un critère d'acceptation mesurable
(CHK-02) ; pas de mot vague du type « rapidement » sans valeur (CHK-03) ; un seul besoin
par exigence, pas de « et » qui en cache deux (CHK-04) ; une trace amont (CHK-06).*

### SRS-002 — [Titre court]
Le module DOIT [comportement].
- Critère d'acceptation : [condition vérifiable].
- Trace amont : [SYS-REQ-xxx].

### SRS-003 — [Fonction de sécurité : détection, repli, protection]
Si [condition], le module DOIT [réaction] en moins de [durée] [unité].
- Critère d'acceptation : [condition vérifiable, temps de réponse borné].
- Trace amont : [SYS-REQ-xxx].

*Fonctions de sécurité : comportement déterministe (CHK-10), temps de réponse borné
(CHK-11), seuils et hystérésis cohérents entre exigences liées (CHK-13).*

### SRS-004 — [Défaillance d'un capteur ou d'une entrée]
Si [entrée invalide ou hors plage], le module DOIT [état de repli sûr].
- Critère d'acceptation : [condition vérifiable].
- Trace amont : [SYS-REQ-xxx].

*Comportement en cas de défaillance spécifié (CHK-12).*

## 4. Exigences non fonctionnelles

### SRS-005 — [Robustesse, performance, mémoire…]
Le module DOIT [exigence mesurable].
- Critère d'acceptation : [condition vérifiable].
- Trace amont : [SYS-REQ-xxx].
