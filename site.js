/* ═══════════════════════════════════════════════
   DRA. GABRIELA ESCOBAR · site.js
   Script liviano para las páginas internas (servicios, sobre mí, legales):
   navbar al hacer scroll + menú hamburguesa.
═══════════════════════════════════════════════ */

'use strict';

(function () {
  const navbar    = document.getElementById('navbar');
  const hamburger = document.getElementById('hamburger');
  const navLinks  = document.getElementById('navLinks');
  if (!navbar || !hamburger || !navLinks) return;

  const onScroll = () => navbar.classList.toggle('scrolled', window.scrollY > 20);
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  const closeMenu = () => {
    hamburger.classList.remove('open');
    navLinks.classList.remove('open');
    hamburger.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  };

  hamburger.addEventListener('click', () => {
    const open = !navLinks.classList.contains('open');
    hamburger.classList.toggle('open', open);
    navLinks.classList.toggle('open', open);
    hamburger.setAttribute('aria-expanded', String(open));
    document.body.style.overflow = open ? 'hidden' : '';
  });

  navLinks.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeMenu(); });
})();
