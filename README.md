# QualityCrew — outils Qualité & Sécurité pour l'automobile

**[qualitycrew.fr](https://qualitycrew.fr)** · six outils de conformité normative et
de sécurité de l'information, en ligne et fonctionnels.

[![Licence MIT](https://img.shields.io/badge/licence-MIT-5dcaa5)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![393 tests](https://img.shields.io/badge/tests-393-5dcaa5)

Projet personnel. Aucune donnée réelle d'entreprise, aucun lien avec un employeur —
les documents d'entrée sont fictifs et le disent en tête de fichier.

---

## Les six outils

| Outil | Ce qu'il fait | Référentiel | IA |
|---|---|---|---|
| **[QualityCrew](https://qualitycrew.fr/qualitycrew)** | Audit de conformité d'un dossier documentaire par 4 agents | ASPICE · ISO 26262 Part 6 | **Indispensable** |
| **[SentinelScan](https://qualitycrew.fr/sentinelscan)** | Veille de fuite d'information sur les dépôts GitHub publics | OSINT passif | Aucune |
| **[SafetyScope](https://qualitycrew.fr/hara)** | Analyse de risques et détermination du niveau ASIL | ISO 26262 Part 3 | Facultative |
| **[ThreatScope](https://qualitycrew.fr/tara)** | Analyse de menaces et de risques cybersécurité | ISO/SAE 21434 · UN R155 | Facultative |
| **[RegWatch](https://qualitycrew.fr/regwatch)** | Veille de signaux publics autour des normes | 5 référentiels | Facultative |
| **[CauseTrace](https://qualitycrew.fr/8d)** | Résolution de réclamation 8D et analyse causale | 8D · 5 Pourquoi · Ishikawa | Facultative |

Le site est **bilingue français / anglais**, rendu côté serveur — chaque langue a
ses propres URL, indexables et partageables (`/tara` ⇄ `/en/tara`).

---

## Le parti pris

Ce qui distingue ces outils d'un habillage de LLM tient en trois règles, tenues
dans le code et vérifiées par des tests.

**Cinq des six outils rendent leur résultat sans appeler un seul modèle.**
Une cotation ASIL est une table de décision : elle est exacte et instantanée. Lui
substituer un modèle de langage la rendrait plus lente, plus chère et moins juste.
L'IA n'intervient que là où elle apporte réellement quelque chose — écrire un audit,
dérouler un balayage STRIDE, reformuler un texte mal écrit.

**L'IA ne cote jamais, ne décide jamais, ne filtre jamais.** Elle propose des
événements redoutés sans les coter, des menaces sans les évaluer, une phrase
d'explication sans choisir ce qui remonte. Les cartes qu'elle produit arrivent
**vides côté cotation** — c'est structurel : les objets de proposition n'ont
simplement pas de champ pour ça, et un test tombe si quelqu'un en ajoute un.

**Un résultat qui ne débouche sur rien n'a rien décidé.** ThreatScope va jusqu'aux
objectifs de cybersécurité et exige une justification écrite pour tout risque
accepté. CauseTrace refuse d'appeler « résolu » un 8D qui ne l'est pas, et nomme
précisément ce qui lui manque.

**Deux outils se parlent.** SafetyScope alimente ThreatScope — mais seule la
**sévérité** traverse le pont. L'exposition et la contrôlabilité, non : un attaquant
choisit son moment et peut neutraliser le recours, la notion s'effondre. La règle
est implémentée *et* expliquée à l'écran.

---

## Architecture

Trois couches strictement séparées. Un moteur ne sait rien du web, ni de la CLI,
ni de la langue d'affichage.

```
src/            moteurs — logique pure, testable hors ligne
  ├── qualitycrew/   safetyscope/   regwatch/     i18n/       ← utilitaires
  ├── sentinelscan/  threatscope/   causetrace/   xlsxsafe/      partagés
api/            enveloppes minces — FastAPI, SSE, rendu bilingue
site/           présentation — HTML/CSS/JS vanilla, aucun framework
```

Chaque moteur expose une **interface stable** que la couche web consomme sans
jamais la contourner — `run_audit()`, `determine_asil()`, `attack_potential()`,
`run_watch()`, `check()`. Les contrats JSON (`/hara/matrix`, `/tara/scales`,
`/8d/rules`) servent les tables du moteur : la page les **lit**, elle ne les
réécrit jamais en JavaScript.

---

## Ce qui est mesuré, et non affirmé

**Détection de défauts (QualityCrew).** Un jeu de documents porte douze défauts
injectés, dont la vérité terrain n'est volontairement pas publiée. Sur sept
exécutions mesurées, **onze des douze défauts sortent à chaque fois, sans
exception** ; le douzième — une exigence conforme qu'il faut penser à citer pour
éclairer sa voisine — sort quatre fois sur sept. Durée : 90 à 200 s selon le run.

**Français contre anglais.** Trois exécutions par langue, avec un barème écrit
*avant* de lire le moindre rapport : moyennes 11,67/12 des deux côtés, **écart
nul**. La variation d'une langue avec elle-même vaut un point ; l'écart entre les
deux vaut zéro. Un écart plus petit que le bruit du procédé ne mesure rien.

**Faux positifs (SentinelScan).** La recherche GitHub par nom de fichier remonte
énormément de bruit — `filename:.env` attrape aussi `.env.example` et
`event.envelope.json`. Un filtre de déclassement fait passer les constats majeurs
de 22 à 3 sur un scan réel, **sans jamais supprimer un constat** : il le déclasse
en donnant son motif, et c'est à l'analyste de qualifier.

---

## Tests

**393 tests, 7 300 lignes**, exécutables sans `pytest` — chaque suite est un
programme autonome.

```bash
for t in tests/test_*.py; do .venv/bin/python3 -B "$t"; done
```

Le drapeau `-B` n'est pas décoratif : CPython valide son cache bytecode sur la
taille du source et sa date **à la seconde près**. Deux versions d'un même fichier
modifiées dans la même seconde sont indistinguables, et les tests se mettent à
mentir — ce qui arrive systématiquement en test de mutation.

**Chaque garde-fou est prouvé par mutation.** Un test qui ne tombe jamais ne prouve
rien : les règles importantes sont cassées volontairement pour vérifier qu'une
suite le voit. Quelques exemples réels, avec leur score après mutation :

| Mutation introduite | Effet |
|---|---|
| Laisser une chaîne de pourquoi s'arrêter sur une personne | 16/20 |
| Accepter un risque sans justification écrite | 9/12 |
| Retirer le durcissement anti-injection de formule Excel | 12/13 |
| Faire traverser l'exposition au pont HARA → TARA | 7/8 |
| Taire une source de veille injoignable | 15/17 |
| Servir l'image de partage française sur une page anglaise | 86/87 |

Une mutation qui ne change pas le comportement ne prouve rien non plus : plusieurs
ont dû être réécrites pour mordre réellement.

⚠️ **Aucun test ne touche le réseau** — ni LLM, ni API GitHub. Les parseurs sont
testés sur des fragments réels capturés et figés, pas sur des exemples inventés :
c'est ce qui a révélé trois défauts qu'aucun cas fabriqué n'aurait montrés.

---

## Sécurité et confidentialité

- **Aucune valeur de secret n'est jamais affichée ni stockée.** SentinelScan ne
  manipule que des métadonnées — dépôt, chemin, URL, criticité. Ses objets n'ont
  volontairement aucun champ de contenu, et le client ne demande jamais à GitHub
  de lui renvoyer les extraits correspondants.
- **Les termes recherchés ne transitent jamais par une URL.** Un mot-clé est
  potentiellement un nom d'entreprise : il ne doit apparaître ni dans les journaux
  du serveur, ni dans l'historique du navigateur, ni dans un en-tête `Referer`.
  D'où un POST qui rend un jeton opaque à usage unique, puis un flux SSE.
- **Injection de formule Excel (CWE-1236).** `openpyxl` écrit toute chaîne
  commençant par `=` comme une **formule**. Or les noms de dépôts GitHub et les
  titres de flux RSS viennent de tiers : il suffit de nommer un dépôt public
  `=HYPERLINK(...)` et d'attendre qu'un scan le remonte. Un utilitaire partagé
  balaie tout classeur juste avant l'écriture et retype les cellules en texte,
  sans altérer le contenu.
- **Les IP ne sont jamais stockées en clair** — seulement une empreinte SHA-256
  tronquée, en mémoire.
- **Aucun secret dans le dépôt** : `.env` est ignoré, `.env.example` versionné sans
  valeurs, et le jeton GitHub demandé est un jeton classic **sans aucun scope**.

---

## Installation locale

Python 3.10+ requis.

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

```bash
cp .env.example .env
```

Renseigner au minimum `GROQ_API_KEY` dans `.env` (palier gratuit suffisant), et
`GITHUB_TOKEN` pour SentinelScan — un jeton **sans aucun scope** : la recherche
publique n'en demande aucun, et si le jeton fuite l'impact est nul.

Lancer le site :

```bash
.venv/bin/uvicorn api.main:app --reload --port 8000
```

Ou en ligne de commande, sans serveur :

```bash
.venv/bin/python3 scripts/run_local.py
```

`scripts/` porte aussi `run_scan_local.py` (avec `--dry-run`),
`run_watch_local.py` (avec `--check-sources`, qui vérifie que les sept sources de
veille répondent encore) et `build_og_image.py`.

---

## Stack

Python 3.10+ · `crewai` · `litellm` · `fastapi` · `uvicorn` · `openpyxl`.
Frontend en HTML/CSS/JavaScript **vanilla** — aucun framework, aucune étape de
build. Le modèle par défaut est `groq/openai/gpt-oss-120b`, configurable via `.env`.

Les parseurs RSS/Atom et HTML de RegWatch n'utilisent que la bibliothèque standard
(`ElementTree`, `html.parser`) : aucune dépendance ajoutée pour cet outil.

---

## Structure du projet

```
src/            les 6 moteurs + 2 utilitaires partagés (i18n, xlsxsafe)
api/            FastAPI — routes, flux SSE, rendu bilingue côté serveur
site/           pages HTML, CSS, JS et images de partage
tests/          19 suites autonomes, exécutables sans pytest
scripts/        points d'entrée CLI
data/           documents d'entrée fictifs
checklists/     checklist ASPICE / ISO 26262 utilisée par l'audit
```

---

## Limites assumées

Ces outils **ne remplacent aucune norme** et ne sont pas des outils certifiés. Ils
implémentent une *méthode*, pas *la* méthode : les barèmes de cotation sont propres
au projet, publiés et documentés dans les exports, précisément pour qu'un résultat
reste relisible six mois plus tard sans l'outil.

Hors périmètre, écarté explicitement : persistance, comptes utilisateurs,
multi-projets, arbres d'attaque graphiques.

---

## Licence

Deux régimes, délimités — le code se réutilise, le contenu éditorial non.

**Le code : licence MIT** (voir [`LICENSE`](LICENSE)).
Couvre `src/`, `api/`, `scripts/`, `tests/`, `checklists/` et les fichiers de
configuration. Réutilisation libre, y compris commerciale, à condition de
conserver la mention de copyright.

**Le contenu : © 2026 Dhafer Bouthelja — tous droits réservés.**
Couvre les textes du site (`site/*.html`, catalogues `src/i18n/`), les images de
partage (`site/og-*.png`), ainsi que le nom et l'identité visuelle. Ces éléments
ne sont pas concédés sous licence MIT : ils ne peuvent être ni republiés, ni
réutilisés, ni adaptés sans autorisation écrite.

**Normes et référentiels.** Ce projet implémente des *logiques de décision*
(tables ASIL, barème de potentiel d'attaque, démarche 8D) sans reproduire le texte
des normes correspondantes. L'ISO 26262, l'ISO/SAE 21434, l'ISO/IEC 27001,
l'ISO 9001 et l'Automotive SPICE restent la propriété de leurs éditeurs, ne sont
pas redistribués ici, et aucun outil ne s'y substitue.

---

**Dhafer Bouthelja** — [qualitycrew.fr](https://qualitycrew.fr)
