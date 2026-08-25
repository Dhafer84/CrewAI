/* Plafonds du jour — lus depuis /ai/status, jamais réécrits ici.
   Même discipline que /hara/matrix : la page affiche, le serveur décide. */
(function () {
  'use strict';
  var boite = document.getElementById('caps');
  var bandeau = document.getElementById('ai-outage');
  if (!boite && !bandeau) { return; }

  function ligne(libelle, valeur, pourquoi) {
    var l = document.createElement('div');
    l.className = 'caps-row';
    var lib = document.createElement('span');
    lib.className = 'caps-label';
    lib.textContent = libelle;
    var val = document.createElement('span');
    val.className = 'caps-count';
    val.textContent = valeur;
    var why = document.createElement('span');
    why.className = 'caps-why';
    why.textContent = pourquoi;
    l.appendChild(lib); l.appendChild(val); l.appendChild(why);
    return l;
  }

  function rendre(d) {
    // Le bandeau seul : les pages d'outil disent que l'IA est en panne,
    // elles n'affichent pas les compteurs (c'est le rôle de la page de garde).
    if (bandeau && !d.available && d.notice) {
      bandeau.className = 'caps-outage';
      bandeau.textContent = d.notice;
    }
    if (!boite) { return; }
    if (!d.available && d.notice) {
      var av = document.createElement('div');
      av.className = 'caps-outage';
      av.textContent = d.notice;
      boite.appendChild(av);
    }
    (d.groups || []).forEach(function (g) {
      var bloc = document.createElement('div');
      bloc.className = 'caps-group';
      var tete = document.createElement('div');
      tete.className = 'caps-head';
      var titre = document.createElement('span');
      titre.className = 'caps-title';
      titre.textContent = g.label;
      tete.appendChild(titre);
      if (g.key === 'ai') {
        var etat = document.createElement('span');
        etat.className = 'caps-state' + (d.available ? '' : ' is-down');
        etat.textContent = d.available
          ? T('status.js.available') : T('status.js.unavailable');
        tete.appendChild(etat);
      }
      bloc.appendChild(tete);
      var note = document.createElement('p');
      note.className = 'caps-note';
      note.textContent = g.note;
      bloc.appendChild(note);
      (g.caps || []).forEach(function (c) {
        bloc.appendChild(ligne(
          c.label,
          T('status.js.remaining', { n: c.remaining, limit: c.limit }),
          c.note));
      });
      boite.appendChild(bloc);
    });
    (d.uncapped || []).forEach(function (u) {
      var bloc = document.createElement('div');
      bloc.className = 'caps-group';
      bloc.appendChild(ligne(u.label, T('status.js.uncapped'), u.note));
      boite.appendChild(bloc);
    });
    // ⚠️ La remise à zéro se lit dans la charge utile, elle ne se devine pas.
    // « minuit UTC » ne dit pas au visiteur si c'est dans 40 minutes ou 23 h.
    // La locale est une chaîne traduisible comme une autre.
    var r = document.createElement('p');
    r.className = 'caps-resets';
    var quand = d.resetsAt;
    try {
      quand = new Date(d.resetsAt).toLocaleString(T('status.js.locale'));
    } catch (e) { /* un format inattendu s'affiche brut plutôt que de casser */ }
    r.textContent = T('status.js.resets', { quand: quand });
    boite.appendChild(r);
  }

  fetch('/ai/status?lang=' + window.LANG)
    .then(function (r) { return r.json(); })
    .then(rendre)
    .catch(function () {
      // Un plafond qu'on n'a pas pu lire ne se devine pas : le dire.
      if (!boite) { return; }
      var p = document.createElement('p');
      p.className = 'caps-note';
      p.textContent = T('status.js.failed');
      boite.appendChild(p);
    });
}());
