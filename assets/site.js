/* The Pilates Room — the only two behaviours the site needs.
   No scroll-reveal: content is visible on arrival, which is faster, more
   accessible, and does not punish anyone who scrolls quickly. */
(function () {
  'use strict';
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* mobile menu */
  var burger = document.getElementById('burger');
  var mnav = document.getElementById('mnav');
  if (burger && mnav) {
    burger.addEventListener('click', function () {
      var open = mnav.classList.toggle('open');
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    document.addEventListener('keydown', function (ev) {
      if (ev.key === 'Escape' && mnav.classList.contains('open')) {
        mnav.classList.remove('open');
        burger.setAttribute('aria-expanded', 'false');
        burger.focus();
      }
    });
  }

  /* ---- the hero logo flies into the nav bar ----
     The logo is position:fixed over an in-flow slot. Inside the travel
     distance the translation is exactly -scrollY, so it rides up with the
     page rather than sliding on its own, shrinking as it goes and parking in
     the header. The header reserves its space but keeps it hidden, so with
     JavaScript off the hero simply keeps its logo and there is never a pair. */
  (function heroLogoFlight() {
    var logo = document.getElementById('heroLogo');
    var slot = document.querySelector('.hero-logo-slot');
    var target = document.getElementById('navLogoTarget');
    var hdr = document.querySelector('.hdr');
    if (!logo || !slot || !target || !document.body.classList.contains('home')) return;

    var img = logo.querySelector('img');
    var distance = 1, dx = 0, endScale = 1, ticking = false;
    logo.classList.add('is-flying');

    function measure() {
      logo.style.transform = 'none';
      logo.style.top = '0px';
      var s = slot.getBoundingClientRect();
      var startTop = s.top + window.scrollY;
      logo.style.top = startTop + 'px';
      var t = target.getBoundingClientRect();
      endScale = s.width ? t.width / s.width : 1;
      distance = Math.max(1, (startTop + s.height / 2) - (t.top + t.height / 2));
      // the hero mark is centred, the nav slot is left-aligned, so it has to
      // travel sideways as well as up
      dx = (s.left + s.width / 2) - (t.left + t.width / 2);
      render();
    }

    function render() {
      var p = Math.min(1, Math.max(0, window.scrollY / distance));
      if (reduce) p = p >= 0.5 ? 1 : 0;
      logo.style.transform =
        'translate3d(' + (-dx * p) + 'px,' + (-distance * p) + 'px,0) scale('
        + (1 + (endScale - 1) * p) + ')';
      // the shadow earns its keep over photography, not over the ivory bar
      img.style.filter = p > 0.72
        ? 'drop-shadow(0 2px 6px rgba(0,0,0,0))'
        : 'drop-shadow(0 6px 26px rgba(0,0,0,.45))';
      if (hdr) hdr.classList.toggle('solid', p > 0.72);
    }

    function onScroll() {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () { render(); ticking = false; });
    }

    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', measure);
    window.addEventListener('orientationchange', measure);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(measure);
    // the logo and its nav twin both affect the geometry, so re-measure once
    // each has actually decoded rather than trusting the first pass
    [img, target.querySelector('img')].forEach(function (el) {
      if (!el) return;
      if (el.complete) return;
      el.addEventListener('load', measure, { once: true });
    });
    if (window.ResizeObserver) new ResizeObserver(measure).observe(slot);
    measure();
  })();

  /* hero photography — crossfade, paused on hover and when the tab is hidden */
  var wrap = document.getElementById('heroSlides');
  var dotsWrap = document.getElementById('heroDots');
  if (!wrap) return;
  var slides = [].slice.call(wrap.querySelectorAll('figure'));
  var dots = dotsWrap ? [].slice.call(dotsWrap.children) : [];
  if (slides.length < 2) return;

  var i = 0, timer = null, HOLD = 6500;
  function show(n) {
    i = (n + slides.length) % slides.length;
    slides.forEach(function (s, k) { s.classList.toggle('on', k === i); });
    dots.forEach(function (d, k) { d.setAttribute('aria-current', k === i ? 'true' : 'false'); });
  }
  function start() { if (!reduce && !timer) timer = setInterval(function () { show(i + 1); }, HOLD); }
  function stop() { clearInterval(timer); timer = null; }

  dots.forEach(function (d, k) {
    d.addEventListener('click', function () { stop(); show(k); start(); });
  });
  wrap.addEventListener('mouseenter', stop);
  wrap.addEventListener('mouseleave', start);
  document.addEventListener('visibilitychange', function () { document.hidden ? stop() : start(); });
  start();
})();
