"use strict";
// View "Neubau" (pipeline/use_cases/new_construction/README.md): new dwellings per year as hollow columns, the
// subsidised part in red from the bottom, provisional years hatched, the conversions as a dashed frame on top. Below
// it, one block of rents, prices and wages as two index charts (2017 = 100). Every number and text comes from Python.
APP.hatch = function (svg, color) {
  const defs = APP.svgElement("defs"), p = APP.svgElement("pattern", { id: "hatch-subsidised", width: 6, height: 6,
    patternUnits: "userSpaceOnUse", patternTransform: "rotate(45)" });
  p.append(APP.svgElement("rect", { width: 6, height: 6, fill: "#fff" }), APP.svgElement("rect", { width: 3, height: 6, fill: color }));
  defs.append(p);
  svg.append(defs);
};
APP.fillOf = (y, n) => (y.provisional ? "url(#hatch-subsidised)" : n.color);

// From this much room the chart is one drawing 760 units wide that scales. Its 12 px labels then stay at 11 px or more
// (12 × 700 / 760 = 11.05); the Trend (APP.WIDE) has larger text and switches earlier.
APP.CONSTRUCTION_WIDE = 700;

// The svg is one role="img": children of it are hidden from screen readers, so its label carries every year.
APP.constructionLabel = (n) => [n.title + ".", ...n.years.map((y) => y.tip)].join(" ");

// Wide: one column per year in a drawing 760 units wide. Narrow (below APP.CONSTRUCTION_WIDE px): one row per year, drawn in px.
// Both scale on n.max, the largest total. The dashed frame is drawn first, so the edge it shares with the solid frame stays solid.
APP.newConstructionChart = function (n, W) {
  const narrow = W < APP.CONSTRUCTION_WIDE, years = n.years;
  if (!narrow) {
    const top = 30, base = 270, step = W / years.length, cw = 34, sc = (base - top) / n.max;
    const svg = APP.svgElement("svg", { viewBox: `0 0 ${W} ${base + 48}`, class: "construction", role: "img",
      "aria-label": APP.constructionLabel(n) });
    APP.hatch(svg, n.color);
    years.forEach((y, i) => {
      const x = i * step + (step - cw) / 2, h = y.new * sc, hc = y.conversions * sc, hf = y.subsidised * sc;
      const g = APP.svgElement("g", { class: y.year === n.highlight ? "last" : "", "data-tip": y.tip });
      g.append(APP.svgElement("rect", { x, y: base - h - hc, width: cw, height: hc, class: "conversions" }),
        APP.svgElement("rect", { x, y: base - h, width: cw, height: h, class: "frame" }),
        APP.svgElement("rect", { x: x + 0.75, y: base - hf, width: cw - 1.5, height: hf, fill: APP.fillOf(y, n) }),
        APP.svgElement("text", { x: x + cw / 2, y: base - h - hc - 7, "text-anchor": "middle", class: "total" }, y.all_text),
        APP.svgElement("text", { x: x + cw / 2, y: base + 20, "text-anchor": "middle", class: "year" }, y.year),
        APP.svgElement("text", { x: x + cw / 2, y: base + 38, "text-anchor": "middle", class: "share" }, y.share_text));
      svg.append(g);
    });
    svg.append(APP.svgElement("line", { x1: 0, x2: W, y1: base, y2: base, stroke: "#000", "stroke-width": 2 }));
    return svg;
  }
  const row = 30, label = 44, room = W - label - 60, sc = room / n.max;
  const svg = APP.svgElement("svg", { viewBox: `0 0 ${W} ${years.length * row + 6}`, width: W, class: "construction",
    role: "img", "aria-label": APP.constructionLabel(n) });
  APP.hatch(svg, n.color);
  years.forEach((y, i) => {
    const top = i * row + 4, g = APP.svgElement("g", { class: y.year === n.highlight ? "last" : "", "data-tip": y.tip });
    g.append(APP.svgElement("text", { x: 0, y: top + 15, class: "year" }, y.year),
      APP.svgElement("rect", { x: label + y.new * sc, y: top, width: y.conversions * sc, height: 20, class: "conversions" }),
      APP.svgElement("rect", { x: label, y: top, width: y.new * sc, height: 20, class: "frame" }),
      APP.svgElement("rect", { x: label, y: top + 0.75, width: y.subsidised * sc, height: 18.5, fill: APP.fillOf(y, n) }),
      APP.svgElement("text", { x: label + y.all * sc + 6, y: top + 15, class: "total" }, y.all_text));
    svg.append(g);
  });
  return svg;
};

