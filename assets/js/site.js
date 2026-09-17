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
  // Each slide runs a pan/zoom animation lasting exactly DELAY ms; the slide
  // changes when that motion ends. One timer, always cleared before it is set,
  // and no hover pause (a cursor resting on the hero used to freeze slide 1).
  var hero = document.querySelector("[data-carousel]");
  if (hero) {
    var slides = Array.prototype.slice.call(hero.querySelectorAll(".hero-slide"));
    var dotWrap = hero.querySelector(".hero-dots");
    var i = 0, timer = null, DELAY = 7000;
    hero.style.setProperty("--hero-ms", DELAY + "ms");

    var dots = slides.map(function (_, idx) {
      var b = document.createElement("button");
      b.setAttribute("aria-label", "Go to slide " + (idx + 1));
      b.addEventListener("click", function () { show(idx); });
      if (dotWrap) dotWrap.appendChild(b);
      return b;
    });

    function restartMotion(el) {
      el.style.animation = "none";
      void el.offsetWidth; // force reflow so the animation starts from frame 0
      el.style.animation = "";
    }
    function show(n) {
      n = (n + slides.length) % slides.length;
      restartMotion(slides[n]);
      slides.forEach(function (s, idx) { s.classList.toggle("active", idx === n); });
      dots.forEach(function (d, idx) { d.classList.toggle("active", idx === n); });
      i = n;
      clearTimeout(timer);
      if (slides.length > 1) timer = setTimeout(function () { show(i + 1); }, DELAY);
    }

    var prevBtn = hero.querySelector(".hero-arrow.prev");
    var nextBtn = hero.querySelector(".hero-arrow.next");
    if (prevBtn) prevBtn.addEventListener("click", function () { show(i - 1); });
    if (nextBtn) nextBtn.addEventListener("click", function () { show(i + 1); });

    // Background tabs throttle timers but pause animations; resync on return.
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) clearTimeout(timer); else show(i);
    });

    show(0);
  }

  /* ---- Hero typewriter: design, build, test (test gets bolded) ---- */
  var typeEl = document.querySelector("[data-type-words]");
  var calm = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (typeEl && !calm) {
    var words = typeEl.getAttribute("data-type-words").split(",");
    var TYPE = 110, ERASE = 60;
    var wait = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
    var typeWord = function (w) {
      var k = 0;
      return (function step() {
        if (k > w.length) return Promise.resolve();
        typeEl.textContent = w.slice(0, k++);
        return wait(TYPE).then(step);
      })();
    };
    var eraseWord = function () {
      return (function step() {
        var t = typeEl.textContent;
        if (!t) return Promise.resolve();
        typeEl.textContent = t.slice(0, -1);
        return wait(ERASE).then(step);
      })();
    };
    var runWord = function (idx) {
      var w = words[idx];
      var last = idx === words.length - 1;
      var chain = typeWord(w).then(function () { return wait(last ? 450 : 1000); });
      if (last) {
        chain = chain
          .then(function () { typeEl.classList.add("is-bold"); return wait(1000); })
          .then(function () { typeEl.classList.remove("is-bold"); return wait(600); });
      }
      return chain.then(eraseWord).then(function () { return wait(350); })
        .then(function () { return runWord((idx + 1) % words.length); });
    };
    typeEl.textContent = "";
    wait(400).then(function () { runWord(0); });
  }

  /* ---- Spin-and-grow transition for turbine links ---- */
  document.querySelectorAll("[data-spin-link]").forEach(function (link) {
    link.addEventListener("click", function (e) {
      if (calm || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      e.preventDefault();
      link.classList.add("is-spinning");
      document.body.classList.add("is-leaving");
      try { sessionStorage.setItem("spinIn", "1"); } catch (err) {}
      setTimeout(function () { window.location.href = link.href; }, 650);
    });
  });
  try {
    if (sessionStorage.getItem("spinIn") === "1") {
      sessionStorage.removeItem("spinIn");
      document.body.classList.add("page-in");
    }
  } catch (err) {}
  // Coming back via the back button restores the page from cache mid-animation.
  window.addEventListener("pageshow", function (e) {
    if (!e.persisted) return;
    document.body.classList.remove("is-leaving");
    document.querySelectorAll(".is-spinning").forEach(function (el) { el.classList.remove("is-spinning"); });
  });

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
