(function () {
  "use strict";

  var RED = [0xcd, 0x28, 0x24], INK = [0, 0, 0];
  var W = 128, H = 64;

  // ---------- 3x5 LCD font (drawn for this page) ----------
  var FONT = {
    "A": ["###", "#.#", "###", "#.#", "#.#"], "B": ["##.", "#.#", "##.", "#.#", "##."],
    "C": ["###", "#..", "#..", "#..", "###"], "D": ["##.", "#.#", "#.#", "#.#", "##."],
    "E": ["###", "#..", "##.", "#..", "###"], "F": ["###", "#..", "##.", "#..", "#.."],
    "G": ["###", "#..", "#.#", "#.#", "###"], "H": ["#.#", "#.#", "###", "#.#", "#.#"],
    "I": ["###", ".#.", ".#.", ".#.", "###"], "J": ["..#", "..#", "..#", "#.#", "###"],
    "K": ["#.#", "#.#", "##.", "#.#", "#.#"], "L": ["#..", "#..", "#..", "#..", "###"],
    "M": ["#.#", "###", "###", "#.#", "#.#"], "N": ["##.", "#.#", "#.#", "#.#", "#.#"],
    "O": ["###", "#.#", "#.#", "#.#", "###"], "P": ["###", "#.#", "###", "#..", "#.."],
    "Q": ["###", "#.#", "#.#", "###", "..#"], "R": ["##.", "#.#", "##.", "#.#", "#.#"],
    "S": ["###", "#..", "###", "..#", "###"], "T": ["###", ".#.", ".#.", ".#.", ".#."],
    "U": ["#.#", "#.#", "#.#", "#.#", "###"], "V": ["#.#", "#.#", "#.#", "#.#", ".#."],
    "W": ["#.#", "#.#", "###", "###", "#.#"], "X": ["#.#", "#.#", ".#.", "#.#", "#.#"],
    "Y": ["#.#", "#.#", ".#.", ".#.", ".#."], "Z": ["###", "..#", ".#.", "#..", "###"],
    "0": ["###", "#.#", "#.#", "#.#", "###"], "1": [".#.", "##.", ".#.", ".#.", "###"],
    "2": ["###", "..#", "###", "#..", "###"], "3": ["###", "..#", ".##", "..#", "###"],
    "4": ["#.#", "#.#", "###", "..#", "..#"], "5": ["###", "#..", "###", "..#", "###"],
    "6": ["###", "#..", "###", "#.#", "###"], "7": ["###", "..#", "..#", ".#.", ".#."],
    "8": ["###", "#.#", "###", "#.#", "###"], "9": ["###", "#.#", "###", "..#", "###"],
    ":": [".", "#", ".", "#", "."], ".": [".", ".", ".", ".", "#"],
    "-": ["...", "...", "###", "...", "..."], "+": ["...", ".#.", "###", ".#.", "..."],
    ">": ["#..", "##.", "###", "##.", "#.."], " ": ["..", "..", "..", "..", ".."]
  };

  function Screen() {
    this.px = new Uint8Array(W * H); // 1 = ink
  }
  Screen.prototype.set = function (x, y, v) {
    if (x >= 0 && y >= 0 && x < W && y < H) this.px[y * W + x] = v ? 1 : 0;
  };
  Screen.prototype.fill = function (x, y, w, h, v) {
    for (var j = 0; j < h; j++) for (var i = 0; i < w; i++) this.set(x + i, y + j, v);
  };
  Screen.prototype.textWidth = function (s) {
    var w = 0;
    for (var i = 0; i < s.length; i++) w += (FONT[s[i]] || FONT[" "])[0].length + 1;
    return Math.max(0, w - 1);
  };
  Screen.prototype.text = function (s, x, y, v) {
    s = s.toUpperCase();
    for (var i = 0; i < s.length; i++) {
      var g = FONT[s[i]] || FONT[" "];
      for (var r = 0; r < 5; r++) for (var c = 0; c < g[r].length; c++) if (g[r][c] === "#") this.set(x + c, y + r, v);
      x += g[0].length + 1;
    }
  };
  Screen.prototype.textC = function (s, cx, y, v) { this.text(s, Math.round(cx - this.textWidth(s.toUpperCase()) / 2), y, v); };
  Screen.prototype.dotsV = function (x, y0, y1) { for (var y = y0; y <= y1; y += 2) this.set(x, y, 1); };
  Screen.prototype.dotsH = function (x0, x1, y) { for (var x = x0; x <= x1; x += 2) this.set(x, y, 1); };
  Screen.prototype.line = function (x0, y0, x1, y1) {
    var dx = Math.abs(x1 - x0), sx = x0 < x1 ? 1 : -1, dy = -Math.abs(y1 - y0), sy = y0 < y1 ? 1 : -1, e = dx + dy;
    for (;;) {
      this.set(x0, y0, 1);
      if (x0 === x1 && y0 === y1) break;
      var e2 = 2 * e;
      if (e2 >= dy) { e += dy; x0 += sx; }
      if (e2 <= dx) { e += dx; y0 += sy; }
    }
  };
  Screen.prototype.circle = function (cx, cy, r) {
    var x = r, y = 0, d = 1 - r;
    while (x >= y) {
      [[x, y], [y, x], [-y, x], [-x, y], [-x, -y], [-y, -x], [y, -x], [x, -y]].forEach(function (p) { this.set(cx + p[0], cy + p[1], 1); }, this);
      y++;
      if (d < 0) d += 2 * y + 1; else { x--; d += 2 * (y - x) + 1; }
    }
  };
  Screen.prototype.logo = function (rows, x0, y0) {
    for (var y = 0; y < rows.length; y++) for (var x = 0; x < rows[y].length; x++) if (rows[y][x] === "1") this.set(x0 + x, y0 + y, 1);
  };
  Screen.prototype.toCanvas = function (cv) {
    cv.width = W; cv.height = H;
    var ctx = cv.getContext("2d"), img = ctx.createImageData(W, H);
    for (var i = 0; i < W * H; i++) {
      var c = this.px[i] ? INK : RED;
      img.data[i * 4] = c[0]; img.data[i * 4 + 1] = c[1]; img.data[i * 4 + 2] = c[2]; img.data[i * 4 + 3] = 255;
    }
    ctx.putImageData(img, 0, 0);
  };

  // ---------- The synthesis page, laid out like the MD's ----------
  // 1px frame; top left the machine graphic (here its 32x24 logo) with the LEV meter beside it;
  // bottom left the kit box, pattern and machine path; right a 4 x 2 grid of labelled knobs.
  Screen.prototype.knob = function (cx, cy, t) {
    // ring of diameter 11
    var ring = [[-2,-5],[-1,-5],[0,-5],[1,-5],[2,-5],[-3,-4],[3,-4],[-4,-3],[4,-3],[-5,-2],[5,-2],[-5,-1],[5,-1],[-5,0],[5,0],
      [-5,1],[5,1],[-5,2],[5,2],[-4,3],[4,3],[-3,4],[3,4],[-2,5],[-1,5],[0,5],[1,5],[2,5]];
    ring.forEach(function (p) { this.set(cx + p[0], cy + p[1], 1); }, this);
    // pointer: a 2x2 dot inside the ring
    var a = (-135 + 270 * t) * Math.PI / 180;
    var px = Math.round(cx + Math.sin(a) * 2.6 - 0.5), py = Math.round(cy - Math.cos(a) * 2.6 - 0.5);
    this.fill(px, py, 2, 2, 1);
    // scale marks: centre above, end stops below left and right
    this.set(cx, cy - 7, 1);
    this.set(cx - 5, cy + 6, 1); this.set(cx + 5, cy + 6, 1);
  };

  function drawScreen(m) {
    var s = new Screen();
    s.fill(0, 0, W, 1, 1); s.fill(0, H - 1, W, 1, 1); s.fill(0, 0, 1, H, 1); s.fill(W - 1, 0, 1, H, 1);
    // machine graphic
    var logo = (window.LOGOS32 || {})[m.id];
    if (logo) s.logo(logo, 0, 4);          // ink in columns 2-29: one red column each side
    s.fill(31, 1, 1, 31, 1);
    // LEV meter
    s.text("LEV", 34, 3, 1);
    for (var y = 12; y <= 30; y += 3) { s.fill(34, y, 2, 1, 1); s.fill(44, y, 2, 1, 1); }
    s.fill(38, 30 - Math.round(18 * 100 / 127), 4, Math.round(18 * 100 / 127) + 1, 1);
    s.dotsV(47, 2, 32);
    // kit box, pattern, machine path
    s.fill(0, 33, 46, 13, 1);
    s.textC(m.id, 23, 34, 0);               // 1px black above, 1px between, 1px below
    s.textC("V" + m.version, 23, 40, 0);
    s.text(">A01", 2, 48, 1);
    s.fill(0, 54, 48, 10, 1);
    s.textC(m.category + ">" + m.id.split("-")[1] + ">USR", 24, 57, 0);
    // parameter grid
    var x0 = 48, cw = 20;
    for (var c = 1; c < 4; c++) s.dotsV(x0 + c * cw - 1, 2, 62);
    s.dotsH(47, 126, 10); s.dotsH(47, 126, 32); s.dotsH(47, 126, 42);
    m.params.forEach(function (p, i) {
      var col = i % 4, row = Math.floor(i / 4);
      var cx = x0 + col * cw + 9, top = row ? 35 : 3, ky = row ? 52 : 21;
      s.textC(p[0], cx, top, 1);
      // every parameter is drawn as a knob at its default (list parameters too, e.g. MODE, PLAY)
      var min = p[3] == null ? 0 : p[3], max = p[4] == null ? 127 : p[4];
      s.knob(cx, ky, (p[1] - min) / (max - min));
    });
    return s;
  }

  // ---------- DOM helpers ----------
  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  // Pixel-font square brackets are hard to read, so they are drawn as boxes.
  function bracketed(node, str) {
    str.split(/([\[\]])/).forEach(function (part) {
      if (!part) return;
      if (part === "[" || part === "]") {
        var b = el("span", "brk " + (part === "[" ? "brk-l" : "brk-r"));
        b.appendChild(el("span", "vh", part));
        node.appendChild(b);
        if (part === "[") node.appendChild(document.createElement("wbr"));
      } else node.appendChild(el("span", "nb", part));
    });
  }

  var screens = [];
  function fitScreens() {
    screens.forEach(function (cv) {
      var wrap = cv.parentNode, card = wrap.parentNode, cs = getComputedStyle(card), ws = getComputedStyle(wrap);
      var avail = card.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight)
        - parseFloat(ws.paddingLeft) - parseFloat(ws.paddingRight);
      var scale = Math.max(1, Math.min(5, Math.floor(avail / W)));
      cv.style.width = W * scale + "px";
      cv.style.height = H * scale + "px";
    });
  }

  function card(m) {
    var c = el("article", "card");
    c.id = m.id.toLowerCase();

    var head = el("header", "card-head");
    var h = el("h3", "card-name");
    bracketed(h, m.name);
    head.appendChild(h);
    head.appendChild(el("span", "card-ver", "v" + m.version));
    c.appendChild(head);

    var wrap = el("div", "lcd-wrap");
    var cv = el("canvas", "lcd");
    cv.setAttribute("role", "img");
    cv.setAttribute("aria-label", "Machinedrum screen for " + m.id + " with its logo and parameters " + m.params.map(function (p) { return p[0]; }).join(", "));
    drawScreen(m).toCanvas(cv);
    wrap.appendChild(cv);
    c.appendChild(wrap);
    screens.push(cv);

    c.appendChild(el("p", "card-desc", m.desc));

    if (m.demo) {
      var fig = el("figure", "demo");
      fig.appendChild(el("figcaption", null, m.demo.label));
      var au = el("audio");
      au.controls = true; au.preload = "none"; au.src = m.demo.file;
      if (m.demo.volume != null) au.volume = m.demo.volume;
      fig.appendChild(au);
      c.appendChild(fig);
    }

    var pl = el("dl", "params");
    m.params.forEach(function (p) {
      var row = el("div");
      row.appendChild(el("dt", null, p[0]));
      row.appendChild(el("dd", null, p[5]));
      pl.appendChild(row);
    });
    c.appendChild(pl);

    if (m.aware && m.aware.length) {
      var box = el("div", "aware");
      box.appendChild(el("h4", null, "Note"));
      var ul = el("ul");
      m.aware.forEach(function (t) { ul.appendChild(el("li", null, t)); });
      box.appendChild(ul);
      c.appendChild(box);
    }

    var tw = el("div", "tracks-wrap");
    tw.appendChild(el("h4", "sub", "Tracks"));
    var ram = m.category === "RAM";
    tw.appendChild(el("p", "tracks-cap", ram
      ? "RAM machines need one of the MD's RAM slots, so a pattern can play at most 4 of them on an MKII (R1–R4) and 2 on an MKI (R1–R2), shared with RAM-R and the other RAM machines."
      : "How many tracks of this machine one kit can run when it is on every track, estimated from its certified DSP cycles. Lighter machines on the other tracks leave room for more; the firmware does the budgeting."));
    var tr = el("dl", "tracks");
    [["MKII", ram ? "4" : m.tracks.mk2], ["MKI", ram ? "2" : m.tracks.mk1]].forEach(function (r) {
      var d = el("div");
      d.appendChild(el("dt", null, r[0]));
      d.appendChild(el("dd", null, r[1] + (ram ? " per pattern" : " tracks")));
      tr.appendChild(d);
    });
    tw.appendChild(tr);
    if (ram) tw.appendChild(el("p", "tracks-cap", "DSP alone would allow " + m.tracks.mk2 + " (MKII) / " + m.tracks.mk1 + " (MKI)."));
    c.appendChild(tw);

    c.appendChild(el("h4", "sub", m.variants.length > 1 ? "Versions by sample bank" : "Download"));
    var dl = el("ul", "downloads");
    m.variants.forEach(function (v) {
      var li = el("li");
      var a = el("a", "dl");
      a.href = v.file;
      a.setAttribute("download", "");
      var vi = el("img", "dl-logo");
      vi.src = v.logo; vi.alt = ""; vi.width = 48; vi.height = 36;
      a.appendChild(vi);
      var txt = el("span", "dl-text");
      txt.appendChild(el("b", null, v.id));
      var meta = el("span", "dl-meta", v.scope);
      if (v.compat) { meta.appendChild(document.createTextNode(" · ")); meta.appendChild(el("i", null, v.compat)); }
      txt.appendChild(meta);
      a.appendChild(txt);
      var btn = el("span", "dl-btn");
      btn.innerHTML = '<svg viewBox="0 0 10 10" width="10" height="10" aria-hidden="true"><path d="M4 0h2v5h2L5 8 2 5h2zM0 9h10v1H0z"/></svg>';
      btn.appendChild(el("span", null, "Download .syx"));
      a.appendChild(btn);
      li.appendChild(a);
      dl.appendChild(li);
    });
    c.appendChild(dl);
    return c;
  }

  // ---------- Sections ----------
  var SECTIONS = [
    { id: "samplers", cat: "SMP", title: "Samplers", sub: "Slice, stretch and granulate the UW ROM and E12 samples." },
    { id: "ram", cat: "RAM", title: "RAM machines", sub: "Record live audio into RAM and play it back." },
    { id: "nfx", cat: "NFX", title: "NFX effects", sub: "Effects that process the tracks before them." }
  ];

  var root = document.getElementById("machines");
  var machines = window.MACHINES || [];
  var nav = el("nav", "section-nav");
  nav.setAttribute("aria-label", "Sections");
  root.appendChild(nav);

  SECTIONS.forEach(function (s) {
    var list = machines.filter(function (m) { return m.category === s.cat; });
    if (!list.length) return;
    var a = el("a", null, s.title);
    a.href = "#" + s.id;
    a.appendChild(el("span", "count", String(list.length)));
    nav.appendChild(a);

    var sec = el("section", "machine-section");
    sec.id = s.id;
    sec.setAttribute("aria-labelledby", s.id + "-h");
    var h = el("h2", "section-head", s.title);
    h.id = s.id + "-h";
    sec.appendChild(h);
    sec.appendChild(el("p", "section-sub", s.sub));
    var grid = el("div", "grid");
    list.forEach(function (m) { grid.appendChild(card(m)); });
    sec.appendChild(grid);
    root.appendChild(sec);
  });

  // Category filter: choosing a section shows only that section; "All" shows everything.
  var allLink = el("a", "is-active", "All");
  allLink.href = "#all";
  allLink.appendChild(el("span", "count", String(machines.length)));
  nav.insertBefore(allLink, nav.firstChild);
  function applyFilter(id) {
    var shown = SECTIONS.some(function (s) { return s.id === id; }) ? id : "all";
    SECTIONS.forEach(function (s) {
      var sec = document.getElementById(s.id);
      if (sec) sec.hidden = !(shown === "all" || shown === s.id);
    });
    Array.prototype.forEach.call(nav.querySelectorAll("a"), function (a) {
      var on = a.getAttribute("href") === "#" + shown;
      a.classList.toggle("is-active", on);
      if (on) a.setAttribute("aria-current", "true"); else a.removeAttribute("aria-current");
    });
    fitScreens();
  }
  nav.addEventListener("click", function (e) {
    var a = e.target.closest("a");
    if (!a) return;
    e.preventDefault();
    var id = a.getAttribute("href").slice(1);
    var url = id === "all" ? location.pathname + location.search : "#" + id;
    if (url !== location.pathname + location.search + location.hash) history.pushState(null, "", url);
    applyFilter(id);
  });
  window.addEventListener("popstate", function () { applyFilter(location.hash.slice(1)); });
  window.addEventListener("hashchange", function () { applyFilter(location.hash.slice(1)); });
  applyFilter(location.hash.slice(1));

  fitScreens();
  window.addEventListener("resize", fitScreens);

})();