// The block of rents (n.rents): per chart one index line per series, one slot per year with the value at its centre.
// The references (prices, wages) come first in c.series: thin grey edges of a light band (c.band) between them,
// drawn under every data line, they read as a scale.
// The series of c.old_base break at c.break.year (Zensus 2022): no segment joins the year before and that year; a
// dotted segment leads to a hollow dot at the value on the old base. A line runs through the years that have a value; a
// series has a dot only in the years of its `dots`. A year of c.survey_years keeps the ink, every other year is grey.
// Colours, widths, dashes and every text come from Python; the browser only places the values on the axis (c.axis.min
// to c.axis.max). Wide: a drawing 760 units wide that scales, the end labels name the lines, one note under chart 1
// explains the hollow dots. Narrow (below APP.CONSTRUCTION_WIDE px): the same drawing in px at the room, lower, every
// second year named, end labels without their names, and the key (one column) instead of the note. A tap on the slot of
// a year shows its tooltip.
APP.RENTS_PLOT = { nominal: 300, real: 230 };
APP.RENTS_GAP = 17;
APP.rentsChart = function (c, W) {
  const narrow = W < APP.CONSTRUCTION_WIDE, a = c.axis, years = c.years, last = years.length - 1;
  const left = narrow ? 34 : 46, right = narrow ? 58 : 200, top = 12, base = top + (narrow ? 220 : APP.RENTS_PLOT[c.id]);
  const step = (W - left - right) / years.length, edge = W - right;
  const cx = (i) => left + step * (i + 0.5), cy = (v) => base - (v - a.min) / (a.max - a.min) * (base - top);
  const svg = APP.svgElement("svg", { viewBox: `0 0 ${W} ${base + 30}`, ...(narrow ? { width: W } : {}), class: "rents", role: "img",
    "aria-label": c.aria_label });
  a.ticks.forEach((v, k) => svg.append(APP.svgElement("line", { x1: left, x2: edge + 6, y1: cy(v), y2: cy(v), class: "grid" }),
    APP.svgElement("text", { x: left - 7, y: cy(v) + 4, "text-anchor": "end", class: "tick" }, a.tick_texts[k])));
  // the band lies between two lines: through the values of the first series and back through the second, under every line
  // (the two cross, so neither is the upper one)
  if (c.band) {
    const [first, second] = c.band.between.map((id) => c.series.find((s) => s.id === id));
    svg.append(APP.svgElement("path", { d: APP.rentsD([...years.map((y, i) => [cx(i), cy(first.values[i])]),
      ...years.map((y, i) => [cx(i), cy(second.values[i])]).reverse()]) + " Z", fill: c.band.colour, stroke: "none", class: "band" }));
  }
  // the note of the break stands left of its line at the foot; on a phone a little lower, clear of the lowest tick label
  if (c.break) {
    const bx = left + years.indexOf(c.break.year) * step;
    svg.append(APP.svgElement("line", { x1: bx, x2: bx, y1: top, y2: base, class: "break" }),
      APP.svgElement("text", { x: bx - 6, y: base - (narrow ? 3 : 8), "text-anchor": "end", class: "note" }, c.break.note));
  }
  APP.rentsLines(svg, c, cx, cy);
  years.forEach((year, i) => {
    const g = APP.svgElement("g", { "data-tip": c.tips[i].text });
    APP.tipContent.set(g, () => APP.rentsTip(c, c.tips[i]));
    g.append(APP.svgElement("rect", { x: left + i * step, y: top, width: step, height: base - top + 30, fill: "transparent", class: "hit" }));
    for (const s of c.series) {
      if (s.dots.includes(year)) g.append(APP.svgElement("circle", { cx: cx(i), cy: cy(s.values[i]), r: 4.5, fill: s.colour, stroke: "#fff",
        "stroke-width": 2, class: "dot", "data-series": s.id }));
    }
    if (!narrow || i % 2 === 0) g.append(APP.svgElement("text", { x: cx(i), y: base + 22, "text-anchor": "middle",
      class: c.survey_years.includes(year) ? "year" : "year off" }, year));
    svg.append(g);
  });
  APP.rentsOldDots(svg, c, cx, cy);
  APP.rentsEnds(svg, c, cx(last), cy, base, narrow);
  return svg;
};

