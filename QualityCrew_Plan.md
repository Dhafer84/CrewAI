# QualityCrew — Plan de projet

**Système multi-agents pour l'audit automatisé de conformité ASPICE / ISO 26262**
Projet personnel de démonstration technique.

---

## 1. Objectif et périmètre

Construire une petite équipe d'agents CrewAI qui analyse un jeu de documents projet (exigences, plan de test, rapport de revue) et produit un rapport de conformité structuré, comme le ferait une revue qualité de première passe.

Le livrable public est un **site vitrine** (Option A) présentant le projet, son architecture et un rapport d'exemple généré en local. L'architecture est conçue dès le départ pour permettre, plus tard, une **démo interactive live** (Option B) sans réécriture.

Contraintes fixées :
- Projet strictement personnel, aucun lien avec un employeur, aucune donnée réelle d'entreprise.
- Jeu de documents 100% fictif (module logiciel embarqué inventé).
- Sécurité et cybersécurité intégrées dès la conception, pas ajoutées après coup.

---

## 2. Principe d'architecture : découplage moteur / présentation

La décision structurante est de séparer trois couches nettes :

1. **Le moteur (core)** — la logique CrewAI pure, exposée derrière une interface simple : une fonction `run_audit(documents) -> rapport`. Elle ne sait rien du web, du CLI ou d'une API. Elle prend des documents en entrée, rend un rapport en sortie.
2. **Les points d'entrée (entrypoints)** — des enveloppes minces autour du moteur :
   - Pour l'Option A : un script CLI local qui lit les documents et écrit le rapport sur disque.
   - Pour l'Option B (plus tard) : un backend FastAPI qui appelle la *même* fonction `run_audit`.
3. **La présentation** — le site statique (Option A) ou le frontend interactif (Option B).

Conséquence : le passage A → B consiste à ajouter un dossier `api/` et un frontend, sans toucher au moteur. C'est le point clé à respecter tout au long du dev.

---

## 3. Stack technique

### Couche moteur (commune A et B)
- Python 3.10+
- `crewai` + `crewai-tools`
- LLM via clé API : Groq (free tier) pour prototyper, option Claude/OpenAI pour la version finale plus soignée
- `python-dotenv` pour les secrets
- `python-docx` / `pypdf` seulement si les documents fictifs sont en .docx/.pdf ; sinon documents en `.md` (recommandé pour la v1, plus simple à versionner)

