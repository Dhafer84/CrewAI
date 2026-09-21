"""Construit l'image de partage (Open Graph) du site, une par langue.

⚠️ **Pourquoi une image par langue et non une seule.** Tout le chantier i18n
a consisté à empêcher le français de survivre dans une page anglaise. Une
carte française servie en `og:image` sur `/en` serait exactement cette faute,
au seul endroit qu'un visiteur voit *avant* d'avoir ouvert le site.

⚠️ **Le gabarit ne recopie pas les couleurs du site, il les LIT.** Les valeurs
viennent de `site/home.css`, la feuille du cadre indigo de tout le site depuis
le 21/09/2026. Une carte qui figerait une couleur en dur cesserait de
ressembler au site au premier changement de thème, sans que rien ne le dise.
Même motif que `/hara/matrix`, qui sert la table plutôt que de la laisser
recopier.

Deux familles de cartes : la carte GÉNÉRALE (accueil, À propos), une par
langue, et une carte PAR OUTIL (depuis le 21/09/2026), qui lit tout ce qu'elle
affiche sur la carte de l'outil dans la page de garde.

Rendu par Chrome sans interface : le gabarit reste du HTML lisible, et le
résultat est un PNG — LinkedIn, Slack et les autres n'acceptent pas de SVG.

    .venv/bin/python3 -B scripts/build_og_image.py
"""

import base64
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_SITE = _ROOT / "site"

# 1200 × 630 — le format que LinkedIn, Facebook et Slack attendent (1.91:1).
# En dessous de 1200 de large, LinkedIn rétrograde l'aperçu en petite vignette
# carrée : la largeur n'est pas cosmétique, elle décide de la mise en page.
WIDTH, HEIGHT = 1200, 630

CHROMES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
)

# Les six outils, dans l'ordre de la page de garde. Le SVG est celui de la
# carte, à l'identique — l'image doit montrer le site, pas s'en inspirer.
TOOLS = (
    ("QualityCrew",
     '<path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>'),
    ("SentinelScan",
     '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/><path d="M11 8v3l2 2"/>'),
    ("SafetyScope",
     '<path d="M13 2 3 14h9l-1 8 10-12h-9z"/>'),
    ("ThreatScope",
     '<path d="M12 2 4 6v6c0 5 3.4 9.4 8 10 4.6-.6 8-5 8-10V6z"/><path d="M12 8v4M12 16h.01"/>'),
    ("RegWatch",
     '<circle cx="12" cy="12" r="3"/><path d="M12 3a9 9 0 0 1 9 9M12 7a5 5 0 0 1 5 5M3 21l6-6"/>'),
    ("CauseTrace",
     '<path d="M2 12h20M7 12 4 7M12 12 9 7M7 12l-3 5M12 12l-3 5"/>'),
)

STANDARDS = "ASPICE · ISO 26262 · ISO/SAE 21434 · ISO/IEC 27001 · ISO 9001 · 8D"

# ⚠️ Les textes viennent du catalogue, pas d'ici : ce sont ceux de la page de
# garde (titre, surtitre, titre du catalogue, badge). Les recopier, ce serait
# deux versions d'une même phrase — et la carte partagée finirait par dire
# autre chose que le site. Noms d'outils, normes et domaine ne se traduisent pas.
sys.path.insert(0, str(_ROOT / "src"))
from i18n import t  # noqa: E402

# ⚠️ Le titre du catalogue porte un DÉCOMPTE (« Six outils. Cinq sans IA. ») :
# ajouter un outil oblige à relancer ce script, sans quoi l'image partagée
# annoncerait l'ancien nombre. Les tests vérifient la page, pas le PNG.
KEYS = {"title": "home.h1", "kicker": "home.hero.kicker",
        "count": "home.cat.title", "live": "home.status.live"}


