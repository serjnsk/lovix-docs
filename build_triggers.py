#!/usr/bin/env python3
"""Build trigger-system.html / trigger-marketing.html from local .md masters.

Template: scenarios.html (styles, nav, marked render pipeline, TOC).
Adds: mermaid schema on a Miro-like canvas (drag pan, wheel zoom, buttons),
clickable nodes with a details panel fed from the page's own tables.
Not committed to the repo (local tooling, like build.sh/serve.mjs).
"""
import re

# Nav is inherited from the scenarios.html template verbatim (it now carries
# the two-level dropdown). We only move the `cur` marker to the built page's
# link — and highlight the dropdown button when that link lives inside it.

VZ_CSS = """<style>
  .vzwrap{background:var(--bg-band);border:1px solid var(--line);border-radius:10px;
    margin:14px 0 0;position:relative;overflow:hidden;height:min(65vh,640px);
    touch-action:none;cursor:grab;user-select:none;-webkit-user-select:none}
  .vzwrap.dragging{cursor:grabbing}
  .vzwrap pre.mermaid{margin:0;background:transparent;border:none;position:absolute;
    left:0;top:0;padding:0;overflow:visible}
  .vzwrap pre.mermaid:not([data-processed]){visibility:hidden}
  .vzwrap svg{display:block;transform-origin:0 0;max-width:none}
  .mermaid g.node.vz-click{cursor:pointer}
  .mermaid g.node.vz-click:hover rect{stroke:var(--accent) !important;stroke-width:2.5px !important}
  .vztools{position:absolute;left:10px;top:10px;z-index:5;display:flex;gap:6px;align-items:center;
    font-size:12.5px;color:var(--dim);background:rgba(255,255,255,.88);backdrop-filter:blur(2px);
    padding:6px 10px;border-radius:8px;border:1px solid var(--line)}
  .vztools button{border:1px solid var(--line2);background:#fff;border-radius:6px;
    padding:3px 10px;font:inherit;color:var(--muted);cursor:pointer}
  .vztools button:hover{border-color:var(--accent);color:var(--accent)}
  .vztools button.on{border-color:var(--accent);color:var(--accent);background:var(--accent-bg);font-weight:600}
  .vzhint{margin-left:4px}
  @media(max-width:900px){.vzhint{display:none}}
  #vzpanel{border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:8px;
    padding:12px 16px;margin:10px 0 6px;font-size:14px;color:var(--muted);background:var(--card)}
  #vzpanel b{color:#000;font-size:14.5px}
  .vzgrid{display:grid;grid-template-columns:180px 1fr;gap:4px 14px;margin:10px 0}
  .vzgrid > span:nth-child(odd){color:var(--dim)}
  .vzgo{color:var(--accent);cursor:pointer;font-weight:600}
  .vzgo:hover{text-decoration:underline}
  tr.vzflash td{animation:vzflash 2.2s ease-out}
  @keyframes vzflash{0%{background:#fff3bf}100%{background:transparent}}
</style>
"""

