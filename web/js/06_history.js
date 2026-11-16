"use strict";
// View "Trend" (pipeline/use_cases/ownership_history/README.md): four charts of ownership as plain SVG
const SVG_NS = "http://www.w3.org/2000/svg";
APP.svgElement = function (tag, attrs, text) {
  const e = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs || {})) e.setAttribute(k, v);
  if (text != null) e.textContent = text;
  return e;
};

// Text inside a bar only if it reaches 4.5:1 and fits with 4 px on each side; else the tooltip carries the value.
// The colour of the text and its contrast come from Python (group.label_color, group.label_contrast).
// The width is estimated (8 px per character at 14 px), because the SVG is not in the page yet.
APP.barLabel = function (parent, x, y, w, h, text, group) {
  if (group.label_contrast < 4.5 || text.length * 8 + 8 > w) return;
  parent.append(APP.svgElement("text", { x: x + w / 2, y: y + h / 2, dy: "0.35em", "text-anchor": "middle",
    class: "in-bar", style: `fill:${group.label_color}` }, text));
};

// `view` names the view of the figure; with the link of the chart it gives the id of a direct link (docs/design.md)
APP.chartFigure = function (texts, content, view) {
  const fig = document.createElement("figure");
  fig.className = "chart";
  if (view && texts.link) fig.id = `${APP.viewLink(view)}-${texts.link}`;
  const h = document.createElement("h2");
  h.textContent = APP.keepUnits(texts.title);
  fig.append(h);
  if (texts.lead) { const p = document.createElement("p"); p.className = "lead"; p.textContent = APP.keepUnits(texts.lead); fig.append(p); }
  fig.append(content);
  if (texts.caveat) { const p = document.createElement("p"); p.className = "caveat"; p.textContent = APP.keepUnits(texts.caveat); fig.append(p); }
  if (texts.source) { const p = document.createElement("p"); p.className = "source"; p.textContent = "Quelle: " + texts.source; fig.append(p); }
  return fig;
};

APP.keyLine = function (entries) {
  const div = document.createElement("div");
  div.className = "key";
  for (const [title, color] of entries) {
    const span = document.createElement("span");
    const i = document.createElement("i");
    i.style.background = color;
    span.append(i, title);
    div.append(span);
  }
  return div;
};

APP.groupsInOrder = (h) => h.bar_order.map((id) => h.groups.find((g) => g.id === id));
// The description of a group, with its examples where they fit the year (catalog GROUP_TEXTS)
APP.groupNote = (g, examples) => [g.about, examples ? g.example : ""].filter(Boolean).map((t) => " " + t).join("");