def palette() -> dict[str, str]:
    """Les couleurs de la page de garde, lues dans `site/home.css`.

    ⚠️ Lire plutôt que recopier : c'est ce qui garantit que la carte partagée
    reste la carte du site. Depuis le 21/09/2026, le cadre indigo de tout le
    site vit dans home.css (jetons `--h-*`). Le préfixe est retiré à la lecture.
    """
    css = (_SITE / "home.css").read_text(encoding="utf-8")
    bloc = css[css.index(":root{"):css.index("\n}", css.index(":root{"))]
    couleurs = dict(re.findall(r"--h-([\w-]+):\s*(#[0-9a-fA-F]+)", bloc))
    couleurs["traces"] = re.search(r'--h-traces:\s*(url\(".*?"\));', bloc).group(1)
    return couleurs


def _font_face() -> str:
    """Archivo, incorporée en base64.

    ⚠️ Chrome sans interface prend sa capture dès que la page est chargée — une
    police chargée par URL peut arriver APRÈS, et l'image partirait avec une
    police de repli. Incorporée, elle est là avant le premier rendu.
    """
    donnees = base64.b64encode((_SITE / "fonts" / "archivo.woff2").read_bytes()).decode()
    return ('@font-face{font-family:"Archivo";'
            f'src:url(data:font/woff2;base64,{donnees}) format("woff2");'
            'font-weight:500 700;font-stretch:100% 125%;font-display:block}')


# Rotation et échelle des tracés, carte par carte — comme sur l'accueil, pour
# que les six tuiles ne se ressemblent pas.
_TRACES = ((12, 150), (-18, 180), (30, 140), (-6, 170), (45, 150), (-28, 190))


def _tile(i: int, nom: str, svg: str, c: dict[str, str]) -> str:
    rot, ms = _TRACES[i - 1]
    return (f'<div class="tile" style="background:{c["t" + str(i)]};--rot:{rot}deg;--ms:{ms}px">'
            '<span class="icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="2">{svg}</svg></span>'
            f'<span class="tname">{nom}</span></div>')


