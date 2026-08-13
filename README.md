# QualityCrew

Système multi-agents (CrewAI) pour l'audit automatisé de conformité
ASPICE / ISO 26262 sur un jeu de documents fictif.

Projet personnel de démonstration technique — aucune donnée réelle
d'entreprise, aucun lien avec un employeur.

> Statut : en construction (Phase 0 — fondations). Ce README sera
> complété au fil des phases (architecture, stack, captures d'écran,
> chiffres mesurés).

## Structure du projet

```
qualitycrew/
├── src/qualitycrew/     # moteur — voir core.py pour l'interface stable
├── data/sample_project/ # documents fictifs (Phase 1)
├── checklists/          # checklist ASPICE/ISO ciblée (Phase 1)
├── scripts/run_local.py # point d'entrée CLI (Phase 3)
├── site/                 # site vitrine statique (Phase 4)
├── api/                  # réservé Option B, vide pour l'instant
└── deploy/               # conf Nginx + notes de déploiement (Phase 5)
```

## Setup local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# éditer .env et renseigner au moins GROQ_API_KEY
```

## Sécurité

- Aucun secret n'est committé : voir `.gitignore` et `.env.example`.
- Le repo reste privé pendant le développement, passage en public
  seulement après vérification (scan des secrets, données bien
  fictives) — voir le plan de projet.
