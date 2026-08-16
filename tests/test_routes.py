"""Test de fumée des routes HTTP — le contrat entre les moteurs et les pages.

Exécutable sans pytest :  .venv/bin/python3 -B tests/test_routes.py

Le drapeau `-B` n'est pas décoratif — voir l'en-tête de `tests/test_asil.py`.

Les autres suites vérifient les moteurs. Celle-ci vérifie ce que le navigateur
reçoit réellement — la couche qui, jusqu'ici, n'était contrôlée qu'à la main.

**Ce qu'elle attrape et qu'aucune autre n'attraperait — mesuré, pas supposé** :
tout ce qui vit dans `api/main.py`, la couche de composition. Retirer la ligne
qui joint `treatment_scales()` au barème laisse les **33 tests de moteurs au
vert** et ne casse que cette suite — la page, elle, tomberait chez le visiteur.
Même chose pour une route non enregistrée, un montage `/static` déplacé, un
rapport servi au mauvais client.

En revanche, une clé renommée **à l'intérieur** d'un moteur est déjà attrapée
par les tests de ce moteur : la liste de chemins ci-dessous est une ceinture en
plus des bretelles, pas la seule protection.

⚠️ **Aucun appel réseau ici.** Ni LLM ni API GitHub : on ne teste que les
routes qui n'en font pas, plus les branches de refus des routes qui en font.
Une suite de tests qui dépend d'Internet ne se lance plus le jour où on en a
besoin.
"""

import sys
from io import BytesIO
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

import openpyxl  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402

PAGES = {
    "/": "tools-grid",
    "/qualitycrew": "QualityCrew",
    "/sentinelscan": "SentinelScan",
    "/hara": "/hara/matrix",
    "/tara": "/tara/scales",
}

# Contrat de /tara/scales : chaque chemin est réellement lu par site/tara.html.
# Renommer une de ces clés casse la page sans casser aucun test de moteur.
TARA_CONTRACT = [
    "calibration",
    "maxPotential",
    "feasibilityByPotential",
    "feasibilityOrder",
    "impactOrder",
    "impactCategories.safety",
    "impactCategories.financial",
    "impactCategories.operational",
    "impactCategories.privacy",
    "parameters.time.label",
    "parameters.time.levels",
    "parameters.expertise.levels",
    "parameters.knowledge.levels",
    "parameters.window.levels",
    "parameters.equipment.levels",
    "risk",
    "riskRange",
    "haraBridge.severityToImpact",
    "haraBridge.transfers",
    "haraBridge.doesNotTransfer",
    "haraBridge.why.severity",
    "haraBridge.why.exposure",
    "haraBridge.why.controllability",
    "haraBridge.why.replacement",
    "treatment.order",
    "treatment.decisionThreshold",
    "treatment.options.reduce.label",
    "treatment.options.reduce.hint",
    "treatment.options.reduce.requires",
    "treatment.options.reduce.prompt",
]

# Contrat de /hara/matrix : lu par site/hara.html.
HARA_CONTRACT = [
    "table",
    "order",
    "decompositions",
    "labels.severity",
    "labels.exposure",
    "labels.controllability",
]


def dig(data, path):
    """Descend un chemin pointé, ou lève une AssertionError explicite."""
    current = data
    for step in path.split("."):
        assert isinstance(current, dict), f"« {path} » : « {step} » n'est pas dans un objet"
        assert step in current, f"« {path} » : clé « {step} » absente"
        current = current[step]
    return current


def client(ip="10.0.0.1"):
    return TestClient(app, headers={"X-Real-IP": ip})


def test_every_page_is_served():
    with client() as c:
        for path, marker in PAGES.items():
            resp = c.get(path)
            assert resp.status_code == 200, f"{path} → {resp.status_code}"
            assert "text/html" in resp.headers["content-type"], f"{path} n'est pas du HTML"
            assert marker in resp.text, f"{path} ne contient pas « {marker} »"


def test_stylesheet_is_reachable_at_the_path_pages_use():
    """Les pages demandent /static/style.css — le montage doit y répondre."""
    with client() as c:
        resp = c.get("/static/style.css")
        assert resp.status_code == 200
        assert ".tools-grid" in resp.text


def test_hara_matrix_keeps_its_contract():
    with client() as c:
        data = c.get("/hara/matrix").json()
    for path in HARA_CONTRACT:
        dig(data, path)
    # Valeurs témoins : si la table changeait, la page mentirait.
    assert data["table"]["S3E4C3"] == "D"
    assert data["table"]["S0E4C3"] == "QM"
    assert data["order"][-1] == "D"


def test_tara_scales_keeps_its_contract():
    with client() as c:
        resp = c.get("/tara/scales")
        assert resp.status_code == 200
        data = resp.json()

    for path in TARA_CONTRACT:
        valeur = dig(data, path)
        assert valeur or valeur == 0, f"« {path} » est vide"

    # Formes attendues par la page, pas seulement présence des clés.
    assert len(data["parameters"]) == 5
    assert len(data["feasibilityByPotential"]) == data["maxPotential"] + 1
    assert len(data["risk"]) == len(data["impactOrder"]) * len(data["feasibilityOrder"])
    assert data["risk"]["I3F3"] == 5
    assert data["risk"]["I0F0"] == 1
    assert data["haraBridge"]["severityToImpact"] == [0, 1, 2, 3]
    assert data["treatment"]["options"]["reduce"]["requires"] == "goal"

    # Chaque niveau de chaque paramètre porte ce que la page affiche.
    for key, parameter in data["parameters"].items():
        for level in parameter["levels"]:
            for champ in ("value", "label", "points"):
                assert champ in level, f"parameters.{key} : « {champ} » manque"