def template(lang: str) -> str:
    c = palette()
    mots = {cle: t(k, lang) for cle, k in KEYS.items()}
    tuiles = "\n".join(_tile(i, nom, svg, c) for i, (nom, svg) in enumerate(TOOLS, start=1))
    etape = ('<svg class="step" viewBox="0 0 76 64" preserveAspectRatio="none">'
             '<path d="M0 0C40 0 36 64 76 64H0Z" fill="currentColor"/></svg>')

    return f'''<!DOCTYPE html>
<html lang="{lang}"><head><meta charset="UTF-8"><style>
{_font_face()}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{WIDTH}px;height:{HEIGHT}px}}
body{{
  background:{c['frame']};color:{c['ink']};
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;
  padding:18px;display:flex;flex-direction:column;overflow:hidden;
}}
/* Le cran de la page de garde : l'onglet porte le nom, la bande le domaine. */
.notch{{display:flex;align-items:flex-end;height:64px;margin-bottom:-1px;position:relative;z-index:2}}
.tab{{background:{c['panel']};height:64px;border-radius:26px 0 0 0;display:flex;align-items:center;padding:0 8px 0 36px}}
.logo{{font-size:23px;font-weight:600;letter-spacing:-.4px;color:#fff}}
.logo em{{color:{c['accent-ink']};font-style:normal}}
.step{{width:76px;height:64px;color:{c['panel']};margin-left:-1px;display:block}}
.band{{flex:1;height:64px;align-self:flex-start;display:flex;align-items:center;justify-content:flex-end;gap:22px;padding-right:8px}}
.live{{display:flex;align-items:center;gap:9px;color:{c['status']};font-size:17px;font-weight:500}}
.dot{{width:9px;height:9px;border-radius:50%;background:{c['status']}}}
.url{{font-size:22px;font-weight:600;color:{c['frame-ink']};letter-spacing:-.3px}}
.panel{{
  flex:1;background:{c['panel']};border-radius:0 26px 26px 26px;position:relative;z-index:1;
  display:grid;grid-template-columns:minmax(0,1fr) 470px;gap:40px;padding:40px 40px 40px 52px;
}}
.left{{display:flex;flex-direction:column;justify-content:space-between}}
.chip{{
  display:inline-flex;align-items:center;gap:9px;border:1px solid {c['line']};
  border-radius:999px;padding:6px 15px;font-size:14px;font-weight:500;letter-spacing:.09em;
  text-transform:uppercase;color:{c['ink-2']};
}}
.chip::before{{content:'';width:7px;height:7px;border-radius:50%;background:{c['accent-ink']}}}
h1,.count,.tname{{font-family:"Archivo",sans-serif;font-weight:600;text-transform:uppercase}}
h1{{font-size:62px;font-stretch:125%;line-height:.95;letter-spacing:-.015em;color:{c['ink']};margin-top:26px}}
h1 em,.count em{{color:{c['accent-ink']};font-style:normal}}
.count{{font-size:25px;font-stretch:112%;color:{c['ink-2']};margin-top:22px;letter-spacing:-.01em}}
.norms{{font-size:16px;color:{c['ink-2']};letter-spacing:.2px}}
.tiles{{display:grid;grid-template-columns:1fr 1fr;grid-auto-rows:1fr;gap:12px}}
.tile{{
  position:relative;overflow:hidden;isolation:isolate;border-radius:16px;padding:14px 16px;
  display:flex;flex-direction:column;justify-content:space-between;
}}
/* Les tracés de circuit imprimé de l'accueil, lus dans home.css. */
.tile::before{{
  content:'';position:absolute;inset:-40%;z-index:-1;background:{c['accent']};filter:brightness(.34);
  -webkit-mask:{c['traces']} 0 0/var(--ms) var(--ms) repeat;transform:rotate(var(--rot));
}}
.icon{{
  width:38px;height:38px;border-radius:50%;display:grid;place-items:center;color:{c['tile-ink']};
  background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.18);
}}
.icon svg{{width:19px;height:19px}}
.tname{{font-size:18px;font-stretch:112%;color:{c['tile-ink']};letter-spacing:-.01em}}
</style></head><body>

  <div class="notch">
    <div class="tab"><div class="logo">Dhafer <em>Bouthelja</em></div></div>
    {etape}
    <div class="band">
      <div class="live"><span class="dot"></span>{mots['live']}</div>
      <div class="url">qualitycrew.fr</div>
    </div>
  </div>

  <div class="panel">
    <div class="left">
      <div>
        <span class="chip">{mots['kicker']}</span>
        <h1>{mots['title']}</h1>
        <div class="count">{mots['count']}</div>
      </div>
      <div class="norms">{STANDARDS}</div>
    </div>
    <div class="tiles">{tuiles}</div>
  </div>

</body></html>'''


def chrome() -> str:
    for chemin in CHROMES:
        if Path(chemin).exists():
            return chemin
    trouve = shutil.which("chromium") or shutil.which("google-chrome")
    if trouve:
        return trouve
    raise SystemExit("Aucun Chrome/Chromium trouvé — impossible de rendre le PNG.")


def _capture(html: str, sortie: Path) -> Path:
    """Rend une page HTML en PNG de 1200 × 630 avec Chrome sans interface."""
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "carte.html"
        source.write_text(html, encoding="utf-8")
        subprocess.run(
            [chrome(), "--headless", "--disable-gpu", "--hide-scrollbars",
             "--force-device-scale-factor=1",
             f"--window-size={WIDTH},{HEIGHT}",
             # Laisse le rendu se stabiliser avant la capture.
             "--virtual-time-budget=3000",
             f"--screenshot={sortie}", source.as_uri()],
            check=True, capture_output=True, timeout=120)
    return sortie


def build(lang: str) -> Path:
    return _capture(template(lang), _SITE / f"og-{lang}.png")


# --------------------------------------------------------------------------
# Une carte PAR OUTIL (21/09/2026)
# --------------------------------------------------------------------------
# Un lien vers /hara partagé sur LinkedIn montre SafetyScope, pas la carte
# générale. ⚠️ Tout ce qu'affiche la carte d'un outil est LU sur sa carte de la
# page de garde — icône, nom, normes, place de l'IA, phrase courte, mention
# d'enchaînement, bouton, teinte de la tuile. Recopier ces six fiches ici, ce
# serait six occasions de laisser la carte partagée dire autre chose que le site.

