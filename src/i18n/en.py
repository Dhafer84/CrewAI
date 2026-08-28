"""English catalogue.

Mirrors `fr.py`, which is the source of truth: every key originates there.
A test rejects any key here that has no French counterpart.
"""

CATALOGUE: dict[str, str] = {
    # --- Navigation, shared by all six pages ------------------------------
    "nav.back": "All tools",
    "nav.github": "GitHub",
    "nav.source": "Source code",

    # --- Footers -----------------------------------------------------------
    "footer.tools": "All tools",
    "footer.index": "100% fictional data",
    "footer.qualitycrew": "QualityCrew — demo project · 100% fictional documents",
    "footer.sentinelscan":
        "Passive OSINT · public sources only · search terms never travel in a URL",
    "footer.hara":
        "SafetyScope · not a substitute for the standard",
    "footer.tara":
        "ThreatScope · not a substitute for the standard",
    "footer.regwatch":
        "On-demand watch · public sources · the content of standards is never "
        "republished",
    # --- SafetyScope — S / E / C scales ---
    "hara.severity.0": "No injuries",
    "hara.severity.1": "Light to moderate injuries",
    "hara.severity.2": "Severe injuries, survival probable",
    "hara.severity.3": "Critical or fatal injuries",
    "hara.exposure.0": "Implausible situation",
    "hara.exposure.1": "Very low probability",
    "hara.exposure.2": "Low probability",
    "hara.exposure.3": "Medium probability",
    "hara.exposure.4": "High probability",
    "hara.controllability.0": "Controllable in general",
    "hara.controllability.1": "Simply controllable",
    "hara.controllability.2": "Normally controllable",
    "hara.controllability.3": "Difficult to control, or not at all",
    # --- ThreatScope — attack potential scale and impact ---
    "tara.param.time": "Elapsed time",
    "tara.param.expertise": "Expertise required",
    "tara.param.knowledge": "Knowledge of the item",
    "tara.param.window": "Window of opportunity",
    "tara.param.equipment": "Equipment",
    "tara.time.0": "Less than a day",
    "tara.time.1": "Less than a week",
    "tara.time.2": "Less than a month",
    "tara.time.3": "Less than six months",
    "tara.time.4": "More than six months",
    "tara.expertise.0": "Layman",
    "tara.expertise.1": "Proficient",
    "tara.expertise.2": "Expert",
    "tara.expertise.3": "Multiple experts from different fields",
    "tara.knowledge.0": "Public",
    "tara.knowledge.1": "Restricted",
    "tara.knowledge.2": "Confidential",
    "tara.knowledge.3": "Strictly confidential",
    "tara.window.0": "Unlimited",
    "tara.window.1": "Easy to obtain",
    "tara.window.2": "Moderate",
    "tara.window.3": "Difficult to obtain",
    "tara.equipment.0": "Standard",
    "tara.equipment.1": "Specialised",
    "tara.equipment.2": "Bespoke",
    "tara.equipment.3": "Multiple bespoke items",
    "tara.feasibility.0": "Very low",
    "tara.feasibility.1": "Low",
    "tara.feasibility.2": "Medium",
    "tara.feasibility.3": "High",
    "tara.impact.0": "Negligible",
    "tara.impact.1": "Moderate",
    "tara.impact.2": "Major",
    "tara.impact.3": "Severe",
    "tara.category.safety": "Safety of persons",
    "tara.category.financial": "Financial",
    "tara.category.operational": "Operational",
    "tara.category.privacy": "Privacy",
    # --- ThreatScope — risk treatment and HARA bridge ---
    "tara.treatment.avoid.label": "Avoid the risk",
    "tara.treatment.avoid.hint":
        "Remove the source of the risk: drop the function, the interface or the data flow concerned.",
    "tara.treatment.avoid.prompt": "What is removed or replaced",
    "tara.treatment.reduce.label": "Reduce the risk",
    "tara.treatment.reduce.hint":
        "Bring the risk down to an acceptable level through cybersecurity measures. This is the case that produces a requirement.",
    "tara.treatment.reduce.prompt": "Cybersecurity goal",
    "tara.treatment.share.label": "Share the risk",
    "tara.treatment.share.hint":
        "Transfer all or part of the risk to a third party — supplier, contract, insurance.",
    "tara.treatment.share.prompt": "With whom, and on what basis",
    "tara.treatment.retain.label": "Retain the risk",
    "tara.treatment.retain.hint": "Keep the risk as it stands, knowingly.",
    "tara.treatment.retain.prompt": "Why this risk is acceptable",
    "bridge.why.severity":
        "The physical seriousness of the consequences does not depend on their cause. Lost braking injures just as much whether it comes from a failure or an attack.",
    "bridge.why.exposure":
        "Exposure measures how likely it is to be in the hazardous situation. An attacker picks the moment: they strike when it hurts. The notion collapses.",
    "bridge.why.controllability":
        "Controllability assumes a driver able to react. An attacker can neutralise that recourse, or target it first.",
    "bridge.why.replacement":
        "On the security side, exposure and controllability are replaced by attack feasibility, which describes what the attack costs.",
    # --- RegWatch — source tiers and notes ---
    "regwatch.tier.officiel": "Official source — the body that produces or administers the standard",
    "regwatch.tier.communaute": "Community database — a third party aggregating public documents",
    "regwatch.tier.commentaire": "Specialist commentary — a blog or consultancy, not a standards body",
    "regwatch.source.intacs.note":
        "The association that administers the Automotive SPICE assessor certification scheme. Publishes rarely — a few news items a year. The feed is not exposed on the site; you have to ask for the RSS format.",
    "regwatch.source.vda_spice.note":
        "The official publications catalogue, not a news feed: this is the strongest ASPICE signal there is — the versions actually published. Caveat: dates to the month, sometimes to the year only, and the page is in German. (The VDA's own RSS feed is abandoned: one 'Test' post from 2024.)",
    "regwatch.source.sres.note":
        "⚠️ No official source is reachable for ISO 26262: ISO.org answers with an anti-bot challenge and TC 22/SC 32 has no micro-site. This specialist blog is therefore a 'commentary' tier, never presented as official. It is the only standard in this situation.",
    "regwatch.source.globalautoregs.note":
        "A third-party database aggregating public WP.29 documents — the workable route, since unece.org answers with an anti-bot challenge. The mapping to a UN regulation comes from the source's own 'Relevant to' field, not from a guess on our part.",
    "regwatch.source.iso27ksecurity.note":
        "A specialist blog kept by a practitioner, remarkably up to date on the drafting stages of the ISO27k family. It is not ISO, and the tone is at times opinion — hence the 'commentary' tier.",
    "regwatch.source.iso_tc176.note":
        "The committee behind ISO 9001. ⚠️ committee.iso.org is open while www.iso.org is closed: two subdomains, two policies. Its robots.txt allows everyone with 'use=reference' — RegWatch copies nothing and links the source, which is exactly that.",
    "regwatch.source.iso_tc176sc2.note":
        "The subcommittee running the ISO 9001 revision — this is where the most concrete signal comes through ('ISO/FDIS 9001 approved'). Same page template as TC 176: one parser covers both, and any ISO committee we may add later.",
    # --- RegWatch Excel export ---
    "xl.rw.title": "Watch on public signals around standards",
    "xl.rw.date": "Watch date (UTC)",
    "xl.rw.window": "Window covered",
    "xl.rw.days.one": "{n} day",
    "xl.rw.days.other": "{n} days",
    "xl.rw.norms": "Standards watched",
    "xl.rw.sources": "Sources queried",
    "xl.rw.kept": "Signals kept",
    "xl.rw.coverage.warning":
        "⚠ INCOMPLETE COVERAGE — {unreachable} source(s) unreachable, {degraded} degraded. An absence of signal proves nothing.",
    "xl.rw.unreachable": "Unreachable",
    "xl.rw.unrecognised": "Structure not recognised",
    "xl.rw.all.answered": "Every source queried answered.",
    "xl.rw.undated.warning": "⚠ {n} relevant item(s) set aside, for want of a usable date",
    "xl.rw.undated": "Undated",
    "xl.rw.by.signal": "Breakdown by signal level",
    "xl.rw.by.norm": "Breakdown by standard",
    "xl.rw.sheet.signals": "Signals",
    "xl.rw.col.norm": "Standard",
    "xl.rw.col.date": "Date",
    "xl.rw.col.signal": "Signal level",
    "xl.rw.col.title": "Title",
    "xl.rw.col.source": "Source",
    "xl.rw.col.tier": "Tier",
    "xl.rw.col.link": "Link",
    "xl.rw.col.why": "Why it matters (AI)",
    "xl.rw.col.read": "To read?",
    "xl.rw.col.impact": "Impact for us",
    "xl.rw.col.action": "Action decided",
    "xl.rw.col.owner": "Owner",
    "xl.rw.col.due": "Due date",
    "xl.rw.col.comment": "Comment",
    "xl.rw.sheet.coverage": "Coverage",
    "xl.rw.coverage.title": "What the watch could see, and what it could not",
    "xl.rw.coverage.state": "State",
    "xl.rw.coverage.detail": "Detail",
    "xl.rw.state.unreachable": "UNREACHABLE",
    "xl.rw.state.unreachable.detail": "No usable answer",
    "xl.rw.state.degraded": "DEGRADED",
    "xl.rw.state.degraded.detail":
        "The page answers but nothing is extracted from it — the site structure has probably changed",
    "xl.rw.state.ok": "Answered",
    "xl.rw.state.ok.detail": "Read and analysed",
    "xl.rw.incidents": "Incident detail",
    "xl.rw.setaside": "Set aside for want of a usable date",
    "xl.rw.sheet.sources": "Sources",
    "xl.rw.sources.title": "Where these signals come from, and what each source is worth",
    "xl.rw.sources.norms": "Standards",
    "xl.rw.sources.address": "Address",
    "xl.rw.sources.know": "What you need to know about it",
    "xl.rw.sources.tiers": "Reliability tiers",
    "xl.rw.sheet.limits": "Limits",
    "xl.rw.limits.title": "What this tool does not do",
    "xl.rw.limits.col": "Limit",
    "xl.rw.limits.detail": "Detail",
    "xl.rw.sheet.summary": "Summary",
    # --- RegWatch Excel export — disclaimer and limits ---
    "xl.rw.disclaimer":
        "RegWatch never republishes the content of standards — they are paid-for and protected: only the title, the date and the link to the source are reported, and the body of the pages is not even downloaded. The signal level is inferred from the title alone: it points the way, the link is what counts. This tool replaces neither reading the standards nor a regulatory watch service.",
    "xl.rw.limit.window": "The window is fixed, it does not track your visits",
    "xl.rw.limit.window.detail":
        "This workbook covers the last {n} days as at the export, not « since last time »: the tool keeps no trace of your visits",
    "xl.rw.limit.signal": "The signal level is inferred from the title alone",
    "xl.rw.limit.signal.detail":
        "With no page body, an article on « how to update your ISMS » may come out as « Publication ». The label points the way, the link is the deliverable",
    "xl.rw.limit.tiers": "Not all sources are equal",
    "xl.rw.limit.tiers.detail":
        "The tier is carried on every row and detailed in the Sources sheet. A specialist blog is not a standards body",
    "xl.rw.limit.absence": "An absence of signal is not proof",
    "xl.rw.limit.absence.detail": "Check the Coverage sheet before concluding that nothing moved",
    "xl.rw.limit.ai": "The « Why it matters » column is written by a model",
    "xl.rw.limit.ai.detail":
        "From the title alone, without having read the document. It played no part in selecting the rows of this workbook",
    "xl.rw.limit.coverage": "The sources do not cover everything that exists",
    "xl.rw.limit.coverage.detail":
        "ISO.org and unece.org refuse access to programs: some standards therefore have no reachable official source",
    "xl.rw.limit.artifact": "This workbook is the only lasting artefact",
    "xl.rw.limit.artifact.detail":
        "Nothing is kept on the server after the export — remember to archive it",
    # --- SafetyScope Excel export ---
    "xl.hara.sheet.analysis": "HARA analysis",
    "xl.hara.sheet.summary": "Summary",
    "xl.hara.sheet.scales": "Scales",
    "xl.hara.sheet.limits": "Limits",
    "xl.hara.title": "SafetyScope — HARA risk analysis",
    "xl.hara.item": "Item under study",
    "xl.hara.date": "Date (UTC)",
    "xl.hara.count": "Number of events",
    "xl.hara.max": "Highest ASIL",
    "xl.hara.events": "Hazardous events",
    "xl.hara.col.malfunction": "Malfunction",
    "xl.hara.col.situation": "Driving situation",
    "xl.hara.col.severity": "Severity (S)",
    "xl.hara.col.exposure": "Exposure (E)",
    "xl.hara.col.controllability": "Controllability (C)",
    "xl.hara.col.asil": "ASIL",
    "xl.hara.col.goal": "Safety goal",
    "xl.hara.col.safestate": "Safe state",
    "xl.hara.col.owner": "Owner",
    "xl.hara.col.comment": "Comment",
    "xl.hara.scales.title": "Rating scales",
    "xl.hara.decomp": "Decompositions allowed for ",
    "xl.hara.decomp.none": "None — a QM does not decompose.",
    "xl.hara.decomp.note": "Subject to sufficient independence between the elements.",
    "xl.hara.limits.col": "Limit",
    "xl.hara.limits.detail": "What that implies",
    "xl.hara.disclaimer":
        "This tool implements the ASIL determination logic with wordings of its own. It does not reproduce the text of ISO 26262, a licensed document, and in no way replaces it.",
    "xl.hara.limit.judgment": "S/E/C rating is a matter of engineering judgement",
    "xl.hara.limit.judgment.detail": "The tool computes, it does not decide for you",
    "xl.hara.limit.situations": "The driving situations are not exhaustive",
    "xl.hara.limit.situations.detail": "A complete HARA systematically sweeps the operational situations",
    "xl.hara.limit.decomp": "Decompositions assume sufficient independence",
    "xl.hara.limit.decomp.detail": "That independence must be demonstrated, not assumed",
    "xl.hara.limit.goal": "No safety goal is generated automatically",
    "xl.hara.limit.goal.detail": "Its wording and the associated safe state remain to be written",
    "xl.hara.limit.privacy": "No data leaves your browser",
    "xl.hara.limit.privacy.detail":
        "Nothing is stored on the server, and the local draft vanishes when the tab closes — this workbook is the only lasting artefact, remember to archive it",
    "xl.hara.col.number": "No.",
    "xl.hara.col.rating": "Rating",
    # --- ThreatScope Excel export ---
    "xl.tara.sheet.summary": "Summary",
    "xl.tara.sheet.table": "TARA table",
    "xl.tara.sheet.goals": "Cybersecurity goals",
    "xl.tara.sheet.scales": "Scale applied",
    "xl.tara.sheet.limits": "Limits",
    "xl.tara.title": "Threat analysis and risk assessment (TARA)",
    "xl.tara.item": "Item under study",
    "xl.tara.date": "Date (UTC)",
    "xl.tara.damages": "Damage scenarios",
    "xl.tara.paths": "Attack paths rated",
    "xl.tara.maxrisk": "Highest risk",
    "xl.tara.goals.count": "Cybersecurity goals produced",
    "xl.tara.fromhara": "Carried over from a HARA analysis",
    "xl.tara.gaps": "⚠ {n} point(s) to complete before closing the analysis",
    "xl.tara.threat.ref": "Threat {ref}",
    "xl.tara.allsettled": "Every risk to be treated is decided and justified.",
    "xl.tara.byrisk": "Breakdown of risk values",
    "xl.tara.risk.value": "Risk {value}",
    "xl.tara.col.ref": "Ref.",
    "xl.tara.col.asset": "Asset",
    "xl.tara.col.damage": "Damage scenario",
    "xl.tara.col.traceability": "Traceability",
    "xl.tara.col.impact": "Impact retained",
    "xl.tara.col.threat": "Threat scenario",
    "xl.tara.col.path": "Attack path",
    "xl.tara.col.potential": "Potential",
    "xl.tara.col.feasibility": "Feasibility",
    "xl.tara.col.risk": "Risk",
    "xl.tara.col.treatment": "Treatment",
    "xl.tara.col.written": "Goal / justification",
    "xl.tara.col.complete": "Completeness",
    "xl.tara.complete": "Complete",
    "xl.tara.col.goal": "Cybersecurity goal",
    "xl.tara.col.fromthreat": "From threat",
    "xl.tara.col.riskteated": "Risk treated",
    "xl.tara.col.owner": "Owner",
    "xl.tara.col.due": "Due date",
    "xl.tara.col.status": "Status",
    "xl.tara.col.check": "Verification",
    "xl.tara.col.comment": "Comment",
    "xl.tara.nogoal": "No goal produced: no decision to reduce a risk was taken.",
    "xl.tara.scales.title": "Attack potential scale actually applied",
    "xl.tara.scales.param": "Parameter",
    "xl.tara.scales.level": "Level",
    "xl.tara.scales.points": "Points",
    "xl.tara.scales.total": "Possible total: 0 to {n} points",
    "xl.tara.scales.potential": "Attack potential",
    "xl.tara.matrix": "Impact × feasibility matrix → risk value",
    "xl.tara.matrix.corner": "Impact \\ Feasibility",
    "xl.tara.decisions": "Treatment decisions and required writing",
    "xl.tara.col.decision": "Decision",
    "xl.tara.decision.requires": "What it requires in writing",
    "xl.tara.decision.scope": "Scope",
    "xl.tara.limits.title": "What this tool does not do",
    "xl.tara.limits.why": "Why it matters",
    "xl.tara.disclaimer":
        "The attack potential scale used here is a calibration of this tool's own: it reproduces neither ISO/SAE 21434 nor ISO 18045, both licensed documents. The standard lets each organisation define its own risk determination method — this is therefore a method, not the method, and replaces no reference framework.",
    "xl.tara.limit.judgment": "Impact and feasibility rating is a matter of engineering judgement",
    "xl.tara.limit.judgment.detail": "The tool computes and records, it does not decide for you",
    "xl.tara.limit.calibration": "The attack potential scale is a calibration of our own",
    "xl.tara.limit.calibration.detail": "To be checked against your organisation's scale before any real use",
    "xl.tara.limit.matrix": "The risk matrix is one method among others",
    "xl.tara.limit.matrix.detail": "The standard lets each organisation define its own",
    "xl.tara.limit.threats": "The threat scenarios are not exhaustive",
    "xl.tara.limit.threats.detail":
        "A complete TARA systematically sweeps the assets and their properties",
    "xl.tara.limit.paths": "Attack paths are described in text, without an attack tree",
    "xl.tara.limit.paths.detail": "The path analysis of a real TARA goes further",
    "xl.tara.limit.bridge": "The severity carried over from a HARA is a proposal",
    "xl.tara.limit.bridge.detail": "Exposure and controllability, for their part, never cross the bridge",
    "xl.tara.limit.privacy": "No data leaves your browser",
    "xl.tara.limit.privacy.detail":
        "Nothing is stored on the server, and the local draft vanishes when the tab closes — this workbook is the only lasting artefact, remember to archive it",
    "tara.calibration":
        "Time and equipment carry the widest ranges, deliberately: these are the two\nfactors that genuinely discriminate an attack on a vehicle. An attack carried\nout with a €30 radio dongle over a few days and one requiring a laboratory\nbench and six months of work bear no resemblance to each other, and a scale\nthat brings them closer together is of no use.\n\nThe window of opportunity follows closely: on a vehicle, being able to act on\na car parked, in motion, or immobilised at the workshop changes everything.\n\nExpertise and knowledge of the item matter, but prove more binary in\npractice — either you have the information, or you do not.",
    # --- SentinelScan — markdown and Excel ---
    "scan.crit.CRITIQUE": "CRITICAL",
    "scan.crit.MAJEUR": "MAJOR",
    "scan.crit.MINEUR": "MINOR",
    "scan.crit.INFO": "INFO",
    "scan.sla.CRITIQUE": "24 h",
    "scan.sla.MAJEUR": "5 working days",
    "scan.sla.MINEUR": "15 days",
    "scan.sla.INFO": "as they come",
    "scan.warn.coverage":
        "⚠️ **Incomplete coverage.** GitHub did not carry {incomplete} of {run} queries through to the end: its search exceeded the time it allows itself and it answered with a partial result. **On those queries, the absence of a detection proves nothing.** Run the scan again for full coverage before concluding anything.",
    "scan.warn.homonym":
        "⚠️ **Likely homonymy.** The {found} detections spread across {owners} distinct owners — the signature of a common term (a first name, an everyday word) rather than an organisation identifier. Homonymy is the main pitfall of this watch. Try again with a more distinctive term: internal project name, e-mail domain, document reference.",
    "scan.proc.1": "1. **Preserve the evidence** — timestamped capture, URL, commit SHA.",
    "scan.proc.2": "2. **Qualify** — false positive / homonym / true positive.",
    "scan.proc.3":
        "3. **If a secret is exposed: revoke within 24 h**, then analyse the logs.",
    "scan.proc.4": "4. **Request takedown** only afterwards — never before revocation.",
    "scan.proc.5":
        "5. **Verify the deletion actually happened** — forks and cache survive.",
    "scan.proc.6": "6. **Address the cause** — `gitleaks` pre-commit hook, awareness.",
    "scan.cov.code": "GitHub — code",
    "scan.cov.code.how": "Search inside file contents",
    "scan.cov.repos": "GitHub — repositories",
    "scan.cov.repos.how": "Search by name and description",
    "scan.cov.gist": "Gist / Pastebin",
    "scan.cov.gist.how": "No usable API",
    "scan.cov.auto": "Automated",
    "scan.cov.manual": "Manual — not covered here",
    "scan.lim.branch": "GitHub indexes only the default branch",
    "scan.lim.branch.detail": "A secret on a secondary branch is not detected",
    "scan.lim.inactive": "GitHub excludes some inactive repositories",
    "scan.lim.inactive.detail": "Blind spot on older repositories",
    "scan.lim.gist": "Gists and Pastebin have no search API",
    "scan.lim.gist.detail": "A manual pass is essential — statistically the first source of leaks",
    "scan.lim.forges": "Other forges are not queried",
    "scan.lim.forges.detail": "GitLab, Gitee, npm, Docker Hub out of scope for this demo",
    "scan.lim.forks": "Repositories deleted but forked",
    "scan.lim.forks.detail": "The content survives deletion — requires a request to support",
    "md.scan.summary": "## Summary",
    "md.scan.keywords": "**Search terms:** {terms}",
    "md.scan.counts":
        "**{found} detection(s)** from {run} search(es) run in {seconds} s.",
    "md.scan.table.head": "| Criticality | Count | Handling time |",
    "md.scan.detections": "## Detections",
    "md.scan.det.head": "| Criticality | Detection | Repository | Path |",
    "md.scan.more": "*{n} further detection(s) in the Excel report.*",
    "md.scan.none": "No exposure detected on this perimeter.",
    "md.scan.procedure": "## Handling procedure",
    "md.scan.limits": "## Known limits",
    "md.scan.lim.head": "| Limit | Consequence |",
    "md.scan.errors": "## Errors",
    "md.scan.errors.note":
        "A platform in failure leaves a hole in the coverage — check before concluding.",
    "xl.scan.sheet.summary": "Summary",
    "xl.scan.sheet.detections": "Detections",
    "xl.scan.sheet.coverage": "Coverage",
    "xl.scan.sheet.limits": "Limits",
    "xl.scan.sheet.errors": "Errors",
    "xl.scan.title": "SentinelScan — watch report",
    "xl.scan.keywords": "Search terms",
    "xl.scan.date": "Scan date (UTC)",
    "xl.scan.duration": "Duration",
    "xl.scan.queries": "Queries run",
    "xl.scan.detections": "Detections",
    "xl.scan.owners": "Distinct owners",
    "xl.scan.coverage.state": "Coverage",
    "xl.scan.coverage.complete": "Complete",
    "xl.scan.coverage.incomplete": "INCOMPLETE",
    "xl.scan.col.criticality": "Criticality",
    "xl.scan.col.count": "Count",
    "xl.scan.col.sla": "Handling time",
    "xl.scan.procedure": "Handling procedure",
    "xl.scan.col.detection": "Detection",
    "xl.scan.col.repo": "Repository",
    "xl.scan.col.owner": "Owner",
    "xl.scan.col.path": "Path",
    "xl.scan.col.url": "URL",
    "xl.scan.col.term": "Term",
    "xl.scan.col.status": "Status",
    "xl.scan.col.truepos": "True positive?",
    "xl.scan.col.secret": "Secret exposed?",
    "xl.scan.col.action": "Action taken",
    "xl.scan.col.owner2": "Owner",
    "xl.scan.col.date": "Handled on",
    "xl.scan.col.comment": "Comment",
    "xl.scan.col.source": "Source",
    "xl.scan.col.method": "Query method",
    "xl.scan.abandoned": "Queries abandoned by GitHub (partial result)",
    "xl.scan.incomplete": "Incomplete result — conclude nothing",
    "xl.scan.col.limit": "Limit",
    "xl.scan.col.consequence": "Consequence",
    "xl.scan.col.error": "Error encountered",
    "xl.scan.noerror": "No error — full coverage on the perimeter queried.",
    # --- Messages destinés au visiteur ---
    "err.quota.llm":
        "The free API's daily quota is exhausted — the demonstration will resume tomorrow. SafetyScope and ThreatScope, for their part, call on no AI to rate: they remain fully usable.",
    "err.quota.daily": "Daily quota for the demonstration reached. Try again tomorrow.",
    "err.quota.github":
        "Daily quota for the demonstration reached — the GitHub API is rate-limited. Try again tomorrow.",
    "err.rate.suggest": "One suggestion per minute. Try again in {wait} s.",
    "err.rate.scan": "One scan every 3 minutes. Try again in {wait} s.",
    "err.rate.watch": "One watch per minute. Try again in {wait} s.",
    "err.session": "Session expired. Start again from the page.",
    "err.session.scan": "Scan session expired. Start again from the page.",
    "err.busy.suggest": "A suggestion is already running. Try again in a moment.",
    "err.busy.audit": "An audit is already running. Try again in a few moments.",
    "err.busy.scan": "A scan is already running. Try again in a moment.",
    "err.busy.watch": "A watch is already running. Try again in a moment.",
    "err.need.item":
        "Describe the item under study in a few words before launching the suggestion.",
    "err.need.context":
        "Describe the asset or the feared consequence before launching the suggestion.",
    "err.fail.hazards": "The suggestion failed. You can enter the events by hand.",
    "err.fail.threats": "The suggestion failed. You can enter the threats by hand.",
    "err.fail.audit": "The audit did not complete. Try again in a moment.",
    "err.fail.scan": "The scan failed. Try again in a few moments.",
    "err.fail.watch": "The watch failed. Try again in a few moments.",
    "err.fail.explain": "The explanation failed. The table remains usable as it stands.",
    "err.need.signals": "No usable signal to explain. Run a watch again.",
    "err.report.gone": "Report expired or not found. Run the export again.",
    "err.report.gone.scan": "Report expired or not found. Run a scan again.",
    "err.timeout": "Timed out.",
    # --- Home page ---
    "home.ss.desc":
        "Information leak watch on public repositories. Enter your search terms, the tool identifies exposures and produces a downloadable report ranked by criticality.",
    "home.title": "Quality &amp; Safety Tools — Automotive industry",
    "home.hara.desc":
        "Risk analysis and ASIL determination. Rating is a decision table: the answer is exact and immediate. AI steps in only as an option, to suggest hazardous events — never to rate them.",
    "home.tara.desc":
        "Cybersecurity threat and risk analysis. Attack feasibility is rated on five criteria, and the risk follows immediately. The chain runs all the way to cybersecurity goals — a TARA produces requirements, not a number.",
    "home.stance.pair":
        "<strong>SafetyScope and ThreatScope talk to each other.</strong> The severity of a hazardous event becomes the « safety of persons » impact of a damage scenario. Exposure and controllability, for their part, do not cross: an attacker picks their moment, and can neutralise the driver's recourse.",
    "home.rw.desc":
        "Watch on public signals around standards: revisions under way, publications, timetables. Attaching a signal to a standard is deterministic — no AI decides what comes up. Every source shows what it is worth.",
    "home.subtitle":
        "A collection of demonstration tools around standards compliance and information security. Each one really runs — nothing is simulated.",
    "home.stance.qc":
        "<strong>Only one really depends on it: QualityCrew</strong>, where four agents write the audit — that is its whole purpose. Everywhere else AI stays optional: it sweeps guide words to prime a line of thought, or sums up in one sentence why a signal deserves attention. <strong>Never does it rate, never does it decide what is kept.</strong> Knowing when not to use an LLM is part of the craft.",
    "home.stance.rw":
        "<strong>RegWatch never republishes the content of a standard.</strong> These documents are paid-for and protected: the tool reports only the title, the date and the link to the source — the body of the pages is not even downloaded. And because not all sources are equal, every signal shows its own tier: an ISO committee is not a consultancy blog.",
    "home.qc.desc":
        "Compliance audit by AI agents. Four agents analyse a documentation set in real time — requirements quality, test coverage, safety risks — and produce a structured report.",
    "home.stance.noai":
        "<strong>Five of these six tools produce their result with no artificial intelligence at all.</strong> Determining an ASIL or a risk value are decision tables: the answer is exact and instantaneous. Refusing to close an 8D whose escape root cause is missing is a set of ordered rules. Attaching a watch signal to a standard is a written rule, reproducible and tested offline. Looking for an exposure on public repositories is an API and criticality criteria. Dropping a language model in would add nothing but latency and uncertainty.",
    "home.rw.tag.public": "Public sources",
    "home.h1": "Quality &amp; <em>Safety</em> tools",
    "home.rw.tag.watch": "Standards watch",
    "home.ss.tag.osint": "Passive OSINT",
    "home.hara.tag.instant": "No waiting",
    "home.section.stance": "Where we stand",
    "home.section.tools": "Tools",
    # --- Home page — labels next to an icon ---
    "home.qc.cta": "Run the demo",
    "home.ss.cta": "Run a scan",
    "home.hara.cta": "Rate an item",
    "home.tara.cta": "Analyse the threats",
    "home.rw.cta": "Run a watch",
    # --- QualityCrew page ---
    "qc.subtitle":
        "4 CrewAI agents analyse a documentation set in real time — requirements quality, test coverage, safety risks — and produce a structured audit report.",
    "qc.agent.1.desc":
        "Quality CHK-01 to CHK-06 — identifiers, criteria, ambiguities, scope, traceability",
    "qc.agent.2.desc":
        "ASPICE SWE.1/SWE.2 + ISO 26262 Part 6 checklist — 15 points, CHK-01 to CHK-15",
    "qc.h1": "Compliance audit<br>by <em>AI agents</em>",
    "qc.stat.checks": "Checkpoints verified (CHK-01 to CHK-15)",
    "qc.stat.defects": "Defects found in the demonstration set",
    "qc.agent.3.desc": "Coverage gaps, ISO 26262 inconsistencies, untested safety functions",
    "qc.title": "QualityCrew — ASPICE / ISO 26262 audit",
    "qc.agent.4.desc": "Final report — severity table, prioritised recommendations",
    "qc.agent.2": "Compliance verifier",
    "qc.report.title": "Audit report — BTM SRS &amp; Test Plan",
    "qc.stat.duration": "Duration of the last audit",
    "qc.agent.4": "Summary writer",
    "qc.agent.1": "Requirements analyst",
    "qc.agent.3": "Risk detector",
    "qc.section.report": "Report generated",
    "qc.section.agents": "Agents",
    "qc.status.waiting": "Waiting",
    "qc.badge": "Live demo — ASPICE / ISO 26262",
    "qc.cta": "Run the audit",
    # --- SentinelScan page ---
    "ss.subtitle":
        "Information leak watch on public GitHub repositories. Enter distinctive terms — company name, internal project, e-mail domain — and the tool identifies exposures and ranks them by criticality.",
    "ss.warn.1":
        "Only scan a <strong>perimeter you are responsible for</strong>. Identifying a third party's exposures without a mandate puts you at risk.",
    "ss.warn.accept": "I understand, and I am scanning a perimeter I am responsible for.",
    "ss.warn.3":
        "The value of a secret is <strong>never read, displayed or stored</strong>. Only metadata is reported.",
    "ss.warn.4":
        "If a secret is exposed: <strong>revoke it</strong>. Do not test it — that is unauthorised access, even if it belongs to your employer.",
    "ss.title": "SentinelScan — Information leak watch",
    "ss.hint":
        "Three terms maximum, comma-separated. Terms that are too generic are refused — they bring up nothing but noise. Allow about 90 s.",
    "ss.warn.2":
        "<strong>Public sources only</strong> — nothing is attempted on a private repository.",
    "ss.h1": "Sentinel<em>Scan</em>",
    "ss.section.terms": "Search terms",
    "ss.report.title": "Watch report",
    "ss.section.progress": "Progress",
    "ss.section.result": "Result",
    "ss.badge": "Live demo — passive OSINT",
    "ss.cta": "Run the scan",
    # --- SentinelScan page — continued ---
    "ss.warn.head": "Terms of use",
    # --- SafetyScope page ---
    "hara.ai.note":
        "The AI suggests events from the usual guide words. It never rates them&nbsp;: severity, exposure and controllability remain your call.",
    "hara.title": "SafetyScope — HARA / ASIL risk analysis",
    "hara.section.events": "Hazardous events",
    "hara.h1": "Safety<em>Scope</em>",
    "hara.none": "No event rated",
    "hara.max": "Highest ASIL",
    "hara.item": "Item under study",
    "hara.spread": "Breakdown",
    "hara.section.summary": "Summary",
    "hara.badge": "Instant rating — no waiting",
    "hara.reset": "Start from a blank analysis",
    "hara.add": "Add an event",
    "hara.ai.cta": "Suggest with AI",
    "hara.export": "Export to Excel",
    "hara.bridge.cta": "Open in ThreatScope",
    # --- ThreatScope page ---
    "tara.title": "ThreatScope — TARA threat and risk analysis",
    "tara.goals": "Cybersecurity goals produced",
    "tara.spread": "Breakdown of risk values",
    "tara.calibration.head": "How this scale is calibrated",
    "tara.none": "No attack path rated",
    "tara.section.damages": "Damage scenarios",
    "tara.h1": "Threat<em>Scope</em>",
    "tara.max": "Highest risk",
    "tara.item": "Item under study",
    "tara.section.summary": "Summary",
    "tara.badge": "Instant rating — no waiting",
    "tara.reset": "Start from a blank analysis",
    "tara.add": "Add a damage scenario",
    "tara.export": "Export to Excel",
    # --- SafetyScope page — continued ---
    "hara.bridge.head": "Continue into cybersecurity analysis",
    # --- RegWatch page ---
    "rw.disclaimer":
        "RegWatch replaces neither reading the standards nor a subscription to a regulatory watch service.",
    "rw.hint": "Select at least one standard. Allow about ten seconds.",
    "rw.title": "RegWatch — Standards and regulatory watch",
    "rw.subtitle":
        "Tick the standards that concern you: the tool queries their public sources and reports what moved. It never republishes the content of a standard.",
    "rw.sources.title": "Sources queried, and what each one is worth",
    "rw.section.norms": "Standards to watch",
    "rw.section.sources": "Sources queried",
    "rw.h1": "Reg<em>Watch</em>",
    "rw.checkall": "Tick all",
    "rw.section.result": "Result",
    "rw.badge": "Live demo — watch on demand",
    "rw.cta": "Run the watch",
    "rw.scope": "What this tool does, and what it does not",
    "rw.explain.cta": "Why it matters",
    # --- QualityCrew page — JavaScript messages ---
    "qc.js.running": "Duration — audit running",
    "qc.js.connecting": "Connecting to the engine…",
    "qc.js.agent": "Agent {n}/4 running…",
    "qc.js.interrupted": "Duration before interruption",
    "qc.js.unknown": "Unknown error.",
    "qc.js.lost": "Connection lost. Check that the server is running.",
    "qc.js.locale": "en-GB",
    # --- SentinelScan page — JavaScript messages ---
    "ss.js.count.one": "· {found} detection in {duration} s",
    "ss.js.count.other": "· {found} detections in {duration} s",
    "ss.js.refused": "Request refused.",
    "ss.js.running": "Scan running on: {terms}",
    "ss.js.query": "Query {index}/{total}…",
    "ss.js.found.one": "{n} detection",
    "ss.js.found.other": "{n} detections",
    "ss.js.failed": "failed",
    "ss.js.incomplete":
        "Incomplete coverage — GitHub abandoned {n} quer(y/ies). Do not conclude there is no exposure.",
    "ss.js.done": "Scan finished. Every finding remains to be qualified.",
    "ss.js.unknown": "Unknown error.",
    # --- RegWatch page — JavaScript messages ---
    "rw.js.hint": "Select at least one standard. {n}-day window, about ten seconds.",
    "rw.js.catalogue.ko": "Source catalogue unavailable.",
    "rw.js.cover.head": "Incomplete coverage — an absence of signal proves nothing",
    "rw.js.unreachable": "{label}: source unreachable.",
    "rw.js.degraded":
        "{label}: the page answers but nothing is extracted from it — the site structure has probably changed.",
    "rw.js.undated": "{n} relevant item(s) set aside, for want of a usable date",
    "rw.js.stat.signals.one": "signal kept",
    "rw.js.stat.signals.other": "signals kept",
    "rw.js.stat.sources": "sources read",
    "rw.js.stat.window": "window",
    "rw.js.stat.duration": "duration",
    "rw.js.none.mute":
        "No signal kept, but {n} source(s) for this standard did not answer: conclude nothing from it.",
    "rw.js.none.ok":
        "No signal over the last {n} days. The sources answered — this is an observed absence, not a failure.",
    "rw.js.refused": "Request refused.",
    "rw.js.export.prep": "Preparing the workbook…",
    "rw.js.export.ko": "Export refused.",
    "rw.js.export.ok": "Workbook ready — it includes the coverage and the source detail.",
    "rw.js.explain.run": "Writing the explanations…",
    "rw.js.explain.done": "{n} explanation(s) added. The table itself owes the model nothing.",
    "rw.js.uncheck": "Untick all",
    "rw.js.running": "Watch running on {n} standard(s)…",
    "rw.js.done.partial":
        "Watch finished, but coverage is incomplete — read the warning before concluding.",
    "rw.js.done": "Watch finished over the last {n} days.",
    "rw.js.unknown": "Unknown error.",
    # --- SafetyScope page — JavaScript messages ---
    "hara.js.matrix.ko": "Could not load the ASIL table.",
    "hara.js.delete": "Delete",
    "hara.js.ph.malfunction": "Malfunction — e.g. unexpected loss of braking torque",
    "hara.js.ph.situation": "Driving situation — e.g. motorway descent, wet road surface",
    "hara.js.event": "Event {n}",
    "hara.js.max": "{n} events maximum for this demonstration.",
    "hara.js.count": "{n} / {max} events",
    "hara.js.rated.one": "{n} event rated",
    "hara.js.rated.other": "{n} events rated",
    "hara.js.decomp": "Decompositions allowed",
    "hara.js.decomp.note": "Subject to sufficient independence between the elements.",
    "hara.js.draft.one":
        "Draft restored — {n} hazardous event. Your input never left this browser and will vanish when the tab closes.",
    "hara.js.draft.other":
        "Draft restored — {n} hazardous events. Your input never left this browser and will vanish when the tab closes.",
    "hara.js.need.item": "Describe the item under study in a few words first.",
    "hara.js.refused": "Request refused.",
    "hara.js.sweep": "Sweeping the guide words…",
    "hara.js.review": "Suggestion drafted, review under way…",
    "hara.js.reviewed": "Review finished.",
    "hara.js.nothing": "No usable suggestion. Enter the events by hand.",
    "hara.js.added":
        "{n} event(s) added, <strong>unrated</strong> — S, E and C are yours to set.",
    "hara.js.unknown": "Unknown error.",
    "hara.js.need.rating": "Rate at least one hazardous event to continue.",
    "hara.js.handoff.one": "1 hazardous event will be carried over with its severity.",
    "hara.js.handoff.other": "{n} hazardous events will be carried over with their severity.",
    "hara.js.handoff.ko": "Could not hand the analysis over to ThreatScope.",
    "hara.js.export.prep": "Preparing the workbook…",
    "hara.js.export.ko": "Export refused.",
    "hara.js.export.ok": "Workbook ready — the download is starting.",
    # --- ThreatScope page — JavaScript messages ---
    "tara.js.scales.ko": "Could not load the scale.",
    "tara.js.bridge.title.one": "{n} hazardous event carried over from your HARA analysis{item}",
    "tara.js.bridge.title.other": "{n} hazardous events carried over from your HARA analysis{item}",
    "tara.js.bridge.item": " — « {item} »",
    "tara.js.bridge.capped":
        "Of {total} rated events, {added} were carried over — this demonstration is capped at {max} damage scenarios.",
    "tara.js.bridge.all":
        "Every event has become a damage scenario to work on. Nothing is rated for you: the proposals are yours to confirm.",
    "tara.js.rule.severity":
        "<strong>Severity crosses</strong> — it becomes the « safety of persons » impact. ",
    "tara.js.rule.exposure": "<strong>Exposure does not cross.</strong> ",
    "tara.js.rule.controllability": "<strong>Controllability does not cross.</strong> ",
    "tara.js.draft.one": "Draft restored — {n} damage scenario",
    "tara.js.draft.other": "Draft restored — {n} damage scenarios",
    "tara.js.draft.sub":
        "Your input was found exactly as you left it. It never left this browser and will vanish when the tab closes.",
    "tara.js.del.damage": "Delete this damage scenario",
    "tara.js.del.threat": "Delete this threat scenario",
    "tara.js.delete": "Delete",
    "tara.js.ph.asset": "Asset concerned — e.g. braking ECU",
    "tara.js.ph.damage":
        "Feared consequence — e.g. braking commanded without driver action",
    "tara.js.ph.threat":
        "Threat — e.g. privilege escalation through the diagnostic interface",
    "tara.js.ph.path":
        "Attack path — e.g. access to the OBD port, then bypassing UDS authentication",
    "tara.js.impact.kept": "Impact retained",
    "tara.js.threats.label": "Threat scenarios",
    "tara.js.add.threat": "Add a threat",
    "tara.js.suggest.hint":
        "The AI sweeps the threat categories from the asset described. It never rates: feasibility and treatment remain your judgement.",
    "tara.js.need.context": "Describe the asset or the feared consequence first.",
    "tara.js.refused": "Request refused.",
    "tara.js.sweep": "Sweeping the threat categories…",
    "tara.js.review": "Suggestion drafted, review under way…",
    "tara.js.reviewed": "Review finished.",
    "tara.js.nothing": "No usable suggestion. Enter the threats by hand.",
    "tara.js.added": "{n} threat(s) added, unrated — feasibility is yours to assess.",
    "tara.js.unknown": "Unknown error.",
    "tara.js.origin.label": "Hazardous event {n}",
    "tara.js.origin": "Carried over from {label}{asil}",
    "tara.js.origin.asil": " — rated ASIL {asil} in the HARA",
    "tara.js.proposal":
        "Severity <strong>S{severity}</strong> in the HARA → suggested safety-of-persons impact: <strong>{impact}</strong>",
    "tara.js.apply": "Apply",
    "tara.js.applied": "Applied",
    "tara.js.feas.none": "Feasibility not rated",
    "tara.js.feas": "{potential} / {max} pt · feasibility {level}{damage}",
    "tara.js.feas.nodamage": " · damage impact not rated",
    "tara.js.risk": "Risk",
    "tara.js.nodecision": "— no decision taken",
    "tara.js.treat.needed":
        "A risk above {threshold} must be settled explicitly — and put in writing.",
    "tara.js.treat.ok": "A risk of {risk} may be retained without further ado.",
    "tara.js.complete": "complete",
    "tara.js.incomplete": "to complete",
    "tara.js.damage.num": "Damage scenario {n}",
    "tara.js.threat.num": "Threat {n}.{p}",
    "tara.js.max": "{n} damage scenarios maximum for this demonstration.",
    "tara.js.count": "{n} / {max} damage scenarios",
    "tara.js.rated.one": "{n} attack path rated",
    "tara.js.rated.other": "{n} attack paths rated",
    "tara.js.needrating": "Rate an impact and a feasibility to obtain a risk value.",
    "tara.js.notreat": "No risk calls for treatment.",
    "tara.js.treated.one": "The risk to be treated is settled and justified.",
    "tara.js.treated.other": "The {n} risks to be treated are settled and justified.",
    "tara.js.nogoal":
        "None yet. A goal is born of a decision to reduce a risk — that is the useful output of the method: a TARA produces requirements, not a number.",
    "tara.js.goals.one": "{n} cybersecurity goal, to be added to the project requirements.",
    "tara.js.goals.other": "{n} cybersecurity goals, to be added to the project requirements.",
    "tara.js.export.prep": "Preparing the workbook…",
    "tara.js.export.ko": "Export refused.",
    "tara.js.export.ok": "Workbook ready — the download is starting.",
    # --- Search-engine descriptions ---
    "qc.meta":
        "ASPICE and ISO 26262 compliance audit by four CrewAI agents: requirement quality, test coverage, safety risks, summary report. The audit really runs, nothing is simulated.",
    "ss.meta":
        "Information leak watch on public GitHub repositories: exposures ranked by criticality, Excel report. No secret is ever displayed or stored — only its metadata.",
    "hara.meta":
        "Risk analysis and ASIL determination, in the spirit of the ISO 26262 HARA method. S/E/C rating is a decision table: exact, immediate, with no artificial intelligence.",
    "tara.meta":
        "Cybersecurity threat and risk analysis, in the spirit of the ISO/SAE 21434 method and UN Regulation R155. From the damage scenario through to the cybersecurity goals.",
    # Alternative text for the sharing image — read by social network screen
    # readers, and displayed when the image fails to load.
    "og.alt":
        "The six Quality & Safety tools of qualitycrew.fr: QualityCrew, SentinelScan, SafetyScope, ThreatScope, RegWatch and CauseTrace.",
    "home.meta":
        "Quality and Safety demonstration tools for the automotive and embedded industry: compliance audit by AI agents, information leak watch, HARA / ASIL analysis, TARA threat analysis.",
    "rw.meta":
        "Watch on public signals around automotive quality and safety standards: ASPICE, ISO 26262, ISO/SAE 21434, ISO/IEC 27001, ISO 9001. Title, date and link to the source — never the content of the standards.",    "home.hara.pair": "Flows on into ThreatScope",    "home.tara.pair": "Carries over the severity from your HARA",    "home.rw.pair": "Never republishes the content of standards",
    # --- hara page — explanatory blocks ---
    "hara.subtitle":
        "Risk analysis and ASIL determination, in the spirit of the ISO 26262 HARA method. Determination is a decision table: it is <strong>exact and immediate</strong>, with no artificial intelligence.",
    "hara.disclaimer":
        "<strong>This tool implements the determination logic</strong> with wordings of our own. It does not reproduce the text of ISO 26262, a licensed document, and does not replace it.",
    "hara.bridge.1":
        "An attack can cause the same malfunctions as a failure. <strong>ThreatScope</strong> carries over your hazardous events and <strong>their severity</strong> to start a TARA analysis (ISO/SAE 21434).",
    "hara.bridge.2":
        "Exposure and controllability, for their part, <strong>are not carried over</strong>: an attacker picks their moment, and can neutralise the driver's recourse. On the security side, they give way to attack feasibility.",
    # --- tara page — explanatory blocks ---
    "tara.subtitle":
        "Cybersecurity threat and risk analysis, in the spirit of the ISO/SAE 21434 TARA method. Attack feasibility is rated, not guessed&nbsp;: the result is <strong>deterministic and immediate</strong>, with no artificial intelligence.",
    "tara.disclaimer":
        "The attack potential scale used here is a <strong>calibration of our own</strong>&nbsp;: it reproduces neither ISO/SAE 21434 nor ISO 18045, both licensed documents. The standard does leave each organisation to define its own method.",
    "tara.damage.note":
        "Every damage scenario carries the <strong>impact</strong> rating — four categories, all to be filled in. The threat scenarios it contains carry the <strong>attack feasibility</strong>. Risk arises from crossing the two.",
    # --- regwatch page — explanatory blocks ---
    "rw.scope.1":
        "<strong>The content of standards is never republished.</strong> They are paid-for and protected. RegWatch reports only the title, the date and the link — the body of the pages is not even downloaded.",
    "rw.scope.2":
        "<strong>The window is <span id=\"window-days\">90</span> days, fixed.</strong> The screen answers « what moved over that period », <em>not</em> « since your last visit »: the tool keeps no trace of your visits.",
    "rw.scope.3":
        "<strong>Every source shows its tier.</strong> An ISO committee and a consultancy blog are not equal, and are not presented as if they were.",
    "rw.scope.4":
        "<strong>No AI decides what is kept.</strong> Attaching a signal to a standard and grading it are deterministic, reproducible, and tested offline.",
    "rw.scope.5":
        "<strong>A silent source is flagged as such.</strong> « Nothing new » and « I could not look » are two different answers — confusing them would be the worst failing of a watch tool.",
    "rw.explain.note":
        "Optional. A model writes one sentence per signal, <strong>from the title alone</strong> — it has not read the documents and decided nothing of what is shown below. The workbook, for its part, also carries the silent sources.",
    # --- Input fields and arrival without a HARA ---
    "hara.ph.item": "e.g. Regenerative braking",
    "tara.ph.item": "e.g. On-board telematics gateway",
    "ss.ph.terms": "e.g. my-company, internal-project",
    "tara.nohara":
        "Already run a HARA analysis&nbsp;? <a href=\"/hara\">SafetyScope</a> can feed this page&nbsp;: the severity of your hazardous events becomes the «&nbsp;safety of persons&nbsp;» impact of your damage scenarios.",
    # --- ThreatScope — traceability ---
    "tara.trace.direct": "Entered directly",
    "tara.trace.hara": "HARA — {origin}{detail}",
    # --- ThreatScope — feasibility ranges ---
    "xl.tara.range": "{from} to {to}",
    "xl.tara.range.above": "{from} and above",
    # --- RegWatch — source labels ---
    "regwatch.source.intacs.label": "iNTACS — news",
    "regwatch.source.vda_spice.label": "VDA QMC — Automotive SPICE publications",
    "regwatch.source.sres.label": "SRES — automotive safety and cybersecurity commentary",
    "regwatch.source.globalautoregs.label": "GlobalAutoRegs — WP.29 documents",
    "regwatch.source.iso27ksecurity.label": "ISO27k Forum — watch on the ISO/IEC 27000 family",
    "regwatch.source.iso_tc176.label": "ISO/TC 176 — committee news",
    "regwatch.source.iso_tc176sc2.label": "ISO/TC 176/SC 2 — subcommittee news",
    # --- SentinelScan — downgrade reasons ---
    "scan.reason.template": "{detection} — template or example",
    "scan.reason.name": "{detection} — inconclusive file name",
    "scan.reason.code": "{detection} — source code or documentation",
    # --- SentinelScan — detection types ---
    "scan.detection.env": "Exposed .env file",
    "scan.detection.pem": "Private key / certificate",
    "scan.detection.credentials": "Credentials file",
    "scan.detection.config": "Configuration file",
    "scan.detection.cooccurrence": "Co-occurrence with « api_key »",
    "scan.detection.repo": "Repository mentioning the term",
    # --- RegWatch — signal levels ---
    "regwatch.signal.publication": "Publication / amendment",
    "regwatch.signal.draft": "Work in progress",
    "regwatch.signal.event": "Announcement / schedule",
    "regwatch.signal.info": "Information",
    # --- QualityCrew — agent states ---
    "qc.status.running": "Running…",
    "qc.status.done": "Done",
    # --- RegWatch — network incidents ---
    "regwatch.err.unreachable": "Unreachable ({cause}).",
    "regwatch.err.refused":
        "Access refused by the source (HTTP {code}) — anti-robot protection likely.",
    "regwatch.err.notfound": "Page not found (HTTP 404) — the URL has changed.",
    "regwatch.err.unexpected": "Unexpected response (HTTP {code}).",
    "regwatch.err.toobig": "Abnormally large response (> {ko} KB).",
    "regwatch.err.challenge":
        "The source answers with an anti-robot challenge: it is not readable by a program, and working around it is out of the question.",
    "regwatch.err.feed": "Unreadable feed: {cause}",
    "regwatch.err.notafeed": "Root « {tag} »: neither RSS nor Atom.",
    "regwatch.err.parser": "{source} — parser failed ({cause}).",
    "regwatch.err.degraded":
        "{source} — the page answers but nothing is extracted from it: the parser no longer recognises its structure.",
    "regwatch.err.line": "{source} — {message}",

    # --- Daily caps and AI availability (25/08/2026) ---
    # ⚠️ Only one of these caps is an AI cap. The other two protect a shared
    # GitHub token and courtesy towards third-party sites. Presenting them
    # together under "AI quota" would contradict the "Our stance" block.
    "status.title": "Today's caps",
    "status.group.ai": "AI features",
    "status.group.service": "Service caps",
    "status.cap.suggestions": "AI suggestions",
    "status.cap.scans": "SentinelScan scans",
    "status.cap.watches": "RegWatch runs",
    "status.uncapped.audit": "QualityCrew audit",
    "status.outage":
        "AI features are unavailable for today: the provider's daily quota is exhausted. "
        "Everything else on the site works normally.",
    "status.js.available": "available",
    "status.js.unavailable": "unavailable today",
    "status.js.remaining.one": "{n} left of {limit}",
    "status.js.remaining.other": "{n} left of {limit}",
    "status.js.resets": "Resets on {quand}.",
    "status.js.locale": "en-GB",
    "status.js.uncapped": "no daily cap",
    "status.js.failed": "Caps unavailable right now.",
    # --- CauseTrace — 8D disciplines and completeness findings ---
    "ct.discipline.d1": "D1 — Team",
    "ct.discipline.d2": "D2 — Problem description",
    "ct.discipline.d3": "D3 — Interim containment actions",
    "ct.discipline.d4": "D4 — Root causes",
    "ct.discipline.d5": "D5 — Permanent corrective actions",
    "ct.discipline.d6": "D6 — Implementation and validation",
    "ct.discipline.d7": "D7 — Prevention",
    "ct.discipline.d8": "D8 — Closure",
    "ct.gap.d1.no_owner": "No champion is named",
    "ct.gap.d2.no_what": "The part and the defect are not described",
    "ct.gap.d2.no_where": "Where it was detected is not stated",
    "ct.gap.d2.no_since": "When it first appeared is not stated",
    "ct.gap.d2.no_extent": "The extent is not quantified",
    "ct.gap.d2.no_is_not": "What is NOT affected is not stated",
    "ct.gap.d3.no_action": "No interim containment action is described",
    "ct.gap.d3.no_due_date": "The containment action has no end date",
    "ct.gap.d3.no_effectiveness_check":
        "The containment action's effectiveness is not verified",
    "ct.gap.d4.locked": "Too early: the problem is not described yet",
    "ct.gap.d4.no_occurrence_cause": "The occurrence root cause is missing",
    "ct.gap.d4.no_escape_cause": "The escape root cause is missing",
    "ct.gap.d5.locked": "Too early: the root causes are not established",
    "ct.gap.d5.no_action_on_occurrence":
        "No permanent action on the occurrence root cause",
    "ct.gap.d5.no_action_on_escape":
        "No permanent action on the escape root cause",
    "ct.gap.d6.locked": "Too early: the permanent actions are not settled",
    "ct.gap.d6.no_date": "The implementation date is missing",
    "ct.gap.d6.no_evidence": "The actions' effectiveness is not evidenced",
    "ct.gap.d7.no_systemic_update": "No reference document has been updated",
    "ct.gap.d8.premature_closure": "The case is declared closed while incomplete",
    "ct.gap.d8.not_closed": "The case is complete but not declared closed",
    "ct.gap.d8.no_closure_date": "The closure date is missing",
    # --- CauseTrace — why-chains (step 2) ---
    "ct.nature.technical": "Observed technical state",
    "ct.nature.process": "Rule, process or work instruction",
    "ct.nature.system": "Management or design system",
    "ct.nature.person": "A person and their action",
    "ct.slot.occurrence": "occurrence root cause",
    "ct.slot.escape": "escape root cause",
    "ct.gap.d4.chain_missing": "No why-chain supports this cause",
    "ct.gap.d4.chain_too_short": "The chain stops too early to establish a root cause",
    "ct.gap.d4.chain_truncated":
        "The chain exceeds the cap: the last whys were dropped",
    "ct.gap.d4.chain_step_without_nature": "One why is not qualified",
    "ct.gap.d4.chain_repeats_itself": "The chain repeats itself: one why adds nothing new",
    "ct.gap.d4.chain_ends_on_person":
        "The chain stops at a person — that is a symptom, not a cause",
    "ct.gap.d4.chain_ends_on_symptom":
        "The chain stops at a technical state — nothing there can be prevented",
    # --- CauseTrace — the deliberately mediocre example 8D (step 3) ---
    "ct.example.title": "Intermittent loss of the wheel speed signal",
    "ct.example.member.1": "Assembly shop",
    "ct.example.member.2": "Supplier quality",
    "ct.example.what": "The front left wheel speed sensor loses its signal",
    "ct.example.where": "Reported by the customer",
    "ct.example.since": "Since the end of May",
    "ct.example.how_many": "Several parts",
    "ct.example.is_not": "No other defect reported",
    "ct.example.containment": "Sorting of the parts in stock",
    "ct.example.occurrence": "Insufficient tightening of the connector",
    "ct.example.why.1": "The connector loses contact",
    "ct.example.why.2": "The applied torque was insufficient",
    "ct.example.why.3": "The operator did not follow the tightening instruction",
    "ct.example.lessons": "Team awareness session on connector tightening",
    # --- CauseTrace — /8d page (step 3) ---
    "ct.title": "CauseTrace — 8D complaint resolution",
    "ct.meta":
        "8D complaint resolution with causal analysis: the tool refuses to call a case "
        "\u00ab resolved \u00bb when it is not, and says exactly where it falls short.",
    "ct.badge": "Immediate verdict — no waiting",
    "ct.h1": "Cause<em>Trace</em>",
    "ct.subtitle":
        "Customer complaint resolution following the 8D method. This tool does not fill "
        "in eight boxes: it <strong>refuses to call a case resolved when it is not</strong>, "
        "and says exactly where it falls short. The verdict is deterministic, with no "
        "artificial intelligence.",
    "ct.note":
        "<strong>The 8D, Ishikawa and 5 Whys are in the "
        "public domain</strong>: this tool may name and implement them without restriction. It "
        "replaces neither your quality system nor your customer's requirements. What you "
        "type stays in your browser; it is sent only when you export, to build the workbook.",
    "ct.reset": "Start from a blank case",
    "ct.section.case": "Case",
    "ct.section.verdict": "Verdict",
    "ct.section.disciplines": "The eight disciplines",
    "ct.load": "Load an example",
    "ct.load.hint":
        "A realistic 8D of the kind you actually receive — and that the tool refuses to "
        "treat as closed.",
    "ct.ph.reference": "e.g. 8D-2026-014",
    "ct.ph.title": "e.g. Intermittent loss of the wheel speed signal",
    "ct.ph.why": "Why?",
    "footer.8d": "CauseTrace · your entries are sent only on export",
    "ct.f.d1.owner": "8D champion",
    "ct.f.d1.members": "Team members",
    "ct.f.d2.what": "What — the part and the defect",
    "ct.f.d2.where": "Where — place of detection",
    "ct.f.d2.since": "Since when",
    "ct.f.d2.how_many": "How many — the extent",
    "ct.f.d2.is_not": "What is NOT affected",
    "ct.f.d3.action": "Interim containment action",
    "ct.f.d3.due_date": "End date",
    "ct.f.d3.effectiveness_check": "Effectiveness verification",
    "ct.f.d4.occurrence": "Occurrence root cause",
    "ct.f.d4.escape": "Escape root cause",
    "ct.f.d5.on_occurrence": "Action on the occurrence root cause",
    "ct.f.d5.on_escape": "Action on the escape root cause",
    "ct.f.d6.implemented_on": "Implementation date",
    "ct.f.d6.evidence": "Evidence of effectiveness",
    "ct.f.d7.systemic_update": "Reference document updated",
    "ct.f.d7.lessons": "Lessons learned (optional)",
    "ct.f.d8.claimed_closed": "Declare the case closed",
    "ct.f.d8.closed_on": "Closure date",
    "ct.ph.d2.what": "e.g. the front left sensor loses its signal above 80 km/h",
    "ct.ph.d2.how_many": "e.g. 7 parts out of 1,240 inspected",
    "ct.ph.d2.is_not": "e.g. no occurrence on the front right wheel nor on the April batch",
    "ct.ph.d3.effectiveness_check": "e.g. no defect escaping the sort over 3 consecutive batches",
    "ct.ph.d4.occurrence": "Why did the defect arise?",
    "ct.ph.d4.escape": "Why did the controls in place let it through?",
    "ct.ph.d6.evidence": "e.g. 0 defects over 4,300 parts produced after implementation",
    "ct.ph.d7.systemic_update": "e.g. process FMEA and control plan updated",
    "ct.js.chain": "Why-chain — {slot}",
    "ct.js.addwhy": "Add a why",
    "ct.js.nature.none": "— nature of this why —",
    "ct.js.del": "Remove",
    "ct.js.state.complete": "complete",
    "ct.js.state.incomplete": "to complete",
    "ct.js.state.locked": "too early",
    "ct.js.verdict.blank": "blank case",
    "ct.js.verdict.hint": "Start typing, or load the example.",
    "ct.js.verdict.closable": "may be closed",
    "ct.js.verdict.ok": "All eight disciplines are complete.",
    "ct.js.verdict.open": "not resolved",
    "ct.js.verdict.count.one": "{n} point blocks closure.",
    "ct.js.verdict.count.other": "{n} points block closure.",
    "ct.js.draft": "Draft restored from this tab.",
    "ct.js.example.failed": "The example could not be loaded.",
    # --- CauseTrace — Excel export (step 4) ---
    "xl.ct.title": "8D report",
    "xl.ct.sheet.form": "8D",
    "xl.ct.sheet.gaps": "What is missing",
    "xl.ct.sheet.chains": "Why-chains",
    "xl.ct.sheet.rules": "Rules applied",
    "xl.ct.sheet.limits": "Limits",
    "xl.ct.state.closed": "CASE CLOSED on {date} — all eight disciplines are complete.",
    "xl.ct.state.draft.one":
        "DRAFT — {n} discipline still to complete. This case is not resolved.",
    "xl.ct.state.draft.other":
        "DRAFT — {n} disciplines still to complete. This case is not resolved.",
    "xl.ct.reference": "Reference",
    "xl.ct.case": "Case title",
    "xl.ct.edited": "Issued on",
    "xl.ct.seechains": "The reasoning is set out in the \u00ab Why-chains \u00bb sheet.",
    "xl.ct.col.discipline": "Discipline",
    "xl.ct.col.slot": "Cause concerned",
    "xl.ct.col.gap": "What is missing",
    "xl.ct.col.owner": "Owner",
    "xl.ct.col.due": "Due date",
    "xl.ct.col.done": "Completed on",
    "xl.ct.col.n": "No.",
    "xl.ct.col.statement": "Why",
    "xl.ct.col.nature": "Nature",
    "xl.ct.col.concludes": "May conclude",
    "xl.ct.nogaps": "Nothing to report: all eight disciplines are complete.",
    "xl.ct.chains.title": "The reasoning leading to each root cause",
    "xl.ct.chain.for": "Chain — {slot}",
    "xl.ct.chain.none": "No chain entered.",
    "xl.ct.rules.title": "The rules this report applies",
    "xl.ct.rules.terminal": "Natures that may conclude a chain",
    "xl.ct.rule.causes": "Two root causes, of equal weight",
    "xl.ct.rule.causes.detail":
        "One cause explains why the defect arose, the other why the controls in place "
        "let it through. Without the second, the next defect — which will not be the "
        "same one — will escape through the same door.",
    "xl.ct.rule.containment": "Interim containment depends on nothing",
    "xl.ct.rule.containment.detail":
        "Protecting the customer does not wait for the root cause. A containment action "
        "without an end date and an effectiveness check, however, never closes.",
    "xl.ct.rule.chain": "Where a why-chain may stop",
    "xl.ct.rule.chain.detail":
        "On a cause that can be changed. A technical state is the symptom you set out to "
        "explain; a person can neither be corrected nor prevented. A why that names a "
        "person is perfectly legitimate mid-chain — stopping there is the fault.",
    "xl.ct.rule.closure": "Order of the disciplines",
    "xl.ct.rule.closure.detail":
        "You do not look for the cause of a problem you have not described, you do not "
        "correct before establishing the cause, and you do not validate what has not "
        "been decided. A case is closed only if the first seven disciplines are.",
    "xl.ct.limits.col": "What this tool does not do",
    "xl.ct.limits.detail": "Detail",
    "xl.ct.limit.form": "It judges the form of the method, not the soundness of the content",
    "xl.ct.limit.form.detail":
        "A chain whose statements are hollow but correctly qualified passes the check. "
        "This report states that a method is complete, never that it is right.",
    "xl.ct.limit.text": "It does not read the text of the whys",
    "xl.ct.limit.text.detail":
        "The verdict rests on the declared nature of each why, never on its words. That "
        "is what makes it reproducible and independent of the language of entry.",
    "xl.ct.limit.scope": "One case, no persistence",
    "xl.ct.limit.scope.detail":
        "No tracking of several 8Ds, no history, no accounts, no indicators.",
    "xl.ct.limit.norm": "It does not replace your quality system",
    "xl.ct.limit.norm.detail":
        "The 8D is in the public domain, but your customer's "
        "requirements cannot be derived from a form.",
    "xl.ct.limit.privacy": "The case is sent only on export",
    "xl.ct.limit.privacy.detail":
        "Entry and the on-screen verdict stay in the browser. The case is sent to the "
        "server only when you export, to build this workbook; it is held in memory for "
        "the duration of the download and never written to disk.",
    "xl.ct.yes": "yes",
    "xl.ct.no": "no",
    # --- CauseTrace — export from the page (step 4) ---
    "ct.export": "Export to Excel",
    "ct.js.export.prep": "Building the workbook\u2026",
    "ct.js.export.ok": "Workbook ready, the download is starting.",
    "ct.js.export.ko": "The workbook could not be built.",
    "ct.js.export.diverged":
        "The server recounted {n} points — the workbook is what counts.",
    # --- CauseTrace — AI review (step 5) ---
    "ct.review.why": "{slot} — why {rank}",
    "err.need.written":
        "Nothing is written in this discipline yet. The AI reviews what you have "
        "written; it does not write it for you.",
    "err.fail.review":
        "The review failed. Your entries are untouched and the verdict still stands.",
    "ct.review": "AI review of this D",
    "ct.js.review.running": "Review under way\u2026",
    "ct.js.review.none": "Nothing to rephrase here, and nothing to ask for.",
    "ct.js.review.demands": "What the AI could not write, for lack of knowing",
    "ct.js.review.apply": "Apply",
    "ct.js.review.applied": "Applied",
    "ct.js.review.ko": "The review failed. Your entries are untouched.",
    # --- CauseTrace — Ishikawa 5M and discriminating questions (step 6) ---
    "ct.5m.method": "Method",
    "ct.5m.machine": "Machine",
    "ct.5m.material": "Material",
    "ct.5m.manpower": "People",
    "ct.5m.environment": "Environment",
    "ct.axis.what": "What — the part and the defect",
    "ct.axis.where": "Where — place and station",
    "ct.axis.when": "When — period and frequency",
    "ct.axis.extent": "How many — extent and trend",
    "ct.ishikawa": "Suggest leads (5M)",
    "ct.questions": "Suggest the \u00ab is / is not \u00bb questions",
    "ct.js.propose.running": "Looking for leads\u2026",
    "ct.js.propose.none": "No usable lead was suggested.",
    "ct.js.propose.ko": "The suggestion failed. Your entries are untouched.",
    "ct.js.propose.title": "Leads to check — unqualified, yours to judge",
    "ct.js.propose.use": "Add as a why",
    "ct.js.propose.used": "Added",
    "ct.js.questions.title": "What could have been affected and is not",
    "ct.js.questions.note":
        "These questions are not meant to be copied into a field: they are meant to be "
        "dug into, and it is their answer that belongs in \u00ab What is NOT affected \u00bb.",
    "err.need.problem":
        "Describe the problem first (D2). Without it there is nothing to explore.",
    "err.fail.propose":
        "The suggestion failed. Your entries are untouched and the verdict still stands.",
    # --- CauseTrace on the catalogue page (step 7) ---
    "home.ct.desc":
        "Customer complaint resolution following the 8D method. This tool does not fill in "
        "eight boxes: it refuses to call a case resolved when it is not, and says where it "
        "falls short — a missing cause, a why-chain that stops at an operator, a claimed "
        "closure.",
    "home.ct.tag.public": "Public-domain methods",
    "home.ct.pair": "Requires the escape root cause, not just the occurrence one",
    "home.ct.cta": "Open an 8D",
    "home.stance.ct":
        "<strong>In CauseTrace the AI does not fill in: it asks.</strong> An 8D report goes "
        "to the customer; an invented fact there would be far worse than a clumsy sentence. "
        "So it tightens what the engineer wrote, and anything it would like to add without "
        "knowing — a date, a number of parts — becomes a question, never a value. An "
        "Ishikawa lead taken up arrives <strong>unqualified</strong>: it is the engineer who "
        "says what it is.",
    "home.status.live": "Online",
    "home.ct.tag.why": "8D · 5 Whys",
    "ct.lock.missing": " — missing: {items}",
    "ct.lock.blocking": " — to settle first: {items}",
}