// Chart 1: per year a bar of buildings ("Häuser") above a bar of dwellings, joined by bands. A black line follows the
// boundary between the two sectors (catalog SECTORS); at its foot their labels face each other in their main colours.
// In 2022 a dashed line marks the boundary of 2011 on the dwellings.
// Narrow (APP.layoutHistory): year and „Häuser“ above the pair, „Wohnungen“ below it, the sector labels a row lower.
// If „Gemeinschaft“ has no room right of the boundary, the line bends to the point where both labels fit.
APP.housesChart = function (h, W) {
  const narrow = W < APP.WIDE, x0 = narrow ? 0 : 96, width = narrow ? W : 660, barH = 34, band = 56,
    sectorH = narrow ? 64 : 30, lift = narrow ? 44 : 8, gap = sectorH + (narrow ? 20 + lift : 34), pairH = 2 * barH + band,
    overhang = 6, labelDrop = narrow ? 56 : 20;
  const groups = APP.groupsInOrder(h);
  const rows = [["Häuser", "buildings"], ["Wohnungen", "values"]];
  const svg = APP.svgElement("svg", { class: "houses", viewBox: `0 0 ${W} ${lift + 2 * pairH + gap + sectorH + 4}`, role: "img",
    "aria-label": "Anteile an Häusern und Wohnungen 2011 und 2022: " + groups.map((g) => `${g.title}: Häuser `
      + ["2011", "2022"].map((y) => APP.format(g.share.buildings[y], 1) + " %").join(" und ")
      + ", Wohnungen " + ["2011", "2022"].map((y) => APP.format(g.share.values[y], 1) + " %").join(" und ")).join("; ") });
  const bands = APP.svgElement("g", {}), bars = APP.svgElement("g", {});
  svg.append(bands, bars);
  ["2011", "2022"].forEach((year, pair) => {
    const top = lift + pair * (pairH + gap);
    bars.append(APP.svgElement("text", { x: 0, y: narrow ? top - 34 : top + barH + band / 2, dy: "0.35em", class: "year" }, year));
    const pos = rows.map(([label, key], r) => {
      const y = top + r * (barH + band);
      bars.append(APP.svgElement("text", { x: narrow ? 0 : x0 - 8, y: narrow ? (r ? y + barH + 14 : y - 14) : y + barH / 2,
        dy: "0.35em", "text-anchor": narrow ? "start" : "end" }, label));
      let x = x0;
      return groups.map((g) => {
        const s = g.share[key][year], w = (s / 100) * width;
        bars.append(APP.svgElement("rect", { x, y, width: w, height: barH, fill: g.color, stroke: "#fff", "stroke-width": 1,
          "data-tip": `${g.title} ${year}: ${APP.format(g[key][year], 0)} ${label} (${APP.format(s, 1)} %).`
            + APP.groupNote(g, year === "2022") }));
        APP.barLabel(bars, x, y, w, barH, APP.keepUnits(`${APP.format(s, 1)} %`), g);
        const p = { x, w, s };
        x += w;
        return p;
      });
    });
    // the boundary: the share of the first sector, in both bars and along the band (the first sector starts at x0)
    const sectorShare = (key, y) => h.sectors[0].share[key][y];
    const xh = x0 + (sectorShare("buildings", year) / 100) * width, xd = x0 + (sectorShare("values", year) / 100) * width;
    const y1 = top + barH, y2 = top + barH + band, m = (y1 + y2) / 2, yb = top + pairH, yLabel = yb + labelDrop;
    // the foot of the line: where both labels fit (8 px per character at 14 px, 8 px from the line)
    const labels = h.sectors.map((sec) => `${sec.title} ${APP.format(sec.share.values[year], 1)} %`);
    const xf = narrow ? Math.max(labels[0].length * 8 + 8, Math.min(xd, W - 8 - labels[1].length * 8)) : xd;
    const foot = xf === xd ? "" : ` L${xd},${yb + 22} C${xd},${yb + 30} ${xf},${yb + 30} ${xf},${yb + 38}`;
    bars.append(APP.svgElement("path", { class: "boundary", fill: "none", stroke: "#1a1a1a", "stroke-width": 2.5, "pointer-events": "none",
      d: `M${xh},${top - overhang} L${xh},${y1} C${xh},${m} ${xd},${m} ${xd},${y2}${foot} L${xf},${yb + sectorH - 4}` }));
    h.sectors.forEach((sec, k) => {
      const n = sec.count.values[year], share = sec.share.values[year];
      const grp = APP.svgElement("g", { class: "sector", "data-tip": `${sec.title} ${year}: ${APP.format(n, 0)} Wohnungen `
        + `(${APP.format(share, 1)} %). Gruppen: ` + sec.groups.map((id) => groups.find((g) => g.id === id).title).join(", ") + "." });
      // invisible strip over the label, so the tooltip is easy to hit
      const x1 = k === 0 ? x0 : xf, x2 = k === 0 ? xf : x0 + width;
      grp.append(APP.svgElement("rect", { x: x1, y: yLabel - 18, width: x2 - x1, height: 24, fill: "#000", "fill-opacity": 0 }),
        APP.svgElement("text", { x: k === 0 ? xf - 8 : xf + 8, y: yLabel, "text-anchor": k === 0 ? "end" : "start",
          style: `font-weight:700;font-size:14px;fill:${sec.color}` }, labels[k]));
      bars.append(grp);
    });
    if (pair === 1) {
      // the boundary of 2011, on the dwellings; its text stands on the side away from the boundary of 2022
      const shares = h.sectors.map((sec) => sec.share.values["2011"]);
      const x11 = x0 + (shares[0] / 100) * width, left = x11 <= xd;
      const grp = APP.svgElement("g", { class: "previous-boundary", "data-tip": "Grenze 2011: " + h.sectors.map((sec, k) =>
        `${sec.title} ${APP.format(shares[k], 1)} %`).join(", ") + " der Wohnungen." });
      grp.append(APP.svgElement("rect", { x: x11 - 5, y: y2, width: 10, height: barH, fill: "#000", "fill-opacity": 0 }),
        APP.svgElement("line", { x1: x11, x2: x11, y1: y2 - 4, y2: yb + 4, stroke: "#6b6b6b", "stroke-width": 2, "stroke-dasharray": "3 3" }),
        APP.svgElement("text", { x: left ? x11 - 4 : x11 + 4, y: y2 - 8, "text-anchor": left ? "end" : "start",
          style: "font-size:12px;fill:#6b6b6b" }, "Grenze 2011"));
      bars.append(grp);
    }
    groups.forEach((g, i) => {
      const a = pos[0][i], b = pos[1][i], y1 = top + barH, y2 = top + barH + band, m = (y1 + y2) / 2;
      bands.append(APP.svgElement("path", { fill: g.color, opacity: g.company ? 0.55 : 0.18,
        d: `M${a.x},${y1} C${a.x},${m} ${b.x},${m} ${b.x},${y2} L${b.x + b.w},${y2} C${b.x + b.w},${m} ${a.x + a.w},${m} ${a.x + a.w},${y1} Z`,
        "data-tip": `${g.title} ${year}: ${APP.format(a.s, 1)} % der Häuser, ${APP.format(b.s, 1)} % der Wohnungen.`
          + APP.groupNote(g, year === "2022") }));
    });
  });
  const wrap = document.createElement("div");
  wrap.append(APP.keyLine(groups.map((g) => [g.title, g.color])), svg);
  return wrap;
};

