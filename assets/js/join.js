/* =====================================================================
   Windpack - Join page
   1. Rise-on-scroll for .jx-rise elements
   2. The hero wind tunnel: mouse movement and scrolling make "wind",
      the rotor speeds up with it, and the brake trips at 13 m/s.
   No dependencies.
   ===================================================================== */
(function () {
  "use strict";

  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- 1. Rise on scroll ---------- */
  var rises = document.querySelectorAll(".jx-rise");
  if (rises.length && "IntersectionObserver" in window && !reduce) {
    var riseIo = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("in"); riseIo.unobserve(e.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    rises.forEach(function (el) { riseIo.observe(el); });
  } else {
    rises.forEach(function (el) { el.classList.add("in"); });
  }

  /* ---------- 2. Wind tunnel ---------- */
  var root = document.querySelector("[data-tunnel]");
  var hero = document.querySelector(".jx-hero");
  if (!root || !hero) return;

  var rotor = root.querySelector("[data-rotor]");
  var windEl = root.querySelector("[data-wind]");
  var needle = root.querySelector("[data-needle]");
  var stateEl = root.querySelector("[data-state]");
  var tripsEl = root.querySelector("[data-trips]");
  var canvas = hero.querySelector(".jx-streaks");
  var ctx = canvas && canvas.getContext ? canvas.getContext("2d") : null;

  // Real numbers from the 2026 turbine: starts at 5 m/s, operating range
  // tops out at 11 m/s, built to survive 13 m/s.
  var CUT_IN = 5, RATED = 11, LIMIT = 13, MAX = 15, BREEZE = 2.2;
  var HUB = " 160 150)";
  var touch = window.matchMedia("(hover: none)").matches;
  var HOW = touch ? "Scroll to make wind." : "Move your mouse or scroll to make wind.";

  if (reduce) {
    // Leave the turbine still and keep the factual line that ships in the HTML.
    windEl.textContent = "0.0";
    return;
  }

  var pushed = 0;      // pixels of movement since the last frame
  var flow = 0;        // smoothed movement, px per second
  var wind = BREEZE;   // m/s
  var omega = 0;       // rotor speed, degrees per second
  var angle = 0;
  var brakeUntil = 0;
  var trips = 0;
  var lastState = "";
  var lastX = null, lastY = null, lastScroll = window.pageYOffset;
  var running = false, onScreen = true, last = 0;
  var streaks = [], W = 0, H = 0;

  window.addEventListener("pointermove", function (e) {
    if (e.pointerType === "touch") return;
    if (lastX !== null) pushed += Math.abs(e.clientX - lastX) + Math.abs(e.clientY - lastY);
    lastX = e.clientX; lastY = e.clientY;
  }, { passive: true });

  window.addEventListener("scroll", function () {
    var y = window.pageYOffset;
    pushed += Math.abs(y - lastScroll) * 0.7;
    lastScroll = y;
  }, { passive: true });

  function sizeCanvas() {
    if (!ctx) return;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = hero.clientWidth; H = hero.clientHeight;
    canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    var count = Math.max(14, Math.round(W / 42));
    streaks = [];
    for (var i = 0; i < count; i++) {
      streaks.push({ x: Math.random() * W, y: Math.random() * H, len: 30 + Math.random() * 90, z: 0.35 + Math.random() * 0.65 });
    }
  }

  function drawStreaks(dt) {
    if (!ctx) return;
    ctx.clearRect(0, 0, W, H);
    ctx.lineCap = "round";
    var speed = 26 + wind * 62;
    for (var i = 0; i < streaks.length; i++) {
      var s = streaks[i];
      s.x += speed * s.z * dt;
      if (s.x - s.len > W) { s.x = -10; s.y = Math.random() * H; }
      ctx.strokeStyle = "rgba(255,255,255," + (0.05 + s.z * 0.13).toFixed(3) + ")";
      ctx.lineWidth = s.z * 2;
      ctx.beginPath();
      ctx.moveTo(s.x - s.len * (0.5 + wind / MAX), s.y);
      ctx.lineTo(s.x, s.y);
      ctx.stroke();
    }
  }

  function say(key, text) {
    if (key === lastState) return;
    lastState = key;
    stateEl.textContent = text;
  }

  function frame(now) {
    if (!running) return;
    var dt = Math.min(0.05, (now - last) / 1000) || 0.016;
    last = now;

    var braking = now < brakeUntil;
    var rate = pushed / dt;
    pushed = 0;
    if (braking) rate = 0;
    flow += (rate - flow) * (1 - Math.exp(-dt * 3));

    var target = Math.min(MAX, BREEZE + flow / 170);
    wind += (target - wind) * (1 - Math.exp(-dt * 4));

    if (!braking && wind >= LIMIT) {
      brakeUntil = now + 2800;
      braking = true;
      flow = 0;
      trips += 1;
      root.classList.add("is-brake");
      tripsEl.hidden = false;
      tripsEl.textContent = "Brake trips: " + trips + (trips === 1 ? ". You would fit right in." : "");
    }
    if (!braking && root.classList.contains("is-brake")) root.classList.remove("is-brake");

    var omegaTarget;
    if (braking) omegaTarget = 0;
    else if (wind < CUT_IN) omegaTarget = (wind / CUT_IN) * 26;
    else omegaTarget = 26 + ((wind - CUT_IN) / (LIMIT - CUT_IN)) * 720;
    omega += (omegaTarget - omega) * (1 - Math.exp(-dt * (braking ? 7 : 2.4)));
    angle = (angle + omega * dt) % 360;
    rotor.setAttribute("transform", "rotate(" + angle.toFixed(1) + HUB);

    windEl.textContent = wind.toFixed(1);
    needle.style.left = Math.min(100, (wind / MAX) * 100).toFixed(1) + "%";
    hero.style.setProperty("--jx-wind", Math.min(1, wind / LIMIT).toFixed(3));

    if (braking) say("brake", "13 m/s! Brake on. That is the most our 2026 turbine was built to survive.");
    else if (wind < CUT_IN) say("calm", "Too calm. Our 2026 turbine starts at 5 m/s. " + HOW);
    else if (wind < RATED) say("run", "Making power. 5 to 11 m/s is the operating range.");
    else say("hot", "Past 11 m/s. Keep going and the brake trips at 13.");

    drawStreaks(dt);
    requestAnimationFrame(frame);
  }

  function start() {
    if (running || !onScreen || document.hidden) return;
    running = true;
    last = performance.now();
    pushed = 0;
    requestAnimationFrame(frame);
  }
  function stop() { running = false; }

  if ("IntersectionObserver" in window) {
    new IntersectionObserver(function (entries) {
      onScreen = entries[0].isIntersecting;
      if (onScreen) start(); else stop();
    }).observe(hero);
  }
  document.addEventListener("visibilitychange", function () {
    if (document.hidden) stop(); else start();
  });
  window.addEventListener("resize", sizeCanvas);

  sizeCanvas();
  start();
})();
