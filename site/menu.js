/* Menu qui se déploie — partagé par les huit pages (balisage : site/partials/menu.html).

   La pastille « Menu » grandit jusqu'à devenir la carte : c'est le MÊME élément
   (`.nav-morph`) dont on anime la largeur et la hauteur. Une largeur `auto` ne
   s'anime pas ; d'où les mesures en pixels, refaites à chaque redimensionnement.

   ⚠️ Un menu qui ne se pilote qu'à la souris n'est pas un menu. Tenu ici :
   Échap ferme et rend le focus au bouton, le focus ne sort pas de la carte
   ouverte, et une carte fermée est `inert` — ses liens ne sont pas atteignables
   au clavier alors qu'on ne les voit pas. */
(() => {
  const menu = document.getElementById('navMenu');
  if (!menu) return;
  const toggle = document.getElementById('navToggle');
  const morph = document.getElementById('navMorph');
  const card = document.getElementById('navCard');

  const MARGE = 16;      // écart minimal avec le bord gauche de l'écran
  const LARGEUR = 380;   // largeur de la carte ouverte, au plus
  let ouvert = false;

  function mesurer() {
    const droite = menu.getBoundingClientRect().right;
    const largeur = Math.min(LARGEUR, droite - MARGE);
    const bords = morph.offsetWidth - morph.clientWidth;
    card.style.width = (largeur - bords) + 'px';
    if (ouvert) {
      morph.style.width = largeur + 'px';
      morph.style.height = (card.offsetTop + card.offsetHeight + bords) + 'px';
    } else {
      morph.style.width = menu.offsetWidth + 'px';
      morph.style.height = menu.offsetHeight + 'px';
    }
  }

  function basculer(etat, auClavier) {
    ouvert = etat;
    menu.classList.toggle('is-open', etat);
    toggle.setAttribute('aria-expanded', String(etat));
    card.inert = !etat;
    mesurer();
    if (etat && auClavier) card.querySelector('a').focus({ preventScroll: true });
  }

  // `detail === 0` : le clic vient du clavier (Entrée, Espace). Le focus part
  // alors dans la carte ; à la souris il reste sur le bouton.
  toggle.addEventListener('click', e => basculer(!ouvert, e.detail === 0));

  menu.addEventListener('keydown', e => {
    if (!ouvert) return;
    if (e.key === 'Escape') { basculer(false); toggle.focus(); return; }
    if (e.key !== 'Tab') return;
    const cibles = [toggle, ...card.querySelectorAll('a')];
    const i = cibles.indexOf(document.activeElement);
    if (e.shiftKey && i <= 0) { e.preventDefault(); cibles[cibles.length - 1].focus(); }
    else if (!e.shiftKey && i === cibles.length - 1) { e.preventDefault(); cibles[0].focus(); }
  });

  document.addEventListener('pointerdown', e => {
    if (ouvert && !menu.contains(e.target)) basculer(false);
  });
  // Retour arrière : la page revient du cache du navigateur telle qu'on l'a
  // quittée, menu ouvert compris. On la rend fermée.
  window.addEventListener('pageshow', e => { if (e.persisted && ouvert) basculer(false); });
  window.addEventListener('resize', mesurer);
  mesurer();
})();
