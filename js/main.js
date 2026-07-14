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
});
