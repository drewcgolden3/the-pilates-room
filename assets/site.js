(function () {
  'use strict';
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* sticky header hairline */
  var hdr = document.getElementById('hdr');
  if (hdr) {
    var onScroll = function () { hdr.classList.toggle('stuck', window.scrollY > 10); };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* mobile menu */
  var burger = document.getElementById('burger'), mnav = document.getElementById('mnav');
  if (burger && mnav) {
    burger.addEventListener('click', function () {
      var open = mnav.classList.toggle('open');
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  /* hero slideshow — pauses when the tab is hidden or the pointer is over it */
  var slidesWrap = document.getElementById('heroSlides');
  var dotsWrap = document.getElementById('heroDots');
  if (slidesWrap) {
    var slides = [].slice.call(slidesWrap.children);
    var dots = dotsWrap ? [].slice.call(dotsWrap.children) : [];
    var i = 0, timer = null, HOLD = 6000;

    function show(n) {
      i = (n + slides.length) % slides.length;
      slides.forEach(function (s, k) { s.classList.toggle('on', k === i); });
      dots.forEach(function (d, k) { d.setAttribute('aria-current', k === i ? 'true' : 'false'); });
    }
    function start() { if (!reduce && slides.length > 1 && !timer) timer = setInterval(function () { show(i + 1); }, HOLD); }
    function stop() { clearInterval(timer); timer = null; }

    dots.forEach(function (d, k) {
      d.addEventListener('click', function () { stop(); show(k); start(); });
    });
    slidesWrap.addEventListener('mouseenter', stop);
    slidesWrap.addEventListener('mouseleave', start);
    document.addEventListener('visibilitychange', function () { document.hidden ? stop() : start(); });
    start();
  }

  /* scroll reveal */
  var els = document.querySelectorAll('[data-reveal]');
  if (reduce || !('IntersectionObserver' in window)) {
    [].forEach.call(els, function (el) { el.classList.add('in'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -10% 0px', threshold: 0.06 });
    [].forEach.call(els, function (el) { io.observe(el); });
  }
})();
