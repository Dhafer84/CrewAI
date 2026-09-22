/* ============================================================
   OUVERTURE DE L'ACCUEIL (22/09/2026)

   Un orbe de particules respire, éclate en galaxie, forme le nom de l'auteur
   en grand ; le nom s'envole se poser sur l'onglet — là où est le vrai —
   pendant qu'un diaphragme PERCE le calque et découvre l'accueil.

   Temps (≈ 2,95 s) :
     0     → 0,8 s   l'orbe respire et tourne ;
     0,8   → 1,25 s  il éclate en galaxie à trois bras ;
     1,25  → 2,05 s  les particules forment le nom ;
     2,05  → 2,35 s  le nom tient, il scintille à peine ;
     2,35  → 2,95 s  le nom se pose sur l'onglet, l'accueil s'ouvre dessous.

   Principe inspiré de modèles payants sous licence (Vesper, Noema, sur
   getlayers.ai) : ni leur code ni leurs textes ne sont repris.

   ⚠️ Règles tenues — chacune a une raison, ne pas les « simplifier » :
     - décidé dans <head> (classe `intro-on`) AVANT le premier affichage,
       sinon l'accueil clignote sous le calque ;
     - une fois par session, jamais si le visiteur demande moins d'animations ;
     - la page est `inert` pendant l'intro, le focus lui est rendu ensuite ;
     - « Passer », Échap ou un clic sautent à l'ouverture — ou ferment net si
       aucune image n'a encore été dessinée ;
     - GARDE-FOU de 4,5 s : un onglet bridé ne dessine aucune image, et le
       calque restait posé indéfiniment sur l'accueil (trouvé en test) ;
     - les positions du nom sont LUES dans la page (l'onglet), dans la vraie
       police, attendue au plus 600 ms ;
     - canvas 2D, aucune dépendance, aucune `opacity`, pas de vert (réservé
       aux statuts).
   ============================================================ */