def test_hara_report_roundtrip_and_no_formula():
    """Le chemin d'export complet, tel que le navigateur l'emprunte."""
    charge = "=cmd|'/c calc'!A1"
    with client() as c:
        resp = c.post("/hara/report", json={"item": charge, "events": [
            {"malfunction": charge, "situation": "S",
             "severity": 3, "exposure": 4, "controllability": 3}]})
        assert resp.status_code == 200, resp.text
        report_id = resp.json()["report_id"]

        xlsx = c.get(f"/hara/report/{report_id}.xlsx")
        assert xlsx.status_code == 200
        assert "spreadsheet" in xlsx.headers["content-type"]

    workbook = openpyxl.load_workbook(BytesIO(xlsx.content))
    formules = [
        f"{sheet.title}!{cell.coordinate}"
        for sheet in workbook.worksheets
        for row in sheet.iter_rows()
        for cell in row
        if cell.data_type == "f"
    ]
    assert not formules, f"des formules sont servies par la route : {formules}"


def test_a_report_is_not_served_to_another_client():
    """Un classeur porte des données de travail : il n'appartient qu'à son auteur."""
    with client("10.0.0.1") as auteur:
        report_id = auteur.post("/hara/report", json={"item": "Item", "events": [
            {"malfunction": "M", "situation": "S",
             "severity": 3, "exposure": 4, "controllability": 3}]}).json()["report_id"]

    with client("10.0.0.2") as autre:
        assert autre.get(f"/hara/report/{report_id}.xlsx").status_code == 404


def test_unknown_report_id_is_a_404_not_a_crash():
    with client() as c:
        assert c.get("/hara/report/inexistant.xlsx").status_code == 404


def test_malformed_report_payload_is_refused_cleanly():
    """Un corps invalide doit donner un 4xx, jamais une erreur serveur."""
    mauvais = [
        {"item": "x", "events": [{"malfunction": "M", "situation": "S", "severity": 9,
                                  "exposure": 4, "controllability": 3}]},
        {"item": "x", "events": [{"malfunction": "M"}]},
        {"item": "x", "events": "pas une liste"},
    ]
    with client() as c:
        for corps in mauvais:
            code = c.post("/hara/report", json=corps).status_code
            assert 400 <= code < 500, f"{corps} → {code}, attendu un 4xx"


def test_scan_prepare_validates_without_touching_the_network():
    with client() as c:
        generique = c.post("/scan/prepare", json={"keywords": ["api"]})
        assert generique.status_code == 400
        assert "error" in generique.json()

        bon = c.post("/scan/prepare", json={"keywords": ["qualitycrew"]})
        assert bon.status_code == 200
        assert bon.json()["token"]
        assert bon.json()["keywords"] == ["qualitycrew"]


def test_an_unknown_token_never_starts_a_scan():
    """Jeton inconnu ou rejoué : même branche, et aucun appel à GitHub."""
    with client() as c:
        resp = c.get("/scan/stream?t=jeton-invente")
        assert resp.status_code == 200
        assert '"type": "error"' in resp.text
        assert "expir" in resp.text


def test_a_token_is_single_use_client_bound_and_typed():
    """Usage unique, lié au client, et cloisonné par `kind`.

    Testé directement sur le magasin, **pas** en ouvrant le flux : consommer un
    jeton valide via /scan/stream lancerait un vrai scan GitHub. Une suite de
    tests n'a rien à faire dans le quota d'API partagé — et le jour où le
    réseau est coupé, elle doit tourner quand même.
    """
    from api.main import _consume_token, _issue_token

    charge = {"keywords": ["qualitycrew"]}

    token = _issue_token("client-a", "scan", charge)
    assert _consume_token(token, "client-a", "scan") == charge, "le bon client doit être servi"
    assert _consume_token(token, "client-a", "scan") is None, "un rejeu doit être refusé"
    assert _consume_token("jamais-emis", "client-a", "scan") is None, "jeton inconnu"

    # Mauvais client : refusé — et le jeton est **brûlé au passage**, parce que
    # `_consume_token` retire avant de valider. Choix « fail closed » assumé :
    # une tentative ratée ne laisse rien derrière elle.
    autre = _issue_token("client-a", "scan", charge)
    assert _consume_token(autre, "client-b", "scan") is None, "mauvais client"
    assert _consume_token(autre, "client-a", "scan") is None, "le jeton doit être brûlé"

    # Cloisonnement par type : une route ne sert que ce qu'elle produit.
    typed = _issue_token("client-a", "hara-report", {"x": 1})
    assert _consume_token(typed, "client-a", "scan") is None, "mauvais kind"


def test_unknown_route_is_a_404():
    with client() as c:
        assert c.get("/nexistepas").status_code == 404


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"  ok    {test.__name__}")
        except AssertionError as exc:
            failures += 1
            print(f"  ÉCHEC {test.__name__} : {exc}")
    print(f"\n{len(tests) - failures}/{len(tests)} tests passés")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