// Chart 3: per group a thin arrow (share of buildings) and a thick arrow (share of dwellings), 2011 to 2022.
// Narrow (APP.layoutHistory): the name of the group stands above its arrows, the axis takes the full width.
APP.arrowsChart = function (h, W) {
  const narrow = W < APP.WIDE, x0 = narrow ? 14 : 262, width = narrow ? W - 32 : 470, max = 70, top = 6;
  const groups = APP.groupsInOrder(h);
  // per group the top of its row and the lines of its name; long names break into two lines
  const rows = [];
  let next = top;
  for (const g of groups) {
    const lines = g.lines || [g.title];
    rows.push({ y: next, lines });
    next += narrow ? lines.length * 17 + 50 : 52;
  }
  const H = next + 24;
  const x = (v) => x0 + (width * v) / max;
  const svg = APP.svgElement("svg", { class: "arrows", viewBox: `0 0 ${W} ${H}`, role: "img",
    "aria-label": "Anteile 2011 und 2022: " + groups.map((g) => `${g.title}: Häuser `
      + `${APP.format(g.share.buildings["2011"], 1)} % und ${APP.format(g.share.buildings["2022"], 1)} %, Wohnungen `
      + `${APP.format(g.share.values["2011"], 1)} % und ${APP.format(g.share.values["2022"], 1)} %`).join("; ") });
  for (let v = 0; v <= max; v += 10) {
    svg.append(APP.svgElement("line", { x1: x(v), x2: x(v), y1: top, y2: H - 22, stroke: "#eeeeee" }),
      APP.svgElement("text", { x: x(v), y: H - 6, "text-anchor": "middle", style: "fill:#6b6b6b;font-size:12px" }, v + " %"));
  }
  const arrow = (g, key, word, y, color, stroke, label, labelStyle) => {
    const a = g.share[key]["2011"], b = g.share[key]["2022"];
    const xa = x(a), xb = x(b), dir = xb >= xa ? 1 : -1;
    const grp = APP.svgElement("g", { "data-tip": `${g.title}, ${word}: ${APP.format(g[key]["2011"], 0)} → `
      + `${APP.format(g[key]["2022"], 0)} (${g.change[key]}); Anteil ${APP.format(a, 1)} → ${APP.format(b, 1)} %.`
      + APP.groupNote(g, true) });
    // invisible strip so that thin arrows are easy to hit
    grp.append(APP.svgElement("rect", { x: Math.min(xa, xb) - 8, y: y - 9, width: Math.abs(xb - xa) + 16, height: 18, fill: "#000", "fill-opacity": 0 }));
    // an arrow shorter than its head would cover the circle: then a dot marks 2022, the tooltip holds the numbers
    if (Math.abs(xb - xa) >= 14) {
      grp.append(APP.svgElement("line", { x1: xa, y1: y, x2: xb - dir * 7, y2: y, stroke: color, "stroke-width": stroke }),
        APP.svgElement("circle", { cx: xa, cy: y, r: 4, fill: "#fff", stroke: color, "stroke-width": 2 }),
        APP.svgElement("path", { d: `M${xb},${y} l${-10 * dir},${-(stroke + 3)} l0,${2 * (stroke + 3)} z`, fill: color }));
    } else {
      grp.append(APP.svgElement("circle", { cx: xa, cy: y, r: 4, fill: "#fff", stroke: color, "stroke-width": 2 }),
        APP.svgElement("circle", { cx: xb, cy: y, r: 3, fill: color }));
    }
    // label right of the arrow; if it would leave the chart, left of it
    const right = Math.max(xa, xb) + 10, fitsRight = right + label.length * 7.6 <= W - 2;
    grp.append(APP.svgElement("text", { x: fitsRight ? right : Math.min(xa, xb) - 10, y, dy: "0.35em",
      "text-anchor": fitsRight ? "start" : "end", class: "arrow-label", style: labelStyle }, label));
    svg.append(grp);
  };
  groups.forEach((g, i) => {
    const { y, lines } = rows[i], bold = g.company ? "font-weight:700;" : "", ya = narrow ? y + lines.length * 17 + 10 : y + 12;
    lines.forEach((line, k) => svg.append(APP.svgElement("text", { x: narrow ? 0 : x0 - 14,
      y: narrow ? y + 9 + k * 17 : y + 22 + (k - (lines.length - 1) / 2) * 17,
      dy: "0.35em", "text-anchor": narrow ? "start" : "end", class: "row-label", style: bold }, line)));
    const b22 = g.share.buildings["2022"], d22 = g.share.values["2022"];
    arrow(g, "buildings", "Häuser", ya, "#9a9a9a", 1.5, `${APP.format(b22, 1)} %`, "fill:#6b6b6b;font-size:12px");
    arrow(g, "values", "Wohnungen", ya + 20, g.line_color, 4,
      `${APP.format(d22, 1)} % (${APP.format(g.values["2022"], 0)})`, bold);
  });
  const key = document.createElement("div");
  key.className = "key";
  key.textContent = h.charts.arrows.key;
  const wrap = document.createElement("div");
  wrap.append(key, svg);
  return wrap;
};

