/* ═══════════════════════════════════════════════
   DRA. GABRIELA ESCOBAR · script.js
   Calculadora · Carrusel · AOS · Comentarios
═══════════════════════════════════════════════ */

'use strict';

/* ────────────────────────────────────────────
   1. NAVBAR — scroll + hamburger
──────────────────────────────────────────── */
const navbar    = document.getElementById('navbar');
const hamburger = document.getElementById('hamburger');
const navLinks  = document.getElementById('navLinks');
const navLinkItems = document.querySelectorAll('.nav-link');

window.addEventListener('scroll', () => {
  navbar.classList.toggle('scrolled', window.scrollY > 20);
  highlightActiveSection();
});

hamburger.addEventListener('click', () => {
  hamburger.classList.toggle('open');
  navLinks.classList.toggle('open');
  document.body.style.overflow = navLinks.classList.contains('open') ? 'hidden' : '';
});

navLinks.querySelectorAll('a').forEach(link => {
  link.addEventListener('click', () => {
    hamburger.classList.remove('open');
    navLinks.classList.remove('open');
    document.body.style.overflow = '';
  });
});

function highlightActiveSection() {
  const sections = document.querySelectorAll('section[id]');
  let current = '';
  sections.forEach(sec => {
    const top = sec.offsetTop - 100;
    if (window.scrollY >= top) current = sec.id;
  });
  navLinkItems.forEach(link => {
    link.classList.toggle('active', link.getAttribute('href') === `#${current}`);
  });
}

/* ────────────────────────────────────────────
   2. AOS — scroll reveal
──────────────────────────────────────────── */
function initAOS() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const delay = entry.target.dataset.delay || 0;
        setTimeout(() => {
          entry.target.classList.add('aos-visible');
        }, parseInt(delay));
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

  document.querySelectorAll('[data-aos]').forEach(el => observer.observe(el));
}
document.addEventListener('DOMContentLoaded', initAOS);

/* ────────────────────────────────────────────
   3. MACRO CALCULATOR
──────────────────────────────────────────── */
document.getElementById('calcBtn').addEventListener('click', calculateMacros);

