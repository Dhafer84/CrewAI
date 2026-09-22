/* ============================================================
   PARTI PRIS — les deux figures animées de l'accueil (22/09/2026)

   À gauche, l'anneau 5/6 : chaque outil est une ligne ; les outils qui
   rendent leur résultat sans IA remplissent un cran de l'anneau. Trois états,
   pas deux — une première version disait « sans IA » pour cinq outils, alors
   que quatre en ont une, facultative :
     aucune IA        point plein, cran plein ;
     IA facultative   point creux, pastille « IA » branchée À CÔTÉ du trajet
                      (le résultat ne passe pas par elle), cran évidé ;
     IA requise       le point bute sur une barrière, le cran reste vide.

   À droite, le pont HARA → TARA : S, E et C d'un événement redouté partent
   vers la TARA ; E et C butent sur un mur, S traverse et allume sa rangée
   d'impact ; la faisabilité arrive d'ailleurs — de l'attaque ; la case
   croisée donne le risque.

   ⚠️ RIEN n'est recopié ici :
     - les outils, leur nom et leur mode d'IA sont LUS sur les cartes de
       l'accueil (`.tool-name`, `.tool-ai[data-i18n]`) — ajouter un outil
       ajoute une ligne à l'anneau et change son décompte ;
     - l'ASIL vient de /hara/matrix, l'impact, la faisabilité et le risque de
       /tara/scales, les libellés du catalogue. Seul l'EXEMPLE est choisi ici
       (S3 E4 C2, un dongle à 6 points), et le texte pour lecteur d'écran le
       décrit — test_the_stance_figures_read_their_data le verrouille.

   Joué une seule fois, quand la section entre à l'écran — pas de boucle : les
   chiffres sont fixes, les faire tourner simulerait une activité. État final
   direct si le visiteur demande moins d'animations. Aucune `opacity`.
   ============================================================ */