// Bar pairs 2011 (light) and 2022 (dark) per row; rows: [{label, values: {2011, 2022}, tips: {2011, 2022}}]
// Narrow (APP.layoutHistory): the label stands above its pair, the bars take the full width.
APP.pairBars = function (rows, cls, ariaLabel, W, unit, labelW = 130) {
  // narrow: a bar per year of 16 px, so the numbers beside the bars keep apart
  const narrow = W < APP.WIDE, x0 = narrow ? 0 : labelW + 8, width = W - x0 - (narrow ? 50 : 82), bar = narrow ? 16 : 13,
    head = narrow ? 20 : 0, rowH = head + 2 * bar + 12;
  const max = Math.max(...rows.flatMap((r) => [r.values["2011"], r.values["2022"]]));
  const colors = { 2011: "#bdbdbd", 2022: "#4d4d4d" };
  const svg = APP.svgElement("svg", { class: cls, viewBox: `0 0 ${W} ${rows.length * rowH + 4}`, role: "img", "aria-label": ariaLabel });
  rows.forEach((r, i) => {
    const yTop = 2 + i * rowH + head;
    svg.append(APP.svgElement("text", { x: narrow ? 0 : labelW, y: narrow ? yTop - 10 : yTop + bar, dy: "0.35em",
      "text-anchor": narrow ? "start" : "end" }, r.label));
    ["2011", "2022"].forEach((year, k) => {
      const w = (r.values[year] / max) * width, yy = yTop + k * bar;
      svg.append(APP.svgElement("rect", { x: x0, y: yy, width: Math.max(w, 1), height: bar - 1, fill: colors[year], "data-tip": r.tips[year] }),
        APP.svgElement("text", { x: x0 + w + 6, y: yy + bar / 2, dy: "0.3em", style: "font-size:12px" }, APP.format(r.values[year], 0)));
    });
  });
  const wrap = document.createElement("div");
  wrap.append(APP.keyLine([[`${unit} 2011`, colors[2011]], [`${unit} 2022`, colors[2022]]]), svg);
  return wrap;
};

// Chart 4: dwellings of private companies by size of the building
APP.sizesChart = function (h, W) {
  const company = h.company;
  const rows = h.sizes.map((s) => ({ label: s.label, values: s.company, tips: Object.fromEntries(["2011", "2022"].map((y) => {
    let tip = `${company.title} ${y}: ${APP.format(s.company[y], 0)} Wohnungen in Häusern mit ${s.long}. `
      + `Das sind ${APP.format(s.company_share[y], 1)} % aller Wohnungen dort.`;
    if (s.size === "13_plus" && y === "2022") {
      tip += " " + h.charts.sizes.tip_large_text;
    }
    return [y, tip];
  })) }));
  return APP.pairBars(rows, "sizes", "Wohnungen privater Unternehmen nach Größe des Hauses: " + h.sizes.map((s) =>
    `${s.label} ${APP.format(s.company["2011"], 0)} (2011) und ${APP.format(s.company["2022"], 0)} (2022)`).join("; "), W, "Wohnungen");
};