// The d of a path through the points
APP.rentsD = (points) => points.map(([x, y], k) => `${k ? "L" : "M"}${x},${y}`).join(" ");

// Per series one path through the years with a value, in its colour, width and dash (a dashed line has flat ends). A
// series of c.old_base has one path up to the year before the break and one from the break year, and a dotted segment
// (the width and dash of the key entry of the old base) from the year before the break to its value on the old base.
APP.rentsLines = function (svg, c, cx, cy) {
  const path = (points, s, extra) => APP.svgElement("path", { d: APP.rentsD(points), fill: "none", stroke: s.colour, "stroke-width": s.width,
    "stroke-linecap": s.dash ? "butt" : "round", "stroke-linejoin": "round", ...(s.dash ? { "stroke-dasharray": s.dash } : {}), "data-series": s.id, ...extra });
  const oldKey = c.key.find((e) => e.kind === "old_base");
  for (const s of c.series) {
    const known = s.values.map((v, i) => [i, v]).filter(([, v]) => v != null), old = c.old_base && c.old_base[s.id];
    const cut = old ? c.years.indexOf(c.break.year) : -1;
    const parts = old ? [known.filter(([i]) => i < cut), known.filter(([i]) => i >= cut)] : [known];
    for (const part of parts) if (part.length > 1) svg.append(path(part.map(([i, v]) => [cx(i), cy(v)]), s));
    if (old) svg.append(path([[cx(cut - 1), cy(s.values[cut - 1])], [cx(cut), cy(old.value)]], s,
      { "stroke-width": oldKey.width, "stroke-dasharray": oldKey.dash, class: "old" }));
  }
};

// The hollow dots of the break year on the old base, each in its own group with its tooltip. Drawn after the years,
// so their smaller target wins over the slot of the year.
APP.rentsOldDots = function (svg, c, cx, cy) {
  if (!c.old_base) return;
  const i = c.years.indexOf(c.old_base.year);
  for (const s of c.series) {
    const old = c.old_base[s.id];
    if (!old) continue;
    const g = APP.svgElement("g", { class: "old", "data-tip": old.tip });
    g.append(APP.svgElement("circle", { cx: cx(i), cy: cy(old.value), r: 8, fill: "transparent", class: "hit" }),
      APP.svgElement("circle", { cx: cx(i), cy: cy(old.value), r: 4, fill: "#fff", stroke: s.colour, "stroke-width": 2, class: "dot",
        "data-series": s.id }));
    svg.append(g);
  }
};

// The end labels right of the last year, from the top in the order of c.end_order: each at the height of its value,
// moved down to keep APP.RENTS_GAP from the one above, and all moved up together if the last falls below the base. A
// thin grey leader joins each label to the end of its line. The value in bold, then the name in regular weight (wide
// only); the colour is the ink of the series (grey for the references).
APP.rentsEnds = function (svg, c, x, cy, base, narrow) {
  const last = c.years.length - 1, ends = c.end_order.map((id) => c.series.find((s) => s.id === id)).map((s) => ({ s, y0: cy(s.values[last]) }));
  ends.forEach((e, k) => { e.y = k ? Math.max(e.y0, ends[k - 1].y + APP.RENTS_GAP) : e.y0; });
  const over = ends[ends.length - 1].y - (base + 4);
  if (over > 0) ends.forEach((e) => { e.y -= over; });
  const lx = x + (narrow ? 12 : 22);
  for (const { s, y0, y } of ends) {
    const label = APP.svgElement("text", { x: lx, y: y + 5, class: "end", style: `fill:${s.ink}`, "data-series": s.id }, s.end_value_text);
    if (!narrow) label.append(APP.svgElement("tspan", { class: "name" }, " " + s.end_name));
    svg.append(APP.svgElement("polyline", { points: `${x + 7},${y0} ${lx - 8},${y0} ${lx - 3},${y}`, class: "leader" }), label);
  }
};

