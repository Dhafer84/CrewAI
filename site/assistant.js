// assistant.js — l'assistant du site, en « orbe » (remplace la bulle de l'assistant 3D
// le 15/11/2026). Pilule → bille qui s'envole → sphère de points qui réfléchit →
// condensation → carte réponse. JavaScript sans dépendance ; maquette validée par
// l'utilisateur (.claude/prototypes/orb/).
//
// Il interroge l'API de l'assistant (dépôt robot-3d-assistant, `POST /api/chat`) à
// l'adresse de `data-origin`, autorisée par la CSP (`connect-src`, api/main.py) ; l'API
// accepte cet appel d'un autre site par CORS, pour les seuls sites qu'elle liste
// (FRAME_ANCESTORS). Textes : catalogue du site (`assistant.*`, via T()).
//
// ⚠️ La réponse de l'IA est posée en textContent, jamais en innerHTML : c'est du texte
// qui vient d'un modèle. Aucune opacity : on cache par visibility, on fait apparaître
// par transform, clip-path et couleur (règle du site).
(() => {
  'use strict';
  const script = document.currentScript;
  if (!script || document.querySelector('.qo') || typeof T !== 'function') return;
  const ORIGIN = script.dataset.origin;
  if (!ORIGIN) return;
  const LANG = window.LANG === 'en' ? 'en' : 'fr';
  const STEPS = [T('assistant.step.1'), T('assistant.step.2'), T('assistant.step.3'), T('assistant.step.4')];
  const HISTORY_KEY = 'qc-assistant';
  const MAX_HISTORY = 10; // messages gardés (questions + réponses), comme le serveur
  const MIN_THINK = 2400; // ms : la sphère a le temps de « réfléchir » même si l'IA est rapide
  const TIMEOUT = 45000;

  /* ── conversation (sessionStorage : un confort par visiteur, jamais indispensable) ── */
  const loadHistory = () => {
    try {
      const h = JSON.parse(sessionStorage.getItem(HISTORY_KEY) || '[]');
      return Array.isArray(h) ? h.filter((m) => m && typeof m.content === 'string' && (m.role === 'user' || m.role === 'assistant')) : [];
    } catch (e) { return []; }
  };
  let history = loadHistory();
  const saveHistory = () => { try { sessionStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(-MAX_HISTORY))); } catch (e) { /* stockage refusé */ } };

  // Les réponses commencent par une balise d'émotion destinée à l'avatar 3D (<joie>…)
  const clean = (s) => s.replace(/<\s*(joie|reflexion|réflexion|surprise|desole|désolé|neutre)\s*>/gi, '').replace(/[ \t]+\n/g, '\n').trim();

  const askServer = async (question) => {
    const messages = [...history, { role: 'user', content: question }].slice(-MAX_HISTORY);
    const ctl = new AbortController();
    const timer = setTimeout(() => ctl.abort(), TIMEOUT);
    try {
      const res = await fetch(ORIGIN + '/api/chat', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages, lang: LANG }), signal: ctl.signal,
      });
      if (!res.ok) {
        let msg = '';
        try { msg = (await res.json()).error || ''; } catch (e) { /* réponse non JSON */ }
        return { ok: false, text: msg || T('assistant.error') };
      }
      const text = clean(await res.text());
      if (!text) return { ok: false, text: T('assistant.error') };
      history = [...messages, { role: 'assistant', content: text }].slice(-MAX_HISTORY);
      saveHistory();
      return { ok: true, text };
    } catch (e) {
      return { ok: false, text: T('assistant.offline') };
    } finally { clearTimeout(timer); }
  };

  /* ── outils ── */
  const clamp01 = (v) => (v < 0 ? 0 : v > 1 ? 1 : v);
  const lerp = (a, b, t) => a + (b - a) * t;
  const eOut = (t) => 1 - Math.pow(1 - t, 3);
  const eIO = (t) => (t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
  const eBack = (t) => { const c = 1.6; return 1 + (c + 1) * Math.pow(t - 1, 3) + c * Math.pow(t - 1, 2); };
  const TAU = Math.PI * 2;
  const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
  let runId = 0;
  const tween = (ms, fn, ease = eOut) => new Promise((res) => {
    const id = runId, d = reduced() ? Math.min(ms, 160) : ms;
    const t0 = performance.now();
    const step = (now) => {
      if (id !== runId) return res(false);
      const p = Math.min(1, (now - t0) / d);
      fn(ease(p), p);
      if (p < 1) requestAnimationFrame(step); else res(true);
    };
    requestAnimationFrame(step);
  });
  const wait = (ms) => new Promise((res) => { const id = runId; setTimeout(() => res(id === runId), ms); });
  const el = (tag, cls) => { const e = document.createElement(tag); if (cls) e.className = cls; return e; };
  const svg = (cls, body) => { const s = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); s.setAttribute('viewBox', '0 0 24 24'); s.setAttribute('fill', 'none'); s.setAttribute('stroke', 'currentColor'); s.setAttribute('stroke-width', '1.7'); s.setAttribute('stroke-linecap', 'round'); s.setAttribute('stroke-linejoin', 'round'); s.setAttribute('aria-hidden', 'true'); if (cls) s.setAttribute('class', cls); s.innerHTML = body; return s; };
  const ICON = {
    spark: () => svg('qo-spark', '<path d="M11 3l1.6 4.9L17.5 9.5l-4.9 1.6L11 16l-1.6-4.9L4.5 9.5l4.9-1.6z"/><path d="M18.5 15l.6 1.7 1.7.6-1.7.6-.6 1.7-.6-1.7-1.7-.6 1.7-.6z"/>'),
    up: () => svg(null, '<path d="M12 19V5M5.5 11.5 12 5l6.5 6.5"/>'),
    x: () => svg(null, '<path d="M6 6l12 12M18 6 6 18"/>'),
  };
  const field = (ph) => { const i = el('input', 'qo-field'); i.maxLength = 500; i.placeholder = ph; i.setAttribute('aria-label', ph); i.autocomplete = 'off'; return i; };
  const sendBtn = () => { const b = el('button', 'qo-send'); b.type = 'submit'; b.setAttribute('aria-label', T('assistant.send')); b.append(ICON.up()); return b; };

  /* ── DOM ── */
  const root = el('div', 'qo');
  const scrim = el('div', 'qo-scrim');
  const canvas = el('canvas', 'qo-canvas'); canvas.setAttribute('aria-hidden', 'true');
  const status = el('div', 'qo-status'); status.setAttribute('aria-hidden', 'true');

  const card = el('section', 'qo-card'); card.setAttribute('role', 'dialog'); card.setAttribute('aria-labelledby', 'qo-title'); card.tabIndex = -1;
  const head = el('div', 'qo-head'); const dot = el('i'); dot.setAttribute('aria-hidden', 'true');
  const h2 = el('h2'); h2.id = 'qo-title'; h2.textContent = T('assistant.title');
  const xBtn = el('button', 'qo-x'); xBtn.type = 'button'; xBtn.setAttribute('aria-label', T('assistant.close')); xBtn.append(ICON.x());
  head.append(dot, h2, xBtn);
  const cQ = el('p', 'qo-q'), cA = el('div', 'qo-a'), note = el('p', 'qo-note');
  note.textContent = T('assistant.notice');
  const cFollow = el('form', 'qo-follow'); cFollow.autocomplete = 'off';
  const cField = field(T('assistant.follow')), cSend = sendBtn();
  cFollow.append(cField, cSend);
  card.append(head, cQ, cA, cFollow, note);

  const pill = el('form', 'qo-pill'); pill.autocomplete = 'off'; pill.dataset.state = 'rest';
  const cell = el('span', 'qo-cell'), label = el('span', 'qo-label');
  label.textContent = T('assistant.label'); label.setAttribute('aria-hidden', 'true');
  const pField = field(T('assistant.placeholder')); pField.tabIndex = -1;
  cell.append(label, pField);
  const pSend = sendBtn(); pSend.tabIndex = -1;
  const pOpen = el('button', 'qo-open'); pOpen.type = 'button'; pOpen.setAttribute('aria-label', T('assistant.label')); pOpen.setAttribute('aria-expanded', 'false');
  pill.append(ICON.spark(), cell, pSend, pOpen);

  const live = el('div', 'qo-live'); live.setAttribute('role', 'status'); live.setAttribute('aria-live', 'polite');
  root.append(scrim, canvas, status, card, pill, live);
  document.body.appendChild(root);

  const measureRest = () => pill.style.setProperty('--qo-rest', Math.ceil(label.scrollWidth + 20 + 10 + 18 + 18) + 'px');
  measureRest();

  /* ── sphère de points (spirale de Fibonacci) ── */
  const N = 420;
  const PX = new Float32Array(N), PY = new Float32Array(N), PZ = new Float32Array(N), PU = new Float32Array(N), PL = new Float32Array(N), PS = new Float32Array(N);
  for (let i = 0; i < N; i++) {
    const y = 1 - (i + .5) / N * 2, r = Math.sqrt(1 - y * y), a = i * 2.399963229728653;
    PX[i] = Math.cos(a) * r; PY[i] = y; PZ[i] = Math.sin(a) * r; PU[i] = (1 - y) / 2;
    PL[i] = Math.atan2(PZ[i], PX[i]); PS[i] = (i * 7.31) % TAU;
  }
  const lit = new Float32Array(N);
  const prog = [1, 0, 0, 0];
  const V = { ballX: 0, ballY: 0, ballR: 0, ballA: 0, trail: 0, orbK: 0, orbA: 0, pop: 1, spin: 0, rot: 0,
    sweep: 0, collapse: 0, discR: 0, discA: 0, pulse: -1, p: 0, time: 0 };
  const hist = [];
  const ctx = canvas.getContext('2d');
  let W = 0, H = 0, drawing = false, last = 0;
  const resize = () => {
    const dpr = Math.min(2, devicePixelRatio || 1); W = innerWidth; H = innerHeight;
    canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  };
  const center = () => ({ x: W / 2, y: H / 2 });
  const BASE = [226, 231, 248], ACC = [158, 172, 254], ACC2 = [111, 125, 255], PANEL = [19, 23, 42];
  const rgba = (c, a) => `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a.toFixed(3)})`;
  const mix = (a, b, t) => [lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)];

  const drawOrb = (dt) => {
    const { x: cx, y: cy } = center();
    V.time += dt; V.rot += V.spin * dt;
    for (let q = 0; q < 4; q++) prog[q] += ((q === V.p ? 1 : 0) - prog[q]) * Math.min(1, dt / .3);
    const t = V.time, decay = Math.exp(-dt / .45);
    const R = 66 * V.pop, CT = Math.cos(.38), ST = Math.sin(.38), cyw = Math.cos(V.rot), syw = Math.sin(V.rot);
    const s1 = [Math.cos(t * .9) * Math.cos(Math.sin(t * .6)), Math.sin(Math.sin(t * .6)), Math.sin(t * .9) * Math.cos(Math.sin(t * .6))];
    const s2 = [Math.cos(t * .6 + 2), Math.sin(Math.cos(t * .5) * .9), Math.sin(t * .6 + 2)];
    const band = Math.sin(t * 2.1), chase = (t * 260) % N;
    const front = [], back = [];
    for (let i = 0; i < N; i++) {
      // quatre façons d'allumer les points, une par étape affichée
      let pulse = 0;
      if (prog[0] > .01) { let d = PL[i] - t * 2.4; d = Math.atan2(Math.sin(d), Math.cos(d)); pulse = Math.max(pulse, Math.pow(Math.max(0, 1 - Math.abs(d) / .45), 2) * prog[0]); }
      if (prog[1] > .01) { const v = Math.max(PX[i] * s1[0] + PY[i] * s1[1] + PZ[i] * s1[2], PX[i] * s2[0] + PY[i] * s2[1] + PZ[i] * s2[2]); pulse = Math.max(pulse, Math.pow(Math.max(0, (v - .74) / .26), 2) * prog[1]); }
      if (prog[2] > .01) { const e = PY[i] - band; pulse = Math.max(pulse, Math.pow(Math.max(0, 1 - e * e / .018), 2) * prog[2]); }
      if (prog[3] > .01) { let d = Math.abs(i - chase); d = Math.min(d, N - d); pulse = Math.max(pulse, Math.pow(Math.max(0, 1 - d / 26), 2) * prog[3]); }
      const l = lit[i] = Math.max(lit[i] * decay, pulse);
      const ki = clamp01(V.orbK * 1.6 - .6 * PU[i]); // le haut apparaît d'abord
      if (ki <= .001) continue;
      const e = eOut(ki);
      const x1 = PX[i] * cyw + PZ[i] * syw, z1 = -PX[i] * syw + PZ[i] * cyw;
      const y2 = PY[i] * CT - z1 * ST, z2 = PY[i] * ST + z1 * CT;
      const f = 2.8 / (2.8 - z2), depth = (z2 + 1) / 2;
      const shrink = 1 - eIO(clamp01(V.collapse * 1.4 - .4 * PU[i]));
      let ox = x1 * R * e * f * shrink, oy = -y2 * R * e * f * shrink;
      if (V.collapse > 0) { const a = V.collapse * 2.2 * (1 - shrink + .2), c = Math.cos(a), s = Math.sin(a); const tx = ox * c - oy * s; oy = ox * s + oy * c; ox = tx; }
      const g = clamp01((V.sweep * 1.4 - PU[i]) / .4);
      let a = .1 + .03 * Math.sin(PS[i] + t * 1.5) + .34 * depth * depth + .72 * l * (1 - g) + g * (.55 + .4 * depth);
      a = Math.min(1, a) * e * V.orbA * (.25 + .75 * shrink);
      if (a < .01) continue;
      const col = mix(mix(BASE, ACC, l * .35), ACC, g);
      const r = ((.5 + .7 * depth) * 1.2 * f + .8 * l + .3 * g) * (.45 + .55 * e);
      (depth >= .5 ? front : back).push([cx + ox, cy + oy, r, rgba(col, a)]);
    }
    for (const list of [back, front]) for (const [x, y, r, c] of list) { ctx.fillStyle = c; ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill(); }
  };
  const drawBall = (x, y, r, a) => {
    const g = ctx.createRadialGradient(x - r * .35, y - r * .4, r * .1, x, y, r);
    g.addColorStop(0, rgba([214, 220, 255], a)); g.addColorStop(.55, rgba(ACC, a)); g.addColorStop(1, rgba(ACC2, a));
    ctx.save(); ctx.shadowColor = rgba(ACC2, .55 * a); ctx.shadowBlur = r * .9;
    ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fill(); ctx.restore();
  };
  const frame = (now) => {
    if (!drawing) return;
    const dt = Math.min(.05, (now - last) / 1000) * (reduced() ? 0 : 1); last = now;
    ctx.clearRect(0, 0, W, H);
    if (V.trail > .01) {
      for (let k = 1; k <= 7; k++) {
        const s = hist[hist.length - 1 - k * 2]; if (!s) break;
        ctx.fillStyle = rgba(ACC, .22 * Math.pow(1 - k / 8, 1.6) * V.trail);
        ctx.beginPath(); ctx.arc(s[0], s[1], s[2] * (1 - .07 * k), 0, TAU); ctx.fill();
      }
    }
    if (V.orbA > .002) drawOrb(dt);
    if (V.ballA > .002) drawBall(V.ballX, V.ballY, V.ballR, V.ballA);
    const { x: cx, y: cy } = center();
    if (V.pulse >= 0) { ctx.strokeStyle = rgba(ACC, .5 * (1 - V.pulse)); ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(cx, cy, 62 * (1 + V.pulse), 0, TAU); ctx.stroke(); }
    if (V.discA > .002) drawBall(cx, cy, V.discR, V.discA);
    requestAnimationFrame(frame);
  };
  const startDrawing = () => { if (drawing) return; resize(); drawing = true; last = performance.now(); requestAnimationFrame(frame); };
  const stopDrawing = () => { drawing = false; ctx.clearRect(0, 0, W, H); };
  addEventListener('resize', () => { if (drawing) resize(); measureRest(); });
  let scrimLevel = 0;
  const setScrim = (a) => { scrimLevel = a; scrim.style.background = `rgba(6,8,15,${(.6 * a).toFixed(3)})`; };

  /* ── étiquette sous l'orbe : rouleau, sans opacity ── */
  const setLabel = (s, done) => {
    const old = status.querySelector('.qo-lab:not(.is-out)');
    const nu = el('div', 'qo-lab');
    const txt = el('span', done ? 'qo-lab-done' : 'qo-lab-t'); txt.textContent = s; nu.append(txt);
    if (!done) { const dots = el('span', 'qo-dots'); dots.append(el('i'), el('i'), el('i')); nu.append(dots); }
    status.appendChild(nu);
    status.style.width = Math.max(nu.scrollWidth, 10) + 'px';
    if (reduced()) { if (old) old.remove(); return; }
    const opts = { duration: 380, easing: 'cubic-bezier(.22,1,.36,1)', fill: 'forwards' };
    nu.animate([{ transform: 'translateY(100%)', filter: 'blur(3px)' }, { transform: 'translateY(0)', filter: 'blur(0)' }], opts);
    if (old) {
      old.classList.add('is-out');
      old.animate([{ transform: 'translateY(0)' }, { transform: 'translateY(-100%)', filter: 'blur(3px)' }], opts).onfinish = () => old.remove();
    }
  };
  const resetLabel = () => { status.textContent = ''; status.classList.remove('is-on'); };

  /* ── carte : ouverture par clip-path, depuis le disque central ── */
  const D0 = 124;
  const clipAt = (w, h, p) => {
    const t = lerp((h - D0) / 2, 0, p), s = lerp((w - D0) / 2, 0, p), r = lerp(D0 / 2, 22, p);
    return `inset(${t.toFixed(1)}px ${s.toFixed(1)}px round ${r.toFixed(1)}px)`;
  };
  const fillCard = (q, answer) => {
    cQ.textContent = '';
    const who = el('b'); who.textContent = T('assistant.you') + ' ';
    cQ.append(who, document.createTextNode(q));
    cA.textContent = ''; cA.classList.remove('is-shown');
    cA.classList.toggle('is-error', !answer.ok);
    for (const para of answer.text.split(/\n{2,}/)) {
      const p = el('p');
      para.split(/\s+/).filter(Boolean).forEach((w, i) => { if (i) p.append(' '); const s = el('span', 'qo-w'); s.textContent = w; p.append(s); });
      cA.append(p);
    }
  };
  const revealWords = () => {
    const words = [...cA.querySelectorAll('.qo-w')];
    if (reduced()) { cA.classList.add('is-shown'); return; }
    const stag = Math.min(28, 900 / Math.max(1, words.length));
    words.forEach((w, i) => {
      w.style.visibility = 'visible';
      w.animate([{ transform: 'translateY(5px)', filter: 'blur(5px)', color: '#5b6283' }, { transform: 'none', filter: 'blur(0)' }],
        { duration: 380, delay: i * stag, easing: 'cubic-bezier(.22,1,.36,1)', fill: 'backwards' });
    });
  };

  /* ── pilule ── */
  const setPill = (s) => {
    pill.dataset.state = s;
    const open = s === 'open';
    pOpen.setAttribute('aria-expanded', String(open));
    pField.tabIndex = open ? 0 : -1; pSend.tabIndex = open ? 0 : -1;
  };
  let busy = false, phase = 'idle';
  const openPill = () => { if (busy) return; setPill('open'); setTimeout(() => pField.focus({ preventScroll: true }), 60); };
  const closePill = () => { if (pill.dataset.state === 'open' && !pField.value.trim()) { setPill('rest'); pOpen.focus({ preventScroll: true }); } };
  pOpen.addEventListener('click', openPill);
  const ready = (f, b) => () => { if (f.value.trim()) b.setAttribute('data-ready', ''); else b.removeAttribute('data-ready'); };
  pField.addEventListener('input', ready(pField, pSend)); cField.addEventListener('input', ready(cField, cSend));
  document.addEventListener('pointerdown', (e) => { if (!pill.contains(e.target)) closePill(); });
  const shake = (node) => { if (!reduced()) node.animate([{ transform: 'translateX(0)' }, { transform: 'translateX(-5px)' }, { transform: 'translateX(5px)' }, { transform: 'translateX(0)' }], { duration: 240 }); };

  /* ── la séquence ── */
  const rest = () => { for (const k in V) if (k !== 'rot' && k !== 'time') V[k] = 0; V.pop = 1; V.pulse = -1; lit.fill(0); prog.fill(0); prog[0] = 1; hist.length = 0; };

  async function ask(text, from) {
    busy = true; phase = 'launch'; const id = ++runId;
    root.setAttribute('data-busy', ''); startDrawing();
    const pending = askServer(text);
    const { x: cx, y: cy } = center();

    if (from === 'pill') {
      setPill('launch');
      if (!await wait(reduced() ? 0 : 380)) return;
      const r = pill.getBoundingClientRect();
      const sx = r.left + r.width / 2, sy = r.top + r.height / 2;
      setPill('gone');
      V.ballX = sx; V.ballY = sy; V.ballR = 28; V.ballA = 1;
      const dir = sx > cx ? -1 : 1, kx = lerp(sx, cx, .5) + dir * .18 * W, ky = Math.min(sy, cy) - .05 * H;
      hist.length = 0;
      if (!await tween(780, (u, p) => {
        V.ballX = (1 - u) * (1 - u) * sx + 2 * (1 - u) * u * kx + u * u * cx;
        V.ballY = (1 - u) * (1 - u) * sy + 2 * (1 - u) * u * ky + u * u * cy;
        V.ballR = p < .8 ? lerp(28, 72, eOut(p / .8)) : lerp(72, 62, eOut((p - .8) / .2));
        V.trail = p < .15 ? p / .15 : p > .8 ? 1 - (p - .8) / .2 : 1;
        hist.push([V.ballX, V.ballY, V.ballR]); if (hist.length > 40) hist.shift();
        setScrim(p);
      }, eIO)) return;
    } else {
      const r = card.getBoundingClientRect();
      if (!await tween(360, (e) => { card.style.clipPath = clipAt(r.width, r.height, 1 - e); }, eIO)) return;
      card.classList.remove('is-on'); card.style.clipPath = '';
      V.ballX = cx; V.ballY = cy; V.ballR = 62; V.ballA = 1;
    }

    // la bille se dissout en points
    phase = 'think';
    V.orbK = 0; V.orbA = 0; V.spin = 0;
    status.textContent = ''; status.classList.add('is-on'); setLabel(STEPS[0]);
    live.textContent = STEPS[0] + '…';
    if (!await tween(800, (e, p) => {
      V.ballA = 1 - clamp01(p / .4); V.ballR = 62 * (1 - .3 * clamp01(p / .4));
      V.orbK = e; V.orbA = e; V.spin = .9 * e; V.pop = p < .5 ? lerp(1, 1.06, eOut(p / .5)) : lerp(1.06, 1, eIO((p - .5) / .5));
    })) return;

    // réflexion : jusqu'à la réponse, et au moins MIN_THINK
    const t0 = performance.now(); let li = 0;
    const loop = setInterval(() => { if (id !== runId) return clearInterval(loop); li = (li + 1) % 4; V.p = li; setLabel(STEPS[li]); }, 1150);
    const answer = await pending;
    const left = MIN_THINK - (performance.now() - t0);
    if (left > 0 && !await wait(left)) { clearInterval(loop); return; }
    clearInterval(loop);
    if (id !== runId) return;

    phase = 'resolve'; setLabel(T('assistant.done'), true);
    if (!await tween(700, (e) => { V.sweep = e; V.spin = lerp(.9, .3, e); }, eIO)) return;

    phase = 'condense';
    status.classList.remove('is-on');
    V.discR = 0; V.discA = 0;
    if (!await tween(650, (e, p) => {
      V.collapse = eIO(clamp01(p / .8));
      const q = clamp01((p - .35) / .65);
      V.discA = clamp01(q * 2); V.discR = 62 * eBack(q);
      V.pulse = p > .45 ? (p - .45) / .55 : -1;
    }, (t) => t)) return;
    V.orbA = 0; V.pulse = -1;

    phase = 'unfold';
    fillCard(text, answer);
    card.classList.add('is-on');
    const r = card.getBoundingClientRect();
    card.style.clipPath = clipAt(r.width, r.height, 0);
    card.style.background = `rgb(${ACC.join(',')})`;
    if (!await tween(620, (e, p) => {
      card.style.clipPath = clipAt(r.width, r.height, e);
      const c = mix(ACC, PANEL, eOut(clamp01(p / .7)));
      card.style.background = `rgb(${c[0] | 0},${c[1] | 0},${c[2] | 0})`;
      V.discA = 1 - clamp01(p / .25);
    }, (t) => 1 - Math.pow(1 - t, 4))) return;
    card.style.clipPath = ''; card.style.background = ''; V.discA = 0;
    phase = 'answered';
    revealWords();
    live.textContent = (answer.ok ? T('assistant.ready') + ' ' : '') + answer.text;
    card.focus({ preventScroll: true });
    cField.value = ''; cSend.removeAttribute('data-ready');
    busy = false;
  }

  async function close() {
    const id = ++runId; busy = true; phase = 'closing';
    resetLabel();
    const wasCard = card.classList.contains('is-on');
    const r = card.getBoundingClientRect();
    const a0 = V.orbA, b0 = V.ballA, d0 = V.discA, s0 = scrimLevel;
    await tween(300, (e) => {
      if (wasCard) card.style.clipPath = clipAt(r.width, r.height, 1 - e);
      V.orbA = a0 * (1 - e); V.ballA = b0 * (1 - e); V.discA = d0 * (1 - e);
      setScrim(s0 * (1 - e));
    }, eIO);
    if (id !== runId) return;
    card.classList.remove('is-on'); card.style.clipPath = ''; card.style.background = '';
    root.removeAttribute('data-busy'); setScrim(0); rest(); stopDrawing();
    pField.value = ''; pSend.removeAttribute('data-ready');
    setPill('rest');
    if (!reduced()) pill.animate([{ transform: 'translateY(14px) scale(.96)' }, { transform: 'none' }], { duration: 420, easing: 'cubic-bezier(.22,1,.36,1)' });
    pOpen.focus({ preventScroll: true });
    busy = false; phase = 'idle';
  }

  pill.addEventListener('submit', (e) => {
    e.preventDefault();
    if (busy || pill.dataset.state !== 'open') return;
    const q = pField.value.trim();
    if (!q) { shake(pill); return; }
    ask(q, 'pill');
  });
  cFollow.addEventListener('submit', (e) => {
    e.preventDefault();
    if (busy) return;
    const q = cField.value.trim();
    if (!q) { shake(cFollow); return; }
    ask(q, 'card');
  });
  xBtn.addEventListener('click', close);
  scrim.addEventListener('click', () => { if (phase === 'answered') close(); });
  addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (phase !== 'idle' && phase !== 'closing') { e.preventDefault(); close(); }
    else if (pill.dataset.state === 'open') { pField.value = ''; closePill(); }
  });
})();