(function () {
  var root = document.documentElement;
  var el = document.getElementById('intro');
  if (!el || !root.classList.contains('intro-on')) return;

  var canvas = el.querySelector('canvas');
  var ctx = canvas.getContext('2d');
  var skipBtn = el.querySelector('.intro-skip');
  var logo = document.querySelector('.h-tab .logo');
  var page = document.querySelectorAll('body > :not(#intro):not(script)');

  window.scrollTo(0, 0);
  page.forEach(function (n) { n.setAttribute('inert', ''); });
  skipBtn.focus({ preventScroll: true });

  var css = getComputedStyle(root);
  var tok = function (n, d) { return (css.getPropertyValue(n) || d).trim(); };
  var BG = tok('--h-panel', '#0e1017');
  var ACCENT = tok('--h-accent-ink', '#aab7ff');
  // L'orbe : indigo du site, bleu froid, lavande. Pas de vert — réservé aux statuts.
  var ORB = ['#6f7dff', '#8fb0ff', '#aab7ff', '#c4a8ff', '#e0d6ff'];

  var T = { burst: 800, gather: 1250, hold: 2050, open: 2350, end: 2950 };

  function rgb(c) {
    if (c[0] === '#') return [parseInt(c.substr(1, 2), 16), parseInt(c.substr(3, 2), 16), parseInt(c.substr(5, 2), 16)];
    var m = c.match(/\d+(\.\d+)?/g);
    return [+m[0], +m[1], +m[2]];
  }
  var ease = function (t) { return t < 0 ? 0 : t > 1 ? 1 : 1 - Math.pow(1 - t, 3); };
  var easeIn = function (t) { return t < 0 ? 0 : t > 1 ? 1 : t * t * t; };
  var easeIO = function (t) { return t < 0 ? 0 : t > 1 ? 1 : t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
  var mix = function (a, b, t) { return a + (b - a) * t; };

  var seed = 11;                                   // la même intro à chaque fois
  function rnd() { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; }

  var W, H, CX, CY, R0, parts = [], targets = [], landing = [], holeC = [0, 0];

  function size() {
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = window.innerWidth; H = window.innerHeight;
    canvas.width = W * dpr; canvas.height = H * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    CX = W / 2; CY = H / 2;
    R0 = Math.min(W, H) * (W > 720 ? 0.2 : 0.3);
  }

  /* ---------- Le nom : lu dans l'onglet de la page ---------- */

  // Chaque caractère visible, avec sa boîte, sa police et sa couleur.
  function charBoxes(elm) {
    var out = [], range = document.createRange();
    var walk = document.createTreeWalker(elm, NodeFilter.SHOW_TEXT), n;
    while ((n = walk.nextNode())) {
      var cs = getComputedStyle(n.parentElement);
      for (var i = 0; i < n.data.length; i++) {
        if (/\s/.test(n.data[i])) continue;
        range.setStart(n, i); range.setEnd(n, i + 1);
        var r = range.getBoundingClientRect();
        if (!r.width) continue;
        out.push({
          ch: cs.textTransform === 'uppercase' ? n.data[i].toUpperCase() : n.data[i],
          x: r.left, top: r.top, h: r.height,
          size: parseFloat(cs.fontSize) || 16,
          font: cs.fontWeight + ' ' + cs.fontSize + ' ' + cs.fontFamily,
          color: cs.color
        });
      }
    }
    return out;
  }
  function drawBoxes(c, boxes) {
    boxes.forEach(function (b) {
      c.font = b.font; c.fillStyle = b.color; c.textBaseline = 'alphabetic';
      var m = c.measureText(b.ch);
      var asc = m.fontBoundingBoxAscent || b.size * .8, desc = m.fontBoundingBoxDescent || b.size * .2;
      c.fillText(b.ch, b.x, b.top + (b.h - asc - desc) / 2 + asc);
    });
  }
  // Le nom en grand, au centre, avec les MOTS et les COULEURS de l'onglet :
  // une ligne sur bureau, un mot par ligne sur téléphone.
  function drawBigName(c) {
    var words = [], walk = document.createTreeWalker(logo, NodeFilter.SHOW_TEXT), n;
    while ((n = walk.nextNode())) {
      var color = getComputedStyle(n.parentElement).color;
      n.data.split(/\s+/).filter(Boolean).forEach(function (w) { words.push([w.toUpperCase(), color]); });
    }
    var lines = W > 720 ? [words] : words.map(function (w) { return [w]; });
    c.textBaseline = 'middle';
    if ('fontStretch' in c) c.fontStretch = 'expanded';
    var face = 'Archivo, "Helvetica Neue", Arial, sans-serif', fs = 200;
    c.font = '600 ' + fs + 'px ' + face;
    var widest = Math.max.apply(null, lines.map(function (l) {
      return c.measureText(l.map(function (w) { return w[0]; }).join(' ')).width;
    }));
    fs = Math.min(fs * (W * 0.86) / widest, H * 0.16);
    c.font = '600 ' + fs + 'px ' + face;
    var lh = fs * 0.95, y0 = CY - (lines.length - 1) * lh / 2;
    lines.forEach(function (l, li) {
      var x = CX - c.measureText(l.map(function (w) { return w[0]; }).join(' ')).width / 2;
      l.forEach(function (w) {
        c.fillStyle = w[1]; c.fillText(w[0], x, y0 + li * lh);
        x += c.measureText(w[0] + ' ').width;
      });
    });
  }
  // Rastérise un dessin hors écran et en tire des points colorés.
  function sample(drawFn, step) {
    var off = document.createElement('canvas');
    off.width = W; off.height = H;
    var c = off.getContext('2d', { willReadFrequently: true });
    drawFn(c);
    var d = c.getImageData(0, 0, W, H).data, pts = [];
    for (var y = 0; y < H; y += step)
      for (var x = 0; x < W; x += step) {
        var i = (y * W + x) * 4;
        if (d[i + 3] > 140) pts.push({ x: x, y: y, c: [d[i], d[i + 1], d[i + 2]] });
      }
    return pts;
  }
  function fit(pts, n) {
    var out = [];
    for (var i = 0; i < n && pts.length; i++) out.push(pts[Math.floor(rnd() * pts.length)]);
    return out;
  }

  function build() {
    parts = [];
    var n = Math.round(Math.min(4200, Math.max(1800, (W * H) / 260)));
    for (var i = 0; i < n; i++) {
      parts.push({
        th: Math.acos(1 - 2 * rnd()), ph: rnd() * Math.PI * 2,
        arm: Math.floor(rnd() * 3), an: (rnd() - 0.5) * 0.55,   // bras de la galaxie
        rr: 0.82 + rnd() * 0.3,                                   // épaisseur de la coquille
        gr: R0 * (0.25 + Math.pow(rnd(), 0.7) * 2.3),             // rayon dans la galaxie
        jit: rnd() * 220,                                          // départ décalé
        size: 1 + rnd() * 1.4,
        col: rgb(ORB[Math.floor(rnd() * ORB.length)])
      });
    }
    targets = fit(sample(drawBigName, 3), n);
    landing = fit(sample(function (c) { drawBoxes(c, charBoxes(logo)); }, 1), n);
    var r = logo.getBoundingClientRect();
    holeC = [r.left + r.width / 2, r.top + r.height / 2];
  }

  /* ---------- Les positions, phase par phase ---------- */
  function orb(p, ms) {
    var rot = ms * 0.0011, r = R0 * p.rr * (1 + 0.05 * Math.sin(ms / 260));
    var X = r * Math.sin(p.th) * Math.cos(p.ph + rot), Y = r * Math.cos(p.th);
    var Z = r * Math.sin(p.th) * Math.sin(p.ph + rot), s = 700 / (700 + Z);
    return [CX + X * s, CY + Y * s, s];
  }
  function galaxy(p, ms) {
    // Trois bras spiraux : l'angle croît avec le rayon.
    var a = p.arm * (Math.PI * 2 / 3) + p.an + (p.gr / R0) * 2.2 + ms * 0.0016;
    return [CX + Math.cos(a) * p.gr, CY + Math.sin(a) * p.gr * 0.42];
  }
  function place(i, ms) {
    var p = parts[i], tg = targets[i];
    var a = orb(p, ms), x = a[0], y = a[1], s = a[2], c = p.col;
    var burst = ease((ms - T.burst) / (T.gather - T.burst));
    if (burst > 0) {
      var g = galaxy(p, ms);
      x = mix(x, g[0], burst); y = mix(y, g[1], burst); s = mix(s, 1, burst);
    }
    if (tg && ms > T.gather) {
      var t = easeIO((ms - T.gather - p.jit) / (T.hold - T.gather - 220));
      if (t > 0) {
        var sw = Math.sin(t * Math.PI) * 40 * (i % 2 ? 1 : -1);   // tourbillon en chemin
        x = mix(x, tg.x, t) + sw * (1 - t);
        y = mix(y, tg.y, t) - sw * 0.5 * (1 - t);
        c = [mix(c[0], tg.c[0], t), mix(c[1], tg.c[1], t), mix(c[2], tg.c[2], t)];
        s = mix(s, 1.25, t);
        if (t === 1) { x += Math.sin(ms / 90 + i) * 0.35; y += Math.cos(ms / 110 + i) * 0.35; }
      }
    }
    return [x, y, s, c];
  }
  function dot(x, y, sz, c) {
    ctx.fillStyle = 'rgb(' + (c[0] | 0) + ',' + (c[1] | 0) + ',' + (c[2] | 0) + ')';
    ctx.fillRect(x - sz / 2, y - sz / 2, sz, sz);
  }

  function draw(ms) {
    ctx.globalCompositeOperation = 'source-over';
    ctx.fillStyle = BG;
    ctx.fillRect(0, 0, W, H);

    var open = easeIn((ms - T.open) / (T.end - T.open));
    var hole = open * Math.hypot(W, H) * 1.05;
    // Le vol dure 60 % de l'ouverture : le nom se POSE sur l'onglet sous les
    // yeux du visiteur, avant que l'ouverture ne l'atteigne.
    var fly = ease((ms - T.open) / (T.end - T.open) / 0.6);

    // Un halo derrière l'orbe, qui s'éteint quand les particules partent en lettres.
    var glow = 1 - ease((ms - T.burst) / (T.hold - T.burst));
    if (glow > 0) {
      var gr = ctx.createRadialGradient(CX, CY, 0, CX, CY, R0 * 1.9);
      gr.addColorStop(0, 'rgba(111,125,255,' + (0.22 * glow) + ')');
      gr.addColorStop(0.5, 'rgba(196,168,255,' + (0.08 * glow) + ')');
      gr.addColorStop(1, 'rgba(14,16,23,0)');
      ctx.fillStyle = gr; ctx.fillRect(0, 0, W, H);
    }

    // 1. Les particules — additionnées en lumière tant qu'elles forment l'orbe,
    //    à plat une fois devenues des lettres (sinon les couleurs saturent en blanc).
    ctx.globalCompositeOperation = ms < T.gather + 400 ? 'lighter' : 'source-over';
    var pos = [];
    for (var i = 0; i < parts.length; i++) {
      var q = place(i, Math.min(ms, T.open)), x = q[0], y = q[1], s = q[2], c = q[3];
      if (fly > 0 && landing[i]) {
        var L = landing[i];
        x = mix(x, L.x, fly); y = mix(y, L.y, fly); s = mix(s, 0.55, fly);
        c = [mix(c[0], L.c[0], fly), mix(c[1], L.c[1], fly), mix(c[2], L.c[2], fly)];
      }
      pos.push([x, y, s, c]);
      dot(x, y, parts[i].size * s, c);
    }

    // 2. Le diaphragme perce le calque ; le nom vole AU-DESSUS de l'ouverture.
    ctx.globalCompositeOperation = 'source-over';
    if (hole > 0) {
      ctx.globalCompositeOperation = 'destination-out';
      ctx.beginPath(); ctx.arc(holeC[0], holeC[1], hole, 0, Math.PI * 2); ctx.fill();
      ctx.globalCompositeOperation = 'source-over';
      ctx.strokeStyle = ACCENT; ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.arc(holeC[0], holeC[1], hole, 0, Math.PI * 2); ctx.stroke();
      if (fly < 1) {
        for (var k = 0; k < pos.length; k++) {
          var P = pos[k];
          if (Math.hypot(P[0] - holeC[0], P[1] - holeC[1]) < hole) dot(P[0], P[1], parts[k].size * P[2], P[3]);
        }
      }
    }
  }

  /* ---------- Déroulé ---------- */
  var start = null, raf, done = false;
  function frame(now) {
    if (start === null) start = now;
    var ms = now - start;
    if (ms > T.open) el.classList.add('is-opening');
    try { draw(ms); } catch (e) { finish(); return; }
    el.classList.add('is-drawn');
    if (ms < T.end) raf = requestAnimationFrame(frame); else finish();
  }
  function finish() {
    if (done) return;
    done = true;
    cancelAnimationFrame(raf);
    root.classList.remove('intro-on');
    page.forEach(function (n) { n.removeAttribute('inert'); });
    // Le focus revient au début de la page, pas dans le vide.
    var first = document.querySelector('.h-shell a, .h-shell button');
    if (first && document.activeElement === skipBtn) first.focus({ preventScroll: true });
    document.removeEventListener('keydown', onKey);
    try { sessionStorage.setItem('qc.intro.seen', '1'); } catch (e) { /* navigation privée */ }
  }
  // Passer = sauter à l'ouverture (0,6 s), ou fermer net si rien n'est encore dessiné.
  function skip() {
    if (done) return;
    if (start === null) { finish(); return; }
    if (performance.now() - start < T.open) start = performance.now() - T.open;
  }
  function onKey(e) { if (e.key === 'Escape') skip(); }
  el.addEventListener('click', skip);
  skipBtn.addEventListener('click', function (e) { e.stopPropagation(); skip(); });
  document.addEventListener('keydown', onKey);

  // GARDE-FOU : le calque ne reste jamais plus de 4,5 s, quoi qu'il arrive.
  setTimeout(finish, 4500);

  if (!logo) { finish(); return; }
  // Le nom se mesure dans la vraie police : on attend Archivo, au plus 600 ms.
  var ready = document.fonts && document.fonts.load
    ? Promise.race([document.fonts.load('600 64px Archivo'), new Promise(function (r) { setTimeout(r, 600); })])
    : Promise.resolve();
  ready.then(function () {
    if (done) return;
    // ⚠️ Une intro ne doit JAMAIS casser l'accueil. Fenêtre sans taille (onglet
    // ouvert en arrière-plan, page préchargée) ou erreur de dessin : on ferme
    // le calque, le visiteur arrive simplement sur la page. Trouvé en test :
    // `getImageData` levait sur une fenêtre de largeur 0.
    try {
      size();
      if (!W || !H) { finish(); return; }
      build();
    } catch (e) { finish(); return; }
    raf = requestAnimationFrame(frame);
  });
})();