// A short line as the chart draws it, for the key: a reference as a piece of the band with its edge on the side of
// e.edge, a data line (with a dot in its middle if e.dot), the old base as a dotted line (e.dash) to a hollow dot. In a
// tooltip (small) only the line, in the colour, width and dash of the series.
APP.rentsSwatch = function (e, small) {
  const dash = e.dash ? { "stroke-dasharray": e.dash } : {};
  if (small) {
    const svg = APP.svgElement("svg", { width: 14, height: 10, class: "swatch", "aria-hidden": "true" }), pad = e.dash ? 0 : e.width / 2;
    svg.append(APP.svgElement("line", { x1: pad, x2: 14 - pad, y1: 5, y2: 5, stroke: e.colour, "stroke-width": e.width,
      "stroke-linecap": e.dash ? "butt" : "round", ...dash }));
    return svg;
  }
  const svg = APP.svgElement("svg", { width: 26, height: 12, class: "swatch", "aria-hidden": "true" });
  if (e.kind === "old_base") {
    svg.append(APP.svgElement("line", { x1: 1, x2: 16, y1: 6, y2: 6, stroke: e.colour, "stroke-width": e.width, "stroke-dasharray": e.dash,
      "stroke-linecap": "round" }), APP.svgElement("circle", { cx: 21, cy: 6, r: 4, fill: "#fff", stroke: e.colour, "stroke-width": 2 }));
  } else if (e.kind === "reference") {
    const y = e.edge === "top" ? e.width / 2 : 12 - e.width / 2;
    svg.append(APP.svgElement("rect", { x: 0, y: 0, width: 26, height: 12, fill: e.band }),
      APP.svgElement("line", { x1: 0, x2: 26, y1: y, y2: y, stroke: e.colour, "stroke-width": e.width, "stroke-linecap": "butt", ...dash }));
  } else {
    svg.append(APP.svgElement("line", { x1: 1, x2: 25, y1: 6, y2: 6, stroke: e.colour, "stroke-width": e.width, "stroke-linecap": "round" }));
    if (e.dot) svg.append(APP.svgElement("circle", { cx: 13, cy: 6, r: 4.5, fill: e.colour, stroke: "#fff", "stroke-width": 2 }));
  }
  return svg;
};

// The key of a chart of rents, for phones: per entry its swatch and its name, one entry below the other in the order of
// c.key (the order of the line ends, then the old base). The names of the references are grey (class ref).
APP.rentsKey = function (c) {
  const div = document.createElement("div");
  div.className = "key rents-key";
  for (const e of c.key) {
    const span = document.createElement("span"), name = document.createElement("span");
    if (e.kind === "reference") name.className = "ref";
    name.textContent = e.name;
    span.append(APP.rentsSwatch(e, false), name);
    div.append(span);
  }
  return div;
};

// The note under a chart for the wide drawing: the old-base swatch in front of the text of c.old_base_note
APP.rentsNote = function (c) {
  const p = document.createElement("p");
  p.className = "old-base-note";
  p.append(APP.rentsSwatch(c.key.find((e) => e.kind === "old_base")), c.old_base_note);
  return p;
};

// The tooltip of a year: the head, one row per series (a swatch in the colour, width and dash of its line, the value,
// the label) and the note, if the year has one
APP.rentsTip = function (c, tip) {
  const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; e.textContent = text; return e; };
  const rows = tip.rows.map(([value, label, id]) => {
    const row = document.createElement("div");
    row.className = "row";
    row.append(APP.rentsSwatch(c.series.find((s) => s.id === id), true), el("b", null, value), el("span", null, label));
    return row;
  });
  return [el("div", "head", tip.head), ...rows, ...(tip.note != null ? [el("div", "note", tip.note)] : [])];
};

// One chart of the block: its title, the line below (if the chart has one), its key (phones) and the body that
// APP.layoutNewConstruction draws into, then the note of the old base (wide) if the chart has one
APP.rentsPart = function (c, body) {
  const div = document.createElement("div"), h = document.createElement("h3"), p = document.createElement("p");
  div.className = "sub";
  h.textContent = c.title;
  p.className = "explain";
  p.textContent = c.explain;
  div.append(h, ...(c.explain != null ? [p] : []), APP.rentsKey(c), body);
  if (c.old_base_note) div.append(APP.rentsNote(c));
  return div;
};