_CARTE = re.compile(
    r'<a class="tool-card[^"]*" href="(?P<chemin>/[^"]+)" style="--tile:var\(--h-(?P<teinte>t\d)\)[^"]*">'
    r'(?P<corps>.*?)</a>', re.S)


def cartes_accueil() -> list[dict]:
    """Les six cartes d'outil de la page de garde, dans leur ordre."""
    accueil = (_SITE / "index.html").read_text(encoding="utf-8")
    cartes = []
    for m in _CARTE.finditer(accueil):
        corps = m.group("corps")
        def cle(motif: str) -> str | None:
            trouve = re.search(motif, corps)
            return trouve.group(1) if trouve else None
        cartes.append({
            "chemin": m.group("chemin"),
            "teinte": m.group("teinte"),
            "icone": re.search(r'<span class="tool-icon">(<svg.*?</svg>)', corps, re.S).group(1),
            "nom": cle(r'<h3 class="tool-name">([^<]+)</h3>'),
            "normes": cle(r'<span class="tool-norms">([^<]+)</span>'),
            "ia": cle(r'<span class="tool-ai" data-i18n="([\w.]+)"'),
            "phrase": cle(r'<span class="tool-desc" data-i18n="([\w.]+)"'),
            "enchainement": cle(r'<span class="tool-pair"><svg.*?</svg><span data-i18n="([\w.]+)"'),
            "bouton": cle(r'<span class="tool-cta"><span data-i18n="([\w.]+)"'),
        })
    manquants = [c["chemin"] for c in cartes if not all(c[k] for k in ("nom", "normes", "ia", "phrase", "bouton"))]
    if len(cartes) != 6 or manquants:
        raise SystemExit(f"La page de garde a changé de forme : {len(cartes)} cartes, incomplètes : {manquants}")
    return cartes


