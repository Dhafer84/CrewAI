#!/bin/bash
# Met à jour qualitycrew.fr sur le VPS avec la dernière version de main.
#   ssh -t nexora-ovh '~/qualitycrew/deploy/update.sh'
#
# Les tests passent AVANT le redémarrage : s'ils échouent, le code revient au
# commit d'avant et l'ancienne version continue de tourner.
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$APP_DIR"

if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "❌ Des fichiers suivis ont été modifiés sur le VPS : rien n'est touché."
  git status --short --untracked-files=no
  exit 1
fi

avant=$(git rev-parse HEAD)
echo "📥 Récupération de la dernière version…"
git pull --ff-only --quiet
apres=$(git rev-parse HEAD)
if [ "$avant" = "$apres" ]; then
  echo "✅ Déjà à jour ($(git log --oneline -1))."
  exit 0
fi
git log --oneline "$avant..$apres"

if ! git diff --quiet "$avant" "$apres" -- requirements.txt; then
  echo "📦 requirements.txt a changé : installation des dépendances…"
  .venv/bin/pip install -q -r requirements.txt
fi

echo "🧪 Tests…"
for t in tests/test_*.py; do
  if ! .venv/bin/python3 -B "$t" > /tmp/qualitycrew-test.log 2>&1; then
    echo "❌ $t échoue : retour au commit ${avant:0:7}, le site n'est pas redémarré."
    tail -20 /tmp/qualitycrew-test.log
    git reset --hard --quiet "$avant"
    exit 1
  fi
done

echo "🔄 Redémarrage du service…"
sudo systemctl restart qualitycrew
sleep 3

echo "🩺 Contrôle de santé…"
code=$(curl -s -o /dev/null -m 15 -w '%{http_code}' http://127.0.0.1:8000/ || true)
if [ "$code" = 200 ]; then
  echo "✅ À jour sur $(git log --oneline -1), le site répond (HTTP 200)."
else
  echo "❌ Le site ne répond pas (HTTP $code) : journalctl -u qualitycrew -n 50"
  echo "   Revenir en arrière : git -C $APP_DIR reset --hard ${avant:0:7} && sudo systemctl restart qualitycrew"
  exit 1
fi
