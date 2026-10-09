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
