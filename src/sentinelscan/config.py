"""Configuration et secrets de SentinelScan.

Le jeton GitHub transite uniquement par le .env local (jamais committé).

Le jeton doit être créé SANS AUCUN SCOPE : la recherche publique n'en demande
aucun, et un jeton sans scope qui fuite n'a aucun impact. Ne jamais utiliser
ici un jeton disposant d'accès à des dépôts privés — le périmètre « ce qui est
visible par n'importe qui sur Internet » est ce qui rend la démarche défendable.
"""

import os

from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# Garde-fous — surchargeables par .env
MAX_KEYWORDS = int(os.getenv("SENTINELSCAN_MAX_KEYWORDS", "3"))
MIN_KEYWORD_LENGTH = int(os.getenv("SENTINELSCAN_MIN_KEYWORD_LENGTH", "3"))
RESULTS_PER_QUERY = int(os.getenv("SENTINELSCAN_RESULTS_PER_QUERY", "20"))

# L'API GitHub code search est plafonnée à 10 requêtes/minute (authentifié).
# On espace donc les appels d'un peu plus de 6 s.
CODE_SEARCH_DELAY_SECONDS = float(os.getenv("SENTINELSCAN_CODE_DELAY", "6.5"))

GITHUB_API_BASE = "https://api.github.com"


def require_github_token() -> None:
    """Vérifie que le jeton GitHub est configuré.

    GitHub refuse les requêtes anonymes sur son API de recherche de code :
    sans jeton, l'outil n'a aucune valeur.
    """
    if not GITHUB_TOKEN:
        raise RuntimeError(
            "GITHUB_TOKEN absent. Créer un jeton GitHub classic SANS AUCUN SCOPE "
            "(https://github.com/settings/tokens) et le renseigner dans le .env. "
            "Aucune permission n'est nécessaire pour la recherche publique."
        )
