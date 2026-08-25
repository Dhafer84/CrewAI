"""Catalogue français — **source de vérité**.

Toute clé naît ici. `en.py` s'aligne, jamais l'inverse : un test refuse une
clé anglaise qui n'aurait pas d'équivalent français.

⚠️ Les valeurs doivent reproduire **exactement** le texte des pages, espaces
et ponctuation compris. `test_the_pages_match_their_catalogue` compare les
deux caractère par caractère — c'est ce qui garantit que l'extraction n'a
rien changé à l'écran.
"""

CATALOGUE: dict[str, str] = {
    # --- Navigation, partagée par les six pages ---------------------------
    "nav.back": "Tous les outils",
    "nav.github": "GitHub",
    "nav.source": "Code source",

    # --- Pieds de page ----------------------------------------------------
    "footer.tools": "Tous les outils",
    "footer.index": "Projets de démonstration · données 100 % fictives",
    "footer.qualitycrew": "QualityCrew — projet démo · documents 100% fictifs",
    "footer.sentinelscan":
        "OSINT passif · sources publiques · les termes ne transitent jamais par une URL",
    "footer.hara":
        "SafetyScope · démonstration pédagogique, ne remplace pas la norme",
    "footer.tara":
        "ThreatScope · démonstration pédagogique, ne remplace pas la norme",
    "footer.regwatch":
        "Veille à la demande · sources publiques · le contenu des normes "
        "n'est jamais republié",
    # --- SafetyScope — échelles S / E / C ---
    "hara.severity.0": "Aucune blessure",
    "hara.severity.1": "Blessures légères à modérées",
    "hara.severity.2": "Blessures graves, survie probable",
    "hara.severity.3": "Blessures critiques ou mortelles",
    "hara.exposure.0": "Situation invraisemblable",
    "hara.exposure.1": "Très faible probabilité",
    "hara.exposure.2": "Faible probabilité",
    "hara.exposure.3": "Probabilité moyenne",
    "hara.exposure.4": "Forte probabilité",
    "hara.controllability.0": "Maîtrisable de façon générale",
    "hara.controllability.1": "Simplement maîtrisable",
    "hara.controllability.2": "Normalement maîtrisable",
    "hara.controllability.3": "Difficilement maîtrisable, voire pas du tout",
    # --- ThreatScope — barème de potentiel d'attaque et impact ---
    "tara.param.time": "Temps nécessaire",
    "tara.param.expertise": "Expertise requise",
    "tara.param.knowledge": "Connaissance de l'item",
    "tara.param.window": "Fenêtre d'opportunité",
    "tara.param.equipment": "Équipement",
    "tara.time.0": "Moins d'une journée",
    "tara.time.1": "Moins d'une semaine",
    "tara.time.2": "Moins d'un mois",
    "tara.time.3": "Moins de six mois",
    "tara.time.4": "Plus de six mois",
    "tara.expertise.0": "Profane",
    "tara.expertise.1": "Compétent",
    "tara.expertise.2": "Expert",
    "tara.expertise.3": "Plusieurs experts de domaines différents",
    "tara.knowledge.0": "Publique",
    "tara.knowledge.1": "Restreinte",
    "tara.knowledge.2": "Confidentielle",
    "tara.knowledge.3": "Strictement confidentielle",
    "tara.window.0": "Illimitée",
    "tara.window.1": "Facile à obtenir",
    "tara.window.2": "Modérée",
    "tara.window.3": "Difficile à obtenir",
    "tara.equipment.0": "Standard",
    "tara.equipment.1": "Spécialisé",
    "tara.equipment.2": "Sur mesure",
    "tara.equipment.3": "Plusieurs équipements sur mesure",
    "tara.feasibility.0": "Très faible",
    "tara.feasibility.1": "Faible",
    "tara.feasibility.2": "Moyenne",
    "tara.feasibility.3": "Élevée",
    "tara.impact.0": "Négligeable",
    "tara.impact.1": "Modéré",
    "tara.impact.2": "Majeur",
    "tara.impact.3": "Sévère",
    "tara.category.safety": "Sécurité des personnes",
    "tara.category.financial": "Financier",
    "tara.category.operational": "Opérationnel",
    "tara.category.privacy": "Vie privée",
    # --- ThreatScope — traitement du risque et pont HARA ---
    "tara.treatment.avoid.label": "Éviter le risque",
    "tara.treatment.avoid.hint":
        "Supprimer la source du risque : retirer la fonction, l'interface ou le flux concerné.",
    "tara.treatment.avoid.prompt": "Ce qui est retiré ou remplacé",
    "tara.treatment.reduce.label": "Réduire le risque",
    "tara.treatment.reduce.hint":
        "Ramener le risque à un niveau acceptable par des mesures de cybersécurité. C'est le cas qui produit une exigence.",
    "tara.treatment.reduce.prompt": "Objectif de cybersécurité",
    "tara.treatment.share.label": "Partager le risque",
    "tara.treatment.share.hint":
        "Transférer tout ou partie du risque à un tiers — fournisseur, contrat, assurance.",
    "tara.treatment.share.prompt": "À qui, et sur quelle base",
    "tara.treatment.retain.label": "Accepter le risque",
    "tara.treatment.retain.hint": "Conserver le risque en l'état, en connaissance de cause.",
    "tara.treatment.retain.prompt": "Pourquoi ce risque est acceptable",
    "bridge.why.severity":
        "La gravité physique des conséquences ne dépend pas de leur cause. Un freinage perdu blesse autant, que l'origine soit une panne ou une attaque.",
    "bridge.why.exposure":
        "L'exposition mesure la probabilité de se trouver dans la situation dangereuse. Un attaquant choisit son moment : il frappe quand ça fait mal. La notion s'effondre.",
    "bridge.why.controllability":
        "La contrôlabilité suppose un conducteur en mesure de réagir. Un attaquant peut neutraliser ce recours, voire l'attaquer en premier.",
    "bridge.why.replacement":
        "Côté sécurité, l'exposition et la contrôlabilité sont remplacées par la faisabilité de l'attaque, qui décrit ce que l'attaque coûte.",
    # --- RegWatch — paliers de fiabilité et notes de source ---
    "regwatch.tier.officiel":
        "Source officielle — l'organisme qui produit ou administre le référentiel",
    "regwatch.tier.communaute": "Base communautaire — un tiers qui agrège des documents publics",
    "regwatch.tier.commentaire":
        "Commentaire spécialisé — blog ou organisme de conseil, pas un normalisateur",
    "regwatch.source.intacs.note":
        "Association qui administre le schéma de certification des assesseurs Automotive SPICE. Publie peu — quelques actualités par an. Le flux n'est pas exposé sur le site, il faut demander le format RSS.",
    "regwatch.source.vda_spice.note":
        "Catalogue officiel des publications, pas un fil d'actualité : c'est le signal ASPICE le plus fort qui soit — les versions réellement publiées. Réserve : dates au mois près, parfois à l'année seule, page en allemand. (Le flux RSS du VDA, lui, est abandonné : un billet « Test » de 2024.)",
    "regwatch.source.sres.note":
        "⚠️ Aucune source officielle n'est atteignable pour l'ISO 26262 : ISO.org répond par un défi anti-robot et le TC 22/SC 32 n'a pas de micro-site. Ce blog spécialisé est donc un palier « commentaire », jamais présenté comme officiel. C'est la seule norme dans ce cas.",
    "regwatch.source.globalautoregs.note":
        "Base tierce qui agrège les documents publics de la WP.29 — la voie praticable puisque unece.org répond par un défi anti-robot. Le rattachement à un règlement UN vient du champ « Relevant to » de la source elle-même, pas d'une devinette de notre part.",
    "regwatch.source.iso27ksecurity.note":
        "Blog spécialisé tenu par un praticien, remarquablement à jour sur les stades de rédaction de la famille ISO27k. Ce n'est pas l'ISO, et le ton y est parfois d'opinion — d'où le palier « commentaire ».",
    "regwatch.source.iso_tc176.note":
        "Le comité qui porte l'ISO 9001. ⚠️ committee.iso.org est ouvert alors que www.iso.org est fermé : deux sous-domaines, deux politiques. Son robots.txt autorise tout le monde avec « use=reference » — RegWatch ne recopie rien et lie la source, ce qui est exactement ça.",
    "regwatch.source.iso_tc176sc2.note":
        "Le sous-comité qui mène la révision de l'ISO 9001 — c'est ici que passe le signal le plus concret (« ISO/FDIS 9001 approuvé »). Même gabarit de page que le TC 176 : un seul parseur couvre les deux, et tout comité ISO qu'on voudra ajouter plus tard.",
    # --- Export Excel RegWatch ---
    "xl.rw.title": "Veille de signaux publics autour des normes",
    "xl.rw.date": "Date de la veille (UTC)",
    "xl.rw.window": "Fenêtre couverte",
    "xl.rw.days.one": "{n} jour",
    "xl.rw.days.other": "{n} jours",
    "xl.rw.norms": "Référentiels surveillés",
    "xl.rw.sources": "Sources interrogées",
    "xl.rw.kept": "Signaux retenus",
    "xl.rw.coverage.warning":
        "⚠ COUVERTURE INCOMPLÈTE — {unreachable} source(s) injoignable(s), {degraded} dégradée(s). Une absence de signal ne prouve rien.",
    "xl.rw.unreachable": "Injoignable",
    "xl.rw.unrecognised": "Structure non reconnue",
    "xl.rw.all.answered": "Toutes les sources interrogées ont répondu.",
    "xl.rw.undated.warning": "⚠ {n} élément(s) pertinent(s) écarté(s), faute de date exploitable",
    "xl.rw.undated": "Sans date",
    "xl.rw.by.signal": "Répartition par niveau de signal",
    "xl.rw.by.norm": "Répartition par référentiel",
    "xl.rw.sheet.signals": "Signaux",
    "xl.rw.col.norm": "Référentiel",
    "xl.rw.col.date": "Date",
    "xl.rw.col.signal": "Niveau de signal",
    "xl.rw.col.title": "Intitulé",
    "xl.rw.col.source": "Source",
    "xl.rw.col.tier": "Palier",
    "xl.rw.col.link": "Lien",
    "xl.rw.col.why": "Pourquoi ça compte (IA)",
    "xl.rw.col.read": "À lire ?",
    "xl.rw.col.impact": "Impact pour nous",
    "xl.rw.col.action": "Action décidée",
    "xl.rw.col.owner": "Responsable",
    "xl.rw.col.due": "Échéance",
    "xl.rw.col.comment": "Commentaire",
    "xl.rw.sheet.coverage": "Couverture",
    "xl.rw.coverage.title": "Ce que la veille a pu voir, et ce qu'elle n'a pas pu voir",
    "xl.rw.coverage.state": "État",
    "xl.rw.coverage.detail": "Détail",
    "xl.rw.state.unreachable": "INJOIGNABLE",
    "xl.rw.state.unreachable.detail": "Aucune réponse exploitable",
    "xl.rw.state.degraded": "DÉGRADÉE",
    "xl.rw.state.degraded.detail":
        "La page répond mais rien ne s'en extrait — la structure du site a probablement changé",
    "xl.rw.state.ok": "Répondu",
    "xl.rw.state.ok.detail": "Lue et analysée",
    "xl.rw.incidents": "Détail des incidents",
    "xl.rw.setaside": "Écartés faute de date exploitable",
    "xl.rw.sheet.sources": "Sources",
    "xl.rw.sources.title": "D'où viennent ces signaux, et ce que chaque source vaut",
    "xl.rw.sources.norms": "Référentiels",
    "xl.rw.sources.address": "Adresse",
    "xl.rw.sources.know": "Ce qu'il faut en savoir",
    "xl.rw.sources.tiers": "Paliers de fiabilité",
    "xl.rw.sheet.limits": "Limites",
    "xl.rw.limits.title": "Ce que cet outil ne fait pas",
    "xl.rw.limits.col": "Limite",
    "xl.rw.limits.detail": "Précision",
    "xl.rw.sheet.summary": "Synthèse",
    # --- Export Excel RegWatch — avertissement et limites ---
    "xl.rw.disclaimer":
        "Démonstration pédagogique. RegWatch ne republie jamais le contenu des normes — elles sont payantes et protégées : seuls le titre, la date et le lien vers la source sont remontés, et le corps des pages n'est même pas téléchargé. Le niveau de signal est déduit du titre seul : il oriente, c'est le lien qui fait foi. Cet outil ne remplace ni la lecture des normes, ni un service de veille réglementaire.",
    "xl.rw.limit.window": "La fenêtre est fixe, elle ne suit pas vos visites",
    "xl.rw.limit.window.detail":
        "Ce classeur couvre les {n} derniers jours au moment de l'export, pas « depuis la dernière fois » : l'outil ne garde aucune trace de vos passages",
    "xl.rw.limit.signal": "Le niveau de signal est déduit du titre seul",
    "xl.rw.limit.signal.detail":
        "Faute de corps de page, un article « comment mettre à jour votre SMSI » peut ressortir en « Publication ». L'étiquette oriente, le lien est le livrable",
    "xl.rw.limit.tiers": "Toutes les sources ne se valent pas",
    "xl.rw.limit.tiers.detail":
        "Le palier est porté par chaque ligne et détaillé dans l'onglet Sources. Un blog spécialisé n'est pas un organisme de normalisation",
    "xl.rw.limit.absence": "Une absence de signal n'est pas une preuve",
    "xl.rw.limit.absence.detail": "Vérifiez l'onglet Couverture avant de conclure que rien n'a bougé",
    "xl.rw.limit.ai": "La colonne « Pourquoi ça compte » est écrite par un modèle",
    "xl.rw.limit.ai.detail":
        "À partir du seul intitulé, sans avoir lu le document. Elle n'a joué aucun rôle dans la sélection des lignes de ce classeur",
    "xl.rw.limit.coverage": "Les sources ne couvrent pas tout ce qui existe",
    "xl.rw.limit.coverage.detail":
        "ISO.org et unece.org refusent l'accès aux programmes : certaines normes n'ont donc aucune source officielle atteignable",
    "xl.rw.limit.artifact": "Ce classeur est le seul artefact durable",
    "xl.rw.limit.artifact.detail":
        "Rien n'est conservé sur le serveur après l'export — pensez à l'archiver",
    # --- Export Excel SafetyScope ---
    "xl.hara.sheet.analysis": "Analyse HARA",
    "xl.hara.sheet.summary": "Synthèse",
    "xl.hara.sheet.scales": "Échelles",
    "xl.hara.sheet.limits": "Limites",
    "xl.hara.title": "SafetyScope — analyse de risques HARA",
    "xl.hara.item": "Item étudié",
    "xl.hara.date": "Date (UTC)",
    "xl.hara.count": "Nombre d'événements",
    "xl.hara.max": "ASIL le plus élevé",
    "xl.hara.events": "Événements redoutés",
    "xl.hara.col.malfunction": "Dysfonctionnement",
    "xl.hara.col.situation": "Situation de conduite",
    "xl.hara.col.severity": "Sévérité (S)",
    "xl.hara.col.exposure": "Exposition (E)",
    "xl.hara.col.controllability": "Contrôlabilité (C)",
    "xl.hara.col.asil": "ASIL",
    "xl.hara.col.goal": "Objectif de sécurité",
    "xl.hara.col.safestate": "État sûr",
    "xl.hara.col.owner": "Responsable",
    "xl.hara.col.comment": "Commentaire",
    "xl.hara.scales.title": "Échelles de cotation",
    "xl.hara.decomp": "Décompositions admises pour ",
    "xl.hara.decomp.none": "Aucune — un QM ne se décompose pas.",
    "xl.hara.decomp.note": "Sous réserve d'une indépendance suffisante entre les éléments.",
    "xl.hara.limits.col": "Limite",
    "xl.hara.limits.detail": "Ce que cela implique",
    "xl.hara.disclaimer":
        "Démonstration pédagogique. Cet outil implémente la logique de détermination ASIL avec des formulations qui lui sont propres. Il ne reproduit pas le texte de l'ISO 26262, document sous licence, et ne s'y substitue en aucun cas.",
    "xl.hara.limit.judgment": "La cotation S/E/C relève du jugement de l'ingénieur",
    "xl.hara.limit.judgment.detail": "L'outil calcule, il ne décide pas à votre place",
    "xl.hara.limit.situations": "Les situations de conduite ne sont pas exhaustives",
    "xl.hara.limit.situations.detail":
        "Une HARA complète balaie systématiquement les situations opérationnelles",
    "xl.hara.limit.decomp": "Les décompositions supposent une indépendance suffisante",
    "xl.hara.limit.decomp.detail": "Cette indépendance doit être démontrée, pas postulée",
    "xl.hara.limit.goal": "Aucun objectif de sécurité n'est généré automatiquement",
    "xl.hara.limit.goal.detail": "Sa formulation et l'état sûr associé restent à rédiger",
    "xl.hara.limit.privacy": "Aucune donnée ne quitte votre navigateur",
    "xl.hara.limit.privacy.detail":
        "Rien n'est enregistré sur le serveur, et le brouillon local disparaît à la fermeture de l'onglet — ce classeur est le seul artefact durable, pensez à l'archiver",
    "xl.hara.col.number": "N°",
    "xl.hara.col.rating": "Cotation",
    # --- Export Excel ThreatScope ---
    "xl.tara.sheet.summary": "Synthèse",
    "xl.tara.sheet.table": "Tableau TARA",
    "xl.tara.sheet.goals": "Objectifs de cybersécurité",
    "xl.tara.sheet.scales": "Barème appliqué",
    "xl.tara.sheet.limits": "Limites",
    "xl.tara.title": "Analyse de menaces et de risques (TARA)",
    "xl.tara.item": "Item étudié",
    "xl.tara.date": "Date (UTC)",
    "xl.tara.damages": "Scénarios de dommage",
    "xl.tara.paths": "Chemins d'attaque cotés",
    "xl.tara.maxrisk": "Risque le plus élevé",
    "xl.tara.goals.count": "Objectifs de cybersécurité produits",
    "xl.tara.fromhara": "Repris d'une analyse HARA",
    "xl.tara.gaps": "⚠ {n} point(s) à compléter avant de clore l'analyse",
    "xl.tara.threat.ref": "Menace {ref}",
    "xl.tara.allsettled": "Tous les risques à traiter sont tranchés et justifiés.",
    "xl.tara.byrisk": "Répartition des valeurs de risque",
    "xl.tara.risk.value": "Risque {value}",
    "xl.tara.col.ref": "Réf.",
    "xl.tara.col.asset": "Actif",
    "xl.tara.col.damage": "Scénario de dommage",
    "xl.tara.col.traceability": "Traçabilité",
    "xl.tara.col.impact": "Impact retenu",
    "xl.tara.col.threat": "Scénario de menace",
    "xl.tara.col.path": "Chemin d'attaque",
    "xl.tara.col.potential": "Potentiel",
    "xl.tara.col.feasibility": "Faisabilité",
    "xl.tara.col.risk": "Risque",
    "xl.tara.col.treatment": "Traitement",
    "xl.tara.col.written": "Objectif / justification",
    "xl.tara.col.complete": "Complétude",
    "xl.tara.complete": "Complet",
    "xl.tara.col.goal": "Objectif de cybersécurité",
    "xl.tara.col.fromthreat": "Issu de la menace",
    "xl.tara.col.riskteated": "Risque traité",
    "xl.tara.col.owner": "Responsable",
    "xl.tara.col.due": "Échéance",
    "xl.tara.col.status": "Statut",
    "xl.tara.col.check": "Vérification",
    "xl.tara.col.comment": "Commentaire",
    "xl.tara.nogoal":
        "Aucun objectif produit : aucune décision de réduire un risque n'a été prise.",
    "xl.tara.scales.title": "Barème de potentiel d'attaque réellement appliqué",
    "xl.tara.scales.param": "Paramètre",
    "xl.tara.scales.level": "Niveau",
    "xl.tara.scales.points": "Points",
    "xl.tara.scales.total": "Total possible : 0 à {n} points",
    "xl.tara.scales.potential": "Potentiel d'attaque",
    "xl.tara.matrix": "Matrice impact × faisabilité → valeur de risque",
    "xl.tara.matrix.corner": "Impact \\ Faisabilité",
    "xl.tara.decisions": "Décisions de traitement et écrit exigé",
    "xl.tara.col.decision": "Décision",
    "xl.tara.decision.requires": "Ce qu'elle impose d'écrire",
    "xl.tara.decision.scope": "Portée",
    "xl.tara.limits.title": "Ce que cet outil ne fait pas",
    "xl.tara.limits.why": "Pourquoi c'est important",
    "xl.tara.disclaimer":
        "Démonstration pédagogique. Le barème de potentiel d'attaque employé ici est une calibration propre à cet outil : il ne reproduit ni l'ISO/SAE 21434 ni l'ISO 18045, documents sous licence. La norme laisse chaque organisation définir sa méthode de détermination du risque — celle-ci est donc une méthode, pas la méthode, et ne se substitue à aucun référentiel.",
    "xl.tara.limit.judgment":
        "La cotation d'impact et de faisabilité relève du jugement de l'ingénieur",
    "xl.tara.limit.judgment.detail": "L'outil calcule et trace, il ne décide pas à votre place",
    "xl.tara.limit.calibration": "Le barème de potentiel d'attaque est une calibration propre",
    "xl.tara.limit.calibration.detail": "À confronter au barème de votre organisation avant tout usage réel",
    "xl.tara.limit.matrix": "La matrice de risque est une méthode parmi d'autres",
    "xl.tara.limit.matrix.detail": "La norme laisse chaque organisation définir la sienne",
    "xl.tara.limit.threats": "Les scénarios de menace ne sont pas exhaustifs",
    "xl.tara.limit.threats.detail":
        "Une TARA complète balaie systématiquement les actifs et leurs propriétés",
    "xl.tara.limit.paths": "Les chemins d'attaque sont décrits en texte, sans arbre d'attaque",
    "xl.tara.limit.paths.detail": "L'analyse de chemins d'une TARA réelle va plus loin",
    "xl.tara.limit.bridge": "La sévérité reprise d'une HARA est une proposition",
    "xl.tara.limit.bridge.detail":
        "L'exposition et la contrôlabilité, elles, ne traversent jamais le pont",
    "xl.tara.limit.privacy": "Aucune donnée ne quitte votre navigateur",
    "xl.tara.limit.privacy.detail":
        "Rien n'est enregistré sur le serveur, et le brouillon local disparaît à la fermeture de l'onglet — ce classeur est le seul artefact durable, pensez à l'archiver",
    "tara.calibration":
        "Le temps et l'équipement portent les écarts les plus larges, délibérément :\nce sont les deux facteurs qui discriminent réellement une attaque sur un\nvéhicule. Une attaque menée avec un dongle radio à 30 € en quelques jours et\nune attaque exigeant un banc de laboratoire et six mois de travail ne se\nressemblent en rien, et un barème qui les rapproche ne sert à rien.\n\nLa fenêtre d'opportunité suit de près : sur un véhicule, pouvoir agir sur une\nvoiture en stationnement, en roulage ou immobilisée à l'atelier change tout.\n\nL'expertise et la connaissance de l'item comptent, mais se révèlent plus\nbinaires en pratique — on a l'information, ou on ne l'a pas.",
    # --- SentinelScan — markdown et Excel ---
    "scan.crit.CRITIQUE": "CRITIQUE",
    "scan.crit.MAJEUR": "MAJEUR",
    "scan.crit.MINEUR": "MINEUR",
    "scan.crit.INFO": "INFO",
    "scan.sla.CRITIQUE": "24 h",
    "scan.sla.MAJEUR": "5 jours ouvrés",
    "scan.sla.MINEUR": "15 jours",
    "scan.sla.INFO": "au fil de l'eau",
    "scan.warn.coverage":
        "⚠️ **Couverture incomplète.** GitHub n'a pas mené à terme {incomplete} requête(s) sur {run} : sa recherche a dépassé le délai qu'il s'accorde et il a répondu par un résultat partiel. **Sur ces requêtes, l'absence de détection ne prouve rien.** Relancez le scan pour obtenir une couverture complète avant de conclure quoi que ce soit.",
    "scan.warn.homonym":
        "⚠️ **Probable homonymie.** Les {found} détections se répartissent sur {owners} propriétaires distincts — la signature d'un terme courant (prénom, mot du langage) plutôt que d'un identifiant d'organisation. L'homonymie est le principal piège de cette veille. Reprenez avec un terme plus distinctif : nom de projet interne, domaine e-mail, référence documentaire.",
    "scan.proc.1": "1. **Préserver la preuve** — capture horodatée, URL, SHA de commit.",
    "scan.proc.2": "2. **Qualifier** — faux positif / homonyme / vrai positif.",
    "scan.proc.3":
        "3. **Si un secret est exposé : révoquer sous 24 h**, puis analyser les logs.",
    "scan.proc.4":
        "4. **Demander le retrait** ensuite seulement — jamais avant la révocation.",
    "scan.proc.5":
        "5. **Vérifier la suppression effective** — les forks et le cache survivent.",
    "scan.proc.6":
        "6. **Traiter la cause** — hook `gitleaks` en pre-commit, sensibilisation.",
    "scan.cov.code": "GitHub — code",
    "scan.cov.code.how": "Recherche dans le contenu des fichiers",
    "scan.cov.repos": "GitHub — dépôts",
    "scan.cov.repos.how": "Recherche par nom et description",
    "scan.cov.gist": "Gist / Pastebin",
    "scan.cov.gist.how": "Aucune API exploitable",
    "scan.cov.auto": "Automatisé",
    "scan.cov.manual": "Manuel — non couvert ici",
    "scan.lim.branch": "GitHub n'indexe que la branche par défaut",
    "scan.lim.branch.detail": "Un secret sur une branche secondaire n'est pas détecté",
    "scan.lim.inactive": "GitHub exclut certains dépôts inactifs",
    "scan.lim.inactive.detail": "Angle mort sur les dépôts anciens",
    "scan.lim.gist": "Gists et Pastebin n'ont pas d'API de recherche",
    "scan.lim.gist.detail":
        "Passage manuel indispensable — c'est statistiquement la 1re source de fuite",
    "scan.lim.forges": "Les autres forges ne sont pas interrogées",
    "scan.lim.forges.detail": "GitLab, Gitee, npm, Docker Hub hors périmètre de cette démo",
    "scan.lim.forks": "Dépôts supprimés mais forkés",
    "scan.lim.forks.detail":
        "Le contenu survit à la suppression — nécessite une demande au support",
    "md.scan.summary": "## Synthèse",
    "md.scan.keywords": "**Termes recherchés :** {terms}",
    "md.scan.counts":
        "**{found} détection(s)** sur {run} requête(s) exécutée(s) en {seconds} s.",
    "md.scan.table.head": "| Criticité | Nombre | Délai de traitement |",
    "md.scan.detections": "## Détections",
    "md.scan.det.head": "| Criticité | Détection | Dépôt | Chemin |",
    "md.scan.more": "*{n} détection(s) supplémentaire(s) dans le rapport Excel.*",
    "md.scan.none": "Aucune exposition détectée sur ce périmètre.",
    "md.scan.procedure": "## Procédure de traitement",
    "md.scan.limits": "## Limites connues",
    "md.scan.lim.head": "| Limite | Conséquence |",
    "md.scan.errors": "## Erreurs",
    "md.scan.errors.note":
        "Une plateforme en échec laisse un trou dans la couverture — à vérifier avant de conclure.",
    "xl.scan.sheet.summary": "Synthèse",
    "xl.scan.sheet.detections": "Détections",
    "xl.scan.sheet.coverage": "Couverture",
    "xl.scan.sheet.limits": "Limites",
    "xl.scan.sheet.errors": "Erreurs",
    "xl.scan.title": "SentinelScan — rapport de veille",
    "xl.scan.keywords": "Termes recherchés",
    "xl.scan.date": "Date du scan (UTC)",
    "xl.scan.duration": "Durée",
    "xl.scan.queries": "Requêtes exécutées",
    "xl.scan.detections": "Détections",
    "xl.scan.owners": "Propriétaires distincts",
    "xl.scan.coverage.state": "Couverture",
    "xl.scan.coverage.complete": "Complète",
    "xl.scan.coverage.incomplete": "INCOMPLÈTE",
    "xl.scan.col.criticality": "Criticité",
    "xl.scan.col.count": "Nombre",
    "xl.scan.col.sla": "Délai de traitement",
    "xl.scan.procedure": "Procédure de traitement",
    "xl.scan.col.detection": "Détection",
    "xl.scan.col.repo": "Dépôt",
    "xl.scan.col.owner": "Propriétaire",
    "xl.scan.col.path": "Chemin",
    "xl.scan.col.url": "URL",
    "xl.scan.col.term": "Terme",
    "xl.scan.col.status": "Statut",
    "xl.scan.col.truepos": "Vrai positif ?",
    "xl.scan.col.secret": "Secret exposé ?",
    "xl.scan.col.action": "Action menée",
    "xl.scan.col.owner2": "Responsable",
    "xl.scan.col.date": "Date traitement",
    "xl.scan.col.comment": "Commentaire",
    "xl.scan.col.source": "Source",
    "xl.scan.col.method": "Méthode d'interrogation",
    "xl.scan.abandoned": "Requêtes abandonnées par GitHub (résultat partiel)",
    "xl.scan.incomplete": "Résultat incomplet — ne rien conclure",
    "xl.scan.col.limit": "Limite",
    "xl.scan.col.consequence": "Conséquence",
    "xl.scan.col.error": "Erreur rencontrée",
    "xl.scan.noerror": "Aucune erreur — couverture complète sur le périmètre interrogé.",
    # --- Messages destinés au visiteur ---
    "err.quota.llm":
        "Le quota quotidien de l'API gratuite est atteint — la démonstration repartira demain. SafetyScope et ThreatScope, eux, ne font appel à aucune IA pour coter : ils restent pleinement utilisables.",
    "err.quota.daily": "Quota quotidien de la démonstration atteint. Réessayez demain.",
    "err.quota.github":
        "Quota quotidien de la démonstration atteint — l'API GitHub est limitée. Réessayez demain.",
    "err.rate.suggest": "Une proposition par minute. Réessayez dans {wait} s.",
    "err.rate.scan": "Un scan toutes les 3 minutes. Réessayez dans {wait} s.",
    "err.rate.watch": "Une veille par minute. Réessayez dans {wait} s.",
    "err.session": "Session expirée. Relancez depuis la page.",
    "err.session.scan": "Session de scan expirée. Relancez depuis la page.",
    "err.busy.suggest": "Une proposition est déjà en cours. Réessayez dans un instant.",
    "err.busy.audit": "Un audit est déjà en cours. Réessayez dans quelques instants.",
    "err.busy.scan": "Un scan est déjà en cours. Réessayez dans un instant.",
    "err.busy.watch": "Une veille est déjà en cours. Réessayez dans un instant.",
    "err.need.item":
        "Décrivez l'item étudié en quelques mots avant de lancer la proposition.",
    "err.need.context":
        "Décrivez l'actif ou la conséquence redoutée avant de lancer la proposition.",
    "err.fail.hazards":
        "La proposition a échoué. Vous pouvez saisir les événements à la main.",
    "err.fail.threats": "La proposition a échoué. Vous pouvez saisir les menaces à la main.",
    "err.fail.audit": "L'audit n'a pas abouti. Réessayez dans un instant.",
    "err.fail.scan": "Le scan a échoué. Réessayez dans quelques instants.",
    "err.fail.watch": "La veille a échoué. Réessayez dans quelques instants.",
    "err.fail.explain": "L'explication a échoué. Le tableau reste utilisable tel quel.",
    "err.need.signals": "Aucun signal exploitable à expliquer. Relancez une veille.",
    "err.report.gone": "Rapport expiré ou introuvable. Relancez l'export.",
    "err.report.gone.scan": "Rapport expiré ou introuvable. Relancez un scan.",
    "err.timeout": "Délai dépassé.",
    # --- Page de garde ---
    "home.ss.desc":
        "Veille de fuite d'information sur les dépôts publics. Saisissez vos termes de recherche, l'outil identifie les expositions et produit un rapport téléchargeable classé par criticité.",
    "home.title": "Outils Qualité &amp; Sécurité — Industrie automobile",
    "home.hara.desc":
        "Analyse de risques et détermination du niveau ASIL. La cotation est une table de décision : la réponse est exacte et immédiate. L'IA n'intervient qu'en option, pour proposer les événements redoutés — jamais pour les coter.",
    "home.tara.desc":
        "Analyse de menaces et de risques cybersécurité. La faisabilité d'une attaque se cote sur cinq critères, le risque en découle immédiatement. La chaîne va jusqu'aux objectifs de cybersécurité — une TARA produit des exigences, pas un chiffre.",
    "home.stance.pair":
        "<strong>SafetyScope et ThreatScope se parlent.</strong> La sévérité d'un événement redouté devient l'impact « sécurité des personnes » d'un scénario de dommage. L'exposition et la contrôlabilité, elles, ne traversent pas : un attaquant choisit son moment, et peut neutraliser le recours du conducteur.",
    "home.rw.desc":
        "Veille de signaux publics autour des normes : révisions en cours, publications, calendriers. Le rattachement à un référentiel est déterministe — aucune IA ne décide de ce qui remonte. Chaque source affiche ce qu'elle vaut.",
    "home.subtitle":
        "Une collection d'outils de démonstration autour de la conformité normative et de la sécurité de l'information. Chacun tourne réellement — rien n'est simulé.",
    "home.stance.qc":
        "<strong>Un seul en dépend réellement : QualityCrew</strong>, où quatre agents rédigent l'audit — c'est sa raison d'être. Partout ailleurs l'IA reste facultative : elle balaie des mots-guides pour amorcer une réflexion, ou résume en une phrase pourquoi un signal mérite l'attention. <strong>Jamais elle ne cote, jamais elle ne décide de ce qui est retenu.</strong> Savoir quand ne pas utiliser un LLM fait partie du métier.",
    "home.stance.rw":
        "<strong>RegWatch ne republie jamais le contenu d'une norme.</strong> Ces documents sont payants et protégés : l'outil ne remonte que le titre, la date et le lien vers la source — le corps des pages n'est même pas téléchargé. Et parce que toutes les sources ne se valent pas, chaque signal affiche le palier de la sienne : un comité ISO n'est pas un blog de conseil.",
    "home.qc.desc":
        "Audit de conformité par agents IA. Quatre agents analysent un dossier documentaire en temps réel — qualité des exigences, couverture de test, risques sûreté — et produisent un rapport structuré.",
    "home.stance.noai":
        "<strong>Quatre de ces cinq outils produisent leur résultat sans aucune intelligence artificielle.</strong> Déterminer un ASIL ou une valeur de risque, ce sont des tables de décision : la réponse est exacte et instantanée. Rattacher un signal de veille à une norme, c'est une règle écrite, reproductible et testée hors ligne. Chercher une exposition sur des dépôts publics, c'est une API et des critères de criticité. Y glisser un modèle de langage n'ajouterait qu'une latence et une incertitude.",
    "home.rw.tag.public": "Sources publiques",
    "home.h1": "Outils <em>Qualité &amp; Sécurité</em>",
    "home.rw.tag.watch": "Veille normative",
    "home.ss.tag.osint": "OSINT passif",
    "home.hara.tag.instant": "Sans attente",
    "home.section.stance": "Parti pris",
    "home.section.tools": "Outils",
    # --- Page de garde — libellés accompagnés d'une icône ---
    "home.badge": "Démos live — automobile &amp; embarqué",
    "home.qc.cta": "Lancer la démo",
    "home.ss.cta": "Lancer un scan",
    "home.hara.cta": "Coter un item",
    "home.tara.cta": "Analyser les menaces",
    "home.rw.cta": "Lancer une veille",
    # --- Page QualityCrew ---
    "qc.subtitle":
        "4 agents CrewAI analysent un dossier documentaire en temps réel — qualité des exigences, couverture de test, risques sûreté — et produisent un rapport structuré en quelques secondes.",
    "qc.agent.1.desc":
        "Qualité CHK-01 à CHK-06 — identifiants, critères, ambiguïtés, périmètre, traçabilité",
    "qc.agent.2.desc":
        "Checklist ASPICE SWE.1/SWE.2 + ISO 26262 Part 6 — 15 points CHK-01 à CHK-15",
    "qc.h1": "Audit de conformité<br>par <em>agents IA</em>",
    "qc.stat.checks": "Points de contrôle vérifiés (CHK-01 à CHK-15)",
    "qc.stat.defects": "Défauts détectés sur le jeu de démonstration",
    "qc.agent.3.desc":
        "Trous de couverture, incohérences ISO 26262, fonctions sûreté non testées",
    "qc.title": "QualityCrew — Audit ASPICE / ISO 26262",
    "qc.agent.4.desc": "Rapport final — tableau de sévérité, recommandations priorisées",
    "qc.agent.2": "Vérificateur de conformité",
    "qc.report.title": "Rapport d'audit — BTM SRS &amp; Test Plan",
    "qc.stat.duration": "Durée du dernier audit",
    "qc.agent.4": "Rédacteur de synthèse",
    "qc.agent.1": "Analyste d'exigences",
    "qc.agent.3": "Détecteur de risques",
    "qc.section.report": "Rapport généré",
    "qc.section.agents": "Agents",
    "qc.status.waiting": "En attente",
    "qc.badge": "Démo live — ASPICE / ISO 26262",
    "qc.cta": "Lancer l'audit",
    # --- Page SentinelScan ---
    "ss.subtitle":
        "Veille de fuite d'information sur les dépôts publics GitHub. Saisissez des termes distinctifs — nom d'entreprise, projet interne, domaine e-mail — l'outil identifie les expositions et les classe par criticité.",
    "ss.warn.1":
        "Ne scannez qu'un <strong>périmètre dont vous avez la responsabilité</strong>. Identifier les expositions d'un tiers sans mandat vous engage.",
    "ss.warn.accept": "J'ai compris et je scanne un périmètre dont j'ai la responsabilité.",
    "ss.warn.3":
        "La valeur d'un secret n'est <strong>jamais lue, affichée ni stockée</strong>. Seules les métadonnées sont remontées.",
    "ss.warn.4":
        "Si un secret est exposé : <strong>révoquez-le</strong>. Ne le testez pas — c'est un accès non autorisé, même s'il appartient à votre employeur.",
    "ss.title": "SentinelScan — Veille de fuite d'information",
    "ss.hint":
        "3 termes maximum, séparés par des virgules. Les termes trop génériques sont refusés — ils ne remontent que du bruit. Comptez environ 90 s.",
    "ss.warn.2":
        "Sources <strong>publiques exclusivement</strong> — rien n'est tenté sur un dépôt privé.",
    "ss.h1": "Sentinel<em>Scan</em>",
    "ss.section.terms": "Termes de recherche",
    "ss.report.title": "Rapport de veille",
    "ss.section.progress": "Progression",
    "ss.section.result": "Résultat",
    "ss.badge": "Démo live — OSINT passif",
    "ss.cta": "Lancer le scan",
    # --- Page SentinelScan — suite ---
    "ss.warn.head": "Conditions d'usage",
    # --- Page SafetyScope ---
    "hara.ai.note":
        "L'IA propose des événements à partir des mots-guides usuels. Elle ne cote jamais&nbsp;: la sévérité, l'exposition et la contrôlabilité restent votre jugement.",
    "hara.title": "SafetyScope — Analyse de risques HARA / ASIL",
    "hara.section.events": "Événements redoutés",
    "hara.h1": "Safety<em>Scope</em>",
    "hara.none": "Aucun événement coté",
    "hara.max": "ASIL le plus élevé",
    "hara.item": "Item étudié",
    "hara.spread": "Répartition",
    "hara.section.summary": "Synthèse",
    "hara.badge": "Cotation instantanée — aucun temps d'attente",
    "hara.reset": "Repartir d'une analyse vierge",
    "hara.add": "Ajouter un événement",
    "hara.ai.cta": "Proposer par IA",
    "hara.export": "Exporter en Excel",
    "hara.bridge.cta": "Ouvrir dans ThreatScope",
    # --- Page ThreatScope ---
    "tara.title": "ThreatScope — Analyse de menaces et de risques TARA",
    "tara.goals": "Objectifs de cybersécurité produits",
    "tara.spread": "Répartition des valeurs de risque",
    "tara.calibration.head": "Comment ce barème est calibré",
    "tara.none": "Aucun chemin d'attaque coté",
    "tara.section.damages": "Scénarios de dommage",
    "tara.h1": "Threat<em>Scope</em>",
    "tara.max": "Risque le plus élevé",
    "tara.item": "Item étudié",
    "tara.section.summary": "Synthèse",
    "tara.badge": "Cotation instantanée — aucun temps d'attente",
    "tara.reset": "Repartir d'une analyse vierge",
    "tara.add": "Ajouter un scénario de dommage",
    "tara.export": "Exporter en Excel",
    # --- Page SafetyScope — suite ---
    "hara.bridge.head": "Poursuivre en analyse cybersécurité",
    # --- Page RegWatch ---
    "rw.disclaimer":
        "Démonstration pédagogique. RegWatch ne remplace ni la lecture des normes, ni un abonnement à un service de veille réglementaire. Les libellés de signal sont déduits du titre seul : ils orientent, c'est le lien vers la source qui fait foi.",
    "rw.hint":
        "Sélectionnez au moins un référentiel. Comptez une dizaine de secondes.",
    "rw.title": "RegWatch — Veille normative et réglementaire",
    "rw.subtitle":
        "Cochez les référentiels qui vous concernent : l'outil interroge leurs sources publiques et remonte ce qui a bougé — révisions, stades de rédaction, publications, calendriers. Titre, date et lien vers la source d'origine.",
    "rw.sources.title": "Sources interrogées, et ce que chacune vaut",
    "rw.section.norms": "Référentiels à surveiller",
    "rw.section.sources": "Sources interrogées",
    "rw.h1": "Reg<em>Watch</em>",
    "rw.checkall": "Tout cocher",
    "rw.section.result": "Résultat",
    "rw.badge": "Démo live — veille à la demande",
    "rw.cta": "Lancer la veille",
    "rw.scope": "Ce que fait cet outil, et ce qu'il ne fait pas",
    "rw.explain.cta": "Pourquoi ça compte",
    # --- Page QualityCrew — messages JavaScript ---
    "qc.js.running": "Durée — audit en cours",
    "qc.js.connecting": "Connexion au moteur…",
    "qc.js.agent": "Agent {n}/4 en cours…",
    "qc.js.interrupted": "Durée avant interruption",
    "qc.js.unknown": "Erreur inconnue.",
    "qc.js.lost": "Connexion interrompue. Vérifiez que le serveur tourne.",
    "qc.js.locale": "fr-FR",
    # --- Page SentinelScan — messages JavaScript ---
    "ss.js.count.one": "· {found} détection en {duration} s",
    "ss.js.count.other": "· {found} détection(s) en {duration} s",
    "ss.js.refused": "Requête refusée.",
    "ss.js.running": "Scan en cours sur : {terms}",
    "ss.js.query": "Requête {index}/{total}…",
    "ss.js.found.one": "{n} détection",
    "ss.js.found.other": "{n} détection(s)",
    "ss.js.failed": "échec",
    "ss.js.incomplete":
        "Couverture incomplète — GitHub a abandonné {n} requête(s). Ne concluez pas à une absence d'exposition.",
    "ss.js.done": "Scan terminé. Chaque constat reste à qualifier.",
    "ss.js.unknown": "Erreur inconnue.",
    # --- Page RegWatch — messages JavaScript ---
    "rw.js.hint":
        "Sélectionnez au moins un référentiel. Fenêtre de {n} jours, une dizaine de secondes.",
    "rw.js.catalogue.ko": "Catalogue des sources indisponible.",
    "rw.js.cover.head": "Couverture incomplète — une absence de signal ne prouve rien",
    "rw.js.unreachable": "{label} : source injoignable.",
    "rw.js.degraded":
        "{label} : la page répond mais rien ne s'en extrait — la structure du site a probablement changé.",
    "rw.js.undated": "{n} élément(s) pertinent(s) écarté(s), faute de date exploitable",
    "rw.js.stat.signals.one": "signal retenu",
    "rw.js.stat.signals.other": "signal(aux) retenu(s)",
    "rw.js.stat.sources": "sources lues",
    "rw.js.stat.window": "fenêtre",
    "rw.js.stat.duration": "durée",
    "rw.js.none.mute":
        "Aucun signal retenu, mais {n} source(s) de ce référentiel n'ont pas répondu : n'en concluez rien.",
    "rw.js.none.ok":
        "Aucun signal sur les {n} derniers jours. Les sources ont répondu — c'est une absence constatée, pas une panne.",
    "rw.js.refused": "Requête refusée.",
    "rw.js.export.prep": "Préparation du classeur…",
    "rw.js.export.ko": "Export refusé.",
    "rw.js.export.ok": "Classeur prêt — il inclut la couverture et le détail des sources.",
    "rw.js.explain.run": "Rédaction des explications…",
    "rw.js.explain.done":
        "{n} explication(s) ajoutée(s). Le tableau, lui, ne doit rien au modèle.",
    "rw.js.uncheck": "Tout décocher",
    "rw.js.running": "Veille en cours sur {n} référentiel(s)…",
    "rw.js.done.partial":
        "Veille terminée, mais la couverture est incomplète — lisez l'avertissement avant de conclure.",
    "rw.js.done": "Veille terminée sur les {n} derniers jours.",
    "rw.js.unknown": "Erreur inconnue.",
    # --- Page SafetyScope — messages JavaScript ---
    "hara.js.matrix.ko": "Impossible de charger la table ASIL.",
    "hara.js.delete": "Supprimer",
    "hara.js.ph.malfunction": "Dysfonctionnement — ex : perte inattendue du couple de freinage",
    "hara.js.ph.situation":
        "Situation de conduite — ex : descente sur autoroute, chaussée mouillée",
    "hara.js.event": "Événement {n}",
    "hara.js.max": "{n} événements maximum pour cette démonstration.",
    "hara.js.count": "{n} / {max} événements",
    "hara.js.rated.one": "{n} événement coté",
    "hara.js.rated.other": "{n} événements cotés",
    "hara.js.decomp": "Décompositions admises",
    "hara.js.decomp.note": "Sous réserve d'une indépendance suffisante entre les éléments.",
    "hara.js.draft.one":
        "Brouillon restauré — {n} événement redouté. Votre saisie n'a jamais quitté ce navigateur et disparaîtra à la fermeture de l'onglet.",
    "hara.js.draft.other":
        "Brouillon restauré — {n} événements redoutés. Votre saisie n'a jamais quitté ce navigateur et disparaîtra à la fermeture de l'onglet.",
    "hara.js.need.item": "Décrivez d'abord l'item étudié en quelques mots.",
    "hara.js.refused": "Requête refusée.",
    "hara.js.sweep": "Balayage des mots-guides…",
    "hara.js.review": "Proposition établie, relecture en cours…",
    "hara.js.reviewed": "Relecture terminée.",
    "hara.js.nothing": "Aucune proposition exploitable. Saisissez les événements à la main.",
    "hara.js.added":
        "{n} événement(s) ajouté(s), <strong>non cotés</strong> — à vous de coter S, E et C.",
    "hara.js.unknown": "Erreur inconnue.",
    "hara.js.need.rating": "Cotez au moins un événement redouté pour poursuivre.",
    "hara.js.handoff.one": "1 événement redouté sera repris avec sa sévérité.",
    "hara.js.handoff.other": "{n} événements redoutés seront repris avec leur sévérité.",
    "hara.js.handoff.ko": "Impossible de transmettre l'analyse à ThreatScope.",
    "hara.js.export.prep": "Préparation du classeur…",
    "hara.js.export.ko": "Export refusé.",
    "hara.js.export.ok": "Classeur prêt — le téléchargement démarre.",
    # --- Page ThreatScope — messages JavaScript ---
    "tara.js.scales.ko": "Impossible de charger le barème.",
    "tara.js.bridge.title.one": "{n} événement redouté repris de votre analyse HARA{item}",
    "tara.js.bridge.title.other": "{n} événements redoutés repris de votre analyse HARA{item}",
    "tara.js.bridge.item": " — « {item} »",
    "tara.js.bridge.capped":
        "Sur {total} événements cotés, {added} ont été repris — cette démonstration est plafonnée à {max} scénarios de dommage.",
    "tara.js.bridge.all":
        "Chaque événement est devenu un scénario de dommage à retravailler. Rien n'est coté d'office : les propositions sont à confirmer.",
    "tara.js.rule.severity":
        "<strong>La sévérité traverse</strong> — elle devient l'impact « sécurité des personnes ». ",
    "tara.js.rule.exposure": "<strong>L'exposition ne traverse pas.</strong> ",
    "tara.js.rule.controllability": "<strong>La contrôlabilité ne traverse pas.</strong> ",
    "tara.js.draft.one": "Brouillon restauré — {n} scénario de dommage",
    "tara.js.draft.other": "Brouillon restauré — {n} scénarios de dommage",
    "tara.js.draft.sub":
        "Votre saisie a été retrouvée telle que vous l'aviez laissée. Elle n'a jamais quitté ce navigateur et disparaîtra à la fermeture de l'onglet.",
    "tara.js.del.damage": "Supprimer ce scénario de dommage",
    "tara.js.del.threat": "Supprimer ce scénario de menace",
    "tara.js.delete": "Supprimer",
    "tara.js.ph.asset": "Actif concerné — ex : calculateur de freinage",
    "tara.js.ph.damage":
        "Conséquence redoutée — ex : freinage commandé sans action du conducteur",
    "tara.js.ph.threat":
        "Menace — ex : élévation de privilèges via l'interface de diagnostic",
    "tara.js.ph.path":
        "Chemin d\'attaque — ex : accès au port OBD, puis contournement de l\'authentification UDS",
    "tara.js.impact.kept": "Impact retenu",
    "tara.js.threats.label": "Scénarios de menace",
    "tara.js.add.threat": "Ajouter une menace",
    "tara.js.suggest.hint":
        "L'IA balaie les catégories de menace à partir de l'actif décrit. Elle ne cote jamais : la faisabilité et le traitement restent votre jugement.",
    "tara.js.need.context": "Décrivez d'abord l'actif ou la conséquence redoutée.",
    "tara.js.refused": "Requête refusée.",
    "tara.js.sweep": "Balayage des catégories de menace…",
    "tara.js.review": "Proposition établie, relecture en cours…",
    "tara.js.reviewed": "Relecture terminée.",
    "tara.js.nothing": "Aucune proposition exploitable. Saisissez les menaces à la main.",
    "tara.js.added":
        "{n} menace(s) ajoutée(s), non cotées — à vous d'évaluer la faisabilité.",
    "tara.js.unknown": "Erreur inconnue.",
    "tara.js.origin.label": "Événement redouté {n}",
    "tara.js.origin": "Repris de l'{label}{asil}",
    "tara.js.origin.asil": " — coté ASIL {asil} en HARA",
    "tara.js.proposal":
        "Sévérité <strong>S{severity}</strong> en HARA → impact sécurité des personnes proposé : <strong>{impact}</strong>",
    "tara.js.apply": "Appliquer",
    "tara.js.applied": "Appliqué",
    "tara.js.feas.none": "Faisabilité non cotée",
    "tara.js.feas": "{potential} / {max} pt · faisabilité {level}{damage}",
    "tara.js.feas.nodamage": " · impact du dommage non coté",
    "tara.js.risk": "Risque",
    "tara.js.nodecision": "— décision non prise",
    "tara.js.treat.needed":
        "Un risque au-dessus de {threshold} doit être tranché explicitement — et l'écrit qui va avec.",
    "tara.js.treat.ok": "Un risque de {risk} peut être retenu sans autre forme de procès.",
    "tara.js.complete": "complet",
    "tara.js.incomplete": "à compléter",
    "tara.js.damage.num": "Scénario de dommage {n}",
    "tara.js.threat.num": "Menace {n}.{p}",
    "tara.js.max": "{n} scénarios de dommage maximum pour cette démonstration.",
    "tara.js.count": "{n} / {max} scénarios de dommage",
    "tara.js.rated.one": "{n} chemin d'attaque coté",
    "tara.js.rated.other": "{n} chemins d'attaque cotés",
    "tara.js.needrating":
        "Cotez un impact et une faisabilité pour obtenir une valeur de risque.",
    "tara.js.notreat": "Aucun risque n'appelle de traitement.",
    "tara.js.treated.one": "Le risque à traiter est tranché et justifié.",
    "tara.js.treated.other": "Les {n} risques à traiter sont tranchés et justifiés.",
    "tara.js.nogoal":
        "Aucun pour l'instant. Un objectif naît d'une décision de réduire un risque — c'est la sortie utile de la démarche : une TARA produit des exigences, pas un chiffre.",
    "tara.js.goals.one": "{n} objectif de cybersécurité, à verser aux exigences du projet.",
    "tara.js.goals.other": "{n} objectifs de cybersécurité, à verser aux exigences du projet.",
    "tara.js.export.prep": "Préparation du classeur…",
    "tara.js.export.ko": "Export refusé.",
    "tara.js.export.ok": "Classeur prêt — le téléchargement démarre.",
    # --- Descriptions pour les moteurs de recherche ---
    "home.meta":
        "Outils de démonstration Qualité et Sécurité pour l'industrie automobile et l'embarqué : audit de conformité par agents IA, veille de fuite d'information, analyse HARA / ASIL, analyse de menaces TARA.",
    "rw.meta":
        "Veille de signaux publics autour des normes qualité et sécurité automobile : ASPICE, ISO 26262, ISO/SAE 21434, ISO/IEC 27001, ISO 9001. Titre, date et lien vers la source — jamais le contenu des normes.",
    "home.hara.pair":
        "S'enchaîne avec ThreatScope",
    "home.tara.pair":
        "Reprend la sévérité de votre HARA",
    "home.rw.pair":
        "Ne republie jamais le contenu des normes",
    # --- Page hara — blocs explicatifs ---
    "hara.subtitle":
        "Analyse de risques et détermination du niveau ASIL, dans l'esprit de la démarche HARA de l'ISO 26262. La détermination est une table de décision : elle est <strong>exacte et immédiate</strong>, sans intelligence artificielle.",
    "hara.disclaimer":
        "<strong>Démonstration pédagogique.</strong> Cet outil implémente la logique de détermination, avec des formulations qui nous sont propres. Il ne reproduit pas le texte de l'ISO 26262, document sous licence, et ne s'y substitue en aucun cas.",
    "hara.bridge.1":
        "Une attaque peut provoquer les mêmes dysfonctionnements qu'une panne. <strong>ThreatScope</strong> reprend vos événements redoutés et <strong>leur sévérité</strong> pour amorcer une analyse TARA (ISO/SAE 21434).",
    "hara.bridge.2":
        "L'exposition et la contrôlabilité, elles, <strong>ne sont pas reprises</strong> : un attaquant choisit son moment, et peut neutraliser le recours du conducteur. Côté sécurité, elles cèdent la place à la faisabilité de l'attaque.",
    # --- Page tara — blocs explicatifs ---
    "tara.subtitle":
        "Analyse de menaces et de risques cybersécurité, dans l'esprit de la démarche TARA de l'ISO/SAE 21434. La faisabilité d'une attaque se cote, elle ne se devine pas&nbsp;: le résultat est <strong>déterministe et immédiat</strong>, sans intelligence artificielle.",
    "tara.disclaimer":
        "<strong>Démonstration pédagogique.</strong> Le barème de potentiel d'attaque employé ici est une <strong>calibration qui nous est propre</strong>&nbsp;: il ne reproduit ni l'ISO/SAE 21434 ni l'ISO 18045, documents sous licence. La norme laisse d'ailleurs chaque organisation définir sa méthode de détermination du risque — celle-ci est donc <em>une</em> méthode, pas <em>la</em> méthode.",
    "tara.damage.note":
        "Chaque scénario de dommage porte la cotation d'<strong>impact</strong> — quatre catégories, toutes à renseigner. Les scénarios de menace qu'il contient portent la <strong>faisabilité de l'attaque</strong>. Le risque naît du croisement des deux.",
    # --- Page regwatch — blocs explicatifs ---
    "rw.scope.1":
        "<strong>Le contenu des normes n'est jamais republié.</strong> Elles sont payantes et protégées. RegWatch ne remonte que le titre, la date et le lien — le corps des pages n'est même pas téléchargé.",
    "rw.scope.2":
        "<strong>La fenêtre est de <span id=\"window-days\">90</span> jours, fixe.</strong> L'écran répond « qu'est-ce qui a bougé sur cette période », <em>pas</em> « depuis votre dernière visite » : l'outil ne garde aucune trace de vos passages.",
    "rw.scope.3":
        "<strong>Le palier de chaque source est affiché.</strong> Un comité ISO et le blog d'un cabinet de conseil ne se valent pas, et ne sont pas présentés comme équivalents.",
    "rw.scope.4":
        "<strong>Aucune IA ne décide de ce qui est retenu.</strong> Le rattachement à une norme et le niveau de signal sont déterministes, reproductibles, et testés hors ligne.",
    "rw.scope.5":
        "<strong>Une source muette est signalée comme telle.</strong> « Rien de neuf » et « je n'ai pas pu regarder » sont deux réponses différentes — les confondre serait le pire défaut d'un outil de veille.",
    "rw.explain.note":
        "Optionnel. Un modèle rédige une phrase par signal, <strong>à partir du seul intitulé</strong> — il n'a pas lu les documents et n'a rien décidé de ce qui est affiché ci-dessous. Le classeur, lui, emporte aussi les sources muettes.",
    # --- Champs de saisie et arrivée sans HARA ---
    "hara.ph.item": "ex : Freinage régénératif",
    "tara.ph.item": "ex : Passerelle télématique embarquée",
    "ss.ph.terms": "ex : mon-entreprise, projet-interne",
    "tara.nohara":
        "Vous avez déjà mené une analyse HARA&nbsp;? <a href=\"/hara\">SafetyScope</a> peut alimenter cette page&nbsp;: la sévérité de vos événements redoutés y devient l'impact «&nbsp;sécurité des personnes&nbsp;» de vos scénarios de dommage.",
    # --- ThreatScope — traçabilité ---
    "tara.trace.direct": "Saisi directement",
    "tara.trace.hara": "HARA — {origin}{detail}",
    # --- ThreatScope — bornes de faisabilité ---
    "xl.tara.range": "{from} à {to}",
    "xl.tara.range.above": "{from} et au-delà",
    # --- RegWatch — libellés de source ---
    "regwatch.source.intacs.label": "iNTACS — actualités",
    "regwatch.source.vda_spice.label": "VDA QMC — publications Automotive SPICE",
    "regwatch.source.sres.label": "SRES — commentaire sûreté et cybersécurité automobile",
    "regwatch.source.globalautoregs.label": "GlobalAutoRegs — documents WP.29",
    "regwatch.source.iso27ksecurity.label": "ISO27k Forum — veille sur la famille ISO/IEC 27000",
    "regwatch.source.iso_tc176.label": "ISO/TC 176 — actualités du comité",
    "regwatch.source.iso_tc176sc2.label": "ISO/TC 176/SC 2 — actualités du sous-comité",
    # --- SentinelScan — motifs de déclassement ---
    "scan.reason.template": "{detection} — modèle ou exemple",
    "scan.reason.name": "{detection} — nom de fichier non concluant",
    "scan.reason.code": "{detection} — code source ou documentation",
    # --- SentinelScan — types de détection ---
    "scan.detection.env": "Fichier .env exposé",
    "scan.detection.pem": "Clé privée / certificat",
    "scan.detection.credentials": "Fichier de credentials",
    "scan.detection.config": "Fichier de configuration",
    "scan.detection.cooccurrence": "Co-occurrence avec « api_key »",
    "scan.detection.repo": "Dépôt mentionnant le terme",
    # --- RegWatch — niveaux de signal ---
    "regwatch.signal.publication": "Publication / amendement",
    "regwatch.signal.draft": "Travaux en cours",
    "regwatch.signal.event": "Annonce / calendrier",
    "regwatch.signal.info": "Information",
    # --- QualityCrew — états d'agent ---
    "qc.status.running": "En cours…",
    "qc.status.done": "Terminé",
    # --- RegWatch — incidents réseau ---
    "regwatch.err.unreachable": "Injoignable ({cause}).",
    "regwatch.err.refused":
        "Accès refusé par la source (HTTP {code}) — protection anti-robot probable.",
    "regwatch.err.notfound": "Page introuvable (HTTP 404) — l'URL a changé.",
    "regwatch.err.unexpected": "Réponse inattendue (HTTP {code}).",
    "regwatch.err.toobig": "Réponse anormalement volumineuse (> {ko} Ko).",
    "regwatch.err.challenge":
        "La source répond par un défi anti-robot : elle n'est pas consultable par un programme, et le contourner est exclu.",
    "regwatch.err.feed": "Flux illisible : {cause}",
    "regwatch.err.notafeed": "Racine « {tag} » : ni RSS ni Atom.",
    "regwatch.err.parser": "{source} — parseur en échec ({cause}).",
    "regwatch.err.degraded":
        "{source} — la page répond mais aucun élément n'en est extrait : le parseur ne reconnaît plus sa structure.",
    "regwatch.err.line": "{source} — {message}",

    # --- Plafonds du jour et disponibilité des fonctions IA (25/08/2026) ---
    # ⚠️ Un seul de ces plafonds est un plafond d'IA. Les deux autres protègent
    # un jeton GitHub partagé et la courtoisie envers des sites tiers. Les
    # présenter ensemble sous « quota IA » contredirait le « Parti pris ».
    "status.title": "Plafonds du jour",
    "status.group.ai": "Fonctions IA",
    "status.group.ai.note":
        "Ces fonctions sont facultatives : chaque outil rend son résultat sans elles.",
    "status.group.service": "Plafonds de service",
    "status.group.service.note":
        "Sans rapport avec l'IA — ils protègent des ressources partagées entre visiteurs.",
    "status.cap.suggestions": "Propositions par IA",
    "status.cap.suggestions.note":
        "Compteur commun à SafetyScope, ThreatScope et RegWatch : un compteur par outil "
        "donnerait trois fois plus d'appels sur une seule enveloppe.",
    "status.cap.scans": "Scans SentinelScan",
    "status.cap.scans.note":
        "Tous les visiteurs partagent un même jeton GitHub — le plafond évite qu'une "
        "personne le monopolise. Cet outil n'appelle aucune IA.",
    "status.cap.watches": "Veilles RegWatch",
    "status.cap.watches.note":
        "Le site interroge sept sources tierces depuis une seule adresse : le plafond "
        "est une courtoisie envers elles. La veille elle-même n'appelle aucune IA.",
    "status.uncapped.audit": "Audit QualityCrew",
    "status.uncapped.audit.note":
        "Aucun plafond quotidien, alors que c'est le plus gros consommateur d'IA du site. "
        "Le dire vaut mieux que le taire.",
    "status.outage":
        "Les fonctions IA sont indisponibles pour aujourd'hui : le quota quotidien du "
        "fournisseur est épuisé. Tout le reste du site fonctionne normalement.",
    "status.js.available": "disponibles",
    "status.js.unavailable": "indisponibles aujourd'hui",
    "status.js.remaining.one": "{n} restante sur {limit}",
    "status.js.remaining.other": "{n} restantes sur {limit}",
    "status.js.resets": "Remise à zéro le {quand}.",
    "status.js.locale": "fr-FR",
    "status.js.uncapped": "non plafonné",
    "status.js.failed": "Plafonds indisponibles pour le moment.",
}