def tool_template(carte: dict, lang: str) -> str:
    c = palette()
    # « SafetyScope » → Safety + Scope : la seconde moitié prend l'accent, comme
    # le titre de la page de l'outil.
    debut, fin = re.match(r"([A-Z][a-z]+)(\w+)", carte["nom"]).groups()
    enchainement = ""
    if carte["enchainement"]:
        enchainement = f'<div class="pair"><span class="arrow">→</span>{t(carte["enchainement"], lang)}</div>'
    grande_icone = carte["icone"].replace('aria-hidden="true"', "")
    etape = ('<svg class="step" viewBox="0 0 76 64" preserveAspectRatio="none">'
             '<path d="M0 0C40 0 36 64 76 64H0Z" fill="currentColor"/></svg>')

    return f'''<!DOCTYPE html>
<html lang="{lang}"><head><meta charset="UTF-8"><style>
{_font_face()}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{WIDTH}px;height:{HEIGHT}px}}
body{{
  background:{c['frame']};color:{c['ink']};
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;
  padding:18px;display:flex;flex-direction:column;overflow:hidden;
}}
.notch{{display:flex;align-items:flex-end;height:64px;margin-bottom:-1px;position:relative;z-index:2}}
.tab{{background:{c['panel']};height:64px;border-radius:26px 0 0 0;display:flex;align-items:center;padding:0 8px 0 36px}}
.logo{{font-size:23px;font-weight:600;letter-spacing:-.4px;color:#fff}}
.logo em{{color:{c['accent-ink']};font-style:normal}}
.step{{width:76px;height:64px;color:{c['panel']};margin-left:-1px;display:block}}
.band{{flex:1;height:64px;align-self:flex-start;display:flex;align-items:center;justify-content:flex-end;gap:22px;padding-right:8px}}
.live{{display:flex;align-items:center;gap:9px;color:{c['status']};font-size:17px;font-weight:500}}
.dot{{width:9px;height:9px;border-radius:50%;background:{c['status']}}}
.url{{font-size:22px;font-weight:600;color:{c['frame-ink']};letter-spacing:-.3px}}
.panel{{
  flex:1;background:{c['panel']};border-radius:0 26px 26px 26px;position:relative;z-index:1;
  display:grid;grid-template-columns:minmax(0,1fr) 400px;gap:44px;padding:44px 40px 40px 52px;
}}
.left{{display:flex;flex-direction:column;justify-content:space-between}}
.meta{{display:flex;flex-wrap:wrap;align-items:center;gap:10px}}
.chip{{
  display:inline-flex;align-items:center;gap:9px;border:1px solid {c['line']};border-radius:999px;
  padding:6px 15px;font-size:15px;font-weight:500;letter-spacing:.06em;color:{c['ink-2']};
}}
.chip.norms::before{{content:'';width:7px;height:7px;border-radius:50%;background:{c['accent-ink']}}}
.chip.ia{{text-transform:uppercase;font-size:13px;letter-spacing:.09em}}
h1{{
  font-family:"Archivo",sans-serif;font-weight:600;text-transform:uppercase;font-stretch:112%;
  font-size:64px;line-height:.95;letter-spacing:-.015em;color:{c['ink']};margin-top:26px;white-space:nowrap;
}}
h1 em{{color:{c['accent-ink']};font-style:normal}}
.phrase{{font-size:28px;line-height:1.3;color:{c['ink']};margin-top:20px;text-wrap:balance}}
.pair{{display:flex;gap:10px;font-size:18px;color:{c['ink-2']};margin-top:16px}}
.pair .arrow{{color:{c['accent-ink']}}}
.cta{{
  align-self:flex-start;display:inline-flex;align-items:center;gap:12px;background:{c['accent']};
  color:{c['on-accent']};font-size:20px;font-weight:600;padding:14px 26px;border-radius:999px;
}}
.tile{{
  position:relative;overflow:hidden;isolation:isolate;border-radius:22px;background:{c[carte['teinte']]};
  display:grid;place-items:center;
}}
/* Les tracés de circuit imprimé de l'accueil, lus dans home.css. */
.tile::before{{
  content:'';position:absolute;inset:-40%;z-index:-1;background:{c['accent']};filter:brightness(.36);
  -webkit-mask:{c['traces']} 0 0/180px 180px repeat;transform:rotate(-14deg);
}}
.big{{
  width:188px;height:188px;border-radius:50%;display:grid;place-items:center;color:{c['tile-ink']};
  background:rgba(255,255,255,.07);border:1.5px solid rgba(255,255,255,.2);
}}
.big svg{{width:92px;height:92px;stroke-width:1.6}}
</style></head><body>

  <div class="notch">
    <div class="tab"><div class="logo">Dhafer <em>Bouthelja</em></div></div>
    {etape}
    <div class="band">
      <div class="live"><span class="dot"></span>{t("home.status.live", lang)}</div>
      <div class="url">qualitycrew.fr</div>
    </div>
  </div>

  <div class="panel">
    <div class="left">
      <div>
        <div class="meta"><span class="chip norms">{carte['normes']}</span><span class="chip ia">{t(carte['ia'], lang)}</span></div>
        <h1>{debut}<em>{fin}</em></h1>
        <div class="phrase">{t(carte['phrase'], lang)}</div>
        {enchainement}
      </div>
      <div class="cta">{t(carte['bouton'], lang)} <span>→</span></div>
    </div>
    <div class="tile"><span class="big">{grande_icone}</span></div>
  </div>

</body></html>'''


def build_tool(carte: dict, lang: str) -> Path:
    # Même nom que celui que choisit api.render.og_image_for — le test
    # test_each_tool_page_shares_its_own_card vérifie que les deux s'accordent.
    return _capture(tool_template(carte, lang), _SITE / f"og-{carte['chemin'].strip('/')}-{lang}.png")


def main() -> int:
    fichiers = [build(lang) for lang in ("fr", "en")]
    fichiers += [build_tool(carte, lang) for carte in cartes_accueil() for lang in ("fr", "en")]
    for fichier in fichiers:
        print(f"{fichier.relative_to(_ROOT)} — {fichier.stat().st_size // 1024} Ko")
    return 0


if __name__ == "__main__":
    sys.exit(main())
