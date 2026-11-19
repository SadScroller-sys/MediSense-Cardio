// MediSense-Cardio site: damage selector, traffic-light bars, dot grids, theme switch. No libraries.
(function () {
  "use strict";

  // ---- numbers (from results/FINAL_NUMBERS.md) ----
  var DATA = {
    res: [
      { big: "3.0%", hot: false, what: "of held-out pages gave a wrong heart rate on the clean page (3/99)." },
      { big: "1 to 6%", hot: false, what: "wrong at medium damage: every damage type stayed close to the clean page." },
      { big: "47.5%", hot: true, what: "wrong when the page is shrunk to 15% of its size (47 of 99 pages)." }
    ],
    blur: [
      { big: "3.0%", hot: false, what: "of held-out pages gave a wrong heart rate on the clean page (3/99)." },
      { big: "1 to 6%", hot: false, what: "wrong at medium damage: every damage type stayed close to the clean page." },
      { big: "17.2%", hot: true, what: "wrong with the heaviest blur, a 21 by 21 kernel (17 of 99 pages)." }
    ]
  };
  var kind = "res", level = 0;

  // ---- illustrative ECG strip (not patient data) ----
  var cv = document.getElementById("strip");
  var ctx = cv.getContext("2d");
  var W = cv.width, H = cv.height;
  var src = document.createElement("canvas");
  src.width = W; src.height = H;
  (function drawSource() {
    var c = src.getContext("2d");
    c.fillStyle = "#fff8f8"; c.fillRect(0, 0, W, H);
    for (var x = 0; x <= W; x += 6) { c.strokeStyle = "rgba(214,120,128,.35)"; c.lineWidth = 1; c.beginPath(); c.moveTo(x + .5, 0); c.lineTo(x + .5, H); c.stroke(); }
    for (var y = 0; y <= H; y += 6) { c.beginPath(); c.moveTo(0, y + .5); c.lineTo(W, y + .5); c.stroke(); }
    for (x = 0; x <= W; x += 30) { c.strokeStyle = "rgba(196,80,92,.6)"; c.beginPath(); c.moveTo(x + .5, 0); c.lineTo(x + .5, H); c.stroke(); }
    for (y = 0; y <= H; y += 30) { c.beginPath(); c.moveTo(0, y + .5); c.lineTo(W, y + .5); c.stroke(); }
    // one PQRST beat as a sum of gaussians
    function g(t, m, s, a) { return a * Math.exp(-Math.pow((t - m) / s, 2)); }
    function beat(t) { return g(t, 0.16, 0.035, 14) + g(t, 0.37, 0.011, -12) + g(t, 0.40, 0.012, 95) + g(t, 0.43, 0.012, -22) + g(t, 0.70, 0.06, 26); }
    var base = H * 0.62, period = 250; // pixels per beat
    c.strokeStyle = "#17151b"; c.lineWidth = 2; c.lineJoin = "round"; c.beginPath();
    for (var px = 0; px <= W; px++) {
      var t = (px % period) / period;
      var yy = base - beat(t) * 1.0;
      if (px === 0) c.moveTo(px, yy); else c.lineTo(px, yy);
    }
    c.stroke();
  })();

  function paint() {
    ctx.clearRect(0, 0, W, H);
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "low";
    if (kind === "res" && level > 0) {
      var f = level === 1 ? 0.2 : 0.07;           // exaggerated so the effect is visible on screen
      var w = Math.max(8, Math.round(W * f)), h = Math.max(4, Math.round(H * f));
      var tmp = document.createElement("canvas"); tmp.width = w; tmp.height = h;
      tmp.getContext("2d").drawImage(src, 0, 0, w, h);
      ctx.drawImage(tmp, 0, 0, W, H);
    } else if (kind === "blur" && level > 0) {
      ctx.filter = "blur(" + (level === 1 ? 3 : 7) + "px)";
      ctx.drawImage(src, 0, 0);
      ctx.filter = "none";
    } else {
      ctx.drawImage(src, 0, 0);
    }
  }

  function readout() {
    var d = DATA[kind][level];
    var big = document.getElementById("big");
    big.textContent = d.big;
    big.className = "big" + (d.hot ? " hot" : "");
    document.getElementById("what").textContent = d.what;
  }

  function setPressed(group, attr, val) {
    [].forEach.call(group.querySelectorAll("button"), function (b) { b.setAttribute("aria-pressed", String(b.getAttribute(attr) === String(val))); });
  }
  var groups = document.querySelectorAll(".seg");
  groups[0].addEventListener("click", function (e) { var b = e.target.closest("button"); if (!b) return; kind = b.getAttribute("data-kind"); setPressed(groups[0], "data-kind", kind); paint(); readout(); });
  groups[1].addEventListener("click", function (e) { var b = e.target.closest("button"); if (!b) return; level = +b.getAttribute("data-level"); setPressed(groups[1], "data-level", level); paint(); readout(); });
  paint(); readout();

  // ---- traffic-light bars (competition real captures, images with a reading) ----
  var L = [
    { name: "GREEN", color: "var(--green)", n: 917, wrong: 2, txt: "0.2% wrong (2 of 917)" },
    { name: "AMBER", color: "var(--amber)", n: 204, wrong: 14, txt: "6.9% wrong (14 of 204)" },
    { name: "RED", color: "var(--red)", n: 82, wrong: 30, txt: "36.6% wrong (30 of 82)" }
  ];
  var box = document.getElementById("lights");
  L.forEach(function (l) {
    var pct = (100 * l.wrong / l.n);
    var el = document.createElement("div");
    el.className = "light";
    el.innerHTML = '<span><i class="dot" style="background:' + l.color + '"></i><b>' + l.name + '</b></span>' +
      '<div class="bar-bg" role="img" aria-label="' + l.txt + '"><div class="bar-fg" style="width:' + Math.max(pct, 1.2).toFixed(1) + '%;background:' + l.color + '"></div></div>' +
      '<span class="vals">' + l.txt + '</span>';
    box.appendChild(el);
  });

  // ---- 40-dot grids ----
  function dots(id, bad) {
    var host = document.getElementById(id);
    for (var i = 0; i < 40; i++) { var d = document.createElement("i"); if (i < bad) d.className = "bad"; host.appendChild(d); }
  }
  dots("dots-before", 14);
  dots("dots-after", 2);

  // ---- look switch: paper (original, default) or blue ----
  var lookCss = document.getElementById("look-css"), lookBtn = document.getElementById("look");
  function showLook() { lookBtn.textContent = "Look: " + (lookCss.getAttribute("href") === "style.css" ? "blue" : "paper"); }
  showLook();
  lookBtn.addEventListener("click", function () {
    var toBlue = lookCss.getAttribute("href") !== "style.css";
    lookCss.setAttribute("href", toBlue ? "style.css" : "style-paper.css");
    try { localStorage.setItem("look", toBlue ? "blue" : "paper"); } catch (e) {}
    showLook();
  });

  // ---- theme switch (remembered when storage is allowed) ----
  var root = document.documentElement;
  try { var saved = localStorage.getItem("theme"); if (saved) root.setAttribute("data-theme", saved); } catch (e) {}
  document.getElementById("theme").addEventListener("click", function () {
    var dark = root.getAttribute("data-theme") === "dark" || (!root.getAttribute("data-theme") && window.matchMedia("(prefers-color-scheme: dark)").matches);
    var next = dark ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("theme", next); } catch (e) {}
  });
})();
