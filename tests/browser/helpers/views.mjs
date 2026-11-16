// Helpers of the chart views Trend, Neubau and Miete (desktop/trend.spec.mjs, desktop/new-construction.spec.mjs,
// desktop/rent-burden.spec.mjs; the drawn widths also mobile/phone.spec.mjs).
import { frames } from "./common.mjs";

// A known state of the map behind a chart view, set before the view opens: tab Stadt, Bezirke, OWN_PUBLIC.
const mapState = (page) => page.evaluate(() => { APP.openTab("city"); APP.setLevel("district"); APP.setIndicator("OWN_PUBLIC"); });

// open the view Trend by its switch in the header
export const openTrend = async (page) => {
  await mapState(page);
  await page.click('#views button[data-view="history"]');
};

// open the view Neubau by its switch in the header
export const openNewConstruction = async (page) => {
  await mapState(page);
  await page.click('#views button[data-view="new_construction"]');
};

// open the view Miete by its switch in the header
export const openRentBurden = async (page) => {
  await mapState(page);
  await page.click('#views button[data-view="rent_burden"]');
};

// Trend: every chart drawn at the given width in units; 0: at its own width in px
export const historyDrawnAt = (page, units) => page.waitForFunction((u) => [...document.querySelectorAll("#view-history svg")].every((s) =>
  Math.abs(s.viewBox.baseVal.width - (u || s.getBoundingClientRect().width)) < 1), units, { timeout: 3000 }).then(() => true, () => false);

// Trend: hover the element and read the chart tooltip (null if hidden)
export const tipText = async (page, locator) => {
  await locator.evaluate((e) => e.scrollIntoView({ block: "center" }));
  // the scroll event comes a frame later and hides the tooltip; wait for it before the pointer moves
  await frames(page);
  const box = await locator.boundingBox();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  return page.evaluate(() => { const t = document.querySelector(".chart-tip"); return t.hidden ? null : t.textContent; });
};

// Neubau: the figure of rents, prices and wages
export const RENTS_FIG = "#view-new-construction figure:nth-of-type(2)";

// "#rrggbb" as getComputedStyle writes it
export const rgb = (hex) => `rgb(${[1, 3, 5].map((k) => parseInt(hex.slice(k, k + 2), 16)).join(", ")})`;

// Neubau: the column chart drawn at the given width in units; 0: at its own width in px
export const drawnNc = (page, units) => page.waitForFunction((u) => { const s = document.querySelector("#view-new-construction svg.construction");
  return s && Math.abs(s.viewBox.baseVal.width - (u || s.getBoundingClientRect().width)) < 1; }, units, { timeout: 3000 }).then(() => true, () => false);

// Neubau: both charts of rents drawn at the given width in units; 0: at their own width in px
export const drawnRents = (page, units) => page.waitForFunction((u) => { const ss = [...document.querySelectorAll("#view-new-construction svg.rents")];
  return ss.length === 2 && ss.every((s) => Math.abs(s.viewBox.baseVal.width - (u || s.getBoundingClientRect().width)) < 1); }, units, { timeout: 3000 }).then(() => true, () => false);

// Neubau: the key serves phones only and the note under chart 1 the wide drawing: both switch with the layout
export const rentsShown = (page) => page.evaluate(() => [...document.querySelectorAll("#view-new-construction div.sub")].map((sub) => {
  const shown = (e) => (e ? getComputedStyle(e).display !== "none" : null);
  return { key: shown(sub.querySelector(".key.rents-key")), note: shown(sub.querySelector("p.old-base-note")) }; }));
export const shownRight = (got, wide) => got.length === 2 && got.every((g) => g.key === !wide) && got[0].note === wide && got[1].note === null;

// Neubau: the ⓘ of each figure stays on the line of the last word of its lead
export const infoKept = (page) => page.evaluate(() => { const keeps = [...document.querySelectorAll("#view-new-construction .lead .keep")];
  return keeps.length === 2 && keeps.every((k) => { const b = k.querySelector(".info-button").getBoundingClientRect(), r = document.createRange();
    r.setStart(k.firstChild, 0); r.setEnd(k.firstChild, k.firstChild.length - 1); const w = r.getBoundingClientRect();
    return w.width > 0 && Math.abs((b.top + b.bottom) / 2 - (w.top + w.bottom) / 2) < 6; }); });

