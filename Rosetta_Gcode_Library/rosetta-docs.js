/* Rosetta manuals - shared script (User Manual and Gcode Library; keep
   the two copies identical). No other files or Internet needed, so it
   works from the Pi's disk (file://) as well as on the website.

   - Search: a box in the header searching both manuals, using
     search-index.js (made by docs/build_manuals.py).
   - Picture zoom: a screenshot shown smaller than its real size can be
     clicked to see it full size; click again or press Esc to close.
   - On the Pi's own copy only, links needing the Internet are coloured. */
(function () {
  "use strict";

  /* Opened from this machine's disk (the Pi), not the website: links that
     need the Internet get their own colour (see rosetta-docs.css). */
  var onThisMachine = location.protocol === "file:";
  if (onThisMachine) document.documentElement.classList.add("on-this-machine");

  /* A link with data-pi-href opens that Internet address instead when read
     on the Pi - for pages whose point is something only the website has
     (e.g. 3D Printable Parts, whose files aren't shipped to the Pi). */
  function usePiLinks() {
    if (!onThisMachine) return;
    document.querySelectorAll("a[data-pi-href]").forEach(function (a) {
      a.href = a.getAttribute("data-pi-href");
      a.classList.add("online");
      a.target = "_blank";
      a.rel = "noopener";
      a.title = "Opens on the Internet";
    });
  }

  function esc(s) {
    return s.replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  /* ---------------- search ---------------- */
  function words(q) {
    return q.toLowerCase().split(/[^a-z0-9.#$-]+/).filter(function (w) { return w.length > 1; });
  }

  function count(hay, w) {
    var n = 0, i = hay.indexOf(w);
    while (i !== -1) { n++; i = hay.indexOf(w, i + w.length); }
    return n;
  }

  function search(q) {
    var ws = words(q), pages = window.ROSETTA_SEARCH || [], out = [];
    if (!ws.length) return out;
    pages.forEach(function (p) {
      var t = p.t.toLowerCase(), x = p.x.toLowerCase(), score = 0, ok = true;
      ws.forEach(function (w) {
        var inT = count(t, w), inX = count(x, w), inH = 0;
        p.h.forEach(function (h) { inH += count(h[1].toLowerCase(), w); });
        if (!inT && !inX && !inH) ok = false;
        score += inT * 20 + inH * 6 + Math.min(inX, 15);
      });
      if (!ok) return;
      // the heading that matches most words, to link straight to it
      var best = null, bestN = 0;
      p.h.forEach(function (h) {
        var lh = h[1].toLowerCase(), n = 0;
        ws.forEach(function (w) { if (lh.indexOf(w) !== -1) n++; });
        if (n > bestN) { best = h; bestN = n; }
      });
      // a snippet around the first match in the text
      var at = -1;
      ws.forEach(function (w) { var i = x.indexOf(w); if (i !== -1 && (at === -1 || i < at)) at = i; });
      var snip = "";
      if (at !== -1) {
        var s = Math.max(0, at - 60), e = Math.min(p.x.length, at + 110);
        snip = (s > 0 ? "…" : "") + p.x.slice(s, e) + (e < p.x.length ? "…" : "");
      }
      out.push({ p: p, score: score, head: best, snip: snip });
    });
    out.sort(function (a, b) { return b.score - a.score; });
    return out.slice(0, 15);
  }

  function highlight(text, ws) {
    var h = esc(text);
    ws.forEach(function (w) {
      var re = new RegExp("(" + w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "ig");
      h = h.replace(re, "<mark>$1</mark>");
    });
    return h;
  }

  function setUpSearch() {
    var header = document.querySelector(".site-header");
    if (!header || !window.ROSETTA_SEARCH) return;
    var box = document.createElement("div");
    box.className = "site-search";
    box.innerHTML =
      '<input type="search" placeholder="Search the manuals" aria-label="Search the manuals" autocomplete="off">' +
      '<div class="search-results" role="listbox" hidden></div>';
    header.insertBefore(box, header.querySelector(".site-nav"));
    var input = box.querySelector("input"), list = box.querySelector(".search-results"), sel = -1;

    function links() { return list.querySelectorAll("a"); }
    function mark(i) {
      var a = links();
      if (!a.length) return;
      sel = (i + a.length) % a.length;
      for (var k = 0; k < a.length; k++) a[k].classList.toggle("active", k === sel);
      a[sel].scrollIntoView({ block: "nearest" });
    }
    function show() {
      var q = input.value.trim(), ws = words(q), res = search(q);
      sel = -1;
      if (!q) { list.hidden = true; list.innerHTML = ""; return; }
      if (!res.length) {
        list.innerHTML = '<p class="search-none">Nothing found for “' + esc(q) + '”.</p>';
      } else {
        list.innerHTML = res.map(function (r) {
          var href = r.p.u + (r.head ? "#" + r.head[0] : "");
          return '<a href="' + esc(href) + '"><span class="search-title">' + highlight(r.p.t, ws) +
            (r.head ? ' <span class="search-head">› ' + highlight(r.head[1], ws) + "</span>" : "") +
            '</span><span class="search-where">' + esc(r.p.m) + "</span>" +
            (r.snip ? '<span class="search-snip">' + highlight(r.snip, ws) + "</span>" : "") + "</a>";
        }).join("");
      }
      list.hidden = false;
    }
    input.addEventListener("input", show);
    input.addEventListener("focus", function () { if (input.value.trim()) show(); });
    input.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown") { e.preventDefault(); mark(sel + 1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); mark(sel - 1); }
      else if (e.key === "Enter") {
        var a = links();
        if (a.length) { e.preventDefault(); window.location.href = a[sel < 0 ? 0 : sel].getAttribute("href"); }
      } else if (e.key === "Escape") { list.hidden = true; input.blur(); }
    });
    document.addEventListener("click", function (e) { if (!box.contains(e.target)) list.hidden = true; });
    // "/" jumps to the search box, as on many sites
    document.addEventListener("keydown", function (e) {
      if (e.key === "/" && document.activeElement !== input &&
          !/input|textarea|select/i.test(document.activeElement.tagName)) {
        e.preventDefault(); input.focus();
      }
    });
  }

  /* ---------------- picture zoom ---------------- */
  function setUpZoom() {
    var overlay = null;
    function close() { if (overlay) { overlay.remove(); overlay = null; } }
    function open(img) {
      close();
      overlay = document.createElement("div");
      overlay.className = "zoom-overlay";
      overlay.setAttribute("role", "dialog");
      overlay.setAttribute("aria-label", "Picture at full size - click or press Esc to close");
      var big = document.createElement("img");
      big.src = img.currentSrc || img.src;
      big.alt = img.alt || "";
      overlay.appendChild(big);
      overlay.addEventListener("click", close);
      document.body.appendChild(overlay);
    }
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") close(); });

    function check(img) {
      if (img.closest("a")) return;                         // already a link (e.g. a G-code file icon)
      if (img.naturalWidth > img.clientWidth * 1.15 && img.naturalWidth > 120) {
        img.classList.add("zoomable");
        img.title = "Click to see full size";
        img.addEventListener("click", function () { open(img); });
      }
    }
    document.querySelectorAll(".content img").forEach(function (img) {
      if (img.complete) check(img); else img.addEventListener("load", function () { check(img); });
    });
  }

  function start() { usePiLinks(); setUpSearch(); setUpZoom(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
