/* FREAK V3 docs — client-side search and navigation.
   No dependencies, no network. Works from file:// as well as http://. */

(function () {
  "use strict";

  var input = document.getElementById("q");
  var panel = document.getElementById("results");
  var index = window.SEARCH_INDEX || [];
  var selected = -1;
  var hits = [];

  /* ---------- helpers ---------- */

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function tokenize(q) {
    return q.toLowerCase().split(/\s+/).filter(function (t) { return t.length > 0; });
  }

  /* Score one record against all query tokens. Every token must appear
     somewhere, otherwise the record is dropped. */
  function score(rec, tokens) {
    var heading = (rec.h || "").toLowerCase();
    var title = (rec.t || "").toLowerCase();
    var text = (rec.x || "").toLowerCase();
    var total = 0;

    for (var i = 0; i < tokens.length; i++) {
      var t = tokens[i];
      var s = 0;

      if (title === t) s += 60;
      if (heading === t) s += 55;
      if (heading.indexOf(t) === 0) s += 34;
      else if (heading.indexOf(t) !== -1) s += 22;
      if (title.indexOf(t) !== -1) s += 10;

      var at = text.indexOf(t);
      if (at !== -1) {
        s += 12;
        /* whole-word hit is worth more than a substring hit */
        var re = new RegExp("\\b" + t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "i");
        if (re.test(text)) s += 8;
        if (at < 120) s += 3;
      }

      if (s === 0) return 0;
      total += s;
    }

    /* prefer shorter, more specific sections */
    total += Math.max(0, 8 - Math.floor((rec.x || "").length / 120));
    return total;
  }

  function snippet(text, tokens) {
    var lower = text.toLowerCase();
    var at = -1;
    for (var i = 0; i < tokens.length; i++) {
      var p = lower.indexOf(tokens[i]);
      if (p !== -1 && (at === -1 || p < at)) at = p;
    }
    if (at === -1) at = 0;
    var start = Math.max(0, at - 48);
    var frag = text.slice(start, start + 190);
    if (start > 0) frag = "…" + frag;
    if (start + 190 < text.length) frag += "…";
    return frag;
  }

  function mark(text, tokens) {
    var out = esc(text);
    tokens.forEach(function (t) {
      var re = new RegExp("(" + t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "gi");
      out = out.replace(re, "<mark>$1</mark>");
    });
    return out;
  }

  /* ---------- rendering ---------- */

  function render(query) {
    var tokens = tokenize(query);
    if (tokens.length === 0) {
      panel.hidden = true;
      panel.innerHTML = "";
      hits = [];
      return;
    }

    var scored = [];
    for (var i = 0; i < index.length; i++) {
      var s = score(index[i], tokens);
      if (s > 0) scored.push({ rec: index[i], s: s });
    }
    scored.sort(function (a, b) { return b.s - a.s; });

    /* A section may be indexed as several chunks. Collapse them to one hit,
       and keep at most 3 sections per page so results stay varied. */
    var seenSection = {};
    var perPage = {};
    hits = [];
    for (var j = 0; j < scored.length && hits.length < 25; j++) {
      var rec = scored[j].rec;
      var key = rec.p + "#" + rec.a;
      if (seenSection[key]) continue;
      seenSection[key] = true;
      perPage[rec.p] = (perPage[rec.p] || 0) + 1;
      if (perPage[rec.p] <= 3) hits.push(rec);
    }

    if (hits.length === 0) {
      panel.innerHTML = '<div class="empty">No matches for <strong>' +
        esc(query) + "</strong></div>";
      panel.hidden = false;
      return;
    }

    var html = hits.map(function (rec, n) {
      var href = rec.p + ".html" + (rec.a ? "#" + rec.a : "");
      return '<a class="hit' + (n === selected ? " sel" : "") + '" href="' + href + '">' +
        '<span class="hit-top">' +
        '<span class="hit-page">' + esc(rec.t) + "</span>" +
        '<span class="hit-head">' + mark(rec.h || rec.t, tokens) + "</span>" +
        "</span>" +
        '<span class="hit-snip">' + mark(snippet(rec.x || "", tokens), tokens) + "</span>" +
        "</a>";
    }).join("");

    html += '<div class="foot">' + hits.length + " result" +
      (hits.length === 1 ? "" : "s") + " · ↑↓ to move · Enter to open · Esc to close</div>";

    panel.innerHTML = html;
    panel.hidden = false;
  }

  function move(delta) {
    if (hits.length === 0) return;
    selected = (selected + delta + hits.length) % hits.length;
    var nodes = panel.querySelectorAll(".hit");
    for (var i = 0; i < nodes.length; i++) nodes[i].classList.toggle("sel", i === selected);
    if (nodes[selected]) nodes[selected].scrollIntoView({ block: "nearest" });
  }

  function close() {
    panel.hidden = true;
    selected = -1;
  }

  /* ---------- events ---------- */

  if (input) {
    input.addEventListener("input", function () {
      selected = -1;
      render(input.value);
    });

    input.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown") { e.preventDefault(); move(1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); move(-1); }
      else if (e.key === "Enter") {
        var target = selected >= 0 ? hits[selected] : hits[0];
        if (target) {
          e.preventDefault();
          window.location.href = target.p + ".html" + (target.a ? "#" + target.a : "");
        }
      } else if (e.key === "Escape") {
        close();
        input.blur();
      }
    });

    input.addEventListener("focus", function () {
      if (input.value.trim()) render(input.value);
    });
  }

  document.addEventListener("click", function (e) {
    if (panel && !panel.contains(e.target) && e.target !== input) close();
  });

  document.addEventListener("keydown", function (e) {
    var typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName);
    if (e.key === "/" && !typing) { e.preventDefault(); input.focus(); input.select(); }
    if ((e.key === "k" || e.key === "K") && (e.metaKey || e.ctrlKey)) {
      e.preventDefault(); input.focus(); input.select();
    }
  });

  var toggle = document.querySelector(".menu-toggle");
  var sidebar = document.querySelector(".sidebar");
  if (toggle && sidebar) {
    toggle.addEventListener("click", function () { sidebar.classList.toggle("open"); });
  }

  /* highlight the table-of-contents entry for the section in view */
  var tocLinks = Array.prototype.slice.call(document.querySelectorAll(".toc a"));
  if (tocLinks.length && "IntersectionObserver" in window) {
    var byId = {};
    tocLinks.forEach(function (a) { byId[a.getAttribute("href").slice(1)] = a; });
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        var link = byId[entry.target.id];
        if (link && entry.isIntersecting) {
          tocLinks.forEach(function (a) { a.style.color = ""; a.style.borderLeftColor = ""; });
          link.style.color = "var(--accent)";
          link.style.borderLeftColor = "var(--accent)";
        }
      });
    }, { rootMargin: "-70px 0px -75% 0px" });
    Object.keys(byId).forEach(function (id) {
      var el = document.getElementById(id);
      if (el) obs.observe(el);
    });
  }
})();
