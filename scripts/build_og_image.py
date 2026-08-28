"""Construit l'image de partage (Open Graph) du site, une par langue.

⚠️ **Pourquoi une image par langue et non une seule.** Tout le chantier i18n
a consisté à empêcher le français de survivre dans une page anglaise. Une
carte française servie en `og:image` sur `/en` serait exactement cette faute,
au seul endroit qu'un visiteur voit *avant* d'avoir ouvert le site.

⚠️ **Le gabarit ne recopie pas les couleurs du site, il les LIT.** Les valeurs
viennent de `site/style.css` : une carte qui fige `#5dcaa5` en dur cesserait
de ressembler au site au premier changement de thème, sans que rien ne le
dise. Même motif que `/hara/matrix`, qui sert la table plutôt que de la
laisser recopier.

Rendu par Chrome sans interface : le gabarit reste du HTML lisible, et le
résultat est un PNG — LinkedIn, Slack et les autres n'acceptent pas de SVG.

    .venv/bin/python3 -B scripts/build_og_image.py
"""

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
    ("QualityCrew", "green",
     '<path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>'),
    ("SentinelScan", "blue",
     '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/><path d="M11 8v3l2 2"/>'),
    ("SafetyScope", "purple",
     '<path d="M13 2 3 14h9l-1 8 10-12h-9z"/>'),
    ("ThreatScope", "coral",
     '<path d="M12 2 4 6v6c0 5 3.4 9.4 8 10 4.6-.6 8-5 8-10V6z"/><path d="M12 8v4M12 16h.01"/>'),
    ("RegWatch", "amber",
     '<circle cx="12" cy="12" r="3"/><path d="M12 3a9 9 0 0 1 9 9M12 7a5 5 0 0 1 5 5M3 21l6-6"/>'),
    ("CauseTrace", "red",
     '<path d="M2 12h20M7 12 4 7M12 12 9 7M7 12l-3 5M12 12l-3 5"/>'),
)

STANDARDS = "ASPICE · ISO 26262 · ISO/SAE 21434 · ISO/IEC 27001 · ISO 9001 · 8D"

# Le seul texte traduisible de la carte. Le reste — noms d'outils, normes,
# nom propre, domaine — est identique dans les deux langues.
WORDS = {
    "fr": {
        "title": "Outils <em>Qualité &amp; Sécurité</em>",
        "sub": "Six outils qui tournent réellement. Industrie automobile et embarqué.",
        "live": "En ligne",
    },
    "en": {
        "title": "<em>Quality &amp; Safety</em> tools",
        "sub": "Six tools that actually run. Automotive and embedded industry.",
        "live": "Online",
    },
}


def palette() -> dict[str, str]:
    """Les couleurs du site, lues dans `site/style.css`.

    ⚠️ Lire plutôt que recopier : c'est ce qui garantit que la carte partagée
    reste la carte du site.
    """
    css = (_SITE / "style.css").read_text(encoding="utf-8")
    bloc = css[css.index(":root{"):css.index("}", css.index(":root{"))]
    return dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]+)", bloc))


def template(lang: str) -> str:
    c = palette()
    mots = WORDS[lang]

    cartes = "\n".join(
        f'''<div class="tool">
              <span class="icon i-{teinte}">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                     stroke-width="2">{svg}</svg>
              </span>
              <span class="tname">{nom}</span>
            </div>'''
        for nom, teinte, svg in TOOLS)

    teintes = "\n".join(
        f'.i-{n}{{background:{c[n + "-bg"]};color:{c[n]}}}'
        for n in ("green", "blue", "purple", "coral", "amber", "red"))

    return f'''<!DOCTYPE html>
<html lang="{lang}"><head><meta charset="UTF-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{WIDTH}px;height:{HEIGHT}px}}
body{{
  background:{c['bg']};color:{c['text']};
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;
  padding:62px 68px;display:flex;flex-direction:column;justify-content:space-between;
  position:relative;overflow:hidden;
}}
/* La lueur reprend l'accent du site — discrète, elle donne de la profondeur
   au fond très sombre sans quoi la vignette paraît éteinte. */
body::before{{
  content:'';position:absolute;top:-320px;right:-220px;width:820px;height:820px;
  background:radial-gradient(circle,{c['green']}22 0%,transparent 62%);
}}
.top{{display:flex;align-items:center;justify-content:space-between;position:relative}}
.logo{{font-size:23px;font-weight:600;letter-spacing:-.4px;color:#fff}}
.logo em{{color:{c['green']};font-style:normal}}
.live{{
  display:flex;align-items:center;gap:10px;background:{c['green-bg']};
  border:1px solid {c['green-border']};color:{c['green']};
  font-size:17px;font-weight:500;padding:9px 20px;border-radius:24px;
}}
.dot{{width:9px;height:9px;border-radius:50%;background:{c['green']}}}
.mid{{position:relative}}
h1{{font-size:66px;font-weight:600;line-height:1.08;letter-spacing:-1.9px;color:#fff}}
h1 em{{color:{c['green']};font-style:normal}}
.sub{{font-size:25px;color:{c['text-muted']};margin-top:22px;letter-spacing:-.2px}}
.grid{{
  position:relative;display:grid;grid-template-columns:repeat(3,1fr);
  gap:14px;margin-top:44px;
}}
.tool{{
  display:flex;align-items:center;gap:14px;background:{c['bg-card']};
  border:1px solid {c['border']};border-radius:12px;padding:15px 18px;
}}
.icon{{
  width:40px;height:40px;border-radius:10px;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;
}}
.icon svg{{width:21px;height:21px}}
{teintes}
.tname{{font-size:21px;font-weight:500;color:#fff;letter-spacing:-.3px}}
.foot{{
  position:relative;display:flex;align-items:baseline;justify-content:space-between;
  border-top:1px solid {c['border-sub']};padding-top:24px;
}}
.norms{{font-size:18px;color:{c['text-muted']};letter-spacing:.2px}}
.url{{font-size:24px;font-weight:600;color:{c['green']};letter-spacing:-.3px}}
</style></head><body>

  <div class="top">
    <div class="logo">Dhafer <em>Bouthelja</em></div>
    <div class="live"><span class="dot"></span>{mots['live']}</div>
  </div>

  <div class="mid">
    <h1>{mots['title']}</h1>
    <div class="sub">{mots['sub']}</div>
    <div class="grid">{cartes}</div>
  </div>

  <div class="foot">
    <div class="norms">{STANDARDS}</div>
    <div class="url">qualitycrew.fr</div>
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

def build(lang: str) -> Path:
    sortie = _SITE / f"og-{lang}.png"
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / f"card-{lang}.html"
        source.write_text(template(lang), encoding="utf-8")
        subprocess.run(
            [chrome(), "--headless", "--disable-gpu", "--hide-scrollbars",
             "--force-device-scale-factor=1",
             f"--window-size={WIDTH},{HEIGHT}",
             f"--screenshot={sortie}", source.as_uri()],
            check=True, capture_output=True, timeout=120)
    return sortie


def main() -> int:
    for lang in ("fr", "en"):
        fichier = build(lang)
        taille = fichier.stat().st_size
        print(f"{fichier.relative_to(_ROOT)} — {taille // 1024} Ko")
    return 0


if __name__ == "__main__":
    sys.exit(main())