VZ_JS = """<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<script>
(function(){
  function esc(s){const d=document.createElement("div");d.textContent=s;return d.innerHTML;}

  // Scenario details come from the page's own summary table — zero duplication.
  const data = {};
  document.querySelectorAll("#out table").forEach(t => {
    const first = t.querySelector("tr th, tr td");
    if (!first || first.textContent.trim() !== "ID") return;
    t.querySelectorAll("tr").forEach((tr, i) => {
      if (i === 0) return;
      const c = tr.cells;
      if (!c || c.length < 7) return;
      const id = c[0].textContent.replace(/🆕/g, "").trim();
      data[id] = {ev: c[1].innerHTML, when: c[2].textContent.trim(), ch: c[3].innerHTML,
                  what: c[4].textContent.trim(), skip: c[5].textContent.trim(), rep: c[6].textContent.trim()};
    });
  });

  const panel = document.getElementById("vzpanel");
  function show(id){
    const d = data[id];
    if (!d || !panel) return;
    panel.innerHTML = "<b>" + esc(id) + " · " + esc(d.what) + "</b>" +
      '<div class="vzgrid">' +
      "<span>Событие / триггер</span><span>" + d.ev + "</span>" +
      "<span>Когда</span><span>" + esc(d.when) + "</span>" +
      "<span>Канал</span><span>" + d.ch + "</span>" +
      "<span>Не отправлять, если</span><span>" + esc(d.skip) + "</span>" +
      "<span>Повтор</span><span>" + esc(d.rep) + "</span>" +
      '</div><span class="vzgo">Показать тексты ↓</span>';
    panel.querySelector(".vzgo").addEventListener("click", () => {
      // Content tables have 5 columns (ID|Канал|Сообщение|CTA|Мерим); summary has 7.
      const tables = Array.from(document.querySelectorAll("#out table")).filter(t => {
        const h = t.querySelectorAll("thead th");
        return h.length === 5 && h[0].textContent.trim() === "ID";
      });
      for (const t of tables) {
        const row = Array.from(t.querySelectorAll("tr")).find(tr =>
          tr.cells && tr.cells[0] && tr.cells[0].tagName === "TD" &&
          tr.cells[0].textContent.replace(/🆕/g, "").trim().startsWith(id));
        if (row) {
          row.scrollIntoView({behavior: "smooth", block: "center"});
          row.classList.remove("vzflash");
          void row.offsetWidth;
          row.classList.add("vzflash");
          return;
        }
      }
      // No table row (e.g. У7-1 — generated text): jump to the group heading.
      const grp = id.split("-")[0] + ".";
      const h2 = Array.from(document.querySelectorAll("#out h2"))
        .find(h => h.textContent.trim().startsWith(grp));
      if (h2) h2.scrollIntoView({behavior: "smooth"});
    });
    panel.scrollIntoView({behavior: "smooth", block: "nearest"});
  }

  mermaid.initialize({startOnLoad: false, securityLevel: "loose", theme: "neutral",
    flowchart: {curve: "basis", htmlLabels: true, useMaxWidth: false}});
  mermaid.run({nodes: document.querySelectorAll("pre.mermaid")}).then(() => {
    document.querySelectorAll(".mermaid g.node").forEach(n => {
      const m = n.textContent.match(/У\\d+-\\d+/);
      if (!m || !data[m[0]]) return;
      n.classList.add("vz-click");
      n.addEventListener("click", () => show(m[0]));
    });

    // Miro-like canvas: drag to pan, wheel / pinch to zoom, buttons for fit/100%/±.
    document.querySelectorAll(".vzwrap").forEach(wrap => {
      const pre = wrap.querySelector("pre.mermaid");
      const svg = pre && pre.querySelector("svg");
      if (!svg) return;
      let k = 1, tx = 0, ty = 0, mode = "", interacted = false;
      function nat(){
        const t = svg.style.transform;
        svg.style.transform = "none";
        const r = svg.getBoundingClientRect();
        svg.style.transform = t;
        return {w: r.width, h: r.height};
      }
      function box(){
        // Hidden tab / collapsed pane can report a 0-height viewport; fall
        // back to sane defaults so fit() never collapses to the min zoom.
        const W = wrap.clientWidth || 960, H = wrap.clientHeight || 480;
        return {W: Math.max(W, 320), H: Math.max(H, 320)};
      }

      const tools = document.createElement("div");
      tools.className = "vztools";
      tools.innerHTML = '<button data-z="fit">Вписать</button>' +
        '<button data-z="1">100%</button><button data-z="-">−</button>' +
        '<button data-z="+">+</button><span class="vzk"></span>' +
        '<span class="vzhint">двигай мышью · зум колесом</span>';
      wrap.appendChild(tools);
      const lbl = tools.querySelector(".vzk");

      function apply(){
        svg.style.transform = "translate(" + tx + "px," + ty + "px) scale(" + k + ")";
        lbl.textContent = Math.round(k * 100) + "%";
        tools.querySelectorAll("button").forEach(b => b.classList.toggle("on", b.dataset.z === mode));
      }
      function clamp(v){ return Math.min(3, Math.max(0.1, v)); }
      function zoomAt(cx, cy, f, m){
        const nk = clamp(k * f);
        tx = cx - (cx - tx) * (nk / k);
        ty = cy - (cy - ty) * (nk / k);
        k = nk; mode = m || ""; apply();
      }
      function fit(){
        const b = box(), n = nat();
        k = clamp(Math.min((b.W - 24) / n.w, (b.H - 24) / n.h));
        tx = (b.W - n.w * k) / 2; ty = (b.H - n.h * k) / 2;
        mode = "fit"; apply();
      }
      function hundred(){
        const b = box(), n = nat();
        k = 1; tx = (b.W - n.w) / 2; ty = (b.H - n.h) / 2;
        mode = "1"; apply();
      }
      tools.addEventListener("click", e => {
        const z = e.target.dataset && e.target.dataset.z;
        if (!z) return;
        e.stopPropagation();
        interacted = true;
        if (z === "fit") fit();
        else if (z === "1") hundred();
        else zoomAt(wrap.clientWidth / 2, wrap.clientHeight / 2, z === "+" ? 1.25 : 0.8);
      });

      wrap.addEventListener("wheel", e => {
        e.preventDefault();
        interacted = true;
        const r = wrap.getBoundingClientRect();
        zoomAt(e.clientX - r.left, e.clientY - r.top, Math.exp(-e.deltaY * 0.0015));
      }, {passive: false});

      wrap.addEventListener("dblclick", e => {
        if (e.target.closest("g.node") || e.target.closest(".vztools")) return;
        const r = wrap.getBoundingClientRect();
        zoomAt(e.clientX - r.left, e.clientY - r.top, 1.5);
      });

      // Pointers: 1 finger/button = pan, 2 fingers = pinch. Click passes through
      // only when the pointer barely moved.
      const pts = new Map();
      let moved = false, suppressClick = false, pin = null, start = null;
      wrap.addEventListener("pointerdown", e => {
        if (e.target.closest(".vztools")) return;
        // No pointer capture yet: capturing here would retarget the follow-up
        // click to the canvas and node clicks would never fire. Capture only
        // once an actual drag starts (threshold crossed) or a pinch begins.
        interacted = true;
        pts.set(e.pointerId, {x: e.clientX, y: e.clientY});
        if (pts.size === 1) { moved = false; suppressClick = false; start = {x: e.clientX, y: e.clientY}; }
        if (pts.size === 2) { try { wrap.setPointerCapture(e.pointerId); } catch(_){} }
        pin = null;
      });
      wrap.addEventListener("pointermove", e => {
        if (!pts.has(e.pointerId)) return;
        const prev = pts.get(e.pointerId);
        pts.set(e.pointerId, {x: e.clientX, y: e.clientY});
        const r = wrap.getBoundingClientRect();
        if (pts.size === 1) {
          if (!moved && start && Math.hypot(e.clientX - start.x, e.clientY - start.y) < 5) return;
          if (!moved) { try { wrap.setPointerCapture(e.pointerId); } catch(_){} }
          moved = true;
          wrap.classList.add("dragging");
          tx += e.clientX - prev.x; ty += e.clientY - prev.y; mode = ""; apply();
        } else if (pts.size === 2) {
          const [a, b] = Array.from(pts.values());
          const dist = Math.hypot(a.x - b.x, a.y - b.y);
          const mid = {x: (a.x + b.x) / 2 - r.left, y: (a.y + b.y) / 2 - r.top};
          if (pin) {
            zoomAt(mid.x, mid.y, dist / pin.dist);
            tx += mid.x - pin.mid.x; ty += mid.y - pin.mid.y; apply();
          }
          pin = {dist: dist, mid: mid};
          moved = true;
        }
      });
      function release(e){
        if (!pts.has(e.pointerId)) return;
        pts.delete(e.pointerId);
        pin = null;
        if (pts.size === 0) {
          wrap.classList.remove("dragging");
          if (moved) suppressClick = true;
        }
      }
      wrap.addEventListener("pointerup", release);
      wrap.addEventListener("pointercancel", release);
      wrap.addEventListener("click", e => {
        if (suppressClick) { suppressClick = false; e.stopPropagation(); e.preventDefault(); }
      }, true);

      // Initial fit; re-fit when the canvas gets its real size (hidden tab,
      // pane resize, late font layout) until the user pans/zooms themselves.
      fit();
      [120, 400, 900].forEach(ms => setTimeout(() => { if (!interacted) fit(); }, ms));
      if (typeof ResizeObserver !== "undefined") {
        new ResizeObserver(() => { if (!interacted) fit(); }).observe(wrap);
      }
    });
  });
})();
</script>
"""

