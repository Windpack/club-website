/* Windpack site interactions - vanilla JS, no dependencies */
(function () {
  "use strict";

  /* ---- Mobile nav toggle ---- */
  var nav = document.querySelector(".nav");
  var toggle = document.querySelector(".nav-toggle");
  if (nav && toggle) {
    toggle.addEventListener("click", function () {
      nav.classList.toggle("open");
      var open = nav.classList.contains("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    // Close the menu after tapping a link (mobile)
    nav.querySelectorAll(".nav-menu a").forEach(function (a) {
      a.addEventListener("click", function () { nav.classList.remove("open"); });
    });
  }

  /* ---- Sticky nav shadow on scroll ---- */
  if (nav) {
    var onScroll = function () {
      nav.classList.toggle("scrolled", window.scrollY > 12);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* ---- Hero carousel ---- */
  var hero = document.querySelector("[data-carousel]");
  if (hero) {
    var slides = Array.prototype.slice.call(hero.querySelectorAll(".hero-slide"));
    var dotWrap = hero.querySelector(".hero-dots");
    var i = 0, timer = null, DELAY = 6000;

    var dots = slides.map(function (_, idx) {
      var b = document.createElement("button");
      b.setAttribute("aria-label", "Go to slide " + (idx + 1));
      b.addEventListener("click", function () { go(idx); restart(); });
      if (dotWrap) dotWrap.appendChild(b);
      return b;
    });

    function show(n) {
      slides.forEach(function (s, idx) { s.classList.toggle("active", idx === n); });
      dots.forEach(function (d, idx) { d.classList.toggle("active", idx === n); });
      i = n;
    }
    function go(n) { show((n + slides.length) % slides.length); }
    function next() { go(i + 1); }
    function start() { if (slides.length > 1) timer = setInterval(next, DELAY); }
    function restart() { clearInterval(timer); start(); }

    var prevBtn = hero.querySelector(".hero-arrow.prev");
    var nextBtn = hero.querySelector(".hero-arrow.next");
    if (prevBtn) prevBtn.addEventListener("click", function () { go(i - 1); restart(); });
    if (nextBtn) nextBtn.addEventListener("click", function () { go(i + 1); restart(); });

    hero.addEventListener("mouseenter", function () { clearInterval(timer); });
    hero.addEventListener("mouseleave", start);

    show(0);
    start();
  }

  /* ---- Turbine development year tabs ---- */
  var tv = document.querySelector("[data-turbine-versions]");
  if (tv) {
    var tvTabs = Array.prototype.slice.call(tv.querySelectorAll(".tv-tab"));
    var tvPanels = Array.prototype.slice.call(tv.querySelectorAll(".tv-panel"));

    var selectYear = function (idx) {
      tvTabs.forEach(function (t, i) {
        var on = i === idx;
        t.classList.toggle("active", on);
        t.setAttribute("aria-selected", on ? "true" : "false");
        t.setAttribute("tabindex", on ? "0" : "-1");
      });
      tvPanels.forEach(function (p, i) { p.classList.toggle("active", i === idx); });
    };

    tvTabs.forEach(function (t, i) {
      t.addEventListener("click", function () { selectYear(i); });
      t.addEventListener("keydown", function (e) {
        var step = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
        if (!step) return;
        e.preventDefault();
        var n = (i + step + tvTabs.length) % tvTabs.length;
        tvTabs[n].focus();
        selectYear(n);
      });
    });

    // Respect whichever tab is marked active in the HTML
    var startAt = tvTabs.indexOf(tv.querySelector(".tv-tab.active"));
    selectYear(startAt < 0 ? 0 : startAt);
  }

  /* ---- Reveal on scroll ---- */
  var reveals = document.querySelectorAll(".reveal");
  if (reveals.length && "IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add("in"); });
  }

  /* ---- Dismissible applications badge ---- */
  var badge = document.querySelector(".meet-badge");
  if (badge) {
    if (sessionStorage.getItem("hideMeet") === "1") {
      badge.style.display = "none";
    }
    var close = badge.querySelector(".mb-close");
    if (close) close.addEventListener("click", function () {
      badge.style.display = "none";
      sessionStorage.setItem("hideMeet", "1");
    });
  }

  /* ---- Sponsorship tier stack: progress rail ---- */
  var stackCards = document.querySelector(".stack-cards");
  if (stackCards) {
    var tiers = [].slice.call(stackCards.querySelectorAll(".stier"));
    var marks = [].slice.call(document.querySelectorAll(".stack-rail-marks li"));
    var fill = document.querySelector(".stack-rail-fill");
    var queued = false;

    function paintRail() {
      queued = false;
      var active = 0;
      for (var i = 0; i < tiers.length; i++) {
        // A tier is "reached" once it has settled at its own sticky offset.
        var pin = parseFloat(window.getComputedStyle(tiers[i]).top) || 0;
        if (tiers[i].getBoundingClientRect().top <= pin + 6) active = i;
      }
      for (var j = 0; j < marks.length; j++) {
        marks[j].classList.toggle("is-active", j === active);
      }
      if (fill) fill.style.height = ((active + 1) / tiers.length) * 100 + "%";
    }
    var raf = window.requestAnimationFrame || function (fn) { return setTimeout(fn, 16); };
    function queueRail() {
      if (!queued) { queued = true; raf(paintRail); }
    }
    if (tiers.length) {
      window.addEventListener("scroll", queueRail, { passive: true });
      window.addEventListener("resize", queueRail);
      // Re-run once images have settled and after any scroll restoration.
      window.addEventListener("load", paintRail);
      document.addEventListener("visibilitychange", function () {
        if (!document.hidden) paintRail();
      });
      paintRail();
    }
  }

  /* ---- Current year in footer ---- */
  var yr = document.querySelector("[data-year]");
  if (yr) yr.textContent = new Date().getFullYear();
})();
