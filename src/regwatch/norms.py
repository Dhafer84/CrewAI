"""Les cinq normes surveillées, et ce qui permet de les reconnaître.

Ce module décrit **ce qu'on cherche**, jamais **où on le cherche** — les
sources vivent dans `sources.py`. Ajouter une sixième norme se fait ici, et
nulle part ailleurs.

**Un seul signal de rattachement : le marqueur.** Il est cherché dans le
titre de l'item et dans les libellés que la source lui attache elle-même —
catégories d'un flux, champ « Relevant to » d'un document réglementaire.

⚠️ **Une catégorie rattache quand elle contient un marqueur, jamais parce
qu'elle nomme un thème.** Cette règle est **mesurée, pas supposée** : sur
14 items réels rangés par leur propre auteur dans la catégorie
« Functional Safety », **2 seulement** concernaient l'ISO 26262 ; les douze
autres traitaient de l'ISO/PAS 8800, de robots humanoïdes ou d'opinion.
« Functional Safety » ne contient aucun marqueur — elle ne rattache donc
rien, et c'est voulu.

Les deux contre-épreuves, réelles elles aussi :
- « ISO27k standards » contient le marqueur `iso27k` : elle rattrape
  « Updated ISO/IEC Directives », qui ne cite aucun numéro dans son titre.
- « UN Regulation No. 155 | Cyber security » contient `regulation no. 155` :
  c'est GlobalAutoRegs lui-même qui dit à quel règlement un document se
  rattache, personne n'a à le deviner.

C'est pourquoi il n'y a **pas** de champ « catégories » ici : il ferait
double emploi avec les marqueurs, et deux mécanismes de rattachement
donneraient deux endroits où se tromper.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Norm:
    """Une norme surveillée.

    `key` est l'identifiant stable : il circule jusque dans les cases à
    cocher de la page et dans les exports. Le renommer casse les deux.
    """

    key: str
    label: str
    markers: tuple[str, ...]


class InvalidSelection(ValueError):
    """Sélection de normes inexploitable, refusée avant tout appel réseau."""


# ⚠️ « spice » seul n'est PAS un marqueur : c'est aussi le simulateur de
# circuits électroniques, et la moitié de l'électronique embarquée en parle.
# Les expressions retenues sont celles qui ne désignent que le référentiel.
_ASPICE = Norm(
    key="aspice",
    label="Automotive SPICE",
    markers=(
        "automotive spice", "aspice", "intacs", "ascon", "gate4spice",
        "spice conference", "spice network", "spice center",
        "process assessment model", "pam 4",
        "provisional assessor", "competent assessor", "principal assessor",
        "iso/iec 33020", "iso/iec 15504",
    ),
)

_ISO_26262 = Norm(
    key="iso26262",
    label="ISO 26262",
    # « 26262 » et « iso26262 » sont deux marqueurs distincts : sans espace,
    # il n'y a pas de frontière de mot entre « iso » et « 26262 ».
    markers=(
        "iso 26262", "iso26262", "26262",
        "asil", "hara", "fusa",
        "safety element out of context", "seooc",
    ),
)

_ISO_21434 = Norm(
    key="iso21434",
    label="ISO/SAE 21434 et UN R155/R156",
    markers=(
        "iso/sae 21434", "iso 21434", "21434",
        "r155", "r156",
        # ⚠️ PAS « wp.29 » ni « grva » : ce sont les noms du forum et du
        # groupe de travail de l'ONU, pas de la norme. GlobalAutoRegs
        # étiquette « WP.29 Discussion Topic | … » TOUS ses documents —
        # éclairage, pneus, enfants oubliés en voiture. Mesuré le
        # 24/08/2026 : avec « wp.29 », la veille cybersécurité remontait
        # 7 documents dont AUCUN ne parlait de cybersécurité. C'est la
        # même erreur que « Functional Safety » — un thème, pas un
        # marqueur — et je l'avais reproduite ici.
        "csms", "cybersecurity management system",
        "software update management system", "sumd",
        "tara", "vehicle cybersecurity", "automotive cybersecurity",
        # GlobalAutoRegs écrit ses rattachements « UN Regulation No. 155 | … ».
        # Les deux graphies existent dans la nature, avec et sans point.
        "regulation no. 155", "regulation no 155",
        "regulation no. 156", "regulation no 156",
    ),
)

_ISO_27001 = Norm(
    key="iso27001",
    label="ISO/IEC 27001",
    # La famille ISO27k entière compte pour qui surveille l'ISO 27001 :
    # une révision de l'ISO/IEC 27002 ou 27017 change l'annexe A ou les
    # mesures qu'on lui rattache.
    markers=(
        "iso/iec 27001", "iso 27001", "27001",
        "27000", "27002", "27005", "27017", "27090",
        "iso27k", "isms", "information security management system",
    ),
)

_ISO_9001 = Norm(
    key="iso9001",
    label="ISO 9001",
    # Comme pour l'ISO27k : la famille du TC 176 compte pour qui surveille
    # l'ISO 9001. Le sous-comité SC 2 publie ses avancées sur l'ISO 9002 et
    # l'ISO 9004 sur la même page que celles de l'ISO 9001.
    markers=(
        "iso 9001", "9001", "9002", "9004",
        "iso/tc 176", "tc 176", "tc176",
        "quality management system", "qms", "iso 19011",
    ),
)

# L'ordre du catalogue est l'ordre d'affichage et l'ordre de restitution.
NORMS: dict[str, Norm] = {
    norm.key: norm
    for norm in (_ASPICE, _ISO_26262, _ISO_21434, _ISO_27001, _ISO_9001)
}

NORM_ORDER: tuple[str, ...] = tuple(NORMS)


def parse_selection(keys: list[str]) -> list[Norm]:
    """Valide les normes cochées et les rend dans l'ordre du catalogue.

    Une clé inconnue est **refusée**, pas ignorée : la sélection vient d'un
    jeu fermé de cases à cocher, donc une clé hors catalogue signale une
    requête trafiquée ou un frontend désynchronisé — deux cas où continuer
    en silence produirait une veille partielle que personne ne remarquerait.

    L'ordre du catalogue l'emporte sur l'ordre de saisie : deux visiteurs
    qui cochent les mêmes normes obtiennent le même rapport.

    Raises:
        InvalidSelection: clé inconnue, ou aucune norme retenue.
    """
    retained: set[str] = set()

    for raw in keys or []:
        key = (raw or "").strip().lower()
        if not key:
            continue
        if key not in NORMS:
            raise InvalidSelection(f"« {raw} » n'est pas une norme surveillée.")
        retained.add(key)

    if not retained:
        raise InvalidSelection("Cochez au moins une norme à surveiller.")

    return [NORMS[key] for key in NORM_ORDER if key in retained]