APP.newConstructionKey = function (n) {
  const div = document.createElement("div");
  div.className = "key";
  for (const [cls, text] of [["solid", n.key.new], ["subsidised", n.key.subsidised], ["hatched", n.key.provisional],
    ["dashed", n.key.conversions]]) {
    const span = document.createElement("span"), i = document.createElement("i");
    i.className = cls;
    span.append(i, text);
    div.append(span);
  }
  return div;
};

// Both figures are built once; APP.layoutNewConstruction draws the charts into them. `view` gives the id of the figure
// (APP.chartFigure), `info` the key of its ⓘ. The ⓘ closes the lead line, its protocol opens below it. The last word
// and the ⓘ stand in one span that does not wrap: Chrome breaks before a button even after a no-break space. The block
// of rents has its own ⓘ, its two charts and one source line under both. That line names its sources itself
// („Quellen:“), so it has no „Quelle:“ in front.
APP.infoFigure = function (view, texts, info, ...parts) {
  const content = document.createElement("div");
  content.append(...parts);
  const fig = APP.chartFigure(texts, content, view), lead = fig.querySelector(".lead"), words = lead.textContent.split(" ");
  const last = words.pop();
  lead.textContent = words.join(" ") + " ";
  lead.insertAdjacentHTML("beforeend", `<span class="keep">${APP.escape(last)}\u00a0${APP.infoButton(info)}</span>`);
  lead.insertAdjacentHTML("afterend", APP.infoBlock(texts.info, info));
  return fig;
};
APP.drawNewConstruction = function () {
  const n = APP.data.new_construction, r = n.rents, view = document.getElementById("view-new-construction");
  view.style.setProperty("--subsidised", n.color);
  const inner = document.createElement("div");
  inner.className = "history";
  APP.newConstructionBody = document.createElement("div");
  APP.rentsBodies = r.charts.map(() => document.createElement("div"));
  const rents = APP.infoFigure("new_construction", { title: r.title, lead: r.lead, info: r.info, link: r.link }, "housing-rents",
    ...r.charts.map((c, k) => APP.rentsPart(c, APP.rentsBodies[k])));
  const source = document.createElement("p");
  source.className = "source";
  source.textContent = r.source;
  rents.append(source);
  inner.append(APP.infoFigure("new_construction", { title: n.title, lead: n.lead, source: n.source, info: n.info, link: n.link }, "new-construction",
    APP.newConstructionKey(n), APP.newConstructionBody), rents);
  view.replaceChildren(inner);
  APP.bindInfo(view);
  APP.chartTip(view);
  APP.newConstructionDrawn = true;
  APP.layoutNewConstruction();
};

// The key of the rents serves phones, the note of the old base the wide drawing: set on every layout, also when the
// width leaves the drawing as it is.
APP.layoutNewConstruction = function () {
  const room = APP.newConstructionBody.clientWidth, W = room >= APP.CONSTRUCTION_WIDE ? 760 : room;
  if (!room) return;
  const narrow = W < APP.CONSTRUCTION_WIDE, view = document.getElementById("view-new-construction");
  view.querySelectorAll(".rents-key").forEach((key) => { key.hidden = !narrow; });
  view.querySelectorAll(".old-base-note").forEach((note) => { note.hidden = narrow; });
  if (W === APP.newConstructionWidth) return;
  APP.newConstructionWidth = W;
  APP.newConstructionBody.replaceChildren(APP.newConstructionChart(APP.data.new_construction, W));
  APP.data.new_construction.rents.charts.forEach((c, k) => APP.rentsBodies[k].replaceChildren(APP.rentsChart(c, W)));
  document.querySelector("#view-new-construction .chart-tip").hidden = true;
};
let newConstructionResize;
window.addEventListener("resize", () => {
  clearTimeout(newConstructionResize);
  newConstructionResize = setTimeout(() => { if (APP.newConstructionDrawn) APP.layoutNewConstruction(); }, 150);
});