def retarget_nav(page, out_file):
    m = re.search(r"<nav>.*?</nav>", page, re.S)
    if not m:
        return page
    nav = m.group(0)
    nav = nav.replace(' class="cur"', "").replace('dd-btn cur', "dd-btn")
    nav = nav.replace(f'<a href="{out_file}">', f'<a class="cur" href="{out_file}">')
    dd = re.search(r'<div class="dd">.*?</nav>', nav, re.S)
    if dd and f'href="{out_file}"' in dd.group(0):
        nav = nav.replace('class="dd-btn"', 'class="dd-btn cur"')
    return page[:m.start()] + nav + page[m.end():]

template = open("scenarios.html").read()

for md_file, out_file, title in [
    ("trigger-system.md", "trigger-system.html", "Lovix — Триггерная системная рассылка"),
    ("trigger-marketing.md", "trigger-marketing.html", "Lovix — Триггерная маркетинговая рассылка"),
    ("admin-content.md", "admin-content.html", "Lovix — Админка: управление контентом"),
    ("support.md", "support.html", "Lovix — Саппорт: инструкция QA + Support"),
    ("razdevator.md", "razdevator.html", "Razdevator.hot — флоу продукта"),
]:
    md = open(md_file).read().strip()
    page = template
    page = re.sub(r"<!-- СГЕНЕРИРОВАНО[^>]*-->\n?", "", page)
    page = page.replace("<html lang=\"ru\">",
        "<html lang=\"ru\">\n<!-- СГЕНЕРИРОВАНО build_triggers.py из " + md_file + " — НЕ ПРАВИТЬ РУКАМИ -->", 1)
    page = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", page, flags=re.S)
    page = retarget_nav(page, out_file)
    page = re.sub(
        r'(<script type="text/markdown" id="src">\n).*?(</script>)',
        lambda m: m.group(1) + md + "\n" + m.group(2),
        page, count=1, flags=re.S,
    )
    page = page.replace("</head>", VZ_CSS + "</head>", 1)
    page = page.replace("</body>", VZ_JS + "</body>", 1)
    open(out_file, "w").write(page)
    print("built", out_file, len(page), "bytes")