// Neubau: everything the checks read of the figure of rents (null if it has not two svg.rents)
export const rentsLayout = (page) => page.evaluate((fig) => {
  const f = document.querySelector(fig), num = (e, a) => parseFloat(e.getAttribute(a));
  if (!f || f.querySelectorAll("svg.rents").length !== 2) return null;
  const box = (e) => { const b = e.getBoundingClientRect(); return { left: b.left, right: b.right, top: b.top, bottom: b.bottom }; };
  const vertices = (p) => p.getAttribute("d").match(/-?[\d.]+,-?[\d.]+/g).map((xy) => xy.split(",").map(Number));
  const charts = [...f.querySelectorAll("div.sub")].map((sub) => {
    const svg = sub.querySelector("svg.rents"), frame = box(svg), w = frame.right - frame.left;
    const dot = (c) => ({ series: c.dataset.series, x: num(c, "cx"), y: num(c, "cy"), fill: getComputedStyle(c).fill, stroke: getComputedStyle(c).stroke });
    return { title: sub.querySelector("h3")?.textContent, explain: sub.querySelector(".explain")?.textContent,
      key: [...sub.querySelectorAll(".key > span")].map((s) => { const sw = s.querySelector("svg.swatch"), line = sw?.querySelector("line"), rect = sw?.querySelector("rect");
        return { text: s.textContent.trim(), weight: getComputedStyle(s.lastElementChild).fontWeight, color: getComputedStyle(s.lastElementChild).color,
          swatch: line?.getAttribute("stroke"), swatchDash: line?.getAttribute("stroke-dasharray"), swatchBand: rect?.getAttribute("fill"),
          swatchEdge: line ? (num(line, "y1") < 6 ? "top" : "bottom") : null, swatchDots: sw?.querySelectorAll("circle").length }; }),
      keyBox: (() => { const k = sub.querySelector(".key"); return k && { cls: k.className, display: getComputedStyle(k).display }; })(),
      note: (() => { const p = sub.querySelector("p.old-base-note"); return p && { text: p.textContent.trim(), display: getComputedStyle(p).display,
        size: getComputedStyle(p).fontSize, color: getComputedStyle(p).color, afterSvg: !!(svg.compareDocumentPosition(p) & Node.DOCUMENT_POSITION_FOLLOWING),
        below: p.getBoundingClientRect().top >= frame.bottom - 0.5, hollow: p.querySelectorAll("svg.swatch circle").length }; })(),
      bands: [...svg.querySelectorAll("path.band")].map((p) => ({ fill: getComputedStyle(p).fill, points: vertices(p),
        afterGrid: [...svg.querySelectorAll("line.grid")].every((g) => !!(g.compareDocumentPosition(p) & Node.DOCUMENT_POSITION_FOLLOWING)),
        beforeLines: [...svg.querySelectorAll("path[data-series], line.break, circle.dot, text.end")].every((o) => !!(p.compareDocumentPosition(o) & Node.DOCUMENT_POSITION_FOLLOWING)) })),
      yearFills: [...svg.querySelectorAll("text.year")].map((t) => ({ year: Number(t.textContent), fill: getComputedStyle(t).fill, weight: getComputedStyle(t).fontWeight })),
      label: svg.getAttribute("aria-label"), role: svg.getAttribute("role"), roles: svg.querySelectorAll("g[role], g[aria-label]").length,
      units: svg.viewBox.baseVal.width,
      paths: [...svg.querySelectorAll("path:not(.band)")].map((p) => ({ series: p.dataset.series, old: p.classList.contains("old"), stroke: p.getAttribute("stroke"),
        width: num(p, "stroke-width"), dash: getComputedStyle(p).strokeDasharray, cap: getComputedStyle(p).strokeLinecap, join: getComputedStyle(p).strokeLinejoin,
        points: vertices(p) })),
      groups: [...svg.querySelectorAll("g[data-tip]:not(.old)")].map((g) => { const r = g.querySelector("rect.hit");
        return { tip: g.dataset.tip, x: num(r, "x") + num(r, "width") / 2, top: num(r, "y"), bottom: num(r, "y") + num(r, "height"),
          fill: getComputedStyle(r).fill, dots: [...g.querySelectorAll("circle.dot")].map(dot) }; }),
      old: [...svg.querySelectorAll("g.old[data-tip]")].map((g) => ({ tip: g.dataset.tip, ...dot(g.querySelector("circle.dot")) })),
      grid: [...svg.querySelectorAll("line.grid")].map((l) => num(l, "y1")), ticks: [...svg.querySelectorAll("text.tick")].map((t) => t.textContent),
      ends: [...svg.querySelectorAll("text.end")].map((t) => ({ series: t.dataset.series, text: t.textContent, y: num(t, "y"), b: box(t),
        fill: getComputedStyle(t).fill, weight: getComputedStyle(t).fontWeight,
        nameWeight: t.querySelector("tspan") ? getComputedStyle(t.querySelector("tspan")).fontWeight : null })),
      leaders: svg.querySelectorAll("polyline.leader").length,
      breaks: [...svg.querySelectorAll("line.break")].map((l) => ({ x: num(l, "x1"), dash: getComputedStyle(l).strokeDasharray })),
      notes: [...svg.querySelectorAll("text.note")].map((t) => t.textContent), years: [...svg.querySelectorAll("text.year")].map((t) => t.textContent),
      width: svg.hasAttribute("width"),
      texts: [...svg.querySelectorAll("text")].map((t) => { const b = box(t); return { text: t.textContent, px: parseFloat(getComputedStyle(t).fontSize) * w / svg.viewBox.baseVal.width,
        inside: b.left >= frame.left - 0.5 && b.right <= frame.right + 0.5 && b.top >= frame.top - 0.5 && b.bottom <= frame.bottom + 0.5 }; }) };
  });
  return { charts, title: f.querySelector("h2").textContent, lead: f.querySelector(".lead").textContent.replace(/\u00a0/g, " "),
    sources: [...f.querySelectorAll(".source")].map((p) => p.textContent), info: !!f.querySelector('.lead .info-button[data-info="housing-rents"]'),
    columns: !!f.querySelector("svg.construction") };
}, RENTS_FIG);