### Option A — site vitrine
- Site statique : HTML/CSS simple, ou générateur statique léger (Astro / Hugo) si tu veux du confort
- Nginx sur le VPS OVH pour servir les fichiers
- Certbot (Let's Encrypt) pour HTTPS gratuit

### Option B — démo live (anticipée, pas construite en v1)
- FastAPI + Uvicorn/Gunicorn comme serveur d'application
- Nginx en reverse proxy devant FastAPI
- Docker (optionnel) pour isoler l'exécution
- Frontend léger (HTML/JS ou petit React) affichant progression + rapport

### Outillage transverse
- Git + GitHub (privé pendant le dev, public au moment de publier)
- Diagramme d'architecture en Mermaid dans le README

---

## 4. Structure de dossiers

```
qualitycrew/
├── .env.example            # modèle de variables, SANS valeurs réelles
├── .gitignore              # exclut .env, caches, rapports générés
├── README.md               # doc + diagramme d'architecture
├── requirements.txt
├── src/
│   └── qualitycrew/
│       ├── __init__.py
│       ├── config.py       # chargement des clés via dotenv
│       ├── agents.py       # définition des 4 agents
│       ├── tasks.py        # définition des tâches
│       ├── crew.py         # assemblage du crew
│       └── core.py         # run_audit() — interface propre et stable
├── data/
│   └── sample_project/     # documents fictifs
│       ├── srs.md
│       ├── test_plan.md
│       └── review_report.md
├── checklists/
│   └── aspice_swe_checklist.md
├── reports/                # sorties générées (gitignored, sauf 1 exemple gardé)
├── scripts/
│   └── run_local.py        # point d'entrée CLI — Option A
├── site/                   # site vitrine statique — Option A
│   ├── index.html
│   ├── style.css
│   └── assets/             # captures d'écran du rapport
├── api/                    # Option B (vide en v1, réservé)
│   └── .gitkeep
├── deploy/
│   ├── nginx-static.conf   # conf Nginx site statique
│   └── notes.md            # procédure de déploiement
└── tests/
```

---

## 5. Les 4 agents (rappel de conception)

| Agent | Rôle | Sortie attendue |
|-------|------|-----------------|
| Analyste d'exigences | Vérifie traçabilité et complétude des exigences vs template ASPICE | Liste des exigences non tracées / incomplètes |
| Vérificateur de conformité | Croise le contenu avec une checklist ciblée (SWE.1/SWE.2 + clauses ISO 26262 Part 6) | Écarts par rapport à la checklist |
| Détecteur de risques | Repère incohérences, exigences non testées, ambiguïtés | Liste de risques avec justification |
| Rédacteur de synthèse | Compile tout en rapport structuré + recommandations priorisées | Rapport final (tableau sévérité / réf. exigence / reco) |

Process **séquentiel** pour la v1 (chaque agent enrichit le contexte du suivant). Checklist volontairement ciblée sur un sous-ensemble ASPICE/ISO plutôt que « tout le référentiel » — plus crédible et défendable.

---

## 6. Sécurité et cybersécurité

### 6.1 Gestion des secrets (critique, dès le premier commit)
- Clé API **jamais** dans le code ni commitée, même en repo privé (elle resterait dans l'historique Git au moment du passage en public).
- `.env` local pour les clés + `.env.example` versionné sans valeurs.
- `.gitignore` incluant `.env` **dès le commit initial**.
- Vérifier avec un outil comme `git-secrets` ou `gitleaks` avant de rendre le repo public, pour scanner l'historique.
- Sur la console du fournisseur LLM : plafonner le budget / activer une limite de dépense, même en dev.

### 6.2 Données fictives
- Les documents d'entrée doivent être authentiquement inventés, pas des exports réels « anonymisés à la va-vite » où subsisteraient des traces (noms, références, métadonnées de fichier).
- Vérifier les métadonnées des fichiers (auteur, propriétés) avant publication.

### 6.3 Dépendances
- Épingler les versions dans `requirements.txt`.
- Activer Dependabot (GitHub) ou lancer `pip-audit` régulièrement pour repérer les vulnérabilités connues.

### 6.4 Durcissement du VPS OVH
- Authentification SSH par **clé** uniquement, désactiver l'auth par mot de passe.
- Désactiver le login root direct (`PermitRootLogin no`), passer par un utilisateur non-privilégié + sudo.
- Changer le port SSH par défaut (mesure d'hygiène, pas une protection en soi).
- Pare-feu UFW : n'ouvrir que 22 (ou ton port SSH), 80 et 443. Tout le reste fermé.
- `fail2ban` pour bloquer les tentatives de brute-force SSH.
- `unattended-upgrades` pour les mises à jour de sécurité automatiques du système.

### 6.5 HTTPS et Nginx (site statique — Option A)
- Certificat Let's Encrypt via Certbot, renouvellement automatique.
- Rediriger tout le trafic HTTP → HTTPS.
- En-têtes de sécurité dans la conf Nginx :
  - `Strict-Transport-Security` (HSTS)
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Content-Security-Policy` adaptée au site
  - `Referrer-Policy`
- Masquer la version de Nginx (`server_tokens off`).
- Pour un site purement statique, la surface d'attaque est minime : c'est le bon point de départ.

### 6.6 Risques spécifiques à l'Option B (à traiter AVANT de l'activer)
Le fait qu'un inconnu puisse déclencher des appels LLM change complètement le profil de risque :
- **Abus de clé API / coût** : rate limiting strict, quota journalier global, plafond de dépense côté fournisseur. Sans ça, ta clé peut être exploitée pour générer une facture.
- **Validation des entrées** : si le visiteur peut soumettre du texte, limiter la taille, filtrer, et ne jamais exécuter ce contenu — juste le passer au LLM comme donnée.
- **Prompt injection** : le texte soumis pourrait tenter de détourner les agents. Traiter tout contenu externe comme non fiable ; ne pas lui laisser déclencher d'actions à effet de bord.
- **Abus automatisé** : CAPTCHA ou challenge léger + rate limiting par IP.
- **Isolation** : faire tourner le backend sous un utilisateur dédié à droits minimaux, idéalement dans un conteneur Docker.
- **CORS** restreint au domaine du site.
- Ne jamais exposer de messages d'erreur techniques détaillés au visiteur.

Tant que ces points ne sont pas en place, rester sur l'Option A. La démo live est optionnelle et vient après une v1 stable.

---

## 7. Plan d'exécution par phases

### Phase 0 — Fondations propres (avant tout code métier)
- Init du repo **privé** avec `.gitignore` + `.env.example` dès le premier commit.
- Structure de dossiers en place.
- `requirements.txt` avec versions épinglées.

### Phase 1 — Jeu de documents fictif
- Inventer un module embarqué simple et cohérent (ex. gestion de niveau de batterie, ou contrôle de capteur).
- SRS de 15-20 exigences, avec **3-4 défauts injectés volontairement** (ambiguë, non testable, non tracée) — dont tu gardes la liste au secret pour mesurer le taux de détection.
- Plan de test partiel (ne couvrant pas toutes les exigences, exprès).
- Rapport de revue avec quelques commentaires.
- Checklist ASPICE/ISO ciblée.

### Phase 2 — Moteur du crew (core)
- Définir les 4 agents et leurs tâches.
- Assembler le crew en process séquentiel.
- Exposer `run_audit()` comme interface propre et stable.
- Faire produire un rapport en markdown lisible (tableau sévérité / réf. / reco), qui rend bien en capture d'écran.

### Phase 3 — Point d'entrée local (Option A)
- Script CLI `run_local.py` : lit `data/sample_project/`, appelle `run_audit()`, écrit le rapport dans `reports/`.
- Mesurer le temps du crew vs une revue manuelle que tu chronomètres toi-même sur le même jeu.
- Calculer le vrai taux de détection (défauts trouvés / défauts injectés).

### Phase 4 — Site vitrine (Option A)
- Page(s) statique(s) : présentation, architecture (Mermaid), stack, captures d'écran du rapport, chiffres mesurés, lien GitHub.
- Rédiger le README technique.

### Phase 5 — Déploiement sécurisé sur OVH
- Durcissement VPS (section 6.4).
- Nginx + Certbot + en-têtes de sécurité (section 6.5).
- Mise en ligne sur ton nom de domaine.
- Passage du repo GitHub en **public** une fois tout propre (scan gitleaks au préalable).

### Phase 6 (optionnelle, plus tard) — Démo live (Option B)
- Ajouter `api/main.py` (FastAPI) appelant `run_audit()`.
- Frontend minimal.
- Mettre en place TOUTES les protections de la section 6.6 avant ouverture au public.

---

## 8. Chiffres de démonstration (approche honnête)

Plutôt qu'un chiffre extrapolé, mesurer réellement sur ton propre jeu de test :
- Temps de ta revue manuelle du dossier fictif (chronométré).
- Temps du crew.
- Taux de détection = défauts injectés retrouvés / défauts injectés.

Formuler les résultats comme « sur mon jeu de test » — mesurable, reproductible, défendable si un pair te challenge.

---

## 9. Ce qu'il ne faut pas faire

- Committer la clé API (même une fois, même en privé).
- Utiliser de vraies données projet.
- Prétendre couvrir l'intégralité d'ASPICE / ISO 26262 (cibler un sous-ensemble).
- Ouvrir une démo live au public sans rate limiting ni plafond de dépense.
- Exposer des erreurs techniques détaillées côté visiteur.
