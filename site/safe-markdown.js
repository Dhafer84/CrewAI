/* ============================================================
   MARKDOWN SANS HTML — la seconde ligne de défense (22/09/2026)

   `marked` ne nettoie RIEN : du HTML brut dans le markdown ressort tel quel,
   et un lien `javascript:` reste un lien. Or les deux pages qui s'en servent
   affichent du texte qu'elles n'ont pas écrit :
     - SentinelScan, des chemins et des noms venus de dépôts GitHub PUBLICS —
       c'est là que l'audit de sécurité du 22/09/2026 a trouvé une XSS stockée ;
     - QualityCrew, la prose d'un modèle de langage.

   Le serveur échappe déjà le texte de tiers (`sentinelscan.report.md_text`).
   Ce fichier ne s'y fie pas : ici, le HTML brut est AFFICHÉ comme du texte,
   un lien ne pointe que vers http(s), mailto ou une adresse du site, et une
   image n'est jamais chargée — seul son texte alternatif paraît. Les rapports
   n'en ont aucun besoin, et une image distante est un mouchard.

   UN seul fichier pour les deux pages : une protection recopiée deux fois
   finit toujours par diverger — le motif de `xlsxsafe`.
   Chargé JUSTE APRÈS marked, avant le script de la page.
   ============================================================ */
(function () {
  if (!window.marked) return;

  function esc(texte) {
    return String(texte == null ? '' : texte).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  // http(s), mailto, ancre, ou chemin du site (« / » mais pas « // »).
  var SUR = /^(https?:|mailto:|#|\/(?!\/))/i;

  marked.use({
    renderer: {
      html: function (brut) {
        return esc(typeof brut === 'string' ? brut : (brut && (brut.raw || brut.text)));
      },
      link: function (href, title, texte) {
        if (!href || !SUR.test(String(href).trim())) return texte;
        return '<a href="' + esc(href) + '"' + (title ? ' title="' + esc(title) + '"' : '') +
               ' rel="noopener noreferrer">' + texte + '</a>';
      },
      image: function (href, title, texte) {
        return esc(texte);
      }
    }
  });

  window.safeMarkdown = function (md) { return marked.parse(md || ''); };
})();
