"""Réglages de RegWatch — fenêtre de veille, plafonds, politesse réseau.

⚠️ **Aucun secret ici, et c'est un fait notable** : RegWatch n'appelle aucune
API authentifiée. Pas de jeton comme SentinelScan, pas de clé LLM pour
produire son résultat. Il lit des pages publiques, c'est tout. La phrase
« pourquoi ça compte » de l'étape 5 sera la seule chose à dépendre d'une clé,
et elle est optionnelle par construction.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# ⚠️ Fenêtre de veille FIXE, arbitrée le 24/08/2026. Il n'existe aucun repère
# de dernière visite — ni côté serveur (pas d'état), ni côté navigateur
# (écarté explicitement). L'écran doit donc dire « ce qui a bougé sur 90
# jours » et **jamais** « depuis votre dernière visite » : la seconde
# formulation serait un mensonge d'interface.
LOOKBACK_DAYS = int(os.getenv("REGWATCH_LOOKBACK_DAYS", "90"))

HTTP_TIMEOUT_SECONDS = float(os.getenv("REGWATCH_HTTP_TIMEOUT", "20"))

# Garde-fou de lecture, pas un réglage : la source la plus lourde (la page
# d'un comité ISO) fait 400 Ko. Une réponse de 3 Mo signale autre chose
# qu'une page d'actualités.
MAX_RESPONSE_BYTES = int(os.getenv("REGWATCH_MAX_RESPONSE_BYTES", str(3 * 1024 * 1024)))

# Politesse : jamais deux requêtes coup sur coup. Le site public tire depuis
# UNE seule IP de datacenter — c'est exactement comme ça qu'on se fait
# blacklister par un hébergeur qui voit passer huit requêtes en une seconde.
REQUEST_DELAY_SECONDS = float(os.getenv("REGWATCH_REQUEST_DELAY", "1.0"))

# Cache mémoire. Protège les sources quand plusieurs visiteurs enchaînent la
# démo : la deuxième veille de la demi-heure ne touche pas le réseau.
CACHE_TTL_SECONDS = float(os.getenv("REGWATCH_CACHE_TTL", "1800"))

# En deçà de ce volume, une page sans item est probablement vide pour de
# vrai. Au-delà, zéro item extrait est le symptôme d'un parseur cassé.
# ⚠️ L'asymétrie est voulue : un faux « source dégradée » est un
# avertissement visible et vérifiable, un faux « rien de neuf » est un
# mensonge silencieux. On préfère largement le premier.
DEGRADED_MIN_BODY_BYTES = int(os.getenv("REGWATCH_DEGRADED_MIN_BODY", "2000"))

# ⚠️ Un User-Agent qui dit la vérité, avec un lien pour nous joindre.
# RegWatch lit des pages publiques, ne recopie aucun contenu et lie toujours
# vers la source : autant que l'administrateur du site puisse le vérifier.
# Se faire passer pour un navigateur serait le premier pas vers le
# contournement d'un anti-bot — ce qui est exclu (voir fetch.py).
#
# ⚠️⚠️ **ASCII PUR, ET CE N'EST PAS UN DÉTAIL DE STYLE.** La première version
# disait « veille normative, démonstration » : l'accent de « démonstration »
# a fait répondre **HTTP 403** à committee.iso.org, et à lui seul. Les
# valeurs d'en-tête HTTP sont ASCII par spécification ; `requests` les encode
# en latin-1, et un pare-feu applicatif rejette l'octet non-ASCII.
#
# Le piège n'est pas la panne, c'est le **diagnostic** : deux sources sur
# sept refusaient l'accès, exactement là où l'on savait déjà que ISO.org
# bloque les robots. La conclusion évidente — « ISO nous bloque aussi » —
# était fausse, et aurait coûté la seule source OFFICIELLE de l'ISO 9001.
# Un test verrouille désormais la contrainte.
USER_AGENT = os.getenv(
    "REGWATCH_USER_AGENT",
    "RegWatch/1.0 (+https://qualitycrew.fr/regwatch; standards watch demo)",
)
