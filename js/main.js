/* =========================================================
   Initializes Materialize components and adds:
     • Animate.css scroll-in animations
     • Stat count-up
   The site still works if JS fails to load.
   ========================================================= */

document.addEventListener('DOMContentLoaded', () => {
  // --- Materialize component init ---
  M.ScrollSpy.init(document.querySelectorAll('.scrollspy'), { scrollOffset: 80 });

  // --- Footer year (rolls over automatically) ---
  const yearEl = document.getElementById('year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  // --- Animate.css on scroll ---
  const animated = document.querySelectorAll('.will-animate');
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const el = entry.target;
        const anim = el.dataset.anim || 'animate__fadeInUp';
        const delay = parseInt(el.dataset.delay || '0', 10);
        setTimeout(() => {
          el.classList.add('animate__animated', anim);
        }, delay);
        io.unobserve(el);
      });
    }, { threshold: 0.15 });
    animated.forEach((el) => io.observe(el));
  } else {
    // No IO support — just reveal everything.
    animated.forEach((el) => el.classList.add('animate__animated'));
  }

  // --- Stat count-up ---
  const nums = document.querySelectorAll('.stat-num[data-count]');
  if (nums.length && 'IntersectionObserver' in window) {
    const animate = (el) => {
      const target = parseInt(el.dataset.count, 10);
      const start = performance.now();
      const step = (now) => {
        const p = Math.min((now - start) / 1400, 1);
        const eased = 1 - Math.pow(1 - p, 3);
        el.textContent = Math.floor(eased * target).toLocaleString();
        if (p < 1) requestAnimationFrame(step);
        else el.textContent = target.toLocaleString() + '+';
      };
      requestAnimationFrame(step);
    };
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) { animate(entry.target); io.unobserve(entry.target); }
      });
    }, { threshold: 0.6 });
    nums.forEach((n) => io.observe(n));
  }

  // --- Skill-card musings: reveal a panel above the hero, pushing it down ---
  const musing = document.getElementById('musing');
  if (musing) {
    const titleEl = musing.querySelector('.musing__title');
    const bodyEl = musing.querySelector('.musing__body');
    const cards = document.querySelectorAll('.mini-card--interactive');

    // A note may be split into "What I did" / "What I think" parts; render each
    // as a labelled section. Notes without the split fall back to raw content.
    const addSection = (heading, contentEl) => {
      if (!contentEl) return;
      const section = document.createElement('div');
      section.className = 'musing__section';
      const h = document.createElement('h4');
      h.className = 'musing__section-title';
      h.textContent = heading;
      const body = document.createElement('div');
      body.className = 'musing__section-body';
      body.innerHTML = contentEl.innerHTML;
      section.append(h, body);
      bodyEl.appendChild(section);
    };

    const openMusing = (card) => {
      const note = card.querySelector('.mini-card__note');
      if (!note) return;
      const label = card.querySelector('.mini-card__label');
      titleEl.textContent = label ? label.textContent : '';
      const did = note.querySelector('.mini-card__did');
      const think = note.querySelector('.mini-card__think');
      if (did || think) {
        bodyEl.innerHTML = '';
        addSection('What I did', did);
        addSection('What I think', think);
      } else {
        bodyEl.innerHTML = note.innerHTML;
      }
      musing.classList.add('musing--open');
      cards.forEach((c) => c.classList.toggle('mini-card--active', c === card));
    };
    const closeMusing = () => {
      musing.classList.remove('musing--open');
      cards.forEach((c) => c.classList.remove('mini-card--active'));
    };

    cards.forEach((card) => {
      // stopPropagation so this same click doesn't immediately trigger the
      // document-level "click anywhere to close" handler below.
      card.addEventListener('click', (e) => { e.stopPropagation(); openMusing(card); });
      card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); e.stopPropagation(); openMusing(card); }
      });
    });

    // Clicking anywhere hides it again and lets the hero move back up.
    document.addEventListener('click', () => {
      if (musing.classList.contains('musing--open')) closeMusing();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeMusing();
    });
  }
});