(function () {
  var box = document.getElementById('stance');
  if (!box || !window.T) return;

  var NS = 'http://www.w3.org/2000/svg';
  var EASE = 'cubic-bezier(.22,1,.36,1)';
  var calm = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var ease = function (t) { return 1 - Math.pow(1 - t, 3); };

  function mk(svg, tag, attrs, text) {
    var n = document.createElementNS(NS, tag);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    if (text != null) n.textContent = text;
    svg.appendChild(n);
    return n;
  }

  /* Un trajet qui se trace derrière son point. */
  function Mover(svg, d, cls) {
    mk(svg, 'path', { d: d, class: 'pp-rail' });
    this.trail = mk(svg, 'path', { d: d, class: 'pp-trail' + (cls.ai ? ' is-ai' : '') });
    this.len = this.trail.getTotalLength();
    this.trail.style.strokeDasharray = this.len;
    this.trail.style.strokeDashoffset = this.len;
    var p = this.trail.getPointAtLength(0);
    this.dot = mk(svg, 'circle', { cx: p.x, cy: p.y, r: 4,
      class: 'pp-dot' + (cls.ai ? ' is-ai' : '') + (cls.opt ? ' is-opt' : '') });
  }
  Mover.prototype.at = function (t) {
    var p = this.trail.getPointAtLength(this.len * t);
    this.dot.setAttribute('cx', p.x); this.dot.setAttribute('cy', p.y);
    this.trail.style.strokeDashoffset = this.len * (1 - t);
  };
  Mover.prototype.vanish = function (instant) {
    if (instant) this.dot.style.transform = 'scale(0)';
    else this.dot.animate([{ transform: 'scale(1)' }, { transform: 'scale(0)' }], { duration: 160, fill: 'forwards' });
  };

  /* Des étapes {at, dur, step(t), end(instant)}, jouées sur rAF — ou d'un coup. */
  function run(steps, instant) {
    if (instant) {
      steps.forEach(function (s) { if (s.step) s.step(1); if (s.end) s.end(true); });
      return;
    }
    var t0 = null;
    function frame(now) {
      if (t0 === null) t0 = now;
      var e = now - t0, busy = false;
      steps.forEach(function (s) {
        if (s.done) return;
        busy = true;
        if (e < s.at) return;
        var t = Math.min(1, (e - s.at) / (s.dur || 1));
        if (s.step) s.step(ease(t));
        if (t === 1) { s.done = true; if (s.end) s.end(false); }
      });
      if (busy) requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  /* Les outils, lus sur les cartes de l'accueil. */
  var MODES = { 'home.ai.required': 'required', 'home.ai.optional': 'optional', 'home.ai.none': 'none' };
  var tools = Array.prototype.map.call(document.querySelectorAll('#toolRail .tool-card'), function (c) {
    var ai = c.querySelector('.tool-ai');
    return {
      name: (c.querySelector('.tool-name') || {}).textContent || '',
      href: c.getAttribute('href') || '',
      mode: MODES[ai && ai.getAttribute('data-i18n')] || 'none'
    };
  });
  function toolName(href) {
    var t = tools.filter(function (x) { return x.href.replace(/^\/en/, '') === href; })[0];
    return t ? t.name : '';
  }

  /* =====================================================================
     L'anneau
     ===================================================================== */
  function ringSteps() {
    var svg = document.getElementById('stanceRing');
    svg.textContent = '';
    var total = tools.length;
    var CX = 318, CY = 98, R = 56, X0 = 122, X1 = 214, GATE = 212, OPT_X = 168;
    var ENTRY = CX - R - 6;
    var rowGap = Math.min(32, 176 / Math.max(1, total - 1));
    function arc(a0, a1) {
      var r = function (a) { return (a - 90) * Math.PI / 180; };
      return 'M' + [CX + R * Math.cos(r(a0)), CY + R * Math.sin(r(a0))] +
             'A' + R + ' ' + R + ' 0 0 1 ' + [CX + R * Math.cos(r(a1)), CY + R * Math.sin(r(a1))];
    }

    var free = tools.filter(function (t) { return t.mode !== 'required'; }).length;
    var step = 360 / total, gap = 5, segs = [];
    for (var s = 0; s < total; s++) {
      var d = arc(s * step + gap / 2, (s + 1) * step - gap / 2);
      mk(svg, 'path', { d: d, class: 'pp-slot' + (s >= free ? ' is-ai' : '') });
      if (s < free) {
        var seg = mk(svg, 'path', { d: d, class: 'pp-seg' });
        var L = seg.getTotalLength();
        seg.style.strokeDasharray = L; seg.style.strokeDashoffset = L;
        segs.push({ el: seg, len: L });
      }
    }
    var count = mk(svg, 'text', { x: CX, y: CY + 4, 'text-anchor': 'middle', class: 'pp-count' }, '0/' + total);
    // « sans IA » seul serait faux : ce qui est compté, c'est le RÉSULTAT.
    mk(svg, 'text', { x: CX, y: CY + 19, 'text-anchor': 'middle', class: 'pp-sub' }, T('home.fig.result'));
    mk(svg, 'text', { x: CX, y: CY + 30, 'text-anchor': 'middle', class: 'pp-sub' }, T('home.fig.noai'));

    var rows = [], slot = 0;
    tools.forEach(function (t, i) {
      var y = 18 + i * rowGap, ai = t.mode === 'required', opt = t.mode === 'optional';
      mk(svg, 'text', { x: 0, y: y + 3.5, class: 'pp-name' }, t.name.toUpperCase());
      var d = ai ? 'M' + X0 + ' ' + y + 'H' + (GATE - 6)
                 : 'M' + X0 + ' ' + y + 'H' + X1 + 'C' + (X1 + 26) + ' ' + y + ' ' +
                   (ENTRY - 26) + ' ' + CY + ' ' + ENTRY + ' ' + CY;
      if (ai) {
        mk(svg, 'line', { x1: GATE, y1: y - 8, x2: GATE, y2: y + 8, class: 'pp-gate' });
        mk(svg, 'text', { x: GATE + 6, y: y + 3, class: 'pp-gate-label' }, T('home.ai.required').toUpperCase());
      }
      if (opt) {
        // L'IA facultative est BRANCHÉE À CÔTÉ du chemin, jamais dessus.
        mk(svg, 'line', { x1: OPT_X, y1: y - 3, x2: OPT_X, y2: y - 7, class: 'pp-stub' });
        mk(svg, 'rect', { x: OPT_X - 10, y: y - 18, width: 20, height: 11, rx: 2, class: 'pp-opt' });
        mk(svg, 'text', { x: OPT_X, y: y - 10, 'text-anchor': 'middle', class: 'pp-opt-label' }, T('home.fig.ai'));
      }
      var m = new Mover(svg, d, { ai: ai, opt: opt });
      var sg = ai ? null : segs[slot++];
      if (sg && opt) {
        sg.hole = mk(svg, 'path', { d: sg.el.getAttribute('d'), class: 'pp-seg-hole' });
        sg.hole.style.strokeDasharray = sg.len; sg.hole.style.strokeDashoffset = sg.len;
      }
      rows.push({ ai: ai, m: m, seg: sg });
    });

    // Ceux qui arrivent d'abord, l'outil à IA requise en dernier.
    var order = rows.filter(function (r) { return !r.ai; }).concat(rows.filter(function (r) { return r.ai; }));
    var arrived = 0;
    return order.map(function (row, k) {
      return {
        at: 150 + k * 260, dur: row.ai ? 900 : 1300,
        step: function (t) { row.m.at(t); },
        end: function (instant) {
          if (!row.seg) return;
          var fill = [{ strokeDashoffset: row.seg.len }, { strokeDashoffset: 0 }];
          row.m.vanish(instant);
          if (instant) {
            row.seg.el.style.strokeDashoffset = 0;
            if (row.seg.hole) row.seg.hole.style.strokeDashoffset = 0;
          } else {
            row.seg.el.animate(fill, { duration: 380, easing: EASE, fill: 'forwards' });
            if (row.seg.hole) row.seg.hole.animate(fill, { duration: 380, easing: EASE, fill: 'forwards' });
            count.animate([{ transform: 'scale(1.12)' }, { transform: 'scale(1)' }], { duration: 260, easing: 'ease-out' });
          }
          count.textContent = (++arrived) + '/' + total;
        }
      };
    });
  }

  /* =====================================================================
     Le pont — l'exemple est choisi ici, tout le reste est lu.
     ===================================================================== */
  var EXAMPLE = { S: 3, E: 4, C: 2, potential: 6 };

  function geometry(narrow) {
    if (!narrow) return {
      vb: '0 0 440 178', barY: [44, 76, 108], asil: [0, 130],
      heads: [[0, 12], [272, 12]],
      wall: [220, 62, 220, 122], wallLab: [220, 142, 'middle', false],
      paths: { S: 'M150 44H236C254 44 250 40 268 40', E: 'M150 76H213', C: 'M150 108H213' },
      cross: { E: [204, 67], C: [204, 99] },
      lab: 330, cells: [336, 30],
      // Trajet de la faisabilité : de la pastille jusqu'au pied de SA colonne.
      feas: { chip: [336, 150, 100], path: function (x) { return 'M386 150V139H' + x + 'V120'; } },
      axis: [336, 130]
    };
    // Sous 400 px : HARA en haut, mur au milieu, matrice en bas.
    return {
      vb: '0 0 300 356', barY: [40, 70, 100], asil: [0, 118],
      heads: [[0, 12], [0, 200]],
      wall: [198, 160, 252, 160], wallLab: [298, 178, 'end', true],
      paths: { S: 'M150 40H180V224H168', E: 'M150 70H210V153', C: 'M150 100H240V153' },
      cross: { E: [222, 150], C: [252, 150] },
      lab: 56, cells: [60, 214],
      feas: { chip: [100, 328, 100], path: function (x) { return 'M150 328V316H' + x + 'V304'; } },
      axis: [0, 314]
    };
  }

  function bridgeSteps(matrix, scales) {
    var svg = document.getElementById('stanceBridge');
    svg.textContent = '';
    var G = geometry(svg.getBoundingClientRect().width < 400);
    svg.setAttribute('viewBox', G.vb);

    var asil = matrix.table['S' + EXAMPLE.S + 'E' + EXAMPLE.E + 'C' + EXAMPLE.C];
    var impact = scales.haraBridge.severityToImpact[EXAMPLE.S];
    var feas = scales.feasibilityByPotential[EXAMPLE.potential];
    var levels = scales.impactOrder.length, cols = scales.feasibilityOrder.length;
    var AXES = [
      { k: 'S', v: EXAMPLE.S, max: Object.keys(matrix.labels.severity).length - 1, pass: true },
      { k: 'E', v: EXAMPLE.E, max: Object.keys(matrix.labels.exposure).length - 1 },
      { k: 'C', v: EXAMPLE.C, max: Object.keys(matrix.labels.controllability).length - 1 }
    ];
    var steps = [];

    mk(svg, 'text', { x: G.heads[0][0], y: G.heads[0][1], class: 'pp-head' }, (toolName('/hara') + ' · HARA').toUpperCase());
    mk(svg, 'text', { x: G.heads[1][0], y: G.heads[1][1], class: 'pp-head' }, (toolName('/tara') + ' · TARA').toUpperCase());

    // --- HARA : trois barres à crans, puis l'ASIL ---
    var cells = [];
    AXES.forEach(function (a, i) {
      var y = G.barY[i];
      mk(svg, 'text', { x: 0, y: y + 5, class: 'pp-letter' }, a.k);
      for (var c = 0; c < a.max; c++) {
        var r = mk(svg, 'rect', { x: 16 + c * 27, y: y - 5, width: 24, height: 10, rx: 2, class: 'pp-cellbar' });
        if (c < a.v) cells.push(r);
      }
      a.val = mk(svg, 'text', { x: 16 + a.max * 27 + 3, y: y + 3.5, class: 'pp-val' }, a.k + a.v);
    });
    cells.forEach(function (r, i) {
      steps.push({ at: i * 55, dur: 1, end: function () { r.classList.add('is-on'); } });
    });
    steps.push({ at: cells.length * 55, dur: 1, end: function () { AXES.forEach(function (a) { a.val.classList.add('is-on'); }); } });
    var chip = mk(svg, 'rect', { x: G.asil[0], y: G.asil[1], width: 66, height: 20, rx: 10, class: 'pp-chip' });
    var chipT = mk(svg, 'text', { x: G.asil[0] + 33, y: G.asil[1] + 13.5, 'text-anchor': 'middle', class: 'pp-chip-text' }, 'ASIL —');
    steps.push({ at: 700, dur: 1, end: function () {
      chip.classList.add('is-on'); chipT.classList.add('is-on');
      chipT.textContent = asil === 'QM' ? 'QM' : 'ASIL ' + asil;
    } });

    // --- Le mur : E et C ne traversent pas ---
    var wall = mk(svg, 'line', { x1: G.wall[0], y1: G.wall[1], x2: G.wall[2], y2: G.wall[3], class: 'pp-wall' });
    var wallText = T('home.fig.wall').toUpperCase();
    // Sur téléphone, sur deux lignes : d'un seul tenant, le libellé mordait sur la voie de S.
    var cut = G.wallLab[3] ? wallText.lastIndexOf(' ') : -1;
    (cut > 0 ? [wallText.slice(0, cut), wallText.slice(cut + 1)] : [wallText]).forEach(function (line, i) {
      mk(svg, 'text', { x: G.wallLab[0], y: G.wallLab[1] + i * 12, 'text-anchor': G.wallLab[2], class: 'pp-head' }, line);
    });

    // --- TARA : la matrice impact × faisabilité, lue dans /tara/scales ---
    var M = {}, rowLabs = {};
    for (var imp = levels - 1; imp >= 0; imp--) {
      var ry = G.cells[1] + (levels - 1 - imp) * 22;
      rowLabs[imp] = mk(svg, 'text', { x: G.lab, y: ry + 13.5, 'text-anchor': 'end', class: 'pp-rowlab' }, scales.impactOrder[imp]);
      for (var f = 0; f < cols; f++) {
        var cx = G.cells[0] + f * 26;
        M[imp + ',' + f] = {
          cell: mk(svg, 'rect', { x: cx, y: ry, width: 24, height: 20, rx: 3, class: 'pp-cell' }),
          num: mk(svg, 'text', { x: cx + 12, y: ry + 13.5, 'text-anchor': 'middle', class: 'pp-num' }, scales.risk['I' + imp + 'F' + f])
        };
      }
    }
    mk(svg, 'text', { x: G.axis[0], y: G.axis[1], class: 'pp-head' }, T('home.fig.feas').toUpperCase() + ' →');

    // --- Les trois points ---
    var movers = {};
    AXES.forEach(function (a, i) {
      movers[a.k] = new Mover(svg, G.paths[a.k], { ai: !a.pass });
      steps.push({
        at: 950 + i * 180, dur: a.pass ? 1100 : 650,
        step: function (t) { movers[a.k].at(t); },
        end: function () {
          if (a.pass) {
            rowLabs[impact].classList.add('is-on');
            for (var f = 0; f < cols; f++) M[impact + ',' + f].cell.classList.add('is-row');
          } else {
            wall.classList.add('is-hit');
            mk(svg, 'text', { x: G.cross[a.k][0], y: G.cross[a.k][1], 'text-anchor': 'middle', class: 'pp-cross' }, '✕');
          }
        }
      });
    });

    // --- La faisabilité arrive d'ailleurs : de l'attaque, pas de la HARA ---
    var fc = G.feas.chip;
    var fChip = mk(svg, 'rect', { x: fc[0], y: fc[1], width: fc[2], height: 20, rx: 10, class: 'pp-chip' });
    var fText = mk(svg, 'text', { x: fc[0] + fc[2] / 2, y: fc[1] + 13.5, 'text-anchor': 'middle', class: 'pp-chip-text' },
                   T('home.fig.dongle').toUpperCase());
    // Le trajet vise la colonne de la faisabilité LUE, pas une colonne supposée.
    var fMove = new Mover(svg, G.feas.path(G.cells[0] + feas * 26 + 12), {});
    steps.push({ at: 2250, dur: 1, end: function () { fChip.classList.add('is-on'); fText.classList.add('is-on'); } });
    steps.push({
      at: 2350, dur: 650, step: function (t) { fMove.at(t); },
      end: function () { for (var i = 0; i < levels; i++) M[i + ',' + feas].cell.classList.add('is-col'); }
    });

    // --- Le croisement : le risque ---
    steps.push({
      at: 3100, dur: 1,
      end: function (instant) {
        var hit = M[impact + ',' + feas];
        hit.cell.classList.add('is-hit'); hit.num.classList.add('is-hit');
        movers.S.vanish(true); fMove.vanish(true);
        if (!instant) hit.num.animate([{ transform: 'scale(1.5)' }, { transform: 'scale(1)' }], { duration: 320, easing: EASE });
      }
    });
    return steps;
  }

  /* ---------- Déclenchement ---------- */
  var lang = window.LANG || 'fr';
  var data = Promise.all([
    fetch('/hara/matrix?lang=' + lang).then(function (r) { if (!r.ok) throw r; return r.json(); }),
    fetch('/tara/scales?lang=' + lang).then(function (r) { if (!r.ok) throw r; return r.json(); })
  ]);

  var played = false;
  function playBridge(instant) {
    // Sans ses données, le pont n'est pas dessiné : les trois règles écrites
    // sous la figure restent, elles, lisibles.
    data.then(function (d) { run(bridgeSteps(d[0], d[1]), instant); }, function () {});
  }
  function playAll() {
    if (played) return;
    played = true;
    run(ringSteps(), calm);
    if (calm) playBridge(true); else setTimeout(function () { playBridge(false); }, 700);
  }

  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      if (es.some(function (e) { return e.isIntersecting; })) { io.disconnect(); playAll(); }
    }, { threshold: 0.35 });
    io.observe(box);
  } else {
    playAll();
  }

  // Bascule bureau ↔ téléphone : le pont change de mise en page — on
  // redessine son état final, sans rejouer.
  var bridgeSvg = document.getElementById('stanceBridge');
  var narrow = bridgeSvg.getBoundingClientRect().width < 400;
  window.addEventListener('resize', function () {
    var n = bridgeSvg.getBoundingClientRect().width < 400;
    if (n !== narrow) { narrow = n; if (played) playBridge(true); }
  });
})();
