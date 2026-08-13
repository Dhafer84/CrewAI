# Checklist de conformité ciblée — ASPICE (SWE.1/SWE.2) & ISO 26262 Part 6

> Sous-ensemble volontairement restreint et défendable, adapté à une
> première passe d'audit automatisée sur un SRS + plan de test.
> Ne prétend pas couvrir l'intégralité des référentiels.

## A. Qualité des exigences (ASPICE SWE.1)

- **CHK-01** — Chaque exigence est identifiée de manière unique.
- **CHK-02** — Chaque exigence est vérifiable / testable (formulation
  mesurable, critère d'acceptation présent).
- **CHK-03** — Chaque exigence est non ambiguë (pas de termes vagues du type
  « rapidement », « agréable », « rapide » sans valeur mesurable).
- **CHK-04** — Chaque exigence exprime un besoin unique (pas de "et" masquant
  deux exigences distinctes).
- **CHK-05** — Chaque exigence relève bien du périmètre du module (pas de
  besoin hors sujet).

## B. Traçabilité (ASPICE SWE.1 / SWE.2)

- **CHK-06** — Chaque exigence logicielle possède une trace amont vers une
  exigence système (ou une justification d'absence).
- **CHK-07** — Chaque exigence est couverte par au moins un cas de test.
- **CHK-08** — Chaque cas de test référence au moins une exigence existante.
- **CHK-09** — La matrice de couverture déclarée est cohérente avec le
  contenu réel du SRS et du plan de test.

## C. Sûreté fonctionnelle (ISO 26262 Part 6, sélection)

- **CHK-10** — Les fonctions de sécurité (détection de défaut, repli sûr,
  action de protection) sont spécifiées avec un comportement déterministe.
- **CHK-11** — Les temps de réponse des fonctions critiques de sécurité sont
  bornés et vérifiables.
- **CHK-12** — Le comportement en cas de défaillance capteur / entrée
  invalide est spécifié (état de repli sûr).
- **CHK-13** — Les mesures liées à une même fonction de sécurité sont
  cohérentes entre elles (seuils, hystérésis, redondance).

## D. Complétude documentaire

- **CHK-14** — Le plan de test couvre toutes les exigences du SRS (absence de
  trous de couverture).
- **CHK-15** — Les constats de revue ouverts sont tracés et rattachés à une
  exigence identifiable.
