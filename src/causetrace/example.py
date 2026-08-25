"""Le 8D d'exemple — **volontairement médiocre**, et c'est le parti pris.

Un exemple parfait ne démontre rien : le visiteur le charge, tout est vert,
et l'outil n'a rien dit. Celui-ci est le 8D qu'on reçoit vraiment d'un
fournisseur — plausible, bien rempli en apparence, **et déclaré clos**.

Ce qu'il fait dire au moteur, et pourquoi chaque défaut est là :

| Défaut de l'exemple | Ce qu'il enseigne |
|---|---|
| D3 sans date de fin ni contrôle d'efficacité | Une action immédiate qui ne se referme jamais |
| **Cause de non-détection absente** | Le trou n° 1 des 8D réels |
| **Chaîne qui s'arrête sur l'opérateur** | Le défaut vedette : un symptôme pris pour une cause |
| D5 et D6 verrouillés en cascade | Corriger avant d'avoir établi la cause |
| D7 : « sensibilisation » mais aucun document mis à jour | Soigner un cas, laisser le système identique |
| **Clôture prétendue** | Le constat le plus grave : « résolu » sans l'être |

Il démontre aussi, en creux, une règle du moteur : la cause de non-détection
étant absente, **sa chaîne n'est pas réclamée en plus** — on ne dit pas deux
fois la même chose.

⚠️ **Ce que le moteur ne peut PAS reprocher à cet exemple**, et qui est tout
aussi mauvais : « Plusieurs pièces » n'est pas une quantité, « Depuis fin
mai » n'est pas une date, et « Pas d'autre défaut signalé » ne dit rien de ce
qui n'est pas touché. Ces champs sont **remplis**, donc conformes. C'est
exactement la matière de l'étape 5 — l'IA réclame ce que la structure ne peut
pas exiger. L'exemple est calibré pour qu'il reste quelque chose à trouver.

⚠️ Références, dates et noms propres ne sont **pas traduits** : ce sont des
identifiants, pas des libellés. Même règle que « ISO 26262 » ou « HARA »,
qu'on n'annote pas non plus.
"""

from i18n import DEFAULT_LANG, t


def mediocre_example(lang: str = DEFAULT_LANG) -> dict:
    """Charge utile d'un 8D réaliste et fautif, prête pour `build_dossier`."""
    return {
        "reference": "8D-2026-014",
        "title": t("ct.example.title", lang),
        "d1": {
            "owner": "A. Mercier",
            "members": [t("ct.example.member.1", lang), t("ct.example.member.2", lang)],
        },
        "d2": {
            "what": t("ct.example.what", lang),
            "where": t("ct.example.where", lang),
            "since": t("ct.example.since", lang),
            "how_many": t("ct.example.how_many", lang),
            "is_not": t("ct.example.is_not", lang),
        },
        # Une action de tri, sans date de fin ni preuve qu'elle a marché.
        "d3": {"action": t("ct.example.containment", lang)},
        "d4": {
            "occurrence": t("ct.example.occurrence", lang),
            # ⚠️ Absente, comme dans la plupart des 8D reçus.
            "escape": "",
            "occurrence_chain": [
                {"statement": t("ct.example.why.1", lang), "nature": "technical"},
                {"statement": t("ct.example.why.2", lang), "nature": "technical"},
                # ⚠️ Le défaut vedette : la chaîne s'arrête sur une personne.
                {"statement": t("ct.example.why.3", lang), "nature": "person"},
            ],
        },
        "d5": {},
        "d6": {},
        # Une « sensibilisation » n'est pas une mise à jour de référentiel.
        "d7": {"lessons": t("ct.example.lessons", lang)},
        # ⚠️ Et pourtant, le fournisseur le déclare clos.
        "d8": {"claimed_closed": True, "closed_on": "2026-06-20"},
    }