// Chart 2: company buildings by year of construction
APP.decadesChart = function (h, W) {
  const company = h.company;
  const rows = h.decades.map((d) => {
    // inside a sentence the label starts in lower case ("Baujahr vor 1919"); the row label stays as it is
    const era = d.label[0].toLowerCase() + d.label.slice(1);
    return { label: d.label, values: d.values, tips: {
      2011: `${company.title} 2011: ${APP.format(d.values["2011"], 0)} Häuser, Baujahr ${era}`,
      2022: `${company.title} 2022: ${APP.format(d.values["2022"], 0)} Häuser, Baujahr ${era} (2011: ${APP.format(d.values["2011"], 0)})` } };
  });
  return APP.pairBars(rows, "decades", "Häuser privater Unternehmen nach Baujahr: " + h.decades.map((d) =>
    `${d.label} ${APP.format(d.values["2011"], 0)} (2011) und ${APP.format(d.values["2022"], 0)} (2022)`).join("; "), W, "Häuser");
};

// One tooltip for all charts: mouse shows it while over an element with data-tip; a tap shows it, a tap elsewhere
// or scrolling hides it. An element in APP.tipContent shows the nodes its function builds (head, rows with a swatch,
// note); every other element shows the text of its data-tip.
APP.tipContent = new WeakMap();
APP.chartTip = function (view) {
  const tip = document.createElement("div");
  tip.className = "chart-tip";
  tip.hidden = true;
  view.append(tip);
  let pointer = "mouse";
  const show = (target, x, y) => {
    const content = APP.tipContent.get(target);
    if (content) tip.replaceChildren(...content()); else tip.textContent = target.dataset.tip;
    tip.hidden = false;
    const w = tip.offsetWidth, h = tip.offsetHeight, touch = pointer === "touch";
    let top = touch ? y - h - 16 : y + 16;
    if (top < 8) top = y + 24;
    if (top + h > window.innerHeight - 8) top = Math.max(8, y - h - 16);
    tip.style.left = Math.max(8, Math.min(x + (touch ? -w / 2 : 14), window.innerWidth - w - 8)) + "px";
    tip.style.top = top + "px";
  };
  view.addEventListener("pointerdown", (e) => { pointer = e.pointerType; });
  view.addEventListener("pointermove", (e) => {
    if (e.pointerType === "touch") return;
    pointer = e.pointerType;
    const t = e.target.closest("[data-tip]");
    if (t) show(t, e.clientX, e.clientY); else tip.hidden = true;
  });
  view.addEventListener("pointerleave", (e) => { if (e.pointerType !== "touch") tip.hidden = true; });
  view.addEventListener("click", (e) => {
    if (pointer !== "touch") return;
    const t = e.target.closest("[data-tip]");
    if (t) show(t, e.clientX, e.clientY); else tip.hidden = true;
  });
  // capture: scroll events do not bubble
  view.addEventListener("scroll", () => { tip.hidden = true; }, { capture: true, passive: true });
};

// The texts of the figures are built once; APP.layoutHistory draws the charts into them
APP.drawHistory = function () {
  const h = APP.data.history, view = document.getElementById("view-history");
  const inner = document.createElement("div");
  inner.className = "history";
  APP.historyCharts = [[h.charts.houses, APP.housesChart], [h.charts.decades, APP.decadesChart],
    [h.charts.arrows, APP.arrowsChart], [h.charts.sizes, APP.sizesChart]].map(([texts, draw]) => {
    const body = document.createElement("div");
    inner.append(APP.chartFigure(texts, body, "history"));
    return { body, draw };
  });
  const source = document.createElement("p");
  source.className = "source";
  source.textContent = APP.keepUnits("Quelle: " + h.source);
  inner.append(source);
  view.replaceChildren(inner);
  APP.chartTip(view);
  APP.historyDrawn = true;
  APP.layoutHistory();
};

// From APP.WIDE px of room a chart is one drawing 760 units wide that scales with the window. Below, it is drawn
// at the room it has, in px, so its text keeps its size and nothing scrolls sideways. A new width redraws the charts.
APP.WIDE = 600;
APP.layoutHistory = function () {
  const room = APP.historyCharts[0].body.clientWidth;
  const W = room >= APP.WIDE ? 760 : room;
  // hidden view (width 0) or the same drawing: nothing to do
  if (!room || W === APP.historyWidth) return;
  APP.historyWidth = W;
  for (const { body, draw } of APP.historyCharts) body.replaceChildren(draw(APP.data.history, W));
  document.querySelector("#view-history .chart-tip").hidden = true;
};
// turning the phone or resizing the window: redraw once the size has settled
let historyResize;
window.addEventListener("resize", () => {
  clearTimeout(historyResize);
  historyResize = setTimeout(() => { if (APP.historyDrawn) APP.layoutHistory(); }, 150);
});