// per series the paths of its line as drawn from the payload: through the years with a value; a series of the old
// base breaks at the break year
export const wantPaths = (c, s, xOf, yOf) => {
  const pts = c.years.map((y, i) => [i, s.values[i]]).filter(([, v]) => v != null), cut = c.old_base?.[s.id] ? c.years.indexOf(c.break.year) : -1;
  return (cut < 0 ? [pts] : [pts.filter(([i]) => i < cut), pts.filter(([i]) => i >= cut)]).map((part) => part.map(([i, v]) => [xOf(i), yOf(v)]));
};
export const near = (p, q) => Math.abs(p[0] - q[0]) < 0.01 && Math.abs(p[1] - q[1]) < 0.01;
export const samePath = (p, q) => p.length === q.length && p.every((xy, k) => near(xy, q[k]));

// Miete: the two drawings (the wage bars, the bars of tenants) drawn at the given width in units; 0: at their own width
// in px
export const drawnRentBurden = (page, units) => page.waitForFunction((u) => { const ss = [...document.querySelectorAll("#view-rent-burden svg.wage, #view-rent-burden svg.burden")];
  return ss.length === 2 && ss.every((s) => Math.abs(s.viewBox.baseVal.width - (u || s.getBoundingClientRect().width)) < 1); }, units, { timeout: 3000 }).then(() => true, () => false);

// Miete: hover the element and read the tooltip of the view (null if hidden)
export const rentTipText = async (page, locator) => {
  await locator.evaluate((e) => e.scrollIntoView({ block: "center" }));
  // the scroll event comes a frame later and hides a chart tooltip; wait for it before the pointer moves
  await frames(page);
  const box = await locator.boundingBox();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  return page.evaluate(() => { const t = document.querySelector("#view-rent-burden .chart-tip"); return t.hidden ? null : t.textContent; });
};