function calculateMacros() {
  const age      = parseInt(document.getElementById('calc-age').value);
  const sex      = document.getElementById('calc-sex').value;
  const weight   = parseFloat(document.getElementById('calc-weight').value);
  const height   = parseFloat(document.getElementById('calc-height').value);
  const activity = parseFloat(document.getElementById('calc-activity').value);
  const goal     = document.querySelector('input[name="goal"]:checked').value;

  // Validation
  if (!age || !weight || !height || age < 15 || age > 90 || weight < 30 || height < 100) {
    shakeButton();
    showError('Por favor completa todos los campos con valores válidos.');
    return;
  }

  // Mifflin-St Jeor BMR
  let tmb;
  if (sex === 'female') {
    tmb = (10 * weight) + (6.25 * height) - (5 * age) - 161;
  } else {
    tmb = (10 * weight) + (6.25 * height) - (5 * age) + 5;
  }

  // TDEE
  const tdee = tmb * activity;

  // Calorie target & macro ratios
  let targetCals, protRatio, carbRatio, fatRatio;

  switch (goal) {
    case 'fat_loss':
      targetCals = tdee - 500;
      protRatio  = 0.40;
      carbRatio  = 0.30;
      fatRatio   = 0.30;
      break;
    case 'maintenance':
      targetCals = tdee;
      protRatio  = 0.30;
      carbRatio  = 0.40;
      fatRatio   = 0.30;
      break;
    case 'muscle_gain':
      targetCals = tdee + 300;
      protRatio  = 0.30;
      carbRatio  = 0.50;
      fatRatio   = 0.20;
      break;
  }

  // Grams per macro
  const protG = Math.round((targetCals * protRatio) / 4);
  const carbG = Math.round((targetCals * carbRatio) / 4);
  const fatG  = Math.round((targetCals * fatRatio)  / 9);

  // Render results
  document.getElementById('res-tmb').textContent  = Math.round(tmb).toLocaleString('es');
  document.getElementById('res-tdee').textContent = Math.round(targetCals).toLocaleString('es');
  document.getElementById('res-prot').textContent = `${protG} g`;
  document.getElementById('res-carb').textContent = `${carbG} g`;
  document.getElementById('res-fat').textContent  = `${fatG} g`;

  // Donut chart
  renderDonut(protRatio, carbRatio, fatRatio);

  // Show results
  document.querySelector('.results-placeholder').style.display = 'none';
  const content = document.getElementById('resultsContent');
  content.style.display = 'block';
  content.style.animation = 'fadeInUp .5s ease both';

  // Scroll to results on mobile
  if (window.innerWidth < 768) {
    setTimeout(() => {
      content.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  }
}

function renderDonut(prot, carb, fat) {
  const donut = document.getElementById('macrosDonut');
  const protPct = Math.round(prot * 100);
  const carbPct = Math.round(carb * 100);
  const fatPct  = Math.round(fat  * 100);

  // SVG donut
  const r = 44;
  const circumference = 2 * Math.PI * r;
  const gap = 2;

  const segments = [
    { pct: protPct, color: '#5BA896', label: 'P' },
    { pct: carbPct, color: '#4A90D9', label: 'C' },
    { pct: fatPct,  color: '#E67E22', label: 'G' },
  ];

  let offset = 0;
  const paths = segments.map(seg => {
    const dash   = (seg.pct / 100) * (circumference - gap * 3);
    const space  = circumference - dash;
    const rotate = (offset / 100) * 360 - 90;
    offset += seg.pct;
    return `<circle
      cx="56" cy="56" r="${r}"
      fill="none"
      stroke="${seg.color}"
      stroke-width="20"
      stroke-dasharray="${dash} ${space}"
      stroke-linecap="round"
      transform="rotate(${rotate} 56 56)"
      style="transition: stroke-dasharray .8s ease"
    />`;
  }).join('');

  donut.innerHTML = `
    <svg viewBox="0 0 112 112" width="120" height="120">
      <circle cx="56" cy="56" r="${r}" fill="none" stroke="rgba(255,255,255,.06)" stroke-width="20"/>
      ${paths}
      <text x="56" y="52" text-anchor="middle" fill="white" font-size="11" font-weight="700" font-family="Inter,sans-serif">Macros</text>
      <text x="56" y="66" text-anchor="middle" fill="rgba(255,255,255,.5)" font-size="9" font-family="Inter,sans-serif">diarios</text>
    </svg>`;
}

function shakeButton() {
  const btn = document.getElementById('calcBtn');
  btn.style.animation = 'shake .4s ease';
  setTimeout(() => btn.style.animation = '', 400);
}

function showError(msg) {
  const existing = document.getElementById('calcError');
  if (existing) existing.remove();
  const err = document.createElement('p');
  err.id = 'calcError';
  err.style.cssText = 'color:#ff7070;font-size:.83rem;margin-top:8px;text-align:center;';
  err.textContent = msg;
  document.getElementById('calcBtn').insertAdjacentElement('afterend', err);
  setTimeout(() => err.remove(), 4000);
}

// CSS keyframes via JS
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  @keyframes fadeInUp { from { opacity:0; transform:translateY(20px); } to { opacity:1; transform:translateY(0); } }
  @keyframes shake {
    0%,100% { transform:translateX(0); }
    20%     { transform:translateX(-8px); }
    40%     { transform:translateX(8px); }
    60%     { transform:translateX(-5px); }
    80%     { transform:translateX(5px); }
  }
`;
document.head.appendChild(styleSheet);

/* ────────────────────────────────────────────
   4. TESTIMONIALS CAROUSEL
──────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  const track   = document.getElementById('carouselTrack');
  const dotsBox = document.getElementById('carouselDots');
  const prevBtn = document.getElementById('prevBtn');
  const nextBtn = document.getElementById('nextBtn');

  if (!track) return;

  const cards    = track.querySelectorAll('.testimonial-card');
  const visCount = window.innerWidth <= 768 ? 1 : 2;
  const total    = cards.length;
  let   current  = 0;
  let   autoplay;

  // Build dots
  const maxDots = total - (visCount - 1);
  for (let i = 0; i < maxDots; i++) {
    const dot = document.createElement('div');
    dot.className = 'dot' + (i === 0 ? ' active' : '');
    dot.addEventListener('click', () => goTo(i));
    dotsBox.appendChild(dot);
  }

  function goTo(idx) {
    const maxIdx = Math.max(0, total - visCount);
    current = Math.max(0, Math.min(idx, maxIdx));

    const cardWidth = cards[0].offsetWidth + 24; // gap = 24px
    track.style.transform = `translateX(-${current * cardWidth}px)`;
    track.style.transition = 'transform .5s cubic-bezier(.4,0,.2,1)';

    dotsBox.querySelectorAll('.dot').forEach((d, i) => d.classList.toggle('active', i === current));
  }

  prevBtn.addEventListener('click', () => { goTo(current - 1); resetAuto(); });
  nextBtn.addEventListener('click', () => { goTo(current + 1); resetAuto(); });

  function startAuto() {
    autoplay = setInterval(() => {
      const maxIdx = total - visCount;
      goTo(current < maxIdx ? current + 1 : 0);
    }, 5000);
  }

  function resetAuto() {
    clearInterval(autoplay);
    startAuto();
  }

  // Touch / swipe support
  let touchStartX = 0;
  track.addEventListener('touchstart', e => { touchStartX = e.touches[0].clientX; }, { passive: true });
  track.addEventListener('touchend',   e => {
    const diff = touchStartX - e.changedTouches[0].clientX;
    if (Math.abs(diff) > 50) { diff > 0 ? goTo(current + 1) : goTo(current - 1); resetAuto(); }
  });

  startAuto();

  // Recalculate on resize
  window.addEventListener('resize', () => {
    track.style.transition = 'none';
    goTo(0);
  });
});

/* ────────────────────────────────────────────
   5. BLOG COMMENTS (localStorage)
──────────────────────────────────────────── */
function addComment(postId) {
  const nameEl = document.getElementById(`comment-name-${postId}`);
  const textEl = document.getElementById(`comment-text-${postId}`);
  const name   = nameEl.value.trim();
  const text   = textEl.value.trim();

  if (!name || !text) {
    textEl.style.borderColor = '#ff7070';
    setTimeout(() => textEl.style.borderColor = '', 2000);
    return;
  }

  const comment = { name, text, date: new Date().toLocaleDateString('es-EC') };
  const key     = `comments_post_${postId}`;
  const stored  = JSON.parse(localStorage.getItem(key) || '[]');
  stored.push(comment);
  localStorage.setItem(key, JSON.stringify(stored));

  nameEl.value = '';
  textEl.value = '';

  renderComments(postId);
}

function renderComments(postId) {
  const key      = `comments_post_${postId}`;
  const stored   = JSON.parse(localStorage.getItem(key) || '[]');
  const listEl   = document.getElementById(`comment-list-${postId}`);
  if (!listEl) return;

  listEl.innerHTML = stored.map(c => `
    <div class="comment-item">
      <div class="comment-author">
        ${escapeHtml(c.name)} <span>${c.date}</span>
      </div>
      <div class="comment-body">${escapeHtml(c.text)}</div>
    </div>
  `).join('');
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}

// Load stored comments on page load
document.addEventListener('DOMContentLoaded', () => {
  [1, 2, 3].forEach(id => renderComments(id));
});

/* ────────────────────────────────────────────
   6. CONTACT FORM
──────────────────────────────────────────── */
/* ── Web3Forms submit ── */
async function submitWeb3Form(e) {
  e.preventDefault();

  const form    = document.getElementById('contactForm');
  const success = document.getElementById('formSuccess');
  const errBox  = document.getElementById('formError');
  const btn     = document.getElementById('submitBtn');
  const original = btn.innerHTML;

  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';
  btn.disabled  = true;
  errBox.style.display = 'none';

  const data = new FormData(form);

  try {
    const res  = await fetch('https://api.web3forms.com/submit', {
      method: 'POST',
      body: data
    });
    const json = await res.json();

    if (json.success) {
      form.style.display    = 'none';
      success.style.display = 'block';
      success.style.animation = 'fadeInUp .5s ease both';
    } else {
      throw new Error(json.message || 'Error desconocido');
    }
  } catch (err) {
    console.error('Web3Forms error:', err);
    errBox.style.display = 'flex';
    btn.innerHTML = original;
    btn.disabled  = false;
  }
}

/* ────────────────────────────────────────────
   7. SMOOTH SCROLL OFFSET (for fixed navbar)
──────────────────────────────────────────── */
document.querySelectorAll('a[href^="#"]').forEach(link => {
  link.addEventListener('click', function(e) {
    const target = document.querySelector(this.getAttribute('href'));
    if (!target) return;
    e.preventDefault();
    const navH   = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--nav-h'));
    const top    = target.getBoundingClientRect().top + window.scrollY - navH - 16;
    window.scrollTo({ top, behavior: 'smooth' });
  });
});

/* ────────────────────────────────────────────
   8. PHARMACOLOGY CARD HOVER EFFECT
──────────────────────────────────────────── */
document.querySelectorAll('.pharma-card').forEach(card => {
  card.addEventListener('mouseenter', () => {
    card.style.borderColor = 'var(--mint-light)';
  });
  card.addEventListener('mouseleave', () => {
    card.style.borderColor = '';
  });
});

/* ────────────────────────────────────────────
   9. NUMBER COUNTER ANIMATION (hero stats)
──────────────────────────────────────────── */
function animateCounter(el, target, suffix, duration = 1800) {
  const isFloat  = target.toString().includes('.');
  const numVal   = parseFloat(target);
  const start    = performance.now();

  function update(now) {
    const elapsed  = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased    = 1 - Math.pow(1 - progress, 3); // ease-out cubic
    const current  = numVal * eased;

    el.textContent = (isFloat ? current.toFixed(1) : Math.round(current)) + suffix;
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

const statsObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const stats = entry.target.querySelectorAll('.stat-num');
      stats.forEach(stat => {
        const text   = stat.textContent;
        const num    = parseFloat(text.replace(/[^0-9.]/g, ''));
        const suffix = text.replace(/[0-9.]/g, '');
        animateCounter(stat, num, suffix);
      });
      statsObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.5 });

document.querySelector('.hero-stats') && statsObserver.observe(document.querySelector('.hero-stats'));

/* ────────────────────────────────────────────
   10. CASES CAROUSEL (Resultados Reales)
──────────────────────────────────────────── */
(function initCasesCarousel() {
  const track   = document.getElementById('casesTrack');
  const prevBtn = document.getElementById('casesPrev');
  const nextBtn = document.getElementById('casesNext');
  const dotsEl  = document.getElementById('casesDots');
  const counter = document.getElementById('casesCurrentNum');
  if (!track || !prevBtn || !nextBtn) return;

  const dots  = dotsEl ? dotsEl.querySelectorAll('.case-dot') : [];
  const total = track.querySelectorAll('.case-slide').length;
  let current = 0;
  let isAnimating = false;

  function goToCase(idx) {
    if (isAnimating) return;
    isAnimating = true;
    current = ((idx % total) + total) % total;
    track.style.transform = `translateX(-${current * 100}%)`;
    dots.forEach((d, i) => d.classList.toggle('active', i === current));
    if (counter) counter.textContent = current + 1;
    setTimeout(() => { isAnimating = false; }, 460);
  }

  prevBtn.addEventListener('click', () => goToCase(current - 1));
  nextBtn.addEventListener('click', () => goToCase(current + 1));
  dots.forEach(dot => dot.addEventListener('click', () => goToCase(+dot.dataset.idx)));

  // Touch / swipe support
  let startX = 0;
  const viewport = track.parentElement;
  viewport.addEventListener('touchstart', e => {
    startX = e.touches[0].clientX;
  }, { passive: true });
  viewport.addEventListener('touchend', e => {
    const diff = startX - e.changedTouches[0].clientX;
    if (Math.abs(diff) > 50) goToCase(diff > 0 ? current + 1 : current - 1);
  });

  // Keyboard navigation when carousel is focused or hovered
  document.addEventListener('keydown', e => {
    const carousel = document.getElementById('casesCarousel');
    if (!carousel) return;
    const rect = carousel.getBoundingClientRect();
    const inView = rect.top < window.innerHeight && rect.bottom > 0;
    if (!inView) return;
    if (e.key === 'ArrowLeft')  goToCase(current - 1);
    if (e.key === 'ArrowRight') goToCase(current + 1);
  });
})();

/* ────────────────────────────────────────────
   11. INIT
──────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  // Set navbar as scrolled on reload if not at top
  if (window.scrollY > 20) navbar.classList.add('scrolled');

  console.log('%c🩺 Dra. Gabriela Escobar · Obesidad & Diabetes',
    'background:#0D2847;color:#A8D5C8;font-size:14px;padding:8px 16px;border-radius:4px;font-weight:bold;');
  console.log('%cSitio web desarrollado con cuidado · Quito, Ecuador',
    'color:#5BA896;font-size:12px;');
});

/* ────────────────────────────────────────────
   12. BIO-PRECISE™ CALCULADORAS
──────────────────────────────────────────── */

/* -- Tab switching -- */
function bpSwitchTab(tab) {
  const isInsulin = tab === 'insulin';
  document.getElementById('bp-panel-insulin').style.display   = isInsulin ? 'block' : 'none';
  document.getElementById('bp-panel-metabolic').style.display = isInsulin ? 'none'  : 'block';
  document.getElementById('bp-tab-insulin').classList.toggle('bp-tab-active',  isInsulin);
  document.getElementById('bp-tab-metabolic').classList.toggle('bp-tab-active', !isInsulin);
}

/* ---- COMPONENTE 1: Test de Resistencia a la Insulina ---- */
const bpInsulinQ = [
  { text: '¿Tienes manchas oscuras en el cuello, axilas o ingles (acantosis nigricans) o pequeñas bolitas colgantes en la piel (acrocordones)?', pts: 3 },
  { text: '¿Tu cintura mide más de 88 cm si eres mujer, o más de 102 cm si eres hombre?', pts: 2 },
  { text: '¿Sientes mucho sueño o cansancio después de comer?', pts: 1 },
  { text: '¿Sientes ansiedad intensa o "necesidad urgente" de comer dulces o carbohidratos?', pts: 1 },
  { text: '¿Te cuesta mucho bajar de peso a pesar de hacer dieta o ejercicio?', pts: 1 }
];

let bpIQ = 0;
let bpIS = 0;

function bpShowInsulinQ() {
  const el = document.getElementById('bp-q-insulin');
  if (!el) return;
  el.innerHTML = '<h3>' + bpInsulinQ[bpIQ].text + '</h3>';
  document.getElementById('bp-q-counter-insulin').textContent = 'Pregunta ' + (bpIQ + 1) + ' de ' + bpInsulinQ.length;
  document.getElementById('bp-progress-insulin').style.width  = ((bpIQ / bpInsulinQ.length) * 100) + '%';
}

function bpAnswerInsulin(yes) {
  if (yes) bpIS += bpInsulinQ[bpIQ].pts;
  bpIQ++;
  if (bpIQ < bpInsulinQ.length) {
    var el = document.getElementById('bp-q-insulin');
    el.style.opacity = '0';
    setTimeout(function() {
      bpShowInsulinQ();
      el.style.opacity = '1';
    }, 220);
  } else {
    document.getElementById('bp-progress-insulin').style.width = '100%';
    setTimeout(function() {
      document.getElementById('bp-step-insulin-quiz').style.display = 'none';
      document.getElementById('bp-step-insulin-lead').style.display = 'block';
    }, 350);
  }
}

function bpRevealInsulinResult() {
  var name = document.getElementById('bp-name-insulin').value.trim();
  var wa   = document.getElementById('bp-wa-insulin').value.trim();
  if (!name || !wa) { alert('Por favor ingresa tu nombre y WhatsApp para ver tu resultado.'); return; }

  var risk, lvl, txt;
  if (bpIS >= 4) {
    risk = 'ALTO'; lvl = 'red';
    txt = 'Tu puntaje indica una <strong>alta probabilidad de resistencia a la insulina</strong>. Estos marcadores son señales tempranas que, sin atención médica, pueden progresar a prediabetes o diabetes tipo 2.';
  } else if (bpIS >= 2) {
    risk = 'MODERADO'; lvl = 'yellow';
    txt = 'Tu puntaje sugiere un <strong>riesgo moderado</strong>. Es importante monitorear estos indicadores con un especialista para prevenir el avance hacia resistencia insulínica establecida.';
  } else {
    risk = 'BAJO'; lvl = 'green';
    txt = 'Tu puntaje indica un <strong>riesgo bajo de resistencia a la insulina</strong>. Sigue manteniendo tus hábitos saludables. Una evaluación médica periódica es siempre recomendable.';
  }

  document.getElementById('bp-step-insulin-lead').style.display   = 'none';
  document.getElementById('bp-step-insulin-result').style.display = 'block';

  ['green','yellow','red'].forEach(function(c) {
    document.getElementById('bp-light-insulin-' + c).classList.remove('bp-active');
  });
  document.getElementById('bp-light-insulin-' + lvl).classList.add('bp-active');
  document.getElementById('bp-result-insulin-text').innerHTML = txt;

  var cta = document.getElementById('bp-result-insulin-cta');
  if (lvl !== 'green') {
    cta.style.display = 'block';
    var msg = encodeURIComponent('Hola Dra. Gabriela, termine mi test de resistencia a la insulina y mi riesgo es ' + risk + '. Me llamo ' + name + '. Quiero agendar una evaluacion en Edificio Metrocity ($60).');
    document.getElementById('bp-wa-link-insulin').href = 'https://wa.me/593998944730?text=' + msg;
  } else {
    cta.style.display = 'none';
  }
}

function bpResetInsulin() {
  bpIQ = 0; bpIS = 0;
  document.getElementById('bp-step-insulin-result').style.display = 'none';
  document.getElementById('bp-step-insulin-lead').style.display   = 'none';
  document.getElementById('bp-step-insulin-quiz').style.display   = 'block';
  document.getElementById('bp-name-insulin').value = '';
  document.getElementById('bp-wa-insulin').value   = '';
  bpShowInsulinQ();
}

/* ---- COMPONENTE 2: Escaneo de Vitalidad Metabólica ---- */
var bpMeta = {};

function bpCalculateMetabolic() {
  var edad     = parseInt(document.getElementById('bp-edad').value);
  var sexo     = document.getElementById('bp-sexo').value;
  var peso     = parseFloat(document.getElementById('bp-peso').value);
  var estatura = parseFloat(document.getElementById('bp-estatura').value);
  var cintura  = parseFloat(document.getElementById('bp-cintura').value);
  var cadera   = parseFloat(document.getElementById('bp-cadera').value);

  if (!edad || !peso || !estatura || !cintura || !cadera ||
      edad < 15 || edad > 90 || peso < 30 || estatura < 100 || cintura < 40 || cadera < 40) {
    alert('Por favor completa todos los campos con valores validos.');
    return;
  }

  var altM = estatura / 100;
  var imc  = peso / (altM * altM);
  var icc  = cintura / cadera;
  var ica  = cintura / estatura;

  var penalty = 0;
  if (imc >= 30)      penalty += 3;
  else if (imc >= 25) penalty += 1;

  var iccLim = sexo === 'female' ? 0.85 : 0.94;
  if (icc > iccLim) penalty += 3;
  if (ica > 0.5)    penalty += 2;

  if (document.getElementById('bp-tabaquismo').checked)  penalty += 3;
  if (document.getElementById('bp-sedentarismo').checked) penalty += 2;
  if (document.getElementById('bp-ronquidos').checked)    penalty += 2;

  bpMeta = { edad: edad, sexo: sexo, imc: imc, icc: icc, ica: ica, penalty: penalty, edadMeta: edad + penalty };

  document.getElementById('bp-step-meta-form').style.display = 'none';
  document.getElementById('bp-step-meta-lead').style.display = 'block';
}

function bpRevealMetabolicResult() {
  var name = document.getElementById('bp-name-meta').value.trim();
  var wa   = document.getElementById('bp-wa-meta').value.trim();
  if (!name || !wa) { alert('Por favor ingresa tu nombre y WhatsApp para ver tu resultado.'); return; }

  var edad = bpMeta.edad, sexo = bpMeta.sexo, imc = bpMeta.imc;
  var icc = bpMeta.icc, ica = bpMeta.ica, penalty = bpMeta.penalty, edadMeta = bpMeta.edadMeta;

  document.getElementById('bp-step-meta-lead').style.display   = 'none';
  document.getElementById('bp-step-meta-result').style.display = 'block';

  document.getElementById('bp-edad-real-display').textContent = edad;
  document.getElementById('bp-edad-meta-display').textContent = edadMeta;

  var metaEl = document.getElementById('bp-edad-meta-display');
  if (penalty >= 5) metaEl.classList.add('bp-danger');
  else              metaEl.classList.remove('bp-danger');

  var imcS, imcC;
  if (imc < 18.5)    { imcS = 'Bajo peso';  imcC = 'bp-metric-warn'; }
  else if (imc < 25) { imcS = 'Normal';     imcC = 'bp-metric-ok';   }
  else if (imc < 30) { imcS = 'Sobrepeso';  imcC = 'bp-metric-warn'; }
  else               { imcS = 'Obesidad';   imcC = 'bp-metric-bad';  }

  var iccLim = sexo === 'female' ? 0.85 : 0.94;
  var iccS = icc > iccLim ? 'Riesgo alto' : 'Normal';
  var iccC = icc > iccLim ? 'bp-metric-bad' : 'bp-metric-ok';
  var icaS = ica > 0.5 ? 'Riesgo alto' : 'Normal';
  var icaC = ica > 0.5 ? 'bp-metric-bad' : 'bp-metric-ok';

  document.getElementById('bp-metrics-grid').innerHTML =
    '<div class="bp-metric-card"><div class="bp-metric-label">IMC</div><div class="bp-metric-value">' + imc.toFixed(1) + '</div><div class="bp-metric-status ' + imcC + '">' + imcS + '</div></div>' +
    '<div class="bp-metric-card"><div class="bp-metric-label">ICC</div><div class="bp-metric-value">' + icc.toFixed(2) + '</div><div class="bp-metric-status ' + iccC + '">' + iccS + '</div></div>' +
    '<div class="bp-metric-card"><div class="bp-metric-label">ICA</div><div class="bp-metric-value">' + ica.toFixed(2) + '</div><div class="bp-metric-status ' + icaC + '">' + icaS + '</div></div>';

  var lvl, risk, txt;
  if (penalty >= 5) {
    lvl = 'red'; risk = 'ALTO';
    txt = 'Tu edad metabolica es <strong>' + penalty + ' años mayor que tu edad real</strong>. Tu cuerpo esta envejeciendo metabolicamente mas rapido de lo esperado. Con intervencion medica adecuada, este proceso es <strong>reversible</strong>.';
  } else if (penalty >= 2) {
    lvl = 'yellow'; risk = 'MODERADO';
    txt = 'Tu edad metabolica supera tu edad real en <strong>' + penalty + ' año' + (penalty > 1 ? 's' : '') + '</strong>. Existen factores de riesgo que conviene abordar con un especialista para revertir este proceso.';
  } else {
    lvl = 'green'; risk = 'BAJO';
    txt = '¡Excelente! Tu edad metabolica es practicamente igual a tu edad real. Tus indicadores metabolicos estan dentro de rangos saludables. Considera una evaluacion anual de seguimiento.';
  }

  ['green','yellow','red'].forEach(function(c) {
    document.getElementById('bp-light-meta-' + c).classList.remove('bp-active');
  });
  document.getElementById('bp-light-meta-' + lvl).classList.add('bp-active');
  document.getElementById('bp-result-meta-text').innerHTML = txt;

  var cta = document.getElementById('bp-result-meta-cta');
  if (lvl !== 'green') {
    cta.style.display = 'block';
    var msg = encodeURIComponent('Hola Dra. Gabriela, termine mi test metabolico y mi riesgo es ' + risk + '. Mi edad real es ' + edad + ' años y mi edad metabolica calculada es ' + edadMeta + ' años. Me llamo ' + name + '. Quiero agendar una cita en Edificio Metrocity ($60).');
    document.getElementById('bp-wa-link-meta').href = 'https://wa.me/593998944730?text=' + msg;
  } else {
    cta.style.display = 'none';
  }
}

function bpResetMetabolic() {
  bpMeta = {};
  document.getElementById('bp-step-meta-result').style.display = 'none';
  document.getElementById('bp-step-meta-lead').style.display   = 'none';
  document.getElementById('bp-step-meta-form').style.display   = 'block';
  ['bp-name-meta','bp-wa-meta'].forEach(function(id) { document.getElementById(id).value = ''; });
  ['bp-edad','bp-peso','bp-estatura','bp-cintura','bp-cadera'].forEach(function(id) { document.getElementById(id).value = ''; });
  ['bp-tabaquismo','bp-sedentarismo','bp-ronquidos'].forEach(function(id) { document.getElementById(id).checked = false; });
}

/* Init insulin quiz on page load */
document.addEventListener('DOMContentLoaded', bpShowInsulinQ);
