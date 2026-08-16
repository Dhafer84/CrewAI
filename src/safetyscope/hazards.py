"""Mots-guides et situations de conduite, matière première de la HARA.

Un événement redouté n'est pas un dysfonctionnement seul : c'est le
croisement d'un dysfonctionnement et d'une situation où il devient
dangereux. Ces deux listes servent à cadrer la proposition de l'IA pour
qu'elle balaie systématiquement, au lieu d'improviser.
"""

# Formulations propres, volontairement génériques.
GUIDE_WORDS = [
    ("Perte de fonction",
     "la fonction ne s'exécute pas alors qu'elle est sollicitée"),
    ("Activation intempestive",
     "la fonction s'exécute sans avoir été sollicitée"),
    ("Amplitude incorrecte",
     "la fonction s'exécute avec une intensité trop forte ou trop faible"),
    ("Décalage temporel",
     "la fonction s'exécute trop tôt ou trop tard"),
    ("Blocage",
     "la fonction reste active alors qu'elle devrait cesser"),
]

DRIVING_SITUATIONS = [
    "Autoroute, vitesse stabilisée, trafic fluide",
    "Descente prolongée, véhicule chargé",
    "Ville, circulation dense, arrêts et redémarrages fréquents",
    "Virage engagé, adhérence réduite",
    "Chaussée mouillée ou verglacée",
    "Manœuvre à basse vitesse, piétons à proximité",
    "Insertion ou dépassement, différentiel de vitesse élevé",
]


def guide_words_block() -> str:
    """Rend les mots-guides sous forme de liste, pour insertion dans un prompt."""
    return "\n".join(f"- {name} : {meaning}" for name, meaning in GUIDE_WORDS)


def situations_block() -> str:
    return "\n".join(f"- {situation}" for situation in DRIVING_SITUATIONS)
