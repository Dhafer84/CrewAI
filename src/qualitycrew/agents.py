"""Définition des 4 agents du crew QualityCrew."""

from crewai import Agent, LLM
from .config import LLM_MODEL, GROQ_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY


def make_llm() -> LLM:
    # LiteLLM détecte le provider depuis le préfixe du model (groq/, claude-, gpt-)
    # Les clés API sont déjà dans l'environnement via config.py / dotenv
    return LLM(model=LLM_MODEL)


def make_agents(llm: LLM) -> dict[str, Agent]:
    analyste = Agent(
        role="Analyste d'exigences logicielles",
        goal=(
            "Examiner chaque exigence du SRS et signaler les problèmes "
            "de qualité : identifiant manquant, critère d'acceptation absent, "
            "formulation ambiguë, périmètre hors-sujet, ou absence de trace amont."
        ),
        backstory=(
            "Tu es un ingénieur qualité senior spécialisé ASPICE SWE.1. "
            "Tu appliques systématiquement les critères CHK-01 à CHK-06 et "
            "tu produis des constats factuels, numérotés, rattachés à "
            "l'identifiant exact de l'exigence concernée."
        ),
        llm=llm,
        verbose=True,
    )

    verificateur = Agent(
        role="Vérificateur de conformité ASPICE / ISO 26262",
        goal=(
            "Croiser le SRS et le plan de test avec la checklist ciblée et "
            "statuer point par point : Conforme, Non conforme ou Non applicable."
        ),
        backstory=(
            "Tu es un auditeur qualité avec une expertise ASPICE (SWE.1/SWE.2) "
            "et ISO 26262 Part 6. Tu travailles méthodiquement : tu lis chaque "
            "point CHK-01 à CHK-15, tu cherches les preuves dans les documents, "
            "et tu formules un verdict motivé avec citation de l'élément de preuve."
        ),
        llm=llm,
        verbose=True,
    )

    detecteur = Agent(
        role="Détecteur de risques et d'incohérences",
        goal=(
            "Identifier les risques qualité et sûreté : exigences non testées, "
            "incohérences entre documents, exigences ISO 26262 spécifiées mais "
            "jamais vérifiées, et constats de revue ouverts non adressés."
        ),
        backstory=(
            "Tu es un expert en sûreté fonctionnelle, habitué à détecter les "
            "pièges dans les dossiers techniques embarqués. Tu relies les constats "
            "des analyses précédentes pour remonter aux risques de plus haut niveau "
            "et qualifier leur impact (Critique / Majeur / Mineur)."
        ),
        llm=llm,
        verbose=True,
    )

    redacteur = Agent(
        role="Rédacteur de rapport d'audit",
        goal=(
            "Compiler tous les constats en un rapport d'audit structuré en markdown, "
            "avec tableau de synthèse trié par sévérité et recommandations priorisées."
        ),
        backstory=(
            "Tu es un responsable qualité qui produit des rapports clairs, concis "
            "et directement actionnables. Tu synthétises sans te répéter, tu "
            "priorises par sévérité décroissante (Critique > Majeur > Mineur > "
            "Observation), et tu conclus avec les 3 actions prioritaires."
        ),
        llm=llm,
        verbose=True,
    )

    return {
        "analyste": analyste,
        "verificateur": verificateur,
        "detecteur": detecteur,
        "redacteur": redacteur,
    }
