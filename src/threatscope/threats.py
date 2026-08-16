"""Mots-guides STRIDE et surfaces d'attaque, matière première de la TARA.

Un scénario de menace n'est pas une inquiétude vague : c'est une **propriété
de sécurité attaquée** sur un actif précis, par un chemin décrit. Ces listes
servent à cadrer la proposition de l'IA pour qu'elle balaie systématiquement
au lieu d'improviser — même rôle que les mots-guides d'une HARA.

STRIDE est une méthode publique de modélisation de menaces (Microsoft), pas
un référentiel sous licence : les catégories peuvent être nommées. Les
descriptions ci-dessous sont des formulations propres.
"""

# Les six catégories STRIDE, décrites pour le contexte véhicule.
GUIDE_WORDS = [
    ("Usurpation d'identité",
     "un composant ou un interlocuteur se fait passer pour un autre"),
    ("Altération",
     "une donnée ou un logiciel est modifié sans autorisation"),
    ("Répudiation",
     "une action est menée sans qu'on puisse ensuite prouver qui l'a faite"),
    ("Divulgation d'information",
     "une donnée censée rester confidentielle devient lisible"),
    ("Déni de service",
     "une fonction devient indisponible au moment où elle est nécessaire"),
    ("Élévation de privilèges",
     "un accès limité permet d'obtenir des droits qui ne devaient pas l'être"),
]

# Surfaces d'attaque typiques d'un véhicule. Volontairement génériques.
ATTACK_SURFACES = [
    "Port de diagnostic embarqué, accessible dans l'habitacle",
    "Interface radio courte portée : clé, badge, télédéverrouillage",
    "Interface cellulaire de la passerelle télématique",
    "Appairage sans fil d'un terminal personnel",
    "Bus de communication interne entre calculateurs",
    "Chaîne de mise à jour logicielle embarquée",
    "Stockage de données embarquées, y compris après revente du véhicule",
    "Capteurs exposés à un signal falsifié depuis l'extérieur",
    "Chaîne d'approvisionnement d'un composant fourni",
]


def guide_words_block() -> str:
    """Rend les mots-guides sous forme de liste, pour insertion dans un prompt."""
    return "\n".join(f"- {name} : {meaning}" for name, meaning in GUIDE_WORDS)


def surfaces_block() -> str:
    return "\n".join(f"- {surface}" for surface in ATTACK_SURFACES)
